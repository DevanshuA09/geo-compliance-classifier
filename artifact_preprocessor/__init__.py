"""Artifact Preprocessor Agent - Normalize PRD/TRD inputs and expand TikTok codenames."""

__version__ = "1.0.0"

from .schema import DocumentArtifact, FeatureRecord, CodenameHit

__all__ = ["DocumentArtifact", "FeatureRecord", "CodenameHit"]
