"""
Evidence System Package

Centralized evidence logging, export, and monitoring for compliance decisions.
"""

from .evidence_exporter import EvidenceExporter
from .evidence_logger import (EvidenceLogger, get_evidence_logger,
                              log_compliance_decision)
from .evidence_verifier import EvidenceVerificationAgent

# Advanced features (optional dependencies)
try:
    from .evidence_alerts import EvidenceAlertSystem
    from .evidence_monitor import EvidenceMonitor
except ImportError:
    EvidenceMonitor = None
    EvidenceAlertSystem = None

__all__ = [
    "EvidenceLogger",
    "get_evidence_logger",
    "log_compliance_decision",
    "EvidenceExporter",
    "EvidenceVerificationAgent",
    "EvidenceMonitor",
    "EvidenceAlertSystem",
]
