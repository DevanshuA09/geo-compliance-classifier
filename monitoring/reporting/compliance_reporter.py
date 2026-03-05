"""
Compliance Reporter Agent
Automates compliance reporting and dashboard generation for geo-regulation workflows.
Handles feature-level compliance data, regulatory summaries, and deadline tracking.
"""

import json
import logging
import os
import re
import sys
import uuid
import webbrowser
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import yaml
from jinja2 import Environment, FileSystemLoader, Template
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)

# Add RAG adapter import
try:
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from src.evidence import log_compliance_decision
    from src.rag import RAGAdapter
except ImportError:
    RAGAdapter = None
    log_compliance_decision = None
    logger.warning("RAG adapter not available, using fallback reporting")


class ComplianceStatus(Enum):
    COMPLIANT = "Compliant"
    NON_COMPLIANT = "Non_Compliant"
    FLAGGED_FOR_REVIEW = "Flagged_For_Review"
    PARTIAL = "Partial"
    UNKNOWN = "Unknown"


class ReportAudience(Enum):
    INTERNAL = "Internal"
    REGULATOR = "Regulator"
    EXTERNAL_PARTNER = "External_Partner"
    EXECUTIVE = "Executive"


@dataclass
class FeatureCompliance:
    """Represents compliance data for a single feature"""

    feature_name: str
    feature_description: str
    geo_compliance: str  # YES, NO, PARTIAL, UNKNOWN
    regulations_matched: List[str]
    status: str  # Compliant, Non_Compliant, Flagged_For_Review, etc.
    jurisdiction: Optional[str] = None
    implementation_date: Optional[str] = None
    last_audit_date: Optional[str] = None
    risk_level: Optional[str] = None  # LOW, MEDIUM, HIGH, CRITICAL


@dataclass
class RegulatorySummary:
    """Represents regulatory requirements and deadlines"""

    regulation_name: str
    jurisdiction: str
    key_requirements: List[str]
    reporting_deadlines: List[Dict[str, str]]
    compliance_triggers: List[str]
    enforcement_actions: List[str]


@dataclass
class SubmissionDeadline:
    """Represents a reporting deadline"""

    regulation: str
    report_type: str
    next_due: str
    frequency: str  # ANNUAL, QUARTERLY, MONTHLY, AD_HOC
    audience: str
    status: str  # UPCOMING, OVERDUE, COMPLETED
    priority: str  # LOW, MEDIUM, HIGH, CRITICAL


@dataclass
class ComplianceReport:
    """Complete compliance report structure"""

    report_id: str
    generated_date: str
    summary_stats: Dict[str, Any]
    feature_matrix: List[Dict[str, Any]]
    dashboard_url: Optional[str] = None
    reports: List[Dict[str, str]] = None
    submission_deadlines: List[Dict[str, str]] = None
    risk_analysis: Dict[str, Any] = None
    recommendations: List[str] = None


