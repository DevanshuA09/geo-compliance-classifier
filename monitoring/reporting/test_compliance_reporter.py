"""
Test script for Compliance Reporter Agent
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from reporting.compliance_reporter import ComplianceReporter
from reporting.example_compliance_reporting import (
    create_sample_feature_data, create_sample_regulatory_summaries,
    create_sample_submission_calendar)


def test_basic_functionality():
    """Test basic compliance reporter functionality"""

    print("Testing Compliance Reporter Agent...")

    try:
        # Initialize reporter
        reporter = ComplianceReporter()
        print("✓ Reporter initialized successfully")

        # Create sample data
        features_data = create_sample_feature_data()
        regulatory_summaries = create_sample_regulatory_summaries()
        submission_calendar = create_sample_submission_calendar()

        print(f"✓ Created {len(features_data)} sample features")
        print(f"✓ Created {len(regulatory_summaries)} regulatory summaries")
        print(f"✓ Created {len(submission_calendar)} submission deadlines")

        # Ingest data
        compliance_data = reporter.ingest_compliance_data(
            features_data=features_data,
            regulatory_summaries=regulatory_summaries,
            submission_calendar=submission_calendar,
        )
        print("✓ Data ingested successfully")

        # Generate report
        report = reporter.generate_compliance_report(
            compliance_data=compliance_data,
            report_id="TEST-2025-01-15",
            audiences=["Internal", "Regulator"],
        )
        print("✓ Report generated successfully")

        # Check report structure
        assert report.report_id == "TEST-2025-01-15"
        assert "summary_stats" in report.__dict__
        assert "feature_matrix" in report.__dict__
        assert "dashboard_url" in report.__dict__
        print("✓ Report structure is correct")

        # Check summary stats
        stats = report.summary_stats
        assert stats["total_features"] == len(features_data)
        assert "compliance_rate" in stats
        assert "risk_rate" in stats
        print("✓ Summary statistics calculated correctly")

        # Export report
        json_file = reporter.export_report(report, "json")
        yaml_file = reporter.export_report(report, "yaml")
        print(f"✓ Reports exported: {json_file}, {yaml_file}")

        # Track deadlines
        deadline_tracking = reporter.track_deadlines(compliance_data["deadlines"])
        assert "summary" in deadline_tracking
        assert "alerts" in deadline_tracking
        print("✓ Deadline tracking working")

        # Generate audit trail
        audit_trail = reporter.generate_audit_trail(compliance_data["features"])
        assert len(audit_trail) == len(features_data)
        print("✓ Audit trail generated")

        print("\n🎉 All tests passed! Compliance Reporter Agent is working correctly.")
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_configuration():
    """Test configuration loading"""

    print("\nTesting configuration...")

    try:
        # Test with default config
        reporter1 = ComplianceReporter()
        print("✓ Default configuration loaded")

        # Test with custom config path
        config_path = Path(__file__).parent / "config.yaml"
        if config_path.exists():
            reporter2 = ComplianceReporter(config_path=str(config_path))
            print("✓ Custom configuration loaded")
        else:
            print("⚠ Custom config file not found, skipping custom config test")

        print("✓ Configuration tests passed")
        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_data_validation():
    """Test data validation and error handling"""

    print("\nTesting data validation...")

    try:
        reporter = ComplianceReporter()

        # Test with empty data
        empty_data = reporter.ingest_compliance_data([])
        assert empty_data["features"] == []
        print("✓ Empty data handled correctly")

        # Test with minimal feature data
        minimal_data = [
            {
                "feature_name": "Test Feature",
                "feature_description": "Test Description",
                "geo_compliance": "YES",
                "regulations_matched": ["GDPR"],
                "status": "Compliant",
            }
        ]

        processed_data = reporter.ingest_compliance_data(minimal_data)
        assert len(processed_data["features"]) == 1
        print("✓ Minimal data processed correctly")

        # Generate report with minimal data
        report = reporter.generate_compliance_report(processed_data)
        assert report.summary_stats["total_features"] == 1
        print("✓ Report generated with minimal data")

        print("✓ Data validation tests passed")
        return True

    except Exception as e:
        print(f"❌ Data validation test failed: {e}")
        return False


def main():
    """Run all tests"""

    print("=" * 60)
    print("COMPLIANCE REPORTER AGENT TEST SUITE")
    print("=" * 60)

    tests = [test_basic_functionality, test_configuration, test_data_validation]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The Compliance Reporter Agent is ready to use.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
