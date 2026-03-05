"""
TikTok Feature Generator Package

A comprehensive synthetic feature generation system for geo-compliance classification training data.

Features:
- Template-based feature synthesis across 7 product domains
- Rule-based compliance evaluation for 4 jurisdictions  
- Configurable geographic and label distributions
- CLI interface for batch generation
- Export to JSONL, CSV, and analysis reports

Usage:
    from featuregen import TikTokFeatureGenerator
    
    generator = TikTokFeatureGenerator(seed=42)
    features = generator.generate_features(
        n=100, 
        geo_filters=['EU', 'US-CA'], 
        target_mix={'Compliant': 0.4, 'Partially Compliant': 0.3, 'Non-Compliant': 0.3}
    )
    
CLI Usage:
    python -m featuregen.cli --n 200 --geo EU,US-CA,US-FL --label_mix 0.4,0.3,0.3 --out ./output
"""

__version__ = "1.0.0"
__author__ = "TikTok TechJam Team"

# Import main classes for easy access
import sys
from pathlib import Path

# Add parent directory to path to import the main generator
sys.path.append(str(Path(__file__).parent.parent))

try:
    from ignored.tiktok_feature_generator import FeatureData, TikTokFeatureGenerator

    __all__ = ["TikTokFeatureGenerator", "FeatureData"]
except ImportError:
    # Fallback for when running as standalone module
    __all__ = []
