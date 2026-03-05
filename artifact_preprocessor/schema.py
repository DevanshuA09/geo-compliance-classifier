"""Data schemas and structures for the Artifact Preprocessor Agent."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CodenameHit:
    """Represents a matched codename with expansion details."""

    term: str
    expansion: str
    count: int
    spans: List[Tuple[int, int]]  # [(start, end), ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "term": self.term,
            "expansion": self.expansion,
            "count": self.count,
            "spans": self.spans,
        }


@dataclass
class DocumentArtifact:
    """Raw document artifact with metadata."""

    doc_id: str
    doc_type: str  # pdf, docx, md, html, txt, csv
    source_path: str
    raw_text: str
    parse_warnings: List[str] = field(default_factory=list)

    @property
    def content_hash(self) -> str:
        """SHA256 hash of normalized raw text."""
        return hashlib.sha256(self.raw_text.encode("utf-8")).hexdigest()


@dataclass
class FeatureRecord:
    """Processed feature record with extracted fields and expansions."""

    # Core identifiers
    feature_id: str
    doc_id: str
    source_path: str

    # Document metadata
    date: Optional[str] = None

    # Feature content
    feature_title: Optional[str] = None
    feature_description: Optional[str] = None

    # Extracted sections
    objectives: Optional[str] = None
    user_segments: Optional[str] = None

    # Geographic information
    geo_country: Optional[str] = None
    geo_state: Optional[str] = None  # N/A for smaller countries with no states

    # Codename expansion
    codename_hits: List[CodenameHit] = field(default_factory=list)

    # Compliance analysis
    domain: Optional[str] = (
        None  # area of feature (recommendations, advertising, safety, etc.)
    )
    label: Optional[str] = None  # non-compliant, partially-compliant, compliant
    implicated_regulations: List[str] = field(
        default_factory=list
    )  # exact legal regulations
    data_practices: List[str] = field(
        default_factory=list
    )  # intervention_logs, content_analysis, etc.
    rationale: Optional[str] = None  # why the regulations apply to this feature
    risk_tags: List[str] = field(
        default_factory=list
    )  # addiction_risk, minor_targeting, etc.
    confidence_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON/CSV output."""
        return {
            "feature_id": self.feature_id,
            "doc_id": self.doc_id,
            "date": self.date,
            "feature_title": self.feature_title,
            "feature_description": self.feature_description,
            "objectives": self.objectives,
            "user_segments": self.user_segments,
            "geo_country": self.geo_country,
            "geo_state": self.geo_state,
            "codename_hits_json": [hit.to_dict() for hit in self.codename_hits],
            "source_path": self.source_path,
            "domain": self.domain,
            "label": self.label,
            "implicated_regulations": self.implicated_regulations,
            "data_practices": self.data_practices,
            "rationale": self.rationale,
            "risk_tags": self.risk_tags,
            "confidence_score": self.confidence_score,
        }


# JSON Schema for output validation
OUTPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "feature_id": {"type": "string"},
        "doc_id": {"type": "string"},
        "date": {"type": ["string", "null"]},
        "feature_title": {"type": ["string", "null"]},
        "feature_description": {"type": ["string", "null"]},
        "objectives": {"type": ["string", "null"]},
        "user_segments": {"type": ["string", "null"]},
        "geo_country": {"type": ["string", "null"]},
        "geo_state": {"type": ["string", "null"]},
        "codename_hits_json": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "term": {"type": "string"},
                    "expansion": {"type": "string"},
                    "count": {"type": "integer"},
                    "spans": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "minItems": 2,
                            "maxItems": 2,
                        },
                    },
                },
                "required": ["term", "expansion", "count", "spans"],
            },
        },
        "source_path": {"type": "string"},
        "domain": {"type": ["string", "null"]},
        "label": {
            "type": ["string", "null"],
            "enum": ["non-compliant", "partially-compliant", "compliant", None],
        },
        "implicated_regulations": {"type": "array", "items": {"type": "string"}},
        "data_practices": {"type": "array", "items": {"type": "string"}},
        "rationale": {"type": ["string", "null"]},
        "risk_tags": {"type": "array", "items": {"type": "string"}},
        "confidence_score": {"type": ["number", "null"]},
    },
    "required": [
        "feature_id",
        "doc_id",
        "codename_hits_json",
        "source_path",
        "implicated_regulations",
        "data_practices",
        "risk_tags",
    ],
}
