"""
Centralized Evidence Logger for Compliance Decisions

This module provides a unified logging interface for all agents and the RAG pipeline
to log compliance decisions with complete traceability and audit-ready transparency.
"""

import json
import logging
import os
import re
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EvidenceLogger:
    """
    Centralized evidence logger for compliance decisions.

    Features:
    - JSONL output with complete traceability
    - Redaction of sensitive information
    - File rotation and retention
    - Concurrency-safe appends
    - Performance monitoring
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the evidence logger with configuration."""
        self.config = config
        self.evidence_config = config.get("evidence", {})

        # Core settings
        self.enabled = self.evidence_config.get("enabled", True)
        self.sink_path = self.evidence_config.get("sink", {}).get(
            "path", "data/evidence"
        )
        self.rotation = self.evidence_config.get("sink", {}).get("rotation", "by_day")
        self.size_mb = self.evidence_config.get("sink", {}).get("size_mb", 100)
        self.retention_days = self.evidence_config.get("retention_days", 90)
        self.flush_interval = self.evidence_config.get("flush_interval", 1)
        self.sync_writes = self.evidence_config.get("sync", False)

        # Redaction settings
        self.redact_enabled = self.evidence_config.get("redact", {}).get(
            "enabled", True
        )
        self.redact_patterns = self.evidence_config.get("redact", {}).get(
            "patterns",
            [
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
                r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # Phone
                r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",  # Credit card
                r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b",  # IBAN
                r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
                r"\b[A-Za-z0-9]{20,}\b",  # Long tokens/keys
            ],
        )

        # Performance tracking
        self.write_count = 0
        self.total_write_time = 0.0
        self.last_rotation_check = time.time()

        # Thread safety
        self._lock = threading.Lock()
        self._current_file = None
        self._current_file_path = None

        # Initialize sink directory
        if self.enabled:
            self._ensure_sink_directory()
            self._cleanup_old_files()

    def _ensure_sink_directory(self):
        """Ensure the sink directory exists."""
        Path(self.sink_path).mkdir(parents=True, exist_ok=True)

    def _get_current_file_path(self) -> str:
        """Get the current file path based on rotation strategy."""
        if self.rotation == "by_day":
            date_str = datetime.now().strftime("%Y-%m-%d")
            return os.path.join(self.sink_path, f"{date_str}.jsonl")
        else:  # by_size
            return os.path.join(self.sink_path, "evidence.jsonl")

    def _should_rotate_file(self) -> bool:
        """Check if file rotation is needed."""
        if not self._current_file_path:
            return True

        if self.rotation == "by_day":
            current_date = datetime.now().strftime("%Y-%m-%d")
            file_date = os.path.basename(self._current_file_path).split(".")[0]
            return current_date != file_date
        else:  # by_size
            if not os.path.exists(self._current_file_path):
                return True
            file_size_mb = os.path.getsize(self._current_file_path) / (1024 * 1024)
            return file_size_mb >= self.size_mb

    def _rotate_file(self):
        """Rotate to a new file if needed."""
        if not self._should_rotate_file():
            return

        # Close current file
        if self._current_file:
            self._current_file.close()
            self._current_file = None

        # Open new file
        self._current_file_path = self._get_current_file_path()
        self._current_file = open(self._current_file_path, "a", encoding="utf-8")
        logger.info(f"Rotated evidence log to: {self._current_file_path}")

    def _cleanup_old_files(self):
        """Clean up files older than retention period."""
        if not self.retention_days:
            return

        cutoff_date = datetime.now() - timedelta(days=self.retention_days)

        try:
            for file_path in Path(self.sink_path).glob("*.jsonl"):
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_date:
                    file_path.unlink()
                    logger.info(f"Deleted old evidence file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup old files: {e}")

    def _redact_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive information from the data."""
        if not self.redact_enabled:
            return data

        redacted_data = data.copy()

        def redact_value(value):
            if isinstance(value, str):
                for pattern in self.redact_patterns:
                    value = re.sub(pattern, "[REDACTED]", value)
                return value
            elif isinstance(value, dict):
                return {k: redact_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [redact_value(v) for v in value]
            else:
                return value

        return redact_value(redacted_data)

    def log_decision(self, evidence_data: Dict[str, Any]) -> bool:
        """
        Log a compliance decision with complete traceability.

        Args:
            evidence_data: Dictionary containing evidence fields

        Returns:
            bool: True if logging succeeded, False otherwise
        """
        if not self.enabled:
            return True

        try:
            # Ensure required fields
            required_fields = [
                "request_id",
                "timestamp_iso",
                "agent_name",
                "decision_flag",
                "reasoning_text",
            ]

            for field in required_fields:
                if field not in evidence_data:
                    logger.warning(f"Missing required field: {field}")
                    evidence_data[field] = f"MISSING_{field.upper()}"

            # Add default values for optional fields
            evidence_data.setdefault("pipeline_version", "1.0.0")
            evidence_data.setdefault("environment", "dev")
            evidence_data.setdefault("confidence", 0.0)
            evidence_data.setdefault("timings_ms", {})
            evidence_data.setdefault("error_info", None)

            # Ensure timestamp is present
            if (
                "timestamp_iso" not in evidence_data
                or evidence_data["timestamp_iso"] == "MISSING_TIMESTAMP_ISO"
            ):
                evidence_data["timestamp_iso"] = datetime.now().isoformat()

            # Redact sensitive data
            redacted_data = self._redact_sensitive_data(evidence_data)

            # Convert to JSON line
            json_line = json.dumps(redacted_data, ensure_ascii=False, default=str)

            # Write to file with thread safety
            with self._lock:
                # Rotate file if needed
                self._rotate_file()

                # Ensure file is open
                if not self._current_file:
                    self._current_file_path = self._get_current_file_path()
                    self._current_file = open(
                        self._current_file_path, "a", encoding="utf-8"
                    )

                # Write the line
                start_time = time.time()
                self._current_file.write(json_line + "\n")

                # Flush if configured
                if self.flush_interval == 1:
                    self._current_file.flush()

                # Sync if configured
                if self.sync_writes:
                    os.fsync(self._current_file.fileno())

                write_time = (time.time() - start_time) * 1000
                self.write_count += 1
                self.total_write_time += write_time

                logger.debug(f"Logged evidence in {write_time:.2f}ms")

                return True

        except Exception as e:
            logger.error(f"Failed to log evidence: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get logger statistics."""
        return {
            "enabled": self.enabled,
            "write_count": self.write_count,
            "avg_write_time_ms": self.total_write_time / max(self.write_count, 1),
            "current_file": self._current_file_path,
            "sink_path": self.sink_path,
            "rotation": self.rotation,
            "retention_days": self.retention_days,
        }

    def close(self):
        """Close the logger and cleanup resources."""
        if self._current_file:
            self._current_file.close()
            self._current_file = None


# Global logger instance
_evidence_logger = None


def get_evidence_logger(config: Optional[Dict[str, Any]] = None) -> EvidenceLogger:
    """Get the global evidence logger instance."""
    global _evidence_logger

    if _evidence_logger is None:
        if config is None:
            # Load default config
            try:
                import yaml

                config_path = "config.yaml"
                if os.path.exists(config_path):
                    with open(config_path, "r") as f:
                        config = yaml.safe_load(f)
                else:
                    config = {}
            except ImportError:
                config = {}

        _evidence_logger = EvidenceLogger(config)

    return _evidence_logger


def log_compliance_decision(evidence_data: Dict[str, Any]) -> bool:
    """Convenience function to log a compliance decision."""
    logger = get_evidence_logger()
    return logger.log_decision(evidence_data)
