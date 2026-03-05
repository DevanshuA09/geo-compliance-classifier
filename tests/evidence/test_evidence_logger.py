"""
Tests for the centralized evidence logger.
"""

import json
import os
# Add src to path for imports
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.evidence import (EvidenceLogger, get_evidence_logger,
                          log_compliance_decision)


class TestEvidenceLogger:
    """Test the EvidenceLogger class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            "evidence": {
                "enabled": True,
                "sink": {"path": self.temp_dir, "rotation": "by_day", "size_mb": 1},
                "retention_days": 7,
                "redact": {
                    "enabled": True,
                    "patterns": [
                        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
                    ],
                },
                "flush_interval": 1,
                "sync": False,
            }
        }
        self.logger = EvidenceLogger(self.config)

    def teardown_method(self):
        """Clean up test fixtures."""
        self.logger.close()
        # Clean up temp files
        for file_path in Path(self.temp_dir).glob("*.jsonl"):
            file_path.unlink()
        os.rmdir(self.temp_dir)

    def test_initialization(self):
        """Test logger initialization."""
        assert self.logger.enabled == True
        assert self.logger.sink_path == self.temp_dir
        assert self.logger.rotation == "by_day"
        assert self.logger.redact_enabled == True
        assert len(self.logger.redact_patterns) > 0

    def test_log_decision_success(self):
        """Test successful decision logging."""
        evidence_data = {
            "request_id": "test-123",
            "timestamp_iso": "2024-01-01T00:00:00",
            "agent_name": "test_agent",
            "decision_flag": True,
            "reasoning_text": "Test decision",
        }

        result = self.logger.log_decision(evidence_data)
        assert result == True

        # Check file was created
        files = list(Path(self.temp_dir).glob("*.jsonl"))
        assert len(files) == 1

        # Check content
        with open(files[0], "r") as f:
            lines = f.readlines()
            assert len(lines) == 1

            logged_data = json.loads(lines[0])
            assert logged_data["request_id"] == "test-123"
            assert logged_data["agent_name"] == "test_agent"
            assert logged_data["decision_flag"] == True

    def test_log_decision_with_missing_fields(self):
        """Test logging with missing required fields."""
        evidence_data = {
            "request_id": "test-123",
            "agent_name": "test_agent",
            # Missing timestamp_iso, decision_flag, reasoning_text
        }

        result = self.logger.log_decision(evidence_data)
        assert result == True

        # Check default values were added
        files = list(Path(self.temp_dir).glob("*.jsonl"))
        with open(files[0], "r") as f:
            logged_data = json.loads(f.readline())
            # The logger now auto-generates timestamp if missing
            assert "timestamp_iso" in logged_data
            assert "MISSING_DECISION_FLAG" in str(logged_data["decision_flag"])
            assert "MISSING_REASONING_TEXT" in logged_data["reasoning_text"]

    def test_redaction(self):
        """Test sensitive data redaction."""
        evidence_data = {
            "request_id": "test-123",
            "timestamp_iso": "2024-01-01T00:00:00",
            "agent_name": "test_agent",
            "decision_flag": True,
            "reasoning_text": "User email: test@example.com and phone: 123-456-7890",
        }

        self.logger.log_decision(evidence_data)

        # Check redaction
        files = list(Path(self.temp_dir).glob("*.jsonl"))
        with open(files[0], "r") as f:
            logged_data = json.loads(f.readline())
            assert "[REDACTED]" in logged_data["reasoning_text"]
            assert "test@example.com" not in logged_data["reasoning_text"]

    def test_file_rotation_by_day(self):
        """Test daily file rotation."""
        # Set rotation to by_day
        self.logger.rotation = "by_day"

        # Log first decision
        evidence_data = {
            "request_id": "test-1",
            "timestamp_iso": "2024-01-01T00:00:00",
            "agent_name": "test_agent",
            "decision_flag": True,
            "reasoning_text": "First decision",
        }
        self.logger.log_decision(evidence_data)

        # Check first file
        files = list(Path(self.temp_dir).glob("*.jsonl"))
        assert len(files) == 1

        # Force rotation by changing date
        with patch("src.evidence.evidence_logger.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2024-01-02"

            # Log second decision
            evidence_data["request_id"] = "test-2"
            evidence_data["reasoning_text"] = "Second decision"
            self.logger.log_decision(evidence_data)

            # Check second file was created
            files = list(Path(self.temp_dir).glob("*.jsonl"))
            assert len(files) == 2

    def test_file_rotation_by_size(self):
        """Test size-based file rotation."""
        # Set rotation to by_size
        self.logger.rotation = "by_size"
        self.logger.size_mb = 0.001  # 1KB for testing

        # Log multiple decisions to trigger rotation
        for i in range(10):
            evidence_data = {
                "request_id": f"test-{i}",
                "timestamp_iso": "2024-01-01T00:00:00",
                "agent_name": "test_agent",
                "decision_flag": True,
                "reasoning_text": f"Decision {i} with some additional text to increase size",
            }
            self.logger.log_decision(evidence_data)

        # Check files were created
        files = list(Path(self.temp_dir).glob("*.jsonl"))
        assert len(files) >= 1

    def test_concurrency_safety(self):
        """Test thread safety of the logger."""

        def log_decision(thread_id):
            for i in range(5):
                evidence_data = {
                    "request_id": f"thread-{thread_id}-{i}",
                    "timestamp_iso": "2024-01-01T00:00:00",
                    "agent_name": f"thread_{thread_id}",
                    "decision_flag": True,
                    "reasoning_text": f"Thread {thread_id} decision {i}",
                }
                self.logger.log_decision(evidence_data)

        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=log_decision, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check all decisions were logged
        files = list(Path(self.temp_dir).glob("*.jsonl"))
        assert len(files) == 1

        with open(files[0], "r") as f:
            lines = f.readlines()
            assert len(lines) == 15  # 3 threads * 5 decisions each

    def test_logger_disabled(self):
        """Test logger when disabled."""
        self.logger.enabled = False

        evidence_data = {
            "request_id": "test-123",
            "timestamp_iso": "2024-01-01T00:00:00",
            "agent_name": "test_agent",
            "decision_flag": True,
            "reasoning_text": "Test decision",
        }

        result = self.logger.log_decision(evidence_data)
        assert result == True

        # Check no files were created
        files = list(Path(self.temp_dir).glob("*.jsonl"))
        assert len(files) == 0

    def test_error_handling(self):
        """Test error handling during logging."""
        # Mock file operations to fail
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            evidence_data = {
                "request_id": "test-123",
                "timestamp_iso": "2024-01-01T00:00:00",
                "agent_name": "test_agent",
                "decision_flag": True,
                "reasoning_text": "Test decision",
            }

            result = self.logger.log_decision(evidence_data)
            assert result == False

    def test_get_stats(self):
        """Test logger statistics."""
        # Log some decisions
        for i in range(3):
            evidence_data = {
                "request_id": f"test-{i}",
                "timestamp_iso": "2024-01-01T00:00:00",
                "agent_name": "test_agent",
                "decision_flag": True,
                "reasoning_text": f"Decision {i}",
            }
            self.logger.log_decision(evidence_data)

        stats = self.logger.get_stats()
        assert stats["enabled"] == True
        assert stats["write_count"] == 3
        assert stats["sink_path"] == self.temp_dir
        assert stats["rotation"] == "by_day"


class TestEvidenceLoggerFunctions:
    """Test the convenience functions."""

    def test_get_evidence_logger(self):
        """Test getting the global logger instance."""
        # Test with config
        config = {"evidence": {"enabled": True, "sink": {"path": "/tmp/test"}}}
        logger1 = get_evidence_logger(config)
        assert logger1 is not None

        # Test singleton behavior
        logger2 = get_evidence_logger()
        assert logger1 is logger2

    def test_log_compliance_decision(self):
        """Test the convenience function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {"evidence": {"enabled": True, "sink": {"path": temp_dir}}}

            # Reset global logger and initialize with test config
            import src.evidence.evidence_logger as evidence_logger

            evidence_logger._evidence_logger = None
            logger = get_evidence_logger(config)

            evidence_data = {
                "request_id": "test-123",
                "timestamp_iso": "2024-01-01T00:00:00",
                "agent_name": "test_agent",
                "decision_flag": True,
                "reasoning_text": "Test decision",
            }

            result = log_compliance_decision(evidence_data)
            assert result == True

            # Check file was created
            files = list(Path(temp_dir).glob("*.jsonl"))
            assert len(files) == 1

            # Clean up
            logger.close()
            evidence_logger._evidence_logger = None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
