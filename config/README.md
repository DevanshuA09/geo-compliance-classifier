# Configuration Overview

This directory contains jurisdiction-specific configuration files that define compliance rules, thresholds, and requirements for different regulatory frameworks.

## Structure

### 📍 Jurisdictions (`/jurisdictions/`)
Regulatory rule definitions for each jurisdiction:
- `eu-dsa.yaml` - EU Digital Services Act requirements
- `eu-gdpr.yaml` - GDPR privacy and data protection rules  
- `california-sb976.yaml` - California social media platform obligations
- `florida-hb3.yaml` - Florida minor protection requirements
- `utah-smra.yaml` - Utah Social Media Regulation Act
- `us-coppa.yaml` - Federal COPPA requirements
- `us-ncmec.yaml` - NCMEC reporting obligations

### 👶 Age Thresholds (`/age-thresholds/`)
Age-based restriction definitions:
- `global-defaults.yaml` - Standard age thresholds
- `jurisdiction-overrides.yaml` - Location-specific age rules
- `feature-age-gates.yaml` - Feature-specific age restrictions

### 🔕 Notification Curfews (`/notification-curfews/`)
Time-based notification restrictions:
- `timezone-rules.yaml` - Timezone-aware curfew enforcement
- `jurisdiction-curfews.yaml` - Location-specific quiet hours
- `emergency-overrides.yaml` - Critical notification exceptions

### 🗄️ Retention Periods (`/retention-periods/`)
Data lifecycle management rules:
- `gdpr-retention.yaml` - EU data retention requirements
- `coppa-retention.yaml` - Children's data retention limits
- `audit-log-retention.yaml` - Compliance audit log periods
- `right-to-deletion.yaml` - User data deletion requirements

## Configuration Schema

### Jurisdiction Rule Format
```yaml
# Example: config/jurisdictions/florida-hb3.yaml
jurisdiction:
  name: "Florida Online Protections for Minors (HB 3)"
  code: "US-FL-HB3"
  effective_date: "2024-01-01"
  scope: "Florida residents under 18"

age_restrictions:
  prohibited_under: 14
  parental_consent_required: [14, 15]
  enhanced_protections_under: 18

addictive_features:
  prohibited:
    - infinite_scroll
    - autoplay_videos
    - push_notifications_nighttime
    - live_streaming_under_16
  
  mitigations_required:
    - daily_time_limits
    - break_reminders
    - parental_oversight

notification_curfew:
  enabled: true
  start_time: "22:00"
  end_time: "07:00"
  timezone: "user_location"
  exceptions: ["emergency_alerts", "parental_messages"]

data_restrictions:
  behavioral_tracking: false
  targeted_advertising: false
  precise_location: false
  biometric_data: false

enforcement:
  penalties:
    per_violation: 50000
    systematic_violations: 250000
  audit_retention_years: 7
```

### Age Threshold Configuration
```yaml
# config/age-thresholds/jurisdiction-overrides.yaml
age_thresholds:
  global_defaults:
    minimum_age: 13
    parental_consent_until: 16
    adult_age: 18
  
  jurisdiction_overrides:
    "US-FL":
      minimum_age: 14
      parental_consent_until: 16
      prohibited_features_until: 16
    
    "US-CA":
      enhanced_protections_until: 18
      algorithmic_controls_required: true
    
    "EU":
      gdpr_consent_age: 16  # Can be lowered by member states
      data_portability_age: 13
```

## Usage Examples

### Loading Jurisdiction Rules
```python
from src.compliance.config import ComplianceConfigLoader

config = ComplianceConfigLoader()

# Load Florida-specific rules
florida_rules = config.load_jurisdiction("US-FL-HB3")

# Check if feature is allowed for user
if config.is_feature_allowed(
    feature="infinite_scroll",
    user_age=15,
    jurisdiction="US-FL-HB3"
):
    enable_infinite_scroll()
```

### Age Threshold Validation
```python
from src.compliance.age_validation import AgeValidator

validator = AgeValidator()

# Check minimum age for jurisdiction
min_age = validator.get_minimum_age(
    jurisdiction="US-FL",
    feature="account_creation"
)

# Validate user meets requirements
validation_result = validator.validate_user_age(
    user_age=15,
    jurisdiction="US-FL",
    parental_consent=True
)
```

### Notification Curfew Enforcement
```python
from src.compliance.notifications import CurfewEnforcer

enforcer = CurfewEnforcer()

# Check if notification can be sent
can_notify = enforcer.can_send_notification(
    user_age=15,
    user_timezone="US/Eastern",
    jurisdiction="US-FL-HB3",
    notification_type="social_update"
)
```

## Configuration Validation

All configuration files are validated using JSON Schema:

```yaml
# schemas/jurisdiction-schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
required: ["jurisdiction", "age_restrictions", "enforcement"]
properties:
  jurisdiction:
    type: object
    required: ["name", "code", "effective_date"]
  age_restrictions:
    type: object
    required: ["prohibited_under"]
  addictive_features:
    type: object
    properties:
      prohibited:
        type: array
        items:
          type: string
```

## Environment-Specific Overrides

Configuration supports environment-specific overrides:

```yaml
# config/jurisdictions/florida-hb3.yaml
base_config: &base
  jurisdiction:
    name: "Florida HB 3"
    code: "US-FL-HB3"

development:
  <<: *base
  enforcement:
    strict_mode: false
    logging_level: debug

production:
  <<: *base  
  enforcement:
    strict_mode: true
    audit_all_decisions: true
```

## Automatic Updates

Configuration files are monitored for regulatory updates:

```yaml
# .github/workflows/config-validation.yml
name: Configuration Validation
on:
  push:
    paths: ['config/**/*.yaml']
  pull_request:
    paths: ['config/**/*.yaml']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate Configuration Schema
        run: |
          python scripts/validate-config.py
      - name: Check Regulatory Currency
        run: |
          python scripts/check-regulation-updates.py
```

## Best Practices

1. **Version Control**: All configuration changes must be reviewed and approved
2. **Schema Validation**: Use JSON Schema to validate configuration structure
3. **Environment Testing**: Test configuration changes in staging before production
4. **Regulatory Monitoring**: Monitor for regulatory updates that require config changes
5. **Audit Logging**: Log all configuration loads and rule applications
6. **Fallback Handling**: Define safe fallback behaviors for missing or invalid configs

## Contributing

When adding new jurisdiction configurations:

1. Create new YAML file following the schema
2. Add corresponding test cases
3. Update jurisdiction mapping logic
4. Document any unique implementation requirements
5. Validate against sample user scenarios
