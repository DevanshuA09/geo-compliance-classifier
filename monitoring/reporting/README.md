# Compliance Reporter Agent

A comprehensive compliance reporting and dashboard generation system for geo-regulation workflows. This agent automates the process of ingesting compliance feature data, tracking regulatory deadlines, and generating tailored reports for different audiences.

## Features

### Core Functionality
- **Data Ingestion**: Parse and process feature-level compliance data, regulatory summaries, and submission calendars
- **Report Generation**: Create comprehensive compliance reports in multiple formats (HTML, CSV, PDF, JSON, YAML)
- **Dashboard Creation**: Generate interactive dashboards with compliance metrics and visualizations
- **Deadline Tracking**: Monitor submission deadlines with automated alerts and status updates
- **Risk Analysis**: Identify and analyze compliance risks across jurisdictions and regulations
- **Audit Trail**: Generate comprehensive audit trails for compliance evidence

### Audience-Specific Reporting
- **Internal Teams**: High-detail reports with full metrics, recommendations, and audit trails
- **Regulators**: Medium-detail reports with compliance metrics and risk analysis
- **Executives**: Low-detail summary reports with key metrics and recommendations
- **External Partners**: Medium-detail reports with compliance metrics only

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure you have the following packages:
- `plotly>=5.15.0` - For interactive dashboards
- `jinja2>=3.1.0` - For HTML template rendering
- `pyyaml>=6.0` - For configuration management
- `pandas>=2.0.0` - For data processing
- `matplotlib>=3.7.0` - For static visualizations

## Quick Start

### Basic Usage

```python
from compliance_reporter import ComplianceReporter

# Initialize the reporter
reporter = ComplianceReporter()

# Create sample data
features_data = [
    {
        "feature_name": "Privacy Controls for EU Users",
        "feature_description": "GDPR-compliant privacy controls for European users",
        "geo_compliance": "YES",
        "regulations_matched": ["GDPR"],
        "status": "Compliant",
        "jurisdiction": "EU"
    }
]

# Ingest data
compliance_data = reporter.ingest_compliance_data(features_data)

# Generate report
report = reporter.generate_compliance_report(
    compliance_data=compliance_data,
    report_id="2025-01-15-COMPLIANCE",
    audiences=["Internal", "Regulator"]
)

# Export report
json_file = reporter.export_report(report, output_format='json')
print(f"Report exported to: {json_file}")
```

### Advanced Usage with Full Data

```python
from compliance_reporter import ComplianceReporter
from datetime import datetime, timedelta

# Initialize with custom config
reporter = ComplianceReporter(config_path="config.yaml")

# Comprehensive feature data
features_data = [
    {
        "feature_name": "Age Verification System",
        "feature_description": "COPPA-compliant age verification for US users under 13",
        "geo_compliance": "YES",
        "regulations_matched": ["COPPA"],
        "status": "Compliant",
        "jurisdiction": "US",
        "implementation_date": "2024-03-15",
        "last_audit_date": "2024-12-01",
        "risk_level": "LOW"
    }
]

# Regulatory summaries
regulatory_summaries = [
    {
        "regulation_name": "COPPA",
        "jurisdiction": "US",
        "key_requirements": ["Parental consent", "Age verification"],
        "reporting_deadlines": [
            {"type": "Annual Certification", "due_date": "2025-02-28"}
        ]
    }
]

# Submission calendar
submission_calendar = [
    {
        "regulation": "COPPA",
        "report_type": "Annual Certification",
        "next_due": "2025-02-28",
        "frequency": "ANNUAL",
        "audience": "Regulator",
        "priority": "HIGH"
    }
]

# Ingest all data
compliance_data = reporter.ingest_compliance_data(
    features_data=features_data,
    regulatory_summaries=regulatory_summaries,
    submission_calendar=submission_calendar
)

# Generate comprehensive report
report = reporter.generate_compliance_report(
    compliance_data=compliance_data,
    audiences=["Internal", "Regulator", "Executive"]
)

# Track deadlines
deadline_tracking = reporter.track_deadlines(compliance_data['deadlines'])

# Generate audit trail
audit_trail = reporter.generate_audit_trail(compliance_data['features'])

# Export in multiple formats
json_file = reporter.export_report(report, 'json')
yaml_file = reporter.export_report(report, 'yaml')
```

## Input Data Formats

### Feature-Level Compliance Data

```json
{
  "feature_name": "String - Name of the feature",
  "feature_description": "String - Detailed description of the feature",
  "geo_compliance": "String - YES/NO/PARTIAL/UNKNOWN",
  "regulations_matched": ["Array of regulation names"],
  "status": "String - Compliant/Non_Compliant/Flagged_For_Review",
  "jurisdiction": "String - Geographic jurisdiction",
  "implementation_date": "String - YYYY-MM-DD format",
  "last_audit_date": "String - YYYY-MM-DD format",
  "risk_level": "String - LOW/MEDIUM/HIGH/CRITICAL"
}
```

### Regulatory Summaries

```json
{
  "regulation_name": "String - Name of regulation",
  "jurisdiction": "String - Geographic jurisdiction",
  "key_requirements": ["Array of requirement descriptions"],
  "reporting_deadlines": [
    {
      "type": "String - Type of report",
      "due_date": "String - Due date"
    }
  ],
  "compliance_triggers": ["Array of trigger conditions"],
  "enforcement_actions": ["Array of enforcement actions"]
}
```

### Submission Calendar

