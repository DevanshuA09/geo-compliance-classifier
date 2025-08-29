"""Codename expansion using terminology table."""

import hashlib
import re
from typing import Dict, List, Tuple

from .logging_conf import get_logger
from .schema import CodenameHit

logger = get_logger(__name__)


class CodenameExpander:
    """Expand TikTok codenames using terminology table with word-boundary matching."""
    
    def __init__(self, terminology: Dict[str, str]):
        """Initialize expander with terminology mapping.
        
        Args:
            terminology: Dictionary mapping terms to explanations
        """
        self.terminology = terminology
        self.compiled_patterns = self._compile_patterns()
        logger.info(f"Initialized expander with {len(terminology)} terms")
    
    def expand_text(self, text: str) -> Tuple[str, str, List[CodenameHit]]:
        """Expand codenames in text with inline annotations.
        
        Args:
            text: Original text to expand
            
        Returns:
            Tuple of (original_hash, expanded_text, hits_list)
        """
        if not text:
            return "", "", []
        
        # Calculate hash of original text
        original_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        
        # Find all matches and their positions
        all_matches = []
        for term, pattern in self.compiled_patterns.items():
            for match in pattern.finditer(text):
                all_matches.append({
                    'term': term,
                    'match': match,
                    'start': match.start(),
                    'end': match.end(),
                    'matched_text': match.group()
                })
        
        # Sort matches by position (reverse order for replacement)
        all_matches.sort(key=lambda x: x['start'], reverse=True)
        
        # Group matches by term for hit counting
        term_matches = {}
        for match_info in all_matches:
            term = match_info['term']
            if term not in term_matches:
                term_matches[term] = []
            term_matches[term].append(match_info)
        
        # Build hits list with deduplicated entries
        hits = []
        for term in sorted(term_matches.keys()):  # Deterministic order
            matches = term_matches[term]
            spans = [(m['start'], m['end']) for m in matches]
            
            hit = CodenameHit(
                term=term,
                expansion=self.terminology[term],
                count=len(matches),
                spans=spans
            )
            hits.append(hit)
        
        # Create expanded text with inline annotations
        expanded_text = text
        processed_terms = set()  # Track to avoid duplicate expansions
        
        for match_info in all_matches:
            term = match_info['term']
            start = match_info['start']
            end = match_info['end']
            matched_text = match_info['matched_text']
            
            # Only expand first occurrence of each term to keep text readable
            if term in processed_terms:
                continue
            processed_terms.add(term)
            
            # Create expansion with inline annotation
            expansion = f"{matched_text} [{self.terminology[term]}]"
            
            # Replace in text
            expanded_text = expanded_text[:start] + expansion + expanded_text[end:]
            
            # Adjust positions of remaining matches
            offset = len(expansion) - len(matched_text)
            for other_match in all_matches:
                if other_match['start'] < start:
                    other_match['start'] += offset
                    other_match['end'] += offset
        
        # Calculate hash of expanded text
        expanded_hash = hashlib.sha256(expanded_text.encode('utf-8')).hexdigest()
        
        logger.debug(f"Expanded {len(hits)} unique terms with {sum(h.count for h in hits)} total occurrences")
        
        return original_hash, expanded_text, hits
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for all terms with word boundaries.
        
        Returns:
            Dictionary mapping terms to compiled patterns
        """
        patterns = {}
        
        for term, explanation in self.terminology.items():
            # Create case-insensitive word-boundary pattern
            # Handle terms that might contain special regex characters
            escaped_term = re.escape(term)
            
            # Use word boundaries for clean matching
            pattern = rf'\b{escaped_term}\b'
            
            try:
                compiled = re.compile(pattern, re.IGNORECASE)
                patterns[term] = compiled
            except re.error as e:
                logger.warning(f"Failed to compile pattern for term '{term}': {e}")
                continue
        
        logger.debug(f"Compiled {len(patterns)} term patterns")
        return patterns
    
    def get_expansion_stats(self, hits: List[CodenameHit]) -> Dict[str, int]:
        """Get statistics about codename expansions.
        
        Args:
            hits: List of codename hits
            
        Returns:
            Dictionary with expansion statistics
        """
        stats = {
            'unique_terms': len(hits),
            'total_occurrences': sum(hit.count for hit in hits),
            'coverage_ratio': len(hits) / len(self.terminology) if self.terminology else 0.0
        }
        
        return stats
    
    def validate_terminology(self) -> List[str]:
        """Validate terminology mapping and return any issues.
        
        Returns:
            List of validation warnings
        """
        warnings = []
        
        if not self.terminology:
            warnings.append("Empty terminology mapping")
            return warnings
        
        for term, explanation in self.terminology.items():
            if not term.strip():
                warnings.append("Empty term found")
                continue
            
            if not explanation.strip():
                warnings.append(f"Empty explanation for term '{term}'")
            
            # Check for potentially problematic terms
            if len(term) < 2:
                warnings.append(f"Very short term '{term}' may cause false matches")
            
            if re.search(r'[^a-zA-Z0-9_-]', term):
                warnings.append(f"Term '{term}' contains special characters")
        
        # Check for duplicate terms (case-insensitive)
        seen_terms = set()
        for term in self.terminology.keys():
            term_lower = term.lower()
            if term_lower in seen_terms:
                warnings.append(f"Duplicate term found (case-insensitive): '{term}'")
            seen_terms.add(term_lower)
        
        return warnings
