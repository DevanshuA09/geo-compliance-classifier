"""Test codename expansion functionality."""

import pytest

from artifact_preprocessor.expand_terms import CodenameExpander
from artifact_preprocessor.schema import CodenameHit


class TestCodenameExpansion:
    """Test suite for codename expansion."""
    
    @pytest.fixture
    def sample_terminology(self):
        """Sample terminology for testing."""
        return {
            "ASL": "Age-sensitive logic",
            "PF": "Personalized feed", 
            "GH": "Geo-handler; a module responsible for routing features based on user region",
            "CDS": "Compliance Detection System",
            "NR": "Not recommended",
            "BB": "Baseline Behavior; standard user behavior used for anomaly detection"
        }
    
    @pytest.fixture
    def expander(self, sample_terminology):
        """Create expander with sample terminology."""
        return CodenameExpander(sample_terminology)
    
    def test_basic_expansion(self, expander):
        """Test basic codename expansion."""
        text = "The PF uses ASL to detect minors."
        
        original_hash, expanded_text, hits = expander.expand_text(text)
        
        assert original_hash != ""
        assert "PF [Personalized feed]" in expanded_text
        assert "ASL [Age-sensitive logic]" in expanded_text
        assert len(hits) == 2
        
        # Check hit details
        pf_hit = next(h for h in hits if h.term == "PF")
        assert pf_hit.expansion == "Personalized feed"
        assert pf_hit.count == 1
        assert len(pf_hit.spans) == 1
        
        asl_hit = next(h for h in hits if h.term == "ASL")
        assert asl_hit.expansion == "Age-sensitive logic"
        assert asl_hit.count == 1
    
    def test_case_insensitive_matching(self, expander):
        """Test case-insensitive codename matching."""
        text = "The pf uses asl and GH for routing."
        
        _, expanded_text, hits = expander.expand_text(text)
        
        assert len(hits) == 3
        assert "pf [Personalized feed]" in expanded_text
        assert "asl [Age-sensitive logic]" in expanded_text
        assert "GH [Geo-handler" in expanded_text
    
    def test_word_boundary_matching(self, expander):
        """Test that expansion respects word boundaries."""
        text = "The PREFIX_PF and PF_SUFFIX don't match, but PF does."
        
        _, expanded_text, hits = expander.expand_text(text)
        
        # Only the standalone PF should be expanded
        assert len(hits) == 1
        assert hits[0].term == "PF"
        assert hits[0].count == 1
        assert "PREFIX_PF" in expanded_text  # Should remain unchanged
        assert "PF_SUFFIX" in expanded_text  # Should remain unchanged
        assert "PF [Personalized feed]" in expanded_text
    
    def test_multiple_occurrences(self, expander):
        """Test handling of multiple occurrences of the same term."""
        text = "PF is important. The PF algorithm uses PF data."
        
        _, expanded_text, hits = expander.expand_text(text)
        
        assert len(hits) == 1
        pf_hit = hits[0]
        assert pf_hit.term == "PF"
        assert pf_hit.count == 3
        assert len(pf_hit.spans) == 3
        
        # Only first occurrence should be expanded to keep text readable
        assert expanded_text.count("PF [Personalized feed]") == 1
        assert expanded_text.count("PF") == 3  # Two unexpanded + one in expansion
    
    def test_empty_text(self, expander):
        """Test expansion with empty text."""
        original_hash, expanded_text, hits = expander.expand_text("")
        
        assert original_hash == ""
        assert expanded_text == ""
        assert len(hits) == 0
    
    def test_no_matches(self, expander):
        """Test expansion when no terms match."""
        text = "This text contains no codenames to expand."
        
        original_hash, expanded_text, hits = expander.expand_text(text)
        
        assert original_hash != ""
        assert expanded_text == text  # Should remain unchanged
        assert len(hits) == 0
    
    def test_complex_text_expansion(self, expander):
        """Test expansion in complex text with multiple terms."""
        text = """
        The system uses PF to recommend content based on ASL detection.
        When GH determines the user's region, it applies NR policies.
        The CDS monitors all interactions and uses BB for anomaly detection.
        PF and ASL work together for compliance.
        """
        
        original_hash, expanded_text, hits = expander.expand_text(text)
        
        assert len(hits) == 6  # All 6 terms should be found
        
        # Check that all terms are found with correct counts
        term_counts = {hit.term: hit.count for hit in hits}
        assert term_counts["PF"] == 2
        assert term_counts["ASL"] == 2
        assert term_counts["GH"] == 1
        assert term_counts["NR"] == 1
        assert term_counts["CDS"] == 1
        assert term_counts["BB"] == 1
        
        # Verify expansions are inline
        assert "PF [Personalized feed]" in expanded_text
        assert "ASL [Age-sensitive logic]" in expanded_text
        assert "GH [Geo-handler" in expanded_text
    
    def test_deterministic_ordering(self, expander):
        """Test that expansion results are deterministic."""
        text = "BB, CDS, ASL, PF, NR, and GH are all codenames."
        
        # Run expansion multiple times
        results = []
        for _ in range(3):
            _, _, hits = expander.expand_text(text)
            results.append([(h.term, h.count) for h in hits])
        
        # All results should be identical
        assert all(result == results[0] for result in results)
        
        # Terms should be in sorted order
        terms = [h.term for h in hits]
        assert terms == sorted(terms)
    
    def test_span_positions(self, expander):
        """Test that span positions are correctly calculated."""
        text = "Start PF middle ASL end"
        
        _, _, hits = expander.expand_text(text)
        
        pf_hit = next(h for h in hits if h.term == "PF")
        asl_hit = next(h for h in hits if h.term == "ASL")
        
        # Check span positions
        pf_span = pf_hit.spans[0]
        asl_span = asl_hit.spans[0]
        
        assert text[pf_span[0]:pf_span[1]] == "PF"
        assert text[asl_span[0]:asl_span[1]] == "ASL"
        
        # PF should come before ASL
        assert pf_span[0] < asl_span[0]
    
    def test_special_characters_in_terms(self):
        """Test handling of terms with special characters."""
        terminology = {
            "T5": "Tier 5 sensitivity data",
            "C++": "Programming language",
            "API-v2": "Version 2 API"
        }
        expander = CodenameExpander(terminology)
        
        text = "Use T5 for sensitive data, C++ for performance, and API-v2 for integration."
        
        _, expanded_text, hits = expander.expand_text(text)
        
        assert len(hits) == 3
        assert "T5 [Tier 5 sensitivity data]" in expanded_text
        # Note: C++ might have issues with word boundaries, this tests the robustness


