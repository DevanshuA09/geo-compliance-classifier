"""Test field extraction functionality."""

import pytest

from artifact_preprocessor.extract import FieldExtractor
from artifact_preprocessor.normalize import normalize_text


class TestFieldExtraction:
    """Test suite for field extraction."""
    
    @pytest.fixture
    def extractor(self):
        """Create field extractor instance."""
        return FieldExtractor()
    
    def test_extract_basic_fields(self, extractor):
        """Test extraction of basic document fields."""
        text = """
        Title: Test Feature Document
        
        Version: 1.2.3
        
        Authors: John Doe, Jane Smith
        
        Date: 2024-01-15
        
        Feature Description: This is a comprehensive test feature
        that spans multiple lines and includes detailed information.
        
        Objectives:
        - Improve user experience
        - Enhance security
        - Reduce latency
        
        Scope: This feature applies to all mobile users
        in the United States and Canada.
        """
        
        normalized = normalize_text(text)
        fields = extractor.extract_fields(normalized)
        
        assert fields['doc_title'] == "Test Feature Document"
        assert fields['version'] == "1.2.3"
        assert fields['authors'] == "John Doe, Jane Smith"
        assert fields['date'] == "2024-01-15"
        assert "comprehensive test feature" in fields['feature_description']
        assert "Improve user experience" in fields['objectives']
        assert "mobile users" in fields['scope']
    
    def test_extract_compliance_fields(self, extractor):
        """Test extraction of compliance-related fields."""
        text = """
        Risk Assessment: High risk due to data collection
        
        Privacy Data: Collects user location and device information
        
        Age Gating: Restricted for users under 13 years old
        
        Geo Regions: United States, European Union, Canada
        
        Rollout: Phase 1 - Beta testing (Q1)
        Phase 2 - Full release (Q2)
        
        Open Questions:
        - How to handle GDPR compliance?
        - What about cross-border data transfers?
        """
        
        normalized = normalize_text(text)
        fields = extractor.extract_fields(normalized)
        
        assert "High risk" in fields['risk_safety']
        assert "location and device" in fields['privacy_data']
        assert "under 13" in fields['age_gating']
        assert "European Union" in fields['geo_regions']
        assert "Phase 1" in fields['rollout']
        assert "GDPR compliance" in fields['open_questions']
    
    def test_extract_case_insensitive(self, extractor):
        """Test case-insensitive field extraction."""
        text = """
        TITLE: Uppercase Title
        
        description: Lowercase description field
        
        OBJECTIVES: Mixed case objectives
        """
        
        normalized = normalize_text(text)
        fields = extractor.extract_fields(normalized)
        
        assert fields['doc_title'] == "Uppercase Title"
        assert fields['feature_description'] == "Lowercase description field"
        assert fields['objectives'] == "Mixed case objectives"
    
    def test_extract_with_colons_and_formatting(self, extractor):
        """Test extraction with various formatting styles."""
        text = """
        Feature Name: Advanced Search
        
        Summary:
        This feature provides advanced search capabilities
        with filters and sorting options.
        
        User Segments:
        - Power users
        - Premium subscribers
        - Admin users
        
        Timeline:
        Development: 6 weeks
        Testing: 2 weeks
        Release: Q3 2024
        """
        
        normalized = normalize_text(text)
        fields = extractor.extract_fields(normalized)
        
        assert fields['feature_title'] == "Advanced Search"
        assert "advanced search capabilities" in fields['feature_description']
        assert "Power users" in fields['user_segments']
        assert "Q3 2024" in fields['rollout']
    
    def test_extract_missing_fields(self, extractor):
        """Test extraction when fields are missing."""
        text = """
        This is a document with minimal structure.
        
        It has some content but no clear field headers.
        Just plain text without formal sections.
        """
        
        normalized = normalize_text(text)
        fields = extractor.extract_fields(normalized)
        
        # Most fields should be None for unstructured text
        assert fields['doc_title'] is None
        assert fields['version'] is None
        assert fields['authors'] is None
        assert fields['feature_title'] is None
        assert fields['objectives'] is None
    
    def test_extract_fuzzy_matching(self, extractor):
        """Test fuzzy matching for field headers."""
        text = """
        Document Title: Fuzzy Matching Test
        
        Feature Summary: This tests fuzzy header matching
        
        Goals and Objectives: Test fuzzy recognition
        
        Safety Considerations: Important safety notes
        
        Privacy and Data Protection: Privacy details
        """
        
        normalized = normalize_text(text)
        fields = extractor.extract_fields(normalized)
        
        assert fields['doc_title'] == "Fuzzy Matching Test"
        assert "fuzzy header matching" in fields['feature_description']
        assert "fuzzy recognition" in fields['objectives']
        assert "safety notes" in fields['risk_safety']
        assert "Privacy details" in fields['privacy_data']
    
    def test_extract_multiline_content(self, extractor):
        """Test extraction of multiline field content."""
        text = """
        Objectives:
        The main objectives of this feature are:
        1. Improve user engagement by 25%
        2. Reduce server load through caching
        3. Enhance accessibility compliance
        4. Support new mobile platforms
        
        The implementation will focus on performance
        and user experience improvements.
        
        Next Section: Different content
        """
        
        normalized = normalize_text(text)
        fields = extractor.extract_fields(normalized)
        
        objectives = fields['objectives']
        assert "main objectives" in objectives
        assert "25%" in objectives
        assert "caching" in objectives
        assert "accessibility" in objectives
        assert "mobile platforms" in objectives
        assert "performance" in objectives
        # Should not include content from next section
        assert "Next Section" not in objectives


class TestFieldNormalization:
    """Test field normalization and cleaning."""
    
    def test_clean_field_prefixes(self, extractor):
        """Test removal of common field prefixes."""
        text = """
        Description: This is the actual description content
        
        Objective: Remove the objective prefix
        
        Scope: Clean scope content
        """
        
        normalized = normalize_text(text)
        fields = extractor.extract_fields(normalized)
        
        # Prefixes should be cleaned
        assert fields['feature_description'] == "This is the actual description content"
        assert fields['objectives'] == "Remove the objective prefix"
        assert fields['scope'] == "Clean scope content"
    
    def test_clean_empty_fields(self, extractor):
        """Test handling of empty fields."""
        text = """
        Title: 
        
        Description:   
        
        Version: 1.0
        
        Authors:
        """
        
        normalized = normalize_text(text)
        fields = extractor.extract_fields(normalized)
        
        # Empty fields should be None
        assert fields['doc_title'] is None
        assert fields['feature_description'] is None
        assert fields['authors'] is None
        # Non-empty field should be preserved
        assert fields['version'] == "1.0"
