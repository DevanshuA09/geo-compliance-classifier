"""
Python SDK for the Regulation Retriever API.
"""

import logging
import time
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    requests = None

from retriever.models import RetrievalRequest, RetrievalResponse, SearchResult

logger = logging.getLogger(__name__)


class RegulationClient:
    """Python client for the Regulation Retriever API."""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        """
        Initialize client.

        Args:
            base_url: API base URL
            timeout: Request timeout in seconds
        """
        if requests is None:
            raise ImportError(
                "requests library required. Install with: pip install requests"
            )

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        # Set default headers
        self.session.headers.update(
            {"Content-Type": "application/json", "User-Agent": "RegulationClient/1.0.0"}
        )

    def retrieve(
        self,
        query: str,
        laws: Optional[List[str]] = None,
        top_k: int = 5,
        max_chars: int = 1200,
        include_citation: bool = True,
    ) -> RetrievalResponse:
        """
        Retrieve relevant legal snippets.

        Args:
            query: Search query
            laws: Filter by specific law IDs (e.g., ['EUDSA', 'FL_HB3'])
            top_k: Number of results to return
            max_chars: Maximum snippet length
            include_citation: Include citation metadata

        Returns:
            Retrieval response with ranked results
        """
        # Validate request
        request = RetrievalRequest(
            query=query,
            laws=laws,
            top_k=top_k,
            max_chars=max_chars,
            include_citation=include_citation,
        )

        # Prepare API request
        payload = {
            "query": request.query,
            "laws": request.laws,
            "top_k": request.top_k,
            "max_chars": request.max_chars,
            "include_citation": request.include_citation,
        }

        try:
            start_time = time.time()

            response = self.session.post(
                f"{self.base_url}/retrieve", json=payload, timeout=self.timeout
            )

            response.raise_for_status()
            data = response.json()

            # Convert to response model
            results = [SearchResult(**r) for r in data["results"]]

            return RetrievalResponse(
                query=data["query"],
                results=results,
                total_latency_ms=data["total_latency_ms"],
                laws_searched=data["laws_searched"],
                total_chunks_searched=data["total_chunks_searched"],
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise RuntimeError(f"Failed to retrieve results: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def health(self) -> Dict[str, Any]:
        """
        Check service health.

        Returns:
            Health status and performance metrics
        """
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Health check failed: {e}")
            raise RuntimeError(f"Service health check failed: {e}")

    def search_by_law(
        self, query: str, law_id: str, top_k: int = 3
    ) -> List[SearchResult]:
        """
        Convenience method to search within a specific law.

        Args:
            query: Search query
            law_id: Specific law to search (e.g., 'EUDSA')
            top_k: Number of results

        Returns:
            List of search results
        """
        response = self.retrieve(query=query, laws=[law_id], top_k=top_k)
        return response.results

    def search_jurisdiction(
        self, query: str, jurisdiction: str, top_k: int = 5
    ) -> List[SearchResult]:
        """
        Search within a specific jurisdiction.

        Args:
            query: Search query
            jurisdiction: Jurisdiction code (e.g., 'US-CA', 'EU')
            top_k: Number of results

        Returns:
            Filtered search results
        """
        # Map jurisdiction to law IDs
        jurisdiction_mapping = {
            "EU": ["EUDSA"],
            "US-CA": ["CA_SB976"],
            "US-FL": ["FL_HB3"],
            "US": ["US_2258A", "CA_SB976", "FL_HB3"],  # All US laws
        }

        laws = jurisdiction_mapping.get(jurisdiction)
        if not laws:
            raise ValueError(f"Unknown jurisdiction: {jurisdiction}")

        response = self.retrieve(query=query, laws=laws, top_k=top_k)
        return response.results

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience functions for common use cases
def quick_search(
    query: str, laws: Optional[List[str]] = None, top_k: int = 3
) -> List[str]:
    """
    Quick search that returns just the snippet text.

    Args:
        query: Search query
        laws: Optional law filter
        top_k: Number of results

    Returns:
        List of snippet texts
    """
    with RegulationClient() as client:
        response = client.retrieve(query=query, laws=laws, top_k=top_k)
        return [result.snippet for result in response.results]


def search_with_citations(query: str, top_k: int = 5) -> List[Dict[str, str]]:
    """
    Search with full citation information.

    Args:
        query: Search query
        top_k: Number of results

    Returns:
        List of dicts with snippet and citation info
    """
    with RegulationClient() as client:
        response = client.retrieve(query=query, top_k=top_k)

        results = []
        for result in response.results:
            results.append(
                {
                    "snippet": result.snippet,
                    "law": result.law_name,
                    "section": result.section_label,
                    "jurisdiction": result.jurisdiction,
                    "score": result.score,
                }
            )

        return results
