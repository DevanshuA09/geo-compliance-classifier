"""
Evidence Alert System

Provides alerting for compliance issues with configurable thresholds
and multiple notification channels.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class AlertRule:
    """Alert rule configuration."""

    name: str
    condition: str  # 'below', 'above'
    threshold: float
    metric: str
    severity: str  # 'low', 'medium', 'high'
    enabled: bool = True


@dataclass
class Alert:
    """Alert instance."""

    rule_name: str
    severity: str
    message: str
    timestamp: datetime
    metric_value: float
    threshold: float


class EvidenceAlertSystem:
    """Simple alert system for compliance monitoring."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.alert_rules = self._load_default_rules()
        self.alert_history = []

    def _load_default_rules(self) -> List[AlertRule]:
        """Load default alert rules."""
        return [
            AlertRule(
                name="low_compliance_rate",
                condition="below",
                threshold=0.8,
                metric="compliance_rate",
                severity="high",
            ),
            AlertRule(
                name="high_error_rate",
                condition="above",
                threshold=0.1,
                metric="error_rate",
                severity="medium",
            ),
        ]

    def check_alerts(self, metrics: Dict[str, Any]) -> List[Alert]:
        """Check metrics against alert rules."""
        triggered_alerts = []

        for rule in self.alert_rules:
            if not rule.enabled:
                continue

            metric_value = metrics.get(rule.metric)
            if metric_value is None:
                continue

            # Check condition
            if rule.condition == "below" and metric_value < rule.threshold:
                alert = Alert(
                    rule_name=rule.name,
                    severity=rule.severity,
                    message=f"{rule.metric} is {metric_value} (below threshold {rule.threshold})",
                    timestamp=datetime.now(),
                    metric_value=metric_value,
                    threshold=rule.threshold,
                )
                triggered_alerts.append(alert)
                self.alert_history.append(alert)

            elif rule.condition == "above" and metric_value > rule.threshold:
                alert = Alert(
                    rule_name=rule.name,
                    severity=rule.severity,
                    message=f"{rule.metric} is {metric_value} (above threshold {rule.threshold})",
                    timestamp=datetime.now(),
                    metric_value=metric_value,
                    threshold=rule.threshold,
                )
                triggered_alerts.append(alert)
                self.alert_history.append(alert)

        return triggered_alerts

    def get_active_alerts(self) -> List[Alert]:
        """Get recent alerts (last 24 hours)."""
        cutoff = datetime.now() - timedelta(hours=24)
        return [a for a in self.alert_history if a.timestamp > cutoff]

    def get_system_status(self) -> Dict[str, Any]:
        """Get alert system status."""
        return {
            "total_rules": len(self.alert_rules),
            "enabled_rules": len([r for r in self.alert_rules if r.enabled]),
            "active_alerts": len(self.get_active_alerts()),
            "total_alerts": len(self.alert_history),
        }


def main():
    """CLI interface for evidence alert system."""
    import argparse

    parser = argparse.ArgumentParser(description="Evidence Alert System")
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--alerts", action="store_true", help="Show active alerts")

    args = parser.parse_args()

    alert_system = EvidenceAlertSystem()

    if args.status:
        status = alert_system.get_system_status()
        print("Alert System Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")

    elif args.alerts:
        alerts = alert_system.get_active_alerts()
        if alerts:
            print("Active Alerts:")
            for alert in alerts:
                print(f"  [{alert.severity.upper()}] {alert.message}")
        else:
            print("No active alerts")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
