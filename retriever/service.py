"""
FastAPI service for regulation retrieval with caching and performance monitoring.
"""
import logging
import time
from typing import List, Optional, Set
from functools import lru_cache
import hashlib

try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
except ImportError:
    FastAPI = HTTPException = Query = CORSMiddleware = BaseModel = Field = None

try:
    import numpy as np
except ImportError:
    np = None

from retriever.models import RetrievalRequest, RetrievalResponse, SearchResult
from retriever.rank import HybridRetriever
from index.build_index import VectorIndexBuilder


logger = logging.getLogger(__name__)


class RetrievalService:
    """High-performance regulation retrieval service."""
    
    def __init__(self, config_path: str = "config.yaml", index_dir: str = "index"):
        """Initialize service with vector index and hybrid retriever."""
        import yaml
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.performance_config = self.config['performance']
        self.retrieval_config = self.config['retrieval']
        
        # Initialize components
        self.index_builder = VectorIndexBuilder(config_path)
        self.hybrid_retriever = None
        self.is_ready = False
        
        # Load index
        self._load_index(index_dir)
        
        # Performance monitoring
        self.query_count = 0
        self.total_latency = 0.0
        self.latencies = []
    
    def _load_index(self, index_dir: str):
        """Load vector index and initialize retriever."""
        logger.info("Loading vector index...")
        
        if not self.index_builder.load_index(index_dir):
            raise RuntimeError(f"Failed to load index from {index_dir}")
        
        # Initialize hybrid retriever
        expansion_terms = self.config.get('query_expansion', {})
        self.hybrid_retriever = HybridRetriever(
            bm25_weight=self.retrieval_config['bm25_weight'],
            dense_weight=self.retrieval_config['dense_weight'],
            expansion_terms=expansion_terms
        )
        
        # Fit retriever with chunks
        self.hybrid_retriever.fit(self.index_builder.chunks_metadata)
        
        self.is_ready = True
        logger.info("Retrieval service ready")
    
    @lru_cache(maxsize=500)
    def _cached_retrieve(self, 
                        query: str, 
                        laws_tuple: Optional[tuple], 
                        top_k: int, 
                        max_chars: int) -> str:
        """Cached retrieval with tuple-based caching."""
        # Convert tuple back to set for filtering
        law_filter = set(laws_tuple) if laws_tuple else None
        
        # Perform retrieval
        results = self._retrieve_internal(query, law_filter, top_k, max_chars)
        
        # Serialize results for caching
        import json
        response = RetrievalResponse(
            query=query,
            results=results,
            total_latency_ms=results[0].latency_ms if results else 0,
            laws_searched=list(law_filter) if law_filter else ["ALL"],
            total_chunks_searched=len(self.index_builder.chunks_metadata)
        )
        
        return response.to_json()
    
    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        """
        Main retrieval endpoint with caching and performance monitoring.
        
        Args:
            request: Validated retrieval request
            
        Returns:
            Retrieval response with ranked results
        """
        if not self.is_ready:
            raise RuntimeError("Service not ready. Index not loaded.")
        
        start_time = time.time()
        
        # Convert laws list to tuple for caching
        laws_tuple = tuple(sorted(request.laws)) if request.laws else None
        
        # Use cached retrieval
        try:
            cached_result = self._cached_retrieve(
                request.query,
                laws_tuple,
                request.top_k,
                request.max_chars
            )
            
            # Deserialize cached result
            import json
            result_dict = json.loads(cached_result)
            
            # Reconstruct response
            results = [SearchResult(**r) for r in result_dict['results']]
            response = RetrievalResponse(
                query=result_dict['query'],
                results=results,
                total_latency_ms=result_dict['total_latency_ms'],
                laws_searched=result_dict['laws_searched'],
                total_chunks_searched=result_dict['total_chunks_searched']
            )
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            # Return empty response
            response = RetrievalResponse(
                query=request.query,
                results=[],
                total_latency_ms=int((time.time() - start_time) * 1000),
                laws_searched=request.laws or [],
                total_chunks_searched=0
            )
        
        # Update performance metrics
        self._update_metrics(response.total_latency_ms)
        
        return response
    
    def _retrieve_internal(self, 
                          query: str, 
                          law_filter: Optional[Set[str]], 
                          top_k: int, 
                          max_chars: int) -> List[SearchResult]:
        """Internal retrieval logic without caching."""
        # Generate query embedding
        query_embedding = self.index_builder.model.encode([query], convert_to_numpy=True)
        
        # Get dense vector results
        dense_results = self.index_builder.search(
            query_embedding[0], 
            top_k=self.retrieval_config['max_results']
        )
        
        # Convert to (score, index) format
        dense_scores = [(score, i) for i, (score, chunk) in enumerate(dense_results) 
                       if chunk in self.index_builder.chunks_metadata]
        
        # Use hybrid retrieval for final ranking
        results = self.hybrid_retriever.retrieve(
            query=query,
            dense_scores=dense_scores,
            law_filter=law_filter,
            top_k=top_k
        )
        
        # Apply max_chars limit to snippets
        for result in results:
            if len(result.snippet) > max_chars:
                result.snippet = self._truncate_snippet(result.snippet, max_chars)
        
        return results
    
    def _truncate_snippet(self, snippet: str, max_chars: int) -> str:
        """Truncate snippet to max_chars with smart boundary detection."""
        if len(snippet) <= max_chars:
            return snippet
        
        truncated = snippet[:max_chars]
        
        # Find last sentence boundary
        last_sentence = max(
            truncated.rfind('. '),
            truncated.rfind('! '),
            truncated.rfind('? ')
        )
        
        if last_sentence > max_chars * 0.7:
            return truncated[:last_sentence + 1]
        
        # Find last word boundary
        last_space = truncated.rfind(' ')
        if last_space > max_chars * 0.8:
            return truncated[:last_space] + "..."
        
        return truncated + "..."
    
    def _update_metrics(self, latency_ms: int):
        """Update performance metrics."""
        self.query_count += 1
        self.total_latency += latency_ms
        self.latencies.append(latency_ms)
        
        # Keep only recent latencies for P95 calculation
        if len(self.latencies) > 1000:
            self.latencies = self.latencies[-1000:]
    
    def get_health_status(self) -> dict:
        """Get service health and performance metrics."""
        if not self.latencies:
            return {
                "status": "ready" if self.is_ready else "not_ready",
                "query_count": self.query_count,
                "avg_latency_ms": 0,
                "p95_latency_ms": 0,
                "cache_info": dict(self._cached_retrieve.cache_info()._asdict())
            }
        
        # Calculate percentiles
        sorted_latencies = sorted(self.latencies)
        p50_idx = int(len(sorted_latencies) * 0.5)
        p95_idx = int(len(sorted_latencies) * 0.95)
        
        return {
            "status": "ready" if self.is_ready else "not_ready",
            "query_count": self.query_count,
            "avg_latency_ms": self.total_latency / self.query_count,
            "p50_latency_ms": sorted_latencies[p50_idx],
            "p95_latency_ms": sorted_latencies[p95_idx],
            "cache_info": dict(self._cached_retrieve.cache_info()._asdict()),
            "total_chunks": len(self.index_builder.chunks_metadata) if self.is_ready else 0
        }


