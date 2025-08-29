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
            "spans": self.spans
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
        return hashlib.sha256(self.raw_text.encode('utf-8')).hexdigest()


@dataclass
class FeatureRecord:
    """Processed feature record with extracted fields and expansions."""
    # Core identifiers
    feature_id: str
    doc_id: str
    doc_type: str
    source_path: str
    
    # Document metadata
    doc_title: Optional[str] = None
    version: Optional[str] = None
    authors: Optional[str] = None
    date: Optional[str] = None
    
    # Feature content
    feature_title: Optional[str] = None
    feature_description: Optional[str] = None
    
    # Extracted sections
    objectives: Optional[str] = None
    scope: Optional[str] = None
    user_segments: Optional[str] = None
    risk_safety: Optional[str] = None
    privacy_data: Optional[str] = None
    age_gating: Optional[str] = None
    geo_regions: Optional[str] = None
    rollout: Optional[str] = None
    open_questions: Optional[str] = None
    appendix_raw: Optional[str] = None
    
    # Text hashes
    text_original_hash: str = ""
    text_expanded_hash: str = ""
    
    # Codename expansion
    codename_hits: List[CodenameHit] = field(default_factory=list)
    
    # Processing metadata
    parse_warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON/CSV output."""
        return {
            "feature_id": self.feature_id,
            "doc_id": self.doc_id,
            "doc_type": self.doc_type,
            "doc_title": self.doc_title,
            "version": self.version,
            "authors": self.authors,
            "date": self.date,
            "feature_title": self.feature_title,
            "feature_description": self.feature_description,
            "objectives": self.objectives,
            "scope": self.scope,
            "user_segments": self.user_segments,
            "risk_safety": self.risk_safety,
            "privacy_data": self.privacy_data,
            "age_gating": self.age_gating,
            "geo_regions": self.geo_regions,
            "rollout": self.rollout,
            "open_questions": self.open_questions,
            "text_original_hash": self.text_original_hash,
            "text_expanded_hash": self.text_expanded_hash,
            "codename_hits_json": [hit.to_dict() for hit in self.codename_hits],
            "parse_warnings": "; ".join(self.parse_warnings),
            "source_path": self.source_path
        }


# JSON Schema for output validation
OUTPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "feature_id": {"type": "string"},
        "doc_id": {"type": "string"},
        "doc_type": {"type": "string"},
        "doc_title": {"type": ["string", "null"]},
        "version": {"type": ["string", "null"]},
        "authors": {"type": ["string", "null"]},
        "date": {"type": ["string", "null"]},
        "feature_title": {"type": ["string", "null"]},
        "feature_description": {"type": ["string", "null"]},
        "objectives": {"type": ["string", "null"]},
        "scope": {"type": ["string", "null"]},
        "user_segments": {"type": ["string", "null"]},
        "risk_safety": {"type": ["string", "null"]},
        "privacy_data": {"type": ["string", "null"]},
        "age_gating": {"type": ["string", "null"]},
        "geo_regions": {"type": ["string", "null"]},
        "rollout": {"type": ["string", "null"]},
        "open_questions": {"type": ["string", "null"]},
        "text_original_hash": {"type": "string"},
        "text_expanded_hash": {"type": "string"},
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
                            "maxItems": 2
                        }
                    }
                },
                "required": ["term", "expansion", "count", "spans"]
            }
        },
        "parse_warnings": {"type": "string"},
        "source_path": {"type": "string"}
    },
    "required": ["feature_id", "doc_id", "doc_type", "text_original_hash", 
                "text_expanded_hash", "codename_hits_json", "parse_warnings", "source_path"]
}
