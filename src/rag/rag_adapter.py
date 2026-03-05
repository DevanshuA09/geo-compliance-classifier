"""
RAG Adapter for unified agent-RAG interactions.
Provides a consistent interface for all agents to access the centralized RAG system.
"""

# Import the existing RAG service
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..evidence import log_compliance_decision

sys.path.append(str(Path(__file__).parent.parent / "retriever"))
from retriever.models import RetrievalRequest, RetrievalResponse
from retriever.service import RetrievalService


class RAGAdapter:
    """Unified RAG interface for all agents."""

    def __init__(self, config_path: str = "config/centralized_rag_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.rag_service = None
        self._initialize_rag_service()

    def _load_config(self) -> Dict[str, Any]:
        """Load centralized RAG configuration."""
        try:
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Fallback to default config
            return {
                "rag_service": {"base_url": "http://localhost:8000"},
                "retrieval": {"top_k": 5, "max_chars": 1200},
            }

    def _initialize_rag_service(self):
        """Initialize the RAG service."""
        try:
            # Use existing config.yaml as fallback
            config_path = "config.yaml"
            if not Path(config_path).exists():
                config_path = "config/centralized_rag_config.yaml"

            # Check if FAISS retriever should be used
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            vectorstore_type = (
                config.get("rag", {}).get("vectorstore", {}).get("type", "fallback")
            )

            if vectorstore_type == "faiss":
                # Use real FAISS retriever with threading fixes
                from retriever.faiss_retriever import FaissRetriever

                self.faiss_retriever = FaissRetriever(config)
                self.rag_service = None
                print("✅ FAISS retriever initialized")
            else:
                # Use legacy retrieval service
                self.rag_service = RetrievalService(config_path=config_path)
                self.faiss_retriever = None
                print("✅ Legacy retrieval service initialized")

        except Exception as e:
            print(f"Warning: RAG service initialization failed: {e}")
            self.rag_service = None
            self.faiss_retriever = None

    def retrieve_regulatory_context(
        self, query: str, jurisdiction: Optional[str] = None, max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve regulatory context using the centralized RAG system.

        Args:
            query: Search query text
            jurisdiction: Optional jurisdiction filter
            max_results: Maximum number of results

        Returns:
            List of regulatory context results
        """
        # Try FAISS retriever first
        if hasattr(self, "faiss_retriever") and self.faiss_retriever:
            try:
                start_time = datetime.now()
                results = self.faiss_retriever.retrieve(query, top_k=max_results)
                retrieval_time = (datetime.now() - start_time).total_seconds() * 1000

                # Log evidence for successful FAISS retrieval
                evidence_data = {
                    "request_id": str(uuid.uuid4()),
                    "timestamp_iso": datetime.now().isoformat(),
                    "agent_name": "rag_adapter",
                    "decision_flag": len(results) > 0,
                    "reasoning_text": f"FAISS retrieval successful with {len(results)} results",
                    "feature_id": query[:50],  # Truncate long queries
                    "retrieval_metadata": {
                        "embedder_name": "faiss",
                        "vectorstore_type": "faiss",
                        "top_k": max_results,
                        "retrieved_count": len(results),
                        "retrieval_time_ms": retrieval_time,
                    },
                    "timings_ms": {"retrieval_ms": retrieval_time},
                }
                log_compliance_decision(evidence_data)

                return [
                    {
                        "text": result.snippet,
                        "source": result.law_name,
                        "regulation": result.law_id,
                        "section": result.section_label,
                        "confidence": result.score,
                        "metadata": {
                            "jurisdiction": result.jurisdiction,
                            "source_path": result.source_path,
                        },
                    }
                    for result in results
                ]
            except Exception as e:
                print(f"FAISS retrieval failed: {e}")

                # Log evidence for failed FAISS retrieval
                evidence_data = {
                    "request_id": str(uuid.uuid4()),
                    "timestamp_iso": datetime.now().isoformat(),
                    "agent_name": "rag_adapter",
                    "decision_flag": False,
                    "reasoning_text": f"FAISS retrieval failed: {str(e)}",
                    "feature_id": query[:50],
                    "error_info": {
                        "type": "retrieval_error",
                        "message": str(e),
                        "retryable": True,
                    },
                }
                log_compliance_decision(evidence_data)

                return self._fallback_retrieval(query, max_results)

        # Fallback to legacy service or mock
        if not self.rag_service or not self.rag_service.is_ready:
            return self._fallback_retrieval(query, max_results)

        try:
            start_time = datetime.now()

            # Create retrieval request
            request = RetrievalRequest(
                query=query,
                top_k=max_results,
                max_chars=self.config.get("retrieval", {}).get("max_chars", 1200),
            )

            # Perform retrieval
            results = self.rag_service._retrieve_internal(
                query=query,
                law_filter=None,  # No filter for now
                top_k=max_results,
                max_chars=request.max_chars,
            )

            retrieval_time = (datetime.now() - start_time).total_seconds() * 1000

            # Log evidence for successful legacy retrieval
            evidence_data = {
                "request_id": str(uuid.uuid4()),
                "timestamp_iso": datetime.now().isoformat(),
                "agent_name": "rag_adapter",
                "decision_flag": len(results) > 0,
                "reasoning_text": f"Legacy RAG retrieval successful with {len(results)} results",
                "feature_id": query[:50],
                "retrieval_metadata": {
                    "embedder_name": "legacy",
                    "vectorstore_type": "legacy",
                    "top_k": max_results,
                    "retrieved_count": len(results),
                    "retrieval_time_ms": retrieval_time,
                },
                "timings_ms": {"retrieval_ms": retrieval_time},
            }
            log_compliance_decision(evidence_data)

            # Convert to standardized format
            return [
                {
                    "text": result.snippet,
                    "source": result.law_name,
                    "regulation": result.law_id,
                    "section": result.section_label,
                    "confidence": result.score,
                    "metadata": {
                        "jurisdiction": result.jurisdiction,
                        "source_path": result.source_path,
                    },
                }
                for result in results
            ]

        except Exception as e:
            print(f"RAG retrieval failed: {e}")

            # Log evidence for failed legacy retrieval
            evidence_data = {
                "request_id": str(uuid.uuid4()),
                "timestamp_iso": datetime.now().isoformat(),
                "agent_name": "rag_adapter",
                "decision_flag": False,
                "reasoning_text": f"Legacy RAG retrieval failed: {str(e)}",
                "feature_id": query[:50],
                "error_info": {
                    "type": "retrieval_error",
                    "message": str(e),
                    "retryable": True,
                },
            }
            log_compliance_decision(evidence_data)

            return self._fallback_retrieval(query, max_results)

    def _fallback_retrieval(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Fallback retrieval when RAG service is unavailable."""
        return [
            {
                "text": f"Fallback context for: {query}",
                "source": "fallback",
                "regulation": "general",
                "section": "fallback",
                "confidence": 0.5,
                "metadata": {"fallback": True},
            }
        ]

    def get_system_status(self) -> Dict[str, Any]:
        """Get RAG system status."""
        if self.rag_service and self.rag_service.is_ready:
            return {
                "status": "ready",
                "service": "centralized_rag",
                "config_source": self.config_path,
            }
        else:
            return {
                "status": "unavailable",
                "service": "centralized_rag",
                "config_source": self.config_path,
                "error": "RAG service not initialized",
            }