class ComplianceReporter:
    """Main compliance reporting agent"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.template_env = self._setup_templates()
        self.output_dir = Path(self.config.get("output_dir", "./compliance_reports"))
        self.output_dir.mkdir(exist_ok=True)

        # Initialize components
        self.analyzer = None  # Will be set from existing compliance_analyzer
        self.dashboard_generator = DashboardGenerator(self.output_dir)
        self.rag_adapter = RAGAdapter() if RAGAdapter else None
        self.deadline_tracker = DeadlineTracker()

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        default_config = {
            "output_dir": "./compliance_reports",
            "templates_dir": "./templates",
            "dashboard_port": 8050,
            "report_formats": ["html", "pdf", "csv"],
            "audience_configs": {
                "Internal": {
                    "detail_level": "high",
                    "include_metrics": True,
                    "include_recommendations": True,
                },
                "Regulator": {
                    "detail_level": "medium",
                    "include_metrics": True,
                    "include_recommendations": False,
                },
                "Executive": {
                    "detail_level": "low",
                    "include_metrics": True,
                    "include_recommendations": True,
                },
            },
        }

        if config_path and Path(config_path).exists():
            with open(config_path, "r") as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)

        return default_config

    def _setup_templates(self) -> Environment:
        """Setup Jinja2 template environment"""
        templates_dir = Path(self.config.get("templates_dir", "./templates"))
        templates_dir.mkdir(exist_ok=True)

        # Create default templates if they don't exist
        self._create_default_templates(templates_dir)

        return Environment(loader=FileSystemLoader(str(templates_dir)))

    def _create_default_templates(self, templates_dir: Path):
        """Create default HTML templates for reports"""

        # Main report template
        main_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Compliance Report - {{ report_id }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 5px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-card { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .feature-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .feature-table th, .feature-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .feature-table th { background-color: #f2f2f2; }
        .compliant { background-color: #d4edda; }
        .non-compliant { background-color: #f8d7da; }
        .flagged { background-color: #fff3cd; }
        .deadlines { margin: 20px 0; }
        .deadline-item { padding: 10px; margin: 5px 0; border-left: 4px solid #007bff; background: #f8f9fa; }
        .overdue { border-left-color: #dc3545; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Compliance Report</h1>
        <p><strong>Report ID:</strong> {{ report_id }}</p>
        <p><strong>Generated:</strong> {{ generated_date }}</p>
        <p><strong>Audience:</strong> {{ audience }}</p>
    </div>
    
    <h2>Summary Statistics</h2>
    <div class="stats-grid">
        <div class="stat-card">
            <h3>Total Features</h3>
            <p>{{ summary_stats.total_features }}</p>
        </div>
        <div class="stat-card">
            <h3>Geo Compliant</h3>
            <p>{{ summary_stats.geo_compliant }}</p>
        </div>
        <div class="stat-card">
            <h3>Flagged for Review</h3>
            <p>{{ summary_stats.flagged_for_review }}</p>
        </div>
        <div class="stat-card">
            <h3>Non Compliant</h3>
            <p>{{ summary_stats.non_compliant }}</p>
        </div>
    </div>
    
    <h2>Feature Compliance Matrix</h2>
    <table class="feature-table">
        <thead>
            <tr>
                <th>Feature Name</th>
                <th>Geo Compliance</th>
                <th>Regulations Matched</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for feature in feature_matrix %}
            <tr class="{{ 'compliant' if feature.status == 'Compliant' else 'non-compliant' if feature.status == 'Non_Compliant' else 'flagged' }}">
                <td>{{ feature.feature_name }}</td>
                <td>{{ feature.geo_compliance }}</td>
                <td>{{ feature.regulations_matched | join(', ') }}</td>
                <td>{{ feature.status }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    {% if submission_deadlines %}
    <h2>Submission Deadlines</h2>
    <div class="deadlines">
        {% for deadline in submission_deadlines %}
        <div class="deadline-item {{ 'overdue' if deadline.status == 'OVERDUE' }}">
            <strong>{{ deadline.regulation }}</strong> - {{ deadline.next_due }}
            <br><small>Status: {{ deadline.status }}</small>
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    {% if recommendations %}
    <h2>Recommendations</h2>
    <ul>
        {% for rec in recommendations %}
        <li>{{ rec }}</li>
        {% endfor %}
    </ul>
    {% endif %}
</body>
</html>
        """

        with open(templates_dir / "main_report.html", "w") as f:
            f.write(main_template)

    def ingest_compliance_data(
        self,
        features_data: List[Dict[str, Any]],
        regulatory_summaries: Optional[List[Dict[str, Any]]] = None,
        submission_calendar: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Ingest and process compliance data

        Args:
            features_data: List of feature compliance dictionaries
            regulatory_summaries: List of regulatory requirement summaries
            submission_calendar: List of submission deadlines and audience mappings

        Returns:
            Processed compliance data structure
        """

        logger.info(f"Ingesting {len(features_data)} features")

        # Convert to structured format
        features = []
        for feature_data in features_data:
            feature = FeatureCompliance(
                feature_name=feature_data.get("feature_name", ""),
                feature_description=feature_data.get("feature_description", ""),
                geo_compliance=feature_data.get("geo_compliance", "UNKNOWN"),
                regulations_matched=feature_data.get("regulations_matched", []),
                status=feature_data.get("status", "Unknown"),
                jurisdiction=feature_data.get("jurisdiction"),
                implementation_date=feature_data.get("implementation_date"),
                last_audit_date=feature_data.get("last_audit_date"),
                risk_level=feature_data.get("risk_level"),
            )
            features.append(feature)

        # Process regulatory summaries
        regulations = []
        if regulatory_summaries:
            for reg_data in regulatory_summaries:
                regulation = RegulatorySummary(
                    regulation_name=reg_data.get("regulation_name", ""),
                    jurisdiction=reg_data.get("jurisdiction", ""),
                    key_requirements=reg_data.get("key_requirements", []),
                    reporting_deadlines=reg_data.get("reporting_deadlines", []),
                    compliance_triggers=reg_data.get("compliance_triggers", []),
                    enforcement_actions=reg_data.get("enforcement_actions", []),
                )
                regulations.append(regulation)

        # Process submission calendar
        deadlines = []
        if submission_calendar:
            for deadline_data in submission_calendar:
                deadline = SubmissionDeadline(
                    regulation=deadline_data.get("regulation", ""),
                    report_type=deadline_data.get("report_type", ""),
                    next_due=deadline_data.get("next_due", ""),
                    frequency=deadline_data.get("frequency", "ANNUAL"),
                    audience=deadline_data.get("audience", ""),
                    status=deadline_data.get("status", "UPCOMING"),
                    priority=deadline_data.get("priority", "MEDIUM"),
                )
                deadlines.append(deadline)

        return {
            "features": features,
            "regulations": regulations,
            "deadlines": deadlines,
        }

    def generate_compliance_report(
        self,
        compliance_data: Dict[str, Any],
        report_id: Optional[str] = None,
        audiences: Optional[List[str]] = None,
    ) -> ComplianceReport:
        """
        Generate comprehensive compliance report

        Args:
            compliance_data: Processed compliance data
            report_id: Optional report identifier
            audiences: List of target audiences

        Returns:
            Complete compliance report
        """

        features = compliance_data["features"]
        deadlines = compliance_data["deadlines"]

        # Generate report ID if not provided
        if not report_id:
            report_id = f"{datetime.now().strftime('%Y-%m-%d')}-COMPLIANCE"

        # Calculate summary statistics
        summary_stats = self._calculate_summary_stats(features)

        # Convert features to matrix format
        feature_matrix = [asdict(feature) for feature in features]

        # Generate dashboard
        dashboard_url = self.dashboard_generator.generate_dashboard(
            features, summary_stats, report_id
        )

        # Generate reports for different audiences
        audiences = audiences or ["Internal", "Regulator"]
        reports = []

        for audience in audiences:
            report_files = self._generate_audience_reports(
                features, summary_stats, deadlines, report_id, audience
            )
            reports.extend(report_files)

        # Process submission deadlines
        submission_deadlines = (
            [asdict(deadline) for deadline in deadlines] if deadlines else []
        )

        # Generate risk analysis
        risk_analysis = self._analyze_risks(features, deadlines)

        # Generate regulatory summaries using RAG if available
        regulatory_summaries = self._get_regulatory_summaries(
            compliance_data.get("regulations", [])
        )

        # Log report generation evidence
        self._log_report_evidence(report_id, features, regulatory_summaries)

        # Generate recommendations
        recommendations = self._generate_recommendations(features, risk_analysis)

        return ComplianceReport(
            report_id=report_id,
            generated_date=datetime.now().isoformat(),
            summary_stats=summary_stats,
            feature_matrix=feature_matrix,
            dashboard_url=dashboard_url,
            reports=reports,
            submission_deadlines=submission_deadlines,
            risk_analysis=risk_analysis,
            recommendations=recommendations,
        )

    def _calculate_summary_stats(
        self, features: List[FeatureCompliance]
    ) -> Dict[str, Any]:
        """Calculate summary statistics from features"""

        total_features = len(features)
        geo_compliant = sum(1 for f in features if f.geo_compliance == "YES")
        flagged_for_review = sum(
            1 for f in features if f.status == "Flagged_For_Review"
        )
        non_compliant = sum(1 for f in features if f.status == "Non_Compliant")

        # Calculate compliance percentages
        compliance_rate = (
            (geo_compliant / total_features * 100) if total_features > 0 else 0
        )
        risk_rate = (
            ((flagged_for_review + non_compliant) / total_features * 100)
            if total_features > 0
            else 0
        )

        # Count by jurisdiction
        jurisdiction_counts = {}
        regulation_counts = {}

        for feature in features:
            if feature.jurisdiction:
                jurisdiction_counts[feature.jurisdiction] = (
                    jurisdiction_counts.get(feature.jurisdiction, 0) + 1
                )

            for regulation in feature.regulations_matched:
                regulation_counts[regulation] = regulation_counts.get(regulation, 0) + 1

        return {
            "total_features": total_features,
            "geo_compliant": geo_compliant,
            "flagged_for_review": flagged_for_review,
            "non_compliant": non_compliant,
            "compliance_rate": round(compliance_rate, 2),
            "risk_rate": round(risk_rate, 2),
            "jurisdiction_breakdown": jurisdiction_counts,
            "regulation_breakdown": regulation_counts,
        }

    def _analyze_risks(
        self, features: List[FeatureCompliance], deadlines: List[SubmissionDeadline]
    ) -> Dict[str, Any]:
        """Analyze compliance risks"""

        # Feature-level risks
        high_risk_features = [
            f for f in features if f.risk_level == "HIGH" or f.risk_level == "CRITICAL"
        ]
        non_compliant_features = [f for f in features if f.status == "Non_Compliant"]
        flagged_features = [f for f in features if f.status == "Flagged_For_Review"]

        # Deadline risks
        overdue_deadlines = [d for d in deadlines if d.status == "OVERDUE"]
        upcoming_deadlines = [d for d in deadlines if d.status == "UPCOMING"]

        # Jurisdiction risks
        jurisdiction_risks = {}
        for feature in features:
            if feature.jurisdiction:
                if feature.jurisdiction not in jurisdiction_risks:
                    jurisdiction_risks[feature.jurisdiction] = {
                        "total": 0,
                        "compliant": 0,
                        "non_compliant": 0,
                        "flagged": 0,
                    }

                jurisdiction_risks[feature.jurisdiction]["total"] += 1
                if feature.status == "Compliant":
                    jurisdiction_risks[feature.jurisdiction]["compliant"] += 1
                elif feature.status == "Non_Compliant":
                    jurisdiction_risks[feature.jurisdiction]["non_compliant"] += 1
                elif feature.status == "Flagged_For_Review":
                    jurisdiction_risks[feature.jurisdiction]["flagged"] += 1

        return {
            "high_risk_features": len(high_risk_features),
            "non_compliant_features": len(non_compliant_features),
            "flagged_features": len(flagged_features),
            "overdue_deadlines": len(overdue_deadlines),
            "upcoming_deadlines": len(upcoming_deadlines),
            "jurisdiction_risks": jurisdiction_risks,
            "critical_issues": [
                f.feature_name
                for f in features
                if f.risk_level == "CRITICAL" or f.status == "Non_Compliant"
            ],
        }

    def _generate_recommendations(
        self, features: List[FeatureCompliance], risk_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on analysis"""

        recommendations = []

        # High-level recommendations
        if risk_analysis["high_risk_features"] > 0:
            recommendations.append(
                f"Address {risk_analysis['high_risk_features']} high-risk features immediately"
            )

        if risk_analysis["non_compliant_features"] > 0:
            recommendations.append(
                f"Prioritize remediation of {risk_analysis['non_compliant_features']} non-compliant features"
            )

        if risk_analysis["overdue_deadlines"] > 0:
            recommendations.append(
                f"Submit {risk_analysis['overdue_deadlines']} overdue reports as soon as possible"
            )

        # Jurisdiction-specific recommendations
        for jurisdiction, risks in risk_analysis["jurisdiction_risks"].items():
            compliance_rate = (
                (risks["compliant"] / risks["total"] * 100) if risks["total"] > 0 else 0
            )
            if compliance_rate < 80:
                recommendations.append(
                    f"Improve compliance rate in {jurisdiction} (currently {compliance_rate:.1f}%)"
                )

        # Feature-specific recommendations
        for feature in features:
            if feature.status == "Flagged_For_Review":
                recommendations.append(
                    f"Review and validate compliance for: {feature.feature_name}"
                )

        return recommendations

    def _generate_audience_reports(
        self,
        features: List[FeatureCompliance],
        summary_stats: Dict[str, Any],
        deadlines: List[SubmissionDeadline],
        report_id: str,
        audience: str,
    ) -> List[Dict[str, str]]:
        """Generate reports for specific audience"""

        audience_config = self.config["audience_configs"].get(audience, {})
        report_files = []

        # Generate HTML report
        html_content = self._render_html_report(
            features, summary_stats, deadlines, report_id, audience, audience_config
        )
        html_file = self.output_dir / f"{report_id}-{audience.lower()}.html"
        with open(html_file, "w") as f:
            f.write(html_content)

        report_files.append(
            {"audience": audience, "format": "html", "report_file": str(html_file)}
        )

        # Generate CSV report
        csv_file = self.output_dir / f"{report_id}-{audience.lower()}.csv"
        self._generate_csv_report(features, summary_stats, csv_file)

        report_files.append(
            {"audience": audience, "format": "csv", "report_file": str(csv_file)}
        )

        return report_files

    def _render_html_report(
        self,
        features: List[FeatureCompliance],
        summary_stats: Dict[str, Any],
        deadlines: List[SubmissionDeadline],
        report_id: str,
        audience: str,
        audience_config: Dict[str, Any],
    ) -> str:
        """Render HTML report using template"""

        template = self.template_env.get_template("main_report.html")

        # Filter data based on audience configuration
        if audience_config.get("detail_level") == "low":
            # Show only summary for executive audience
            feature_matrix = [asdict(f) for f in features if f.status != "Compliant"]
        else:
            feature_matrix = [asdict(f) for f in features]

        # Filter deadlines based on audience
        if audience == "Regulator":
            submission_deadlines = [
                asdict(d) for d in deadlines if d.audience == "Regulator"
            ]
        else:
            submission_deadlines = [asdict(d) for d in deadlines]

        return template.render(
            report_id=report_id,
            generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            audience=audience,
            summary_stats=summary_stats,
            feature_matrix=feature_matrix,
            submission_deadlines=submission_deadlines,
            recommendations=[],  # Will be populated based on audience config
        )

    def _generate_csv_report(
        self,
        features: List[FeatureCompliance],
        summary_stats: Dict[str, Any],
        csv_file: Path,
    ):
        """Generate CSV report"""

        # Create DataFrame for features
        feature_data = []
        for feature in features:
            feature_data.append(
                {
                    "feature_name": feature.feature_name,
                    "geo_compliance": feature.geo_compliance,
                    "regulations_matched": ", ".join(feature.regulations_matched),
                    "status": feature.status,
                    "jurisdiction": feature.jurisdiction or "",
                    "risk_level": feature.risk_level or "",
                    "implementation_date": feature.implementation_date or "",
                    "last_audit_date": feature.last_audit_date or "",
                }
            )

        df = pd.DataFrame(feature_data)
        df.to_csv(csv_file, index=False)

    def export_report(
        self, report: ComplianceReport, output_format: str = "json"
    ) -> str:
        """Export report in specified format"""

        if output_format == "json":
            output_file = self.output_dir / f"{report.report_id}.json"
            with open(output_file, "w") as f:
                json.dump(asdict(report), f, indent=2, default=str)
            return str(output_file)

        elif output_format == "yaml":
            output_file = self.output_dir / f"{report.report_id}.yaml"
            with open(output_file, "w") as f:
                yaml.dump(asdict(report), f, default_flow_style=False)
            return str(output_file)

        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def schedule_report_job(
        self, compliance_data: Dict[str, Any], schedule_config: Dict[str, Any]
    ) -> str:
        """Schedule regular report generation"""

        # This would integrate with a task scheduler like Celery or APScheduler
        # For now, return a job identifier
        job_id = f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"Scheduled compliance report job: {job_id}")
        logger.info(f"Schedule config: {schedule_config}")

        return job_id

    def track_deadlines(self, deadlines: List[SubmissionDeadline]) -> Dict[str, Any]:
        """Track and update submission deadlines"""

        return self.deadline_tracker.process_deadlines(deadlines)

    def generate_audit_trail(
        self, features: List[FeatureCompliance]
    ) -> List[Dict[str, Any]]:
        """Generate audit trail for compliance evidence"""

        audit_trail = []

        for feature in features:
            trail_entry = {
                "feature_name": feature.feature_name,
                "timestamp": datetime.now().isoformat(),
                "compliance_status": feature.status,
                "regulations_matched": feature.regulations_matched,
                "evidence": {
                    "implementation_date": feature.implementation_date,
                    "last_audit_date": feature.last_audit_date,
                    "jurisdiction": feature.jurisdiction,
                    "risk_level": feature.risk_level,
                },
                "traceability": {
                    "feature_description": feature.feature_description,
                    "geo_compliance": feature.geo_compliance,
                },
            }
            audit_trail.append(trail_entry)

        return audit_trail

    def _get_rag_regulatory_context(self, regulation_name: str) -> List[Dict]:
        """Get regulatory context using centralized RAG system."""
        if not self.rag_adapter:
            return []

        try:
            return self.rag_adapter.retrieve_regulatory_context(
                query=f"{regulation_name} requirements compliance", max_results=3
            )
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            return []

    def _get_regulatory_summaries(self, regulations: List[str]) -> List[Dict]:
        """Get regulatory summaries using RAG system."""
        summaries = []

        for regulation in regulations:
            context = self._get_rag_regulatory_context(regulation)
            if context:
                summaries.append(
                    {
                        "regulation": regulation,
                        "context": context,
                        "summary": f"Retrieved {len(context)} regulatory contexts for {regulation}",
                    }
                )

        return summaries

    def _log_report_evidence(
        self,
        report_id: str,
        features: List[FeatureCompliance],
        regulatory_summaries: List[Dict],
    ):
        """Log compliance report generation evidence using centralized logger."""
        if log_compliance_decision:
            evidence_data = {
                "request_id": str(uuid.uuid4()),
                "timestamp_iso": datetime.now().isoformat(),
                "agent_name": "compliance_reporter",
                "decision_flag": len(features) > 0,
                "reasoning_text": f"Report generated for {len(features)} features and {len(regulatory_summaries)} regulations",
                "feature_id": report_id,
                "feature_title": f"Compliance Report {report_id}",
                "related_regulations": [
                    summary.get("regulation_name", "unknown")
                    for summary in regulatory_summaries
                ],
                "confidence": 1.0,  # Report generation is deterministic
                "retrieval_metadata": {
                    "agent_specific": "compliance_reporting",
                    "reporting_top_k": 3,
                    "features_count": len(features),
                    "regulations_count": len(regulatory_summaries),
                },
                "timings_ms": {
                    "report_generation_ms": 0  # Will be populated if timing is tracked
                },
            }
            log_compliance_decision(evidence_data)
        else:
            # Fallback to local logging
            evidence = {
                "report_id": report_id,
                "features_count": len(features),
                "regulations_count": len(regulatory_summaries),
                "timestamp": datetime.now().isoformat(),
            }
            logger.info(f"Compliance report evidence logged (local): {evidence}")


