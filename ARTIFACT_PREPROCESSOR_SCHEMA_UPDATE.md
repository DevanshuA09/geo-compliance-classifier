# Artifact Preprocessor Schema Update

## Overview
Updated the artifact preprocessor schema to align with the geo-compliance classifier requirements, keeping only necessary properties and adding new compliance-related fields.

## Changes Made

### FeatureRecord Schema Updates

#### Removed Properties:
- `doc_type` - No longer needed
- `doc_title` - Removed to focus on feature-level data
- `version` - Not relevant for compliance analysis
- `authors` - Not needed for compliance tracking
- `scope` - Replaced with more specific fields
- `risk_safety` - Replaced with structured compliance fields
- `privacy_data` - Replaced with structured compliance fields
- `age_gating` - Replaced with structured compliance fields
- `geo_regions` - Split into `geo_country` and `geo_state`
- `rollout` - Not needed for compliance analysis
- `open_questions` - Not relevant for compliance tracking
- `appendix_raw` - Not needed
- `text_original_hash` - Not needed for compliance
- `text_expanded_hash` - Not needed for compliance
- `parse_warnings` - Simplified processing

#### Kept Properties:
- `feature_id` - Core identifier
- `doc_id` - Document reference
- `date` - Document/feature date
- `feature_title` - Feature name
- `feature_description` - Feature description
- `objectives` - Feature objectives
- `user_segments` - Target user segments
- `codename_hits_json` - Codename expansion data
- `source_path` - Source file path

#### Added Properties:
- `geo_country` - Country where feature operates (replaces geo_regions)
- `geo_state` - State/province (N/A for smaller countries)
- `domain` - Feature area (recommendations, advertising, safety, etc.)
- `label` - Compliance status (non-compliant, partially-compliant, compliant)
- `implicated_regulations` - List of exact legal regulations that apply
- `data_practices` - List of data practices (intervention_logs, content_analysis, etc.)
- `rationale` - Explanation of why regulations apply to this feature
- `risk_tags` - List of risk categories (addiction_risk, minor_targeting, etc.)
- `confidence_score` - Confidence in the compliance assessment

### Updated Files

#### 1. `schema.py`
- Updated `FeatureRecord` dataclass with new field structure
- Updated `to_dict()` method to output only needed fields
- Updated `OUTPUT_SCHEMA` JSON schema for validation
- Added proper type hints and enums for new fields

#### 2. `cli.py`
- Updated `FeatureRecord` instantiation to use new schema
- Removed references to deleted fields
- Updated field extraction calls

#### 3. `extract.py`
- Updated `_build_field_patterns()` to only extract needed fields
- Added patterns for `geo_country` and `geo_state`
- Removed patterns for deleted fields

#### 4. `reporter.py`
- Updated field statistics calculation for new schema
- Replaced document type breakdown with domain breakdown
- Updated field names in reports
- Removed references to parse_warnings

## Data Structure Alignment

The new schema aligns with the `generated_features.jsonl` structure:

```python
# Example aligned fields:
{
    "feature_id": "GEN-0001",
    "domain": "advertising", 
    "geo_country": "USA",
    "geo_state": "Texas",
    "label": "Compliant",
    "implicated_regulations": ["US-2258A"],
    "data_practices": ["browsing_behavior", "demographic_data"],
    "rationale": "Feature meets all requirements...",
    "risk_tags": ["minor_targeting"],
    "confidence_score": 0.79
}
```

## Validation

All changes have been tested and validated:
- ✅ Schema imports successfully
- ✅ CLI module imports successfully
- ✅ JSON schema validation updated
- ✅ Field extraction patterns updated
- ✅ No syntax errors

## Usage

The updated artifact preprocessor now produces output that's compatible with the geo-compliance classifier system, focusing on compliance-relevant fields while maintaining the core document processing capabilities.
