"""Text normalization utilities."""

import re
from typing import Optional

from .logging_conf import get_logger

logger = get_logger(__name__)


def normalize_text(text: str) -> str:
    """Normalize text by cleaning whitespace, bullets, and headings.

    Args:
        text: Raw text to normalize

    Returns:
        Normalized text
    """
    if not text:
        return ""

    # Strip boilerplate patterns (common footer/header text)
    text = _remove_boilerplate(text)

    # Normalize line endings
    text = re.sub(r"\r\n|\r", "\n", text)

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)  # Multiple spaces/tabs to single space
    text = re.sub(r"\n[ \t]+", "\n", text)  # Remove leading whitespace on lines
    text = re.sub(r"[ \t]+\n", "\n", text)  # Remove trailing whitespace on lines

    # Normalize bullet points
    text = _normalize_bullets(text)

    # Normalize headings
    text = _normalize_headings(text)

    # Collapse excessive blank lines (keep maximum 2)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def _remove_boilerplate(text: str) -> str:
    """Remove common boilerplate text patterns.

    Args:
        text: Input text

    Returns:
        Text with boilerplate removed
    """
    # Common boilerplate patterns
    boilerplate_patterns = [
        r"(?i)confidential.*?not.*?distribute",
        r"(?i)this.*?document.*?proprietary",
        r"(?i)copyright.*?\d{4}",
        r"(?i)page \d+ of \d+",
        r"(?i)printed on.*?\d{4}",
        r"(?i)document.*?version.*?\d+\.\d+",
    ]

    for pattern in boilerplate_patterns:
        text = re.sub(pattern, "", text)

    return text


def _normalize_bullets(text: str) -> str:
    """Normalize bullet point formats.

    Args:
        text: Input text

    Returns:
        Text with normalized bullets
    """
    # Convert various bullet formats to standard dash
    bullet_patterns = [
        (r"^[\s]*[•·▪▫‣⁃]\s*", "- "),  # Unicode bullets
        (r"^[\s]*[*]\s*", "- "),  # Asterisk bullets
        (r"^[\s]*[+]\s*", "- "),  # Plus bullets
        (r"^[\s]*[\d]+\.\s*", "- "),  # Numbered lists to bullets
        (r"^[\s]*[a-zA-Z]\.\s*", "- "),  # Lettered lists to bullets
    ]

    lines = text.split("\n")
    normalized_lines = []

    for line in lines:
        for pattern, replacement in bullet_patterns:
            if re.match(pattern, line):
                line = re.sub(pattern, replacement, line)
                break
        normalized_lines.append(line)

    return "\n".join(normalized_lines)


def _normalize_headings(text: str) -> str:
    """Normalize heading formats.

    Args:
        text: Input text

    Returns:
        Text with normalized headings
    """
    lines = text.split("\n")
    normalized_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            normalized_lines.append(line)
            continue

        # Check if this looks like a heading
        if _is_heading_line(stripped, lines, i):
            # Ensure heading has proper spacing
            if normalized_lines and normalized_lines[-1].strip():
                normalized_lines.append("")  # Add blank line before heading
            normalized_lines.append(stripped)
            # Add blank line after heading if next line isn't empty
            if i + 1 < len(lines) and lines[i + 1].strip():
                normalized_lines.append("")
        else:
            normalized_lines.append(line)

    return "\n".join(normalized_lines)


def _is_heading_line(line: str, all_lines: list, line_index: int) -> bool:
    """Determine if a line is likely a heading.

    Args:
        line: The line to check
        all_lines: All lines in the document
        line_index: Index of the current line

    Returns:
        True if line appears to be a heading
    """
    # Check for markdown-style headings
    if re.match(r"^#{1,6}\s+", line):
        return True

    # Check for ALL CAPS headings (short lines)
    if line.isupper() and len(line) < 100 and not re.search(r"[.!?]$", line):
        return True

    # Check for title case headings that end with colons
    if line.endswith(":") and len(line) < 100:
        words = line[:-1].split()
        if len(words) > 0 and all(word[0].isupper() for word in words if word):
            return True

    # Check for underlined headings (next line is dashes or equals)
    if line_index + 1 < len(all_lines):
        next_line = all_lines[line_index + 1].strip()
        if re.match(r"^[-=]{3,}$", next_line) and len(next_line) >= len(line) * 0.8:
            return True

    return False


def clean_extracted_field(text: Optional[str]) -> Optional[str]:
    """Clean and normalize extracted field text.

    Args:
        text: Raw field text

    Returns:
        Cleaned text or None if empty
    """
    if not text:
        return None

    # Basic cleaning
    text = text.strip()
    if not text:
        return None

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove common field prefixes/suffixes
    text = re.sub(
        r"^(description|objective|scope|summary):\s*", "", text, flags=re.IGNORECASE
    )
    text = re.sub(r"\s*[-–—]\s*$", "", text)  # Remove trailing dashes

    return text if text else None
