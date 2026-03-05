# Florida HB 3 - Online Protections for Minors

## Overview
Florida House Bill 3 (2024) establishes comprehensive restrictions on social media platforms regarding minors, including account restrictions, addictive feature limitations, and parental control requirements.

## Key Provisions

### 1. Age-Based Account Restrictions

**Under 14**: Complete prohibition on social media accounts
**Ages 14-15**: Parental consent required for account creation

```python
# Implementation example
def validate_florida_age_restrictions(user_age: int, parental_consent: bool = False) -> dict:
    """Validate compliance with Florida HB 3 age restrictions"""
    
    if user_age < 14:
        return {
            "allowed": False,
            "reason": "Florida HB 3 prohibits accounts for users under 14",
            "code": "FL_HB3_UNDER_14_PROHIBITION"
        }
    
    if user_age >= 14 and user_age < 16:
        if not parental_consent:
            return {
                "allowed": False,
                "reason": "Parental consent required for ages 14-15 in Florida",
                "code": "FL_HB3_PARENTAL_CONSENT_REQUIRED"
            }
    
    return {"allowed": True}
```

### 2. Addictive Design Feature Restrictions

**Prohibited Features for Minors**:
- Infinite scroll
- Auto-play videos  
- Push notifications between 10pm - 7am
- Live streaming for under 16
- Features designed to cause compulsive usage

```yaml
# config/jurisdictions/florida-hb3.yaml
addictive_features:
  prohibited_under_16:
    - infinite_scroll
    - autoplay_videos
    - push_notifications_nighttime
    - live_streaming
    - variable_reward_schedules
    - social_approval_indicators
  
  notification_curfew:
    start_time: "22:00"
    end_time: "07:00"
    timezone_enforcement: "user_location"
  
  required_mitigations:
    - daily_time_limits
    - break_reminders
    - parental_oversight_tools
```

### 3. Parental Control Requirements

**Required Parental Tools**:
- Account oversight and supervision
- Time limit setting capabilities
- Content filtering controls
- Activity reporting

```python
class FloridaParentalControls:
    """Parental control implementation for Florida HB 3 compliance"""
    
    def __init__(self, minor_user_id: str, parent_user_id: str):
        self.minor_id = minor_user_id
        self.parent_id = parent_user_id
        
    def set_daily_time_limit(self, minutes: int) -> bool:
        """Set daily usage time limit (required by HB 3)"""
        if minutes > 0 and minutes <= 1440:  # Max 24 hours
            return self.storage.set_time_limit(self.minor_id, minutes)
        return False
    
    def generate_weekly_report(self) -> dict:
        """Generate parental oversight report"""
        return {
            "week_ending": datetime.now().isoformat(),
            "total_time_minutes": self.get_weekly_usage(),
            "content_interactions": self.get_content_summary(),
            "platform_features_used": self.get_feature_usage(),
            "concerning_activity": self.flag_concerning_behavior()
        }
```

### 4. Data Collection Limitations

**Restricted Data Collection for Minors**:
- No targeted advertising based on personal data
- Limited behavioral tracking
- Enhanced data deletion rights

```python
def florida_minor_data_policy(user_age: int, data_type: str) -> dict:
    """Determine data collection permissions under Florida HB 3"""
    
    restricted_data = [
        "location_precise",
        "browsing_behavior", 
        "purchase_history",
        "biometric_data",
        "social_connections_detailed"
    ]
    
    if user_age < 16 and data_type in restricted_data:
        return {
            "collection_allowed": False,
            "retention_days": 0,
            "targeted_ads_allowed": False,
            "reason": "Florida HB 3 minor data protection"
        }
    
    return {"collection_allowed": True, "enhanced_deletion_rights": True}
```

## Implementation Checklist

### Account Creation Flow
- [ ] Age verification system for Florida users
- [ ] Parental consent collection for ages 14-15
- [ ] Account denial for under 14 with clear explanation
- [ ] Audit logging of all age verification attempts

### Feature Restrictions
- [ ] Disable infinite scroll for minor accounts
- [ ] Remove autoplay functionality for minors
- [ ] Implement notification curfew (10pm-7am)
- [ ] Block live streaming for under 16
- [ ] Add usage time warnings and limits

### Parental Controls
- [ ] Parent account linking system
- [ ] Time limit setting interface
- [ ] Weekly activity reporting
- [ ] Content filtering controls
- [ ] Emergency override capabilities

## Technical Integration

### Age Verification Integration
```python
from src.compliance.age_verification import FloridaAgeVerifier

verifier = FloridaAgeVerifier()
result = verifier.verify_age(
    document_type="drivers_license",
    document_data=uploaded_document,
    state="Florida"
)

if result.age < 14:
    return redirect("/account/denied/florida-under-14")
elif result.age < 16:
    return redirect("/account/parental-consent-required")
```

### Feature Control System
```python
from src.compliance.feature_controls import FloridaFeatureController

controller = FloridaFeatureController(user_id=current_user.id)

# Check if infinite scroll is allowed
if controller.is_feature_allowed("infinite_scroll"):
    template_context["infinite_scroll_enabled"] = True
else:
    template_context["infinite_scroll_enabled"] = False
    template_context["restriction_reason"] = "Florida minor protection"
```

## Monitoring and Compliance

### Required Metrics
- Minor account creation attempts vs. approvals
- Parental consent completion rates  
- Feature restriction bypass attempts
- Time limit adherence rates
- Parental control activation rates

### Audit Requirements
```python
# Example compliance audit log
florida_audit_entry = {
    "timestamp": "2024-08-30T15:45:00Z",
    "regulation": "Florida-HB-3",
    "user_age": 15,
    "user_state": "Florida", 
    "action": "feature_restriction_applied",
    "feature": "infinite_scroll",
    "reason": "minor_protection",
    "parental_override": False,
    "retention_period_years": 7
}
```

## Legal References

- **Section 501.2041**: Age verification requirements
- **Section 501.2042**: Addictive feature restrictions  
- **Section 501.2043**: Parental consent mechanisms
- **Section 501.2044**: Data collection limitations
- **Section 501.2045**: Enforcement provisions

## Enforcement Considerations

**Penalties**:
- Up to $50,000 per violation for systematic non-compliance
- Additional damages for harm to minors
- Potential platform operating restrictions in Florida

**Safe Harbors**:
- Good faith age verification efforts
- Prompt remediation of identified violations
- Proactive parental control implementation

## Testing Requirements

```python
def test_florida_under_14_prohibition():
    """Test that users under 14 cannot create accounts"""
    response = attempt_account_creation(age=13, state="Florida")
    assert response.status_code == 403
    assert "Florida HB 3" in response.error_message

def test_parental_consent_flow():
    """Test parental consent requirement for 14-15 year olds"""
    response = attempt_account_creation(age=15, state="Florida")
    assert response.redirect_url.includes("parental-consent")
    
def test_notification_curfew():
    """Test notification blocking during curfew hours"""
    florida_time = datetime.now(timezone("US/Eastern")).replace(hour=23)
    result = can_send_notification(user_age=15, user_state="Florida", time=florida_time)
    assert result == False
```
