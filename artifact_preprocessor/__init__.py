"""Artifact Preprocessor Agent - Normalize PRD/TRD inputs and expand TikTok codenames."""

__version__ = "1.0.0"

from .schema import CodenameHit, DocumentArtifact, FeatureRecord

__all__ = ["DocumentArtifact", "FeatureRecord", "CodenameHit"]
