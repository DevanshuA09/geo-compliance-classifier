"""Field extraction from normalized document text."""

import re
from typing import Dict, List, Optional, Tuple

from .logging_conf import get_logger
from .normalize import clean_extracted_field

logger = get_logger(__name__)


class FieldExtractor:
    """Extract structured fields from document text using header/keyword heuristics."""

    def __init__(self):
        """Initialize the field extractor with patterns."""
        self.field_patterns = self._build_field_patterns()

    def extract_fields(self, text: str) -> Dict[str, Optional[str]]:
        """Extract all fields from document text.

        Args:
            text: Normalized document text

        Returns:
            Dictionary of extracted fields
        """
        # Split text into sections based on headings
        sections = self._split_into_sections(text)

        # Extract fields using pattern matching
        fields = {}
        for field_name, patterns in self.field_patterns.items():
            fields[field_name] = self._extract_field(sections, patterns)

        # Post-process and clean fields
        for field_name, value in fields.items():
            fields[field_name] = clean_extracted_field(value)

        logger.debug(
            f"Extracted {sum(1 for v in fields.values() if v)} non-empty fields"
        )
        return fields

    def _build_field_patterns(self) -> Dict[str, List[str]]:
        """Build regex patterns for each field type.

        Returns:
            Dictionary mapping field names to pattern lists
        """
        return {
            "date": [
                r"(?i)^date:?\s*(.+)$",
                r"(?i)^created:?\s*(.+)$",
                r"(?i)^updated:?\s*(.+)$",
                r"(?i)^last\s+modified:?\s*(.+)$",
                r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                r"(\d{4}-\d{1,2}-\d{1,2})",
                r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})",
            ],
            "feature_title": [
                r"(?i)^feature\s+name:?\s*(.+)$",
                r"(?i)^feature\s+title:?\s*(.+)$",
                r"(?i)^feature:?\s*(.+)$",
                r"(?i)^title:?\s*(.+)$",
            ],
            "feature_description": [
                r"(?i)^(?:feature\s+)?description:?\s*(.+)$",
                r"(?i)^summary:?\s*(.+)$",
                r"(?i)^overview:?\s*(.+)$",
            ],
            "objectives": [
                r"(?i)^objectives?:?\s*(.+)$",
                r"(?i)^goals?:?\s*(.+)$",
                r"(?i)^purpose:?\s*(.+)$",
                r"(?i)^aims?:?\s*(.+)$",
            ],
            "user_segments": [
                r"(?i)^(?:target\s+)?users?:?\s*(.+)$",
                r"(?i)^(?:user\s+)?segments?:?\s*(.+)$",
                r"(?i)^audience:?\s*(.+)$",
                r"(?i)^demographics:?\s*(.+)$",
            ],
            "geo_country": [
                r"(?i)^country:?\s*(.+)$",
                r"(?i)^countries:?\s*(.+)$",
                r"(?i)^nation:?\s*(.+)$",
                r"(?i)^jurisdiction:?\s*(.+)$",
            ],
            "geo_state": [
                r"(?i)^state:?\s*(.+)$",
                r"(?i)^province:?\s*(.+)$",
                r"(?i)^region:?\s*(.+)$",
                r"(?i)^territory:?\s*(.+)$",
            ],
        }

    def _split_into_sections(self, text: str) -> List[Tuple[str, str]]:
        """Split text into sections based on headings.

        Args:
            text: Document text

        Returns:
            List of (heading, content) tuples
        """
        lines = text.split("\n")
        sections = []
        current_heading = ""
        current_content = []

        for line in lines:
            stripped = line.strip()

            # Check if this line is a heading
            if self._is_section_heading(stripped):
                # Save previous section
                if current_heading or current_content:
                    content = "\n".join(current_content).strip()
                    sections.append((current_heading, content))

                # Start new section
                current_heading = stripped
                current_content = []
            else:
                current_content.append(line)

        # Add final section
        if current_heading or current_content:
            content = "\n".join(current_content).strip()
            sections.append((current_heading, content))

        return sections

    def _is_section_heading(self, line: str) -> bool:
        """Check if a line appears to be a section heading.

        Args:
            line: Line to check

        Returns:
            True if line appears to be a heading
        """
        if not line:
            return False

        # Markdown headings
        if re.match(r"^#{1,6}\s+", line):
            return True

        # Lines ending with colon
        if line.endswith(":") and len(line) < 100:
            return True

        # Short uppercase lines
        if line.isupper() and len(line) < 80 and not re.search(r"[.!?]$", line):
            return True

        # Lines that match common heading patterns
        heading_keywords = [
            "title",
            "description",
            "objective",
            "goal",
            "scope",
            "overview",
            "summary",
            "background",
            "purpose",
            "requirements",
            "specifications",
            "implementation",
            "testing",
            "deployment",
            "rollout",
            "timeline",
            "risks",
            "safety",
            "privacy",
            "security",
            "compliance",
            "legal",
            "questions",
            "issues",
            "assumptions",
            "dependencies",
            "appendix",
        ]

        for keyword in heading_keywords:
            if re.match(rf"(?i)^{keyword}s?:?\s*$", line.strip()):
                return True

        return False

    def _extract_field(
        self, sections: List[Tuple[str, str]], patterns: List[str]
    ) -> Optional[str]:
        """Extract a field value using patterns.

        Args:
            sections: Document sections as (heading, content) tuples
            patterns: Regex patterns to match

        Returns:
            Extracted field value or None
        """
        # Try to match patterns in section headings and content
        for heading, content in sections:
            # Check patterns against heading
            for pattern in patterns:
                match = re.search(pattern, heading, re.MULTILINE | re.IGNORECASE)
                if match:
                    result = (
                        match.group(1).strip()
                        if match.groups()
                        else match.group(0).strip()
                    )
                    if result:
                        return result

            # Check patterns against content (first few lines)
            content_lines = content.split("\n")[:5]  # Only check first 5 lines
            for line in content_lines:
                for pattern in patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        result = (
                            match.group(1).strip()
                            if match.groups()
                            else match.group(0).strip()
                        )
                        if result:
                            return result

        # If no specific match found, try fuzzy matching for section content
        for heading, content in sections:
            if self._heading_matches_field(heading, patterns):
                # Return the content of this section
                if content.strip():
                    return content.strip()

        return None

    def _heading_matches_field(self, heading: str, patterns: List[str]) -> bool:
        """Check if a heading fuzzy matches any of the field patterns.

        Args:
            heading: Section heading
            patterns: Field patterns to match against

        Returns:
            True if heading matches field
        """
        heading_lower = heading.lower().strip(":")

        # Extract keywords from patterns
        field_keywords = set()
        for pattern in patterns:
            # Extract word characters from pattern
            words = re.findall(r"\b\w+\b", pattern.lower())
            field_keywords.update(words)

        # Remove common regex keywords
        field_keywords.discard("i")
        field_keywords.discard("s")

        # Check if any keywords appear in heading
        for keyword in field_keywords:
            if len(keyword) > 2 and keyword in heading_lower:
                return True

        return False