```json
{
  "regulation": "String - Regulation name",
  "report_type": "String - Type of report",
  "next_due": "String - YYYY-MM-DD format",
  "frequency": "String - ANNUAL/QUARTERLY/MONTHLY/AD_HOC",
  "audience": "String - Target audience",
  "status": "String - UPCOMING/OVERDUE/COMPLETED",
  "priority": "String - LOW/MEDIUM/HIGH/CRITICAL"
}
```

## Output Formats

### JSON Report Structure

```json
{
  "report_id": "String - Unique report identifier",
  "generated_date": "String - ISO timestamp",
  "summary_stats": {
    "total_features": "Number",
    "geo_compliant": "Number",
    "flagged_for_review": "Number",
    "non_compliant": "Number",
    "compliance_rate": "Number - Percentage",
    "risk_rate": "Number - Percentage",
    "jurisdiction_breakdown": "Object - Counts by jurisdiction",
    "regulation_breakdown": "Object - Counts by regulation"
  },
  "feature_matrix": [
    {
      "feature_name": "String",
      "geo_compliance": "String",
      "regulations_matched": ["Array"],
      "status": "String"
    }
  ],
  "dashboard_url": "String - URL to interactive dashboard",
  "reports": [
    {
      "audience": "String",
      "format": "String",
      "report_file": "String - File path"
    }
  ],
  "submission_deadlines": [
    {
      "regulation": "String",
      "next_due": "String",
      "status": "String"
    }
  ],
  "risk_analysis": {
    "high_risk_features": "Number",
    "non_compliant_features": "Number",
    "overdue_deadlines": "Number",
    "jurisdiction_risks": "Object",
    "critical_issues": ["Array"]
  },
  "recommendations": ["Array of recommendation strings"]
}
```

## Configuration

The system uses a YAML configuration file (`config.yaml`) to customize behavior:

```yaml
# Output directories
output_dir: "./compliance_reports"
templates_dir: "./templates"

# Audience configurations
audience_configs:
  Internal:
    detail_level: "high"
    include_metrics: true
    include_recommendations: true
    
  Regulator:
    detail_level: "medium"
    include_metrics: true
    include_recommendations: false

# Dashboard settings
dashboard:
  auto_open: false
  theme: "plotly_white"
  height: 800

# Deadline tracking
deadline_tracking:
  urgent_threshold_days: 7
  critical_threshold_days: 3
```

## Dashboard Features

The interactive dashboard includes:

1. **Compliance Overview**: Pie chart showing compliance status distribution
2. **Jurisdiction Breakdown**: Bar chart of features by jurisdiction
3. **Regulation Coverage**: Bar chart of features by regulation
4. **Risk Analysis**: Scatter plot of risk scores by feature

## Deadline Tracking

The system automatically:

- Updates deadline statuses (UPCOMING, URGENT, OVERDUE)
- Generates alerts for overdue and urgent deadlines
- Provides summary statistics for deadline management
- Tracks deadline priorities and frequencies

## Risk Analysis

The risk analysis includes:

- **Feature-level risks**: Based on risk levels and compliance status
- **Jurisdiction risks**: Compliance rates by geographic region
- **Deadline risks**: Overdue and upcoming submission deadlines
- **Critical issues**: High-priority compliance problems

## Audit Trail

The audit trail provides:

- Feature compliance status changes
- Implementation and audit dates
- Regulatory mapping evidence
- Traceability information

## Scheduling

The system supports scheduled report generation:

```python
# Schedule regular reports
schedule_config = {
    "frequency": "weekly",
    "audiences": ["Internal", "Regulator"],
    "report_types": ["summary", "detailed"]
}

job_id = reporter.schedule_report_job(compliance_data, schedule_config)
```

## Integration

### With Existing Compliance Analyzer

```python
from compliance_analyzer import ComplianceAnalyzer
from compliance_reporter import ComplianceReporter

# Use existing analyzer
analyzer = ComplianceAnalyzer()
reporter = ComplianceReporter()

# Analyze features
features_df = pd.DataFrame(feature_data)
analyses = analyzer.analyze_features_batch(features_df)

# Convert to reporter format
features_data = []
for analysis in analyses:
    features_data.append({
        "feature_name": analysis.feature_name,
        "feature_description": analysis.feature_description,
        "geo_compliance": "YES" if analysis.overall_compliance == "COMPLIANT" else "NO",
        "regulations_matched": [m.regulation_name for m in analysis.matches],
        "status": analysis.overall_compliance,
        "flagged_for_review": analysis.flagged_for_review
    })

# Generate report
compliance_data = reporter.ingest_compliance_data(features_data)
report = reporter.generate_compliance_report(compliance_data)
```

## Examples

See `example_compliance_reporting.py` for a complete working example with sample data.

## File Structure

```
src/reporting/
├── compliance_reporter.py      # Main compliance reporter agent
├── example_compliance_reporting.py  # Usage examples
├── config.yaml                 # Configuration file
├── README.md                   # This file
└── templates/                  # HTML templates (auto-generated)
    └── main_report.html
```

## Dependencies

- **pandas**: Data processing and CSV generation
- **plotly**: Interactive dashboard creation
- **jinja2**: HTML template rendering
- **pyyaml**: Configuration file parsing
- **matplotlib**: Static visualizations
- **seaborn**: Enhanced plotting

## Contributing

1. Follow the existing code structure and patterns
2. Add comprehensive docstrings for new functions
3. Include type hints for all function parameters
4. Add tests for new functionality
5. Update documentation for new features

## License

This project is part of the geo-compliance-classifier system. 