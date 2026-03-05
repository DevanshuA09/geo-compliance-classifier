"""
Data models and schemas for the Regulation Retriever Agent.
"""

import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class Jurisdiction(str, Enum):
    """Supported jurisdictions."""

    EU = "EU"
    US_CA = "US-CA"
    US_FL = "US-FL"
    US = "US"


@dataclass
class LegalDocument:
    """Represents a legal document with metadata."""

    law_id: str
    law_name: str
    jurisdiction: Jurisdiction
    source_path: str
    content: str
    total_lines: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata and positioning."""

    chunk_id: str
    law_id: str
    law_name: str
    jurisdiction: str
    section_label: str
    section_path: str
    content: str
    start_line: int
    end_line: int
    source_path: str
    char_start: int
    char_end: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SearchResult:
    """Search result with scoring and metadata."""

    law_id: str
    law_name: str
    jurisdiction: str
    section_label: str
    score: float
    snippet: str
    start_line: int
    end_line: int
    source_path: str
    latency_ms: int
    dense_score: float = 0.0
    sparse_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class RetrievalRequest:
    """Request schema for retrieval API."""

    query: str
    laws: Optional[List[str]] = None
    top_k: int = 5
    max_chars: int = 1200
    include_citation: bool = True

    def __post_init__(self):
        if self.top_k <= 0:
            raise ValueError("top_k must be positive")
        if self.max_chars <= 0:
            raise ValueError("max_chars must be positive")
        if not self.query.strip():
            raise ValueError("query cannot be empty")


@dataclass
class RetrievalResponse:
    """Response schema for retrieval API."""

    query: str
    results: List[SearchResult]
    total_latency_ms: int
    laws_searched: List[str]
    total_chunks_searched: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "total_latency_ms": self.total_latency_ms,
            "laws_searched": self.laws_searched,
            "total_chunks_searched": self.total_chunks_searched,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class IndexStats:
    """Statistics about the vector index."""

    total_documents: int
    total_chunks: int
    embedding_dimension: int
    index_size_mb: float
    laws_indexed: List[str]
    build_time_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