class DashboardGenerator:
    """Generates interactive dashboards for compliance data"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.dashboard_dir = output_dir / "dashboards"
        self.dashboard_dir.mkdir(exist_ok=True)

    def generate_dashboard(
        self,
        features: List[FeatureCompliance],
        summary_stats: Dict[str, Any],
        report_id: str,
    ) -> str:
        """Generate interactive dashboard"""

        # Create Plotly dashboard
        fig = self._create_dashboard_figure(features, summary_stats, report_id)

        # Save dashboard
        dashboard_file = self.dashboard_dir / f"{report_id}_dashboard.html"
        fig.write_html(str(dashboard_file))

        # Return URL (in production, this would be a web server URL)
        return f"file://{dashboard_file.absolute()}"

    def _create_dashboard_figure(
        self,
        features: List[FeatureCompliance],
        summary_stats: Dict[str, Any],
        report_id: str = "Unknown",
    ) -> go.Figure:
        """Create Plotly dashboard figure"""

        # Create subplots
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "Compliance Overview",
                "Jurisdiction Breakdown",
                "Regulation Coverage",
                "Risk Analysis",
            ),
            specs=[
                [{"type": "pie"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "scatter"}],
            ],
        )

        # 1. Compliance Overview (Pie Chart)
        compliance_counts = [
            summary_stats["geo_compliant"],
            summary_stats["flagged_for_review"],
            summary_stats["non_compliant"],
        ]
        compliance_labels = ["Compliant", "Flagged for Review", "Non-Compliant"]

        fig.add_trace(
            go.Pie(
                labels=compliance_labels,
                values=compliance_counts,
                name="Compliance Status",
            ),
            row=1,
            col=1,
        )

        # 2. Jurisdiction Breakdown (Bar Chart)
        if summary_stats.get("jurisdiction_breakdown"):
            jurisdictions = list(summary_stats["jurisdiction_breakdown"].keys())
            counts = list(summary_stats["jurisdiction_breakdown"].values())

            fig.add_trace(
                go.Bar(x=jurisdictions, y=counts, name="Features by Jurisdiction"),
                row=1,
                col=2,
            )

        # 3. Regulation Coverage (Bar Chart)
        if summary_stats.get("regulation_breakdown"):
            regulations = list(summary_stats["regulation_breakdown"].keys())
            counts = list(summary_stats["regulation_breakdown"].values())

            fig.add_trace(
                go.Bar(x=regulations, y=counts, name="Features by Regulation"),
                row=2,
                col=1,
            )

        # 4. Risk Analysis (Scatter Plot)
        risk_data = []
        for feature in features:
            if feature.risk_level:
                risk_score = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}.get(
                    feature.risk_level, 0
                )
                risk_data.append(
                    {
                        "feature": feature.feature_name,
                        "risk_score": risk_score,
                        "jurisdiction": feature.jurisdiction or "Unknown",
                    }
                )

        if risk_data:
            df_risk = pd.DataFrame(risk_data)
            fig.add_trace(
                go.Scatter(
                    x=df_risk["feature"],
                    y=df_risk["risk_score"],
                    mode="markers",
                    text=df_risk["jurisdiction"],
                    name="Risk Analysis",
                ),
                row=2,
                col=2,
            )

        # Update layout
        fig.update_layout(
            title_text=f"Compliance Dashboard - {report_id}",
            height=800,
            showlegend=True,
        )

        return fig


class DeadlineTracker:
    """Tracks and manages submission deadlines"""

    def __init__(self):
        self.deadlines = []

    def process_deadlines(self, deadlines: List[SubmissionDeadline]) -> Dict[str, Any]:
        """Process and update deadline statuses"""

        current_date = datetime.now()
        updated_deadlines = []

        for deadline in deadlines:
            # Update status based on current date
            due_date = datetime.strptime(deadline.next_due, "%Y-%m-%d")

            if due_date < current_date:
                deadline.status = "OVERDUE"
            elif due_date - current_date <= timedelta(days=7):
                deadline.status = "URGENT"
            else:
                deadline.status = "UPCOMING"

            updated_deadlines.append(deadline)

        # Generate summary
        overdue_count = sum(1 for d in updated_deadlines if d.status == "OVERDUE")
        urgent_count = sum(1 for d in updated_deadlines if d.status == "URGENT")
        upcoming_count = sum(1 for d in updated_deadlines if d.status == "UPCOMING")

        return {
            "deadlines": [asdict(d) for d in updated_deadlines],
            "summary": {
                "overdue": overdue_count,
                "urgent": urgent_count,
                "upcoming": upcoming_count,
                "total": len(updated_deadlines),
            },
            "alerts": self._generate_alerts(updated_deadlines),
        }

    def _generate_alerts(self, deadlines: List[SubmissionDeadline]) -> List[str]:
        """Generate deadline alerts"""

        alerts = []

        for deadline in deadlines:
            if deadline.status == "OVERDUE":
                alerts.append(
                    f"CRITICAL: {deadline.regulation} report is OVERDUE (due: {deadline.next_due})"
                )
            elif deadline.status == "URGENT":
                alerts.append(
                    f"URGENT: {deadline.regulation} report due in 7 days ({deadline.next_due})"
                )

        return alerts

    def _get_rag_regulatory_context(self, regulation_name: str) -> List[Dict]:
        """Get regulatory context using centralized RAG system."""
        if not self.rag_adapter:
            return []

        try:
            return self.rag_adapter.retrieve_regulatory_context(
                query=f"{regulation_name} requirements compliance", max_results=3
            )
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            return []

    def _get_regulatory_summaries(self, regulations: List[str]) -> List[Dict]:
        """Get regulatory summaries using RAG system."""
        summaries = []

        for regulation in regulations:
            context = self._get_rag_regulatory_context(regulation)
            if context:
                summaries.append(
                    {
                        "regulation": regulation,
                        "context": context,
                        "summary": f"Retrieved {len(context)} regulatory contexts for {regulation}",
                    }
                )

        return summaries

    def _log_report_evidence(
        self,
        report_id: str,
        features: List[FeatureCompliance],
        regulatory_summaries: List[Dict],
    ):
        """Log compliance report generation evidence using centralized logger."""
        if log_compliance_decision:
            evidence_data = {
                "request_id": str(uuid.uuid4()),
                "timestamp_iso": datetime.now().isoformat(),
                "agent_name": "compliance_reporter",
                "decision_flag": len(features) > 0,
                "reasoning_text": f"Report generated for {len(features)} features and {len(regulatory_summaries)} regulations",
                "feature_id": report_id,
                "feature_title": f"Compliance Report {report_id}",
                "related_regulations": [
                    summary.get("regulation_name", "unknown")
                    for summary in regulatory_summaries
                ],
                "confidence": 1.0,  # Report generation is deterministic
                "retrieval_metadata": {
                    "agent_specific": "compliance_reporting",
                    "reporting_top_k": 3,
                    "features_count": len(features),
                    "regulations_count": len(regulatory_summaries),
                },
                "timings_ms": {
                    "report_generation_ms": 0  # Will be populated if timing is tracked
                },
            }
            log_compliance_decision(evidence_data)
        else:
            # Fallback to local logging
            evidence = {
                "report_id": report_id,
                "features_count": len(features),
                "regulations_count": len(regulatory_summaries),
                "timestamp": datetime.now().isoformat(),
            }
            logger.info(f"Compliance report evidence logged (local): {evidence}")
