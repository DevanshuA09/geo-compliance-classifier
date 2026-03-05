"""
Example Usage of Compliance Reporter Agent
Demonstrates how to use the compliance reporting system with sample data
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from compliance_reporter import (ComplianceReport, ComplianceReporter,
                                 FeatureCompliance, RegulatorySummary,
                                 SubmissionDeadline)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_feature_data() -> List[Dict[str, Any]]:
    """Create sample feature compliance data based on the image description"""

    return [
        {
            "feature_name": "Curfew login blocker with ASL and GH for Utah minors",
            "feature_description": "Curfew-based login restriction system for users under 18 in Utah, implementing Utah Social Media Regulation Act requirements with ASL (Age Safety Layer) and GH (Guardian Hub) integration",
            "geo_compliance": "YES",
            "regulations_matched": ["Utah Social Media Regulation Act"],
            "status": "Compliant",
            "jurisdiction": "Utah, US",
            "implementation_date": "2024-03-15",
            "last_audit_date": "2024-12-01",
            "risk_level": "LOW",
        },
        {
            "feature_name": "PF default toggle with NR enforcement for California teens",
            "feature_description": "Privacy Features (PF) disabled by default for California users under 18, with NR (Notification Requirements) enforcement as part of California's SB976 compliance",
            "geo_compliance": "YES",
            "regulations_matched": ["California SB976", "COPPA"],
            "status": "Compliant",
            "jurisdiction": "California, US",
            "implementation_date": "2024-02-20",
            "last_audit_date": "2024-11-15",
            "risk_level": "MEDIUM",
        },
        {
            "feature_name": "Child abuse content scanner using T5 and CDS triggers",
            "feature_description": "Automated content scanning system using T5 (Text-to-Text Transfer Transformer) model to detect and flag suspected child abuse materials, integrated with CDS (Content Detection System) triggers for US federal law compliance",
            "geo_compliance": "YES",
            "regulations_matched": ["US Federal Law", "NCMEC Reporting"],
            "status": "Compliant",
            "jurisdiction": "US",
            "implementation_date": "2024-01-10",
            "last_audit_date": "2024-12-10",
            "risk_level": "HIGH",
        },
        {
            "feature_name": "Content visibility lock with NSP for EU DSA",
            "feature_description": "Visibility lock mechanism for flagged user-generated content, implementing EU Digital Services Act requirements with NSP (Network Safety Protocol) integration",
            "geo_compliance": "PARTIAL",
            "regulations_matched": ["EU Digital Services Act"],
            "status": "Flagged_For_Review",
            "jurisdiction": "EU",
            "implementation_date": "2024-04-05",
            "last_audit_date": "2024-11-30",
            "risk_level": "HIGH",
        },
        {
            "feature_name": "Jellybean-based parental notifications for Florida regulation",
            "feature_description": "Parental notification system using Jellybean framework to comply with Florida's Online Protections for Minors law, providing real-time alerts for underage user activities",
            "geo_compliance": "YES",
            "regulations_matched": ["Florida Online Protections for Minors"],
            "status": "Compliant",
            "jurisdiction": "Florida, US",
            "implementation_date": "2024-03-01",
            "last_audit_date": "2024-12-05",
            "risk_level": "MEDIUM",
        },
        {
            "feature_name": "Unified retention control via DRT & CDS",
            "feature_description": "Centralized data retention management system using DRT (Data Retention Tool) and CDS (Content Detection System) for GDPR compliance across EEA regions",
            "geo_compliance": "YES",
            "regulations_matched": ["GDPR", "EU Data Retention"],
            "status": "Compliant",
            "jurisdiction": "EEA",
            "implementation_date": "2024-01-25",
            "last_audit_date": "2024-11-20",
            "risk_level": "LOW",
        },
        {
            "feature_name": "NSP auto-flagging",
            "feature_description": "Automated flagging system using Network Safety Protocol (NSP) for content that may violate community guidelines or regulatory requirements",
            "geo_compliance": "UNKNOWN",
            "regulations_matched": ["DSA", "Community Guidelines"],
            "status": "Flagged_For_Review",
            "jurisdiction": "Global",
            "implementation_date": "2024-05-10",
            "last_audit_date": "2024-12-01",
            "risk_level": "MEDIUM",
        },
        {
            "feature_name": "T5 tagging for sensitive reports",
            "feature_description": "AI-powered content tagging system using T5 model to identify and categorize sensitive content for regulatory reporting requirements",
            "geo_compliance": "YES",
            "regulations_matched": ["DSA", "GDPR"],
            "status": "Compliant",
            "jurisdiction": "EU",
            "implementation_date": "2024-02-15",
            "last_audit_date": "2024-11-25",
            "risk_level": "MEDIUM",
        },
        {
            "feature_name": "Underage protection via Snowcap trigger",
            "feature_description": "Age verification and protection system using Snowcap triggers to detect and protect underage users across multiple jurisdictions",
            "geo_compliance": "NO",
            "regulations_matched": ["COPPA", "GDPR"],
            "status": "Non_Compliant",
            "jurisdiction": "Global",
            "implementation_date": "2024-06-01",
            "last_audit_date": "2024-12-15",
            "risk_level": "CRITICAL",
        },
        {
            "feature_name": "Universal PF deactivation on guest mode",
            "feature_description": "Privacy Features (PF) automatically deactivated for guest users to ensure minimal data collection and processing",
            "geo_compliance": "YES",
            "regulations_matched": ["GDPR", "CCPA"],
            "status": "Compliant",
            "jurisdiction": "Global",
            "implementation_date": "2024-04-20",
            "last_audit_date": "2024-11-10",
            "risk_level": "LOW",
        },
    ]


def create_sample_regulatory_summaries() -> List[Dict[str, Any]]:
    """Create sample regulatory summaries"""

    return [
        {
            "regulation_name": "EU Digital Markets Act (DMA)",
            "jurisdiction": "EU",
            "key_requirements": [
                "Gatekeeper obligations",
                "Interoperability requirements",
                "Data portability",
                "Alternative app stores",
                "Choice screens",
                "Bundling restrictions",
            ],
            "reporting_deadlines": [
                {"type": "Annual Compliance Report", "due_date": "2025-03-01"},
                {"type": "Quarterly Metrics", "due_date": "2025-01-15"},
            ],
            "compliance_triggers": [
                "Designation as gatekeeper",
                "Core platform service changes",
                "Market position changes",
            ],
            "enforcement_actions": [
                "Fines up to 10% of global turnover",
                "Behavioral remedies",
                "Structural remedies",
            ],
        },
        {
            "regulation_name": "GDPR",
            "jurisdiction": "EU",
            "key_requirements": [
                "Data protection by design",
                "Privacy by default",
                "Consent management",
                "Data subject rights",
                "Data minimization",
                "Purpose limitation",
            ],
            "reporting_deadlines": [
                {"type": "Breach Notification", "due_date": "Within 72 hours"},
                {"type": "Annual Privacy Report", "due_date": "2025-01-31"},
            ],
            "compliance_triggers": [
                "Personal data processing",
                "Data subject requests",
                "Data breaches",
            ],
            "enforcement_actions": [
                "Fines up to €20 million or 4% of global turnover",
                "Corrective powers",
                "Suspension of data processing",
            ],
        },
        {
            "regulation_name": "COPPA",
            "jurisdiction": "US",
            "key_requirements": [
                "Parental consent",
                "Age verification",
                "Data minimization for children",
                "Safe harbor provisions",
                "Notice requirements",
            ],
            "reporting_deadlines": [
                {"type": "Annual Safe Harbor Certification", "due_date": "2025-02-28"},
                {"type": "Incident Reporting", "due_date": "Within 30 days"},
            ],
            "compliance_triggers": [
                "Collection of personal information from children under 13",
                "Changes to privacy practices",
                "Data breaches involving children",
            ],
            "enforcement_actions": [
                "Civil penalties up to $50,120 per violation",
                "Injunctive relief",
                "Corrective actions",
            ],
        },
    ]


def create_sample_submission_calendar() -> List[Dict[str, Any]]:
    """Create sample submission calendar with deadlines"""

    today = datetime.now()

    return [
        {
            "regulation": "EU DMA",
            "report_type": "Annual Compliance Report",
            "next_due": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "frequency": "ANNUAL",
            "audience": "Regulator",
            "status": "UPCOMING",
            "priority": "HIGH",
        },
        {
            "regulation": "GDPR",
            "report_type": "Annual Privacy Report",
            "next_due": (today + timedelta(days=15)).strftime("%Y-%m-%d"),
            "frequency": "ANNUAL",
            "audience": "Regulator",
            "status": "UPCOMING",
            "priority": "HIGH",
        },
        {
            "regulation": "COPPA",
            "report_type": "Safe Harbor Certification",
            "next_due": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "frequency": "ANNUAL",
            "audience": "Regulator",
            "status": "UPCOMING",
            "priority": "MEDIUM",
        },
        {
            "regulation": "EU DSA",
            "report_type": "Transparency Report",
            "next_due": (today - timedelta(days=5)).strftime("%Y-%m-%d"),
            "frequency": "ANNUAL",
            "audience": "Regulator",
            "status": "OVERDUE",
            "priority": "CRITICAL",
        },
    ]


def main():
    """Main example demonstrating compliance reporting workflow"""

    logger.info("Starting Compliance Reporting Example")

    # Initialize the compliance reporter
    reporter = ComplianceReporter()

    # Create sample data
    features_data = create_sample_feature_data()
    regulatory_summaries = create_sample_regulatory_summaries()
    submission_calendar = create_sample_submission_calendar()

    logger.info(f"Created {len(features_data)} sample features")
    logger.info(f"Created {len(regulatory_summaries)} regulatory summaries")
    logger.info(f"Created {len(submission_calendar)} submission deadlines")

    # Ingest compliance data
    compliance_data = reporter.ingest_compliance_data(
        features_data=features_data,
        regulatory_summaries=regulatory_summaries,
        submission_calendar=submission_calendar,
    )

    logger.info("Successfully ingested compliance data")

    # Generate comprehensive compliance report
    report = reporter.generate_compliance_report(
        compliance_data=compliance_data,
        report_id="2025-01-15-COMPLIANCE-DEMO",
        audiences=["Internal", "Regulator", "Executive"],
    )

    logger.info(f"Generated compliance report: {report.report_id}")
    logger.info(f"Summary stats: {report.summary_stats}")

    # Export report in different formats
    json_file = reporter.export_report(report, output_format="json")
    yaml_file = reporter.export_report(report, output_format="yaml")

    logger.info(f"Exported JSON report: {json_file}")
    logger.info(f"Exported YAML report: {yaml_file}")

    # Track deadlines
    deadline_tracking = reporter.track_deadlines(compliance_data["deadlines"])
    logger.info(f"Deadline tracking summary: {deadline_tracking['summary']}")

    # Generate audit trail
    audit_trail = reporter.generate_audit_trail(compliance_data["features"])
    logger.info(f"Generated audit trail with {len(audit_trail)} entries")

    # Schedule a report job (example)
    schedule_config = {
        "frequency": "weekly",
        "audiences": ["Internal", "Regulator"],
        "report_types": ["summary", "detailed"],
    }

    job_id = reporter.schedule_report_job(compliance_data, schedule_config)
    logger.info(f"Scheduled report job: {job_id}")

    # Print summary of generated files
    output_dir = Path(reporter.output_dir)
    generated_files = list(output_dir.rglob("*"))

    logger.info("Generated files:")
    for file_path in generated_files:
        if file_path.is_file():
            logger.info(f"  - {file_path.relative_to(output_dir)}")

    # Display key metrics
    print("\n" + "=" * 60)
    print("COMPLIANCE REPORT SUMMARY")
    print("=" * 60)
    print(f"Report ID: {report.report_id}")
    print(f"Generated: {report.generated_date}")
    print(f"Dashboard URL: {report.dashboard_url}")
    print()

    print("SUMMARY STATISTICS:")
    print(f"  Total Features: {report.summary_stats['total_features']}")
    print(f"  Geo Compliant: {report.summary_stats['geo_compliant']}")
    print(f"  Flagged for Review: {report.summary_stats['flagged_for_review']}")
    print(f"  Non Compliant: {report.summary_stats['non_compliant']}")
    print(f"  Compliance Rate: {report.summary_stats['compliance_rate']}%")
    print(f"  Risk Rate: {report.summary_stats['risk_rate']}%")
    print()

    print("RISK ANALYSIS:")
    print(f"  High Risk Features: {report.risk_analysis['high_risk_features']}")
    print(f"  Non Compliant Features: {report.risk_analysis['non_compliant_features']}")
    print(f"  Overdue Deadlines: {report.risk_analysis['overdue_deadlines']}")
    print()

    print("DEADLINE ALERTS:")
    for alert in deadline_tracking["alerts"]:
        print(f"  - {alert}")
    print()

    print("RECOMMENDATIONS:")
    for rec in report.recommendations:
        print(f"  - {rec}")
    print()

    print("GENERATED REPORTS:")
    for report_info in report.reports:
        print(
            f"  - {report_info['audience']} ({report_info['format']}): {report_info['report_file']}"
        )

    print("\n" + "=" * 60)
    logger.info("Compliance reporting example completed successfully!")


if __name__ == "__main__":
    main()
