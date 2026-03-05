"""
Text chunking pipeline with section-aware splitting.
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

from ingest.loader import DocumentLoader
from retriever.models import LegalDocument, TextChunk

logger = logging.getLogger(__name__)


@dataclass
class ChunkingConfig:
    """Configuration for text chunking."""

    min_chars: int = 600
    max_chars: int = 900
    overlap_ratio: float = 0.15
    preserve_sections: bool = True


class TextChunker:
    """Intelligent text chunker for legal documents."""

    def __init__(self, config: ChunkingConfig):
        """Initialize chunker with configuration."""
        self.config = config
        self.overlap_chars = int(config.max_chars * config.overlap_ratio)
        self.loader = DocumentLoader()

    def chunk_document(self, document: LegalDocument) -> List[TextChunk]:
        """
        Chunk a legal document into overlapping segments.

        Preserves section boundaries and maintains metadata.
        """
        sections = self.loader.detect_sections(document.law_id, document.content)
        chunks = []

        for section_label, start_line, end_line in sections:
            section_chunks = self._chunk_section(
                document, section_label, start_line, end_line
            )
            chunks.extend(section_chunks)

        logger.info(f"Generated {len(chunks)} chunks for {document.law_id}")
        return chunks

    def _chunk_section(
        self,
        document: LegalDocument,
        section_label: str,
        start_line: int,
        end_line: int,
    ) -> List[TextChunk]:
        """Chunk a specific section of a document."""
        lines = document.content.splitlines()
        section_lines = lines[start_line : end_line + 1]
        section_text = "\\n".join(section_lines)

        # Calculate character positions
        char_start = len("\\n".join(lines[:start_line]))
        if start_line > 0:
            char_start += 1  # Account for newline

        chunks = []

        if len(section_text) <= self.config.max_chars:
            # Section fits in one chunk
            chunk = self._create_chunk(
                document,
                section_label,
                section_text,
                start_line,
                end_line,
                char_start,
                char_start + len(section_text),
            )
            chunks.append(chunk)
        else:
            # Split section into multiple chunks
            section_chunks = self._split_with_overlap(
                document, section_label, section_text, start_line, char_start
            )
            chunks.extend(section_chunks)

        return chunks

    def _split_with_overlap(
        self,
        document: LegalDocument,
        section_label: str,
        text: str,
        base_line: int,
        base_char_pos: int,
    ) -> List[TextChunk]:
        """Split text into overlapping chunks."""
        chunks = []
        text_len = len(text)
        pos = 0
        chunk_idx = 0

        while pos < text_len:
            # Determine chunk end position
            end_pos = min(pos + self.config.max_chars, text_len)

            # Try to break at sentence or paragraph boundaries
            if end_pos < text_len:
                end_pos = self._find_good_break_point(text, pos, end_pos)

            chunk_text = text[pos:end_pos]

            # Calculate line numbers for this chunk
            lines_before = text[:pos].count("\\n")
            lines_in_chunk = chunk_text.count("\\n")

            start_line = base_line + lines_before
            end_line = start_line + lines_in_chunk

            chunk = self._create_chunk(
                document,
                f"{section_label}.{chunk_idx}" if chunk_idx > 0 else section_label,
                chunk_text,
                start_line,
                end_line,
                base_char_pos + pos,
                base_char_pos + end_pos,
            )
            chunks.append(chunk)

            # Move to next position with overlap
            pos = max(pos + self.config.min_chars, end_pos - self.overlap_chars)
            chunk_idx += 1

        return chunks

    def _find_good_break_point(self, text: str, start: int, max_end: int) -> int:
        """Find optimal break point near max_end position."""
        # Look for sentence endings first
        sentence_ends = []
        for match in re.finditer(r"[.!?]\\s+", text[start:max_end]):
            sentence_ends.append(start + match.end())

        if sentence_ends:
            return sentence_ends[-1]

        # Look for paragraph breaks
        para_breaks = []
        for match in re.finditer(r"\\n\\s*\\n", text[start:max_end]):
            para_breaks.append(start + match.end())

        if para_breaks:
            return para_breaks[-1]

        # Look for line breaks
        line_breaks = []
        for match in re.finditer(r"\\n", text[start:max_end]):
            line_breaks.append(start + match.end())

        if line_breaks:
            return line_breaks[-1]

        # Default to max position
        return max_end

    def _create_chunk(
        self,
        document: LegalDocument,
        section_label: str,
        content: str,
        start_line: int,
        end_line: int,
        char_start: int,
        char_end: int,
    ) -> TextChunk:
        """Create a TextChunk with complete metadata."""
        chunk_id = f"{document.law_id}_{start_line}_{end_line}"
        section_path = self.loader.get_section_hierarchy(document.law_id, section_label)

        return TextChunk(
            chunk_id=chunk_id,
            law_id=document.law_id,
            law_name=document.law_name,
            jurisdiction=document.jurisdiction.value,
            section_label=section_label,
            section_path=section_path,
            content=content.strip(),
            start_line=start_line,
            end_line=end_line,
            source_path=document.source_path,
            char_start=char_start,
            char_end=char_end,
        )
