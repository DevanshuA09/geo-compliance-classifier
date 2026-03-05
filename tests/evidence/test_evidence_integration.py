"""
Integration tests for evidence logging across all agents and RAG pipeline.
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))
sys.path.append(str(Path(__file__).parent.parent))

from src.evidence import get_evidence_logger, log_compliance_decision


class TestEvidenceIntegration:
    """Test evidence logging integration across the system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            "evidence": {
                "enabled": True,
                "sink": {"path": self.temp_dir, "rotation": "by_day", "size_mb": 10},
                "retention_days": 7,
                "redact": {"enabled": True, "patterns": []},
                "flush_interval": 1,
                "sync": False,
            }
        }

        # Initialize logger with test config and override global instance
        import src.evidence.evidence_logger

        src.evidence.evidence_logger._evidence_logger = None  # Reset global instance
        self.logger = get_evidence_logger(self.config)

    def teardown_method(self):
        """Clean up test fixtures."""
        self.logger.close()
        # Reset global logger
        import src.evidence.evidence_logger

        src.evidence.evidence_logger._evidence_logger = None
        # Clean up temp files
        for file_path in Path(self.temp_dir).glob("*.jsonl"):
            file_path.unlink()
        os.rmdir(self.temp_dir)

    def test_rag_adapter_evidence_logging(self):
        """Test that RAG adapter logs evidence for retrievals."""
        try:
            from src.rag import RAGAdapter

            # Create RAG adapter with test config
            adapter = RAGAdapter()

            # Test retrieval (this should trigger evidence logging)
            results = adapter.retrieve_regulatory_context("test query", max_results=3)

            # Check evidence was logged
            files = list(Path(self.temp_dir).glob("*.jsonl"))
            assert len(files) >= 1

            # Check content
            with open(files[0], "r") as f:
                lines = f.readlines()
                assert len(lines) >= 1

                # Find RAG adapter evidence
                rag_evidence = None
                for line in lines:
                    data = json.loads(line)
                    if data.get("agent_name") == "rag_adapter":
                        rag_evidence = data
                        break

                assert rag_evidence is not None
                assert "request_id" in rag_evidence
                assert "decision_flag" in rag_evidence
                assert "reasoning_text" in rag_evidence
                assert "retrieval_metadata" in rag_evidence

        except ImportError:
            pytest.skip("RAG adapter not available")

    def test_tiktok_feature_generator_evidence_logging(self):
        """Test that TikTokFeatureGenerator logs evidence for compliance decisions."""
        try:
            from src.compliance.feature_generation.tiktok_feature_generator import \
                TikTokFeatureGenerator

            # Create generator
            generator = TikTokFeatureGenerator(seed=42)

            # Generate a feature (this should trigger evidence logging)
            feature = generator.generate_feature()

            # Check evidence was logged
            files = list(Path(self.temp_dir).glob("*.jsonl"))
            assert len(files) >= 1

            # Check content
            with open(files[0], "r") as f:
                lines = f.readlines()
                assert len(lines) >= 1

                # Find TikTok generator evidence
                tiktok_evidence = None
                for line in lines:
                    data = json.loads(line)
                    if data.get("agent_name") == "tiktok_feature_generator":
                        tiktok_evidence = data
                        break

                assert tiktok_evidence is not None
                assert "request_id" in tiktok_evidence
                assert "decision_flag" in tiktok_evidence
                assert "reasoning_text" in tiktok_evidence
                assert "feature_id" in tiktok_evidence
                assert "feature_title" in tiktok_evidence

        except ImportError:
            pytest.skip("TikTokFeatureGenerator not available")

    def test_compliance_analyzer_evidence_logging(self):
        """Test that ComplianceAnalyzer logs evidence for analysis decisions."""
        try:
            from monitoring.reporting.compliance_analyzer import \
                ComplianceAnalyzer

            # Create analyzer
            analyzer = ComplianceAnalyzer()

            # Analyze a feature (this should trigger evidence logging)
            analysis = analyzer.analyze_feature(
                feature_name="Test Feature",
                feature_description="A test feature for compliance analysis",
            )

            # Check evidence was logged
            files = list(Path(self.temp_dir).glob("*.jsonl"))
            assert len(files) >= 1

            # Check content
            with open(files[0], "r") as f:
                lines = f.readlines()
                assert len(lines) >= 1

                # Find compliance analyzer evidence
                analyzer_evidence = None
                for line in lines:
                    data = json.loads(line)
                    if data.get("agent_name") == "compliance_analyzer":
                        analyzer_evidence = data
                        break

                assert analyzer_evidence is not None
                assert "request_id" in analyzer_evidence
                assert "decision_flag" in analyzer_evidence
                assert "reasoning_text" in analyzer_evidence
                assert "feature_id" in analyzer_evidence
                assert "retrieval_metadata" in analyzer_evidence

        except ImportError:
            pytest.skip("ComplianceAnalyzer not available")

    def test_compliance_reporter_evidence_logging(self):
        """Test that ComplianceReporter logs evidence for report generation."""
        try:
            from monitoring.reporting.compliance_reporter import \
                ComplianceReporter

            # Create reporter
            reporter = ComplianceReporter()

            # Generate a report (this should trigger evidence logging)
            # Create sample feature data with proper FeatureCompliance objects
            from monitoring.reporting.compliance_reporter import \
                FeatureCompliance

            feature_data = {
                "features": [
                    FeatureCompliance(
                        feature_name="Test Feature",
                        feature_description="A test feature for compliance",
                        geo_compliance="YES",
                        regulations_matched=["GDPR", "DMA"],
                        status="Compliant",
                        jurisdiction="EU",
                        risk_level="LOW",
                    )
                ],
                "deadlines": [],
            }

            report = reporter.generate_compliance_report(feature_data)

            # Check evidence was logged
            files = list(Path(self.temp_dir).glob("*.jsonl"))
            assert len(files) >= 1

            # Check content
            with open(files[0], "r") as f:
                lines = f.readlines()
                assert len(lines) >= 1

                # Find compliance reporter evidence
                reporter_evidence = None
                for line in lines:
                    data = json.loads(line)
                    if data.get("agent_name") == "compliance_reporter":
                        reporter_evidence = data
                        break

                assert reporter_evidence is not None
                assert "request_id" in reporter_evidence
                assert "decision_flag" in reporter_evidence
                assert "reasoning_text" in reporter_evidence
                assert "feature_id" in reporter_evidence
                assert "retrieval_metadata" in reporter_evidence

        except ImportError:
            pytest.skip("ComplianceReporter not available")

    def test_evidence_record_completeness(self):
        """Test that all evidence records contain required fields."""
        # Generate some evidence from different sources
        test_evidence = [
            {
                "request_id": "test-1",
                "timestamp_iso": "2024-01-01T00:00:00",
                "agent_name": "test_agent_1",
                "decision_flag": True,
                "reasoning_text": "Test decision 1",
            },
            {
                "request_id": "test-2",
                "timestamp_iso": "2024-01-01T00:00:00",
                "agent_name": "test_agent_2",
                "decision_flag": False,
                "reasoning_text": "Test decision 2",
            },
        ]

        # Log evidence
        for evidence in test_evidence:
            log_compliance_decision(evidence)

        # Check all records have required fields
        files = list(Path(self.temp_dir).glob("*.jsonl"))
        assert len(files) == 1

        with open(files[0], "r") as f:
            lines = f.readlines()
            assert len(lines) == 2

            for line in lines:
                data = json.loads(line)

                # Required fields
                assert "request_id" in data
                assert "timestamp_iso" in data
                assert "agent_name" in data
                assert "decision_flag" in data
                assert "reasoning_text" in data

                # Optional fields with defaults
                assert "pipeline_version" in data
                assert "environment" in data
                assert "confidence" in data
                assert "timings_ms" in data
                assert "error_info" in data

    def test_evidence_file_format(self):
        """Test that evidence files are proper JSONL format."""
        # Log multiple evidence records
        for i in range(5):
            evidence_data = {
                "request_id": f"format-test-{i}",
                "timestamp_iso": "2024-01-01T00:00:00",
                "agent_name": "format_test_agent",
                "decision_flag": i % 2 == 0,
                "reasoning_text": f"Format test decision {i}",
            }
            log_compliance_decision(evidence_data)

        # Check file format
        files = list(Path(self.temp_dir).glob("*.jsonl"))
        assert len(files) == 1

        with open(files[0], "r") as f:
            lines = f.readlines()
            assert len(lines) == 5

            # Each line should be valid JSON
            for i, line in enumerate(lines):
                try:
                    data = json.loads(line.strip())
                    assert isinstance(data, dict)
                    assert data["request_id"] == f"format-test-{i}"
                except json.JSONDecodeError:
                    pytest.fail(f"Line {i} is not valid JSON: {line}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