class TestCodenameValidation:
    """Test terminology validation functionality."""
    
    def test_validate_good_terminology(self):
        """Test validation of well-formed terminology."""
        terminology = {
            "ASL": "Age-sensitive logic",
            "PF": "Personalized feed"
        }
        expander = CodenameExpander(terminology)
        warnings = expander.validate_terminology()
        
        assert len(warnings) == 0
    
    def test_validate_empty_terminology(self):
        """Test validation of empty terminology."""
        expander = CodenameExpander({})
        warnings = expander.validate_terminology()
        
        assert "Empty terminology mapping" in warnings
    
    def test_validate_problematic_terms(self):
        """Test validation of problematic terminology."""
        terminology = {
            "": "Empty term",
            "A": "Very short term",
            "TERM": "",  # Empty explanation
            "SPEC@AL": "Term with special chars"
        }
        expander = CodenameExpander(terminology)
        warnings = expander.validate_terminology()
        
        assert any("Empty term" in w for w in warnings)
        assert any("Very short term" in w for w in warnings)  
        assert any("Empty explanation" in w for w in warnings)
        assert any("special characters" in w for w in warnings)
    
    def test_expansion_stats(self, sample_terminology):
        """Test expansion statistics calculation."""
        expander = CodenameExpander(sample_terminology)
        
        text = "PF uses ASL and GH for routing. PF is important."
        _, _, hits = expander.expand_text(text)
        
        stats = expander.get_expansion_stats(hits)
        
        assert stats['unique_terms'] == 3
        assert stats['total_occurrences'] == 4  # PF(2) + ASL(1) + GH(1)
        assert stats['coverage_ratio'] == 3 / 6  # 3 terms found out of 6 total