# FastAPI app setup
if FastAPI is not None:
    app = FastAPI(
        title="Regulation Retriever API",
        description="High-performance legal document retrieval service",
        version="1.0.0"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Global service instance
    service = None
    
    
    class RetrievalRequestAPI(BaseModel):
        """API request model."""
        query: str = Field(..., description="Search query")
        laws: Optional[List[str]] = Field(None, description="Filter by specific laws")
        top_k: int = Field(5, ge=1, le=20, description="Number of results")
        max_chars: int = Field(1200, ge=100, le=5000, description="Maximum snippet length")
        include_citation: bool = Field(True, description="Include citation metadata")
    
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize service on startup."""
        global service
        try:
            service = RetrievalService()
            logger.info("Retrieval service started successfully")
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            raise
    
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        if service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        return service.get_health_status()
    
    
    @app.post("/retrieve", response_model=dict)
    async def retrieve_endpoint(request: RetrievalRequestAPI):
        """Main retrieval endpoint."""
        if service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        try:
            # Convert to internal request format
            internal_request = RetrievalRequest(
                query=request.query,
                laws=request.laws,
                top_k=request.top_k,
                max_chars=request.max_chars,
                include_citation=request.include_citation
            )
            
            response = service.retrieve(internal_request)
            return response.to_dict()
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "service": "Regulation Retriever API",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "retrieve": "/retrieve",
                "docs": "/docs"
            }
        }

else:
    # Fallback for missing FastAPI
    logger.warning("FastAPI not available. Install with: pip install fastapi uvicorn")
    app = None
