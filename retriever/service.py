"""
FastAPI service for regulation retrieval with caching and performance monitoring.
"""

import hashlib
import logging
import os
import time
from datetime import datetime
from functools import lru_cache
from typing import List, Optional, Set

try:
    from contextlib import asynccontextmanager

    from fastapi import FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
except ImportError:
    FastAPI = HTTPException = Query = CORSMiddleware = BaseModel = Field = None

try:
    import numpy as np
except ImportError:
    np = None

from fastapi import Query
from fastapi.responses import Response

from index.build_index import VectorIndexBuilder
from retriever.models import RetrievalRequest, RetrievalResponse, SearchResult
from retriever.rank import HybridRetriever
from src.evidence import EvidenceExporter

# MCP imports
try:
    from src.mcp import MCPOrchestrator, MCPRequest, MCPResponse, MCPStatus

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    MCPOrchestrator = None
    MCPRequest = None
    MCPResponse = None
    MCPStatus = None


logger = logging.getLogger(__name__)


class RetrievalService:
    """High-performance regulation retrieval service."""

    def __init__(self, config_path: str = "config.yaml", index_dir: str = "index"):
        """Initialize service with vector index and hybrid retriever."""
        import yaml

        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.performance_config = self.config["performance"]
        self.retrieval_config = self.config["retrieval"]

        # Initialize components
        self.index_builder = VectorIndexBuilder(config_path)
        self.hybrid_retriever = None
        self.is_ready = False

        # Initialize MCP orchestrator if available
        self.mcp_orchestrator = None
        if MCP_AVAILABLE:
            try:
                self.mcp_orchestrator = MCPOrchestrator(config_path)
                logger.info("MCP orchestrator initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize MCP orchestrator: {e}")

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
        expansion_terms = self.config.get("query_expansion", {})
        self.hybrid_retriever = HybridRetriever(
            bm25_weight=self.retrieval_config["bm25_weight"],
            dense_weight=self.retrieval_config["dense_weight"],
            expansion_terms=expansion_terms,
        )

        # Fit retriever with chunks
        self.hybrid_retriever.fit(self.index_builder.chunks_metadata)

        self.is_ready = True
        logger.info("Retrieval service ready")

    @lru_cache(maxsize=500)
    def _cached_retrieve(
        self, query: str, laws_tuple: Optional[tuple], top_k: int, max_chars: int
    ) -> str:
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
            total_chunks_searched=len(self.index_builder.chunks_metadata),
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
                request.query, laws_tuple, request.top_k, request.max_chars
            )

            # Deserialize cached result
            import json

            result_dict = json.loads(cached_result)

            # Reconstruct response
            results = [SearchResult(**r) for r in result_dict["results"]]
            response = RetrievalResponse(
                query=result_dict["query"],
                results=results,
                total_latency_ms=result_dict["total_latency_ms"],
                laws_searched=result_dict["laws_searched"],
                total_chunks_searched=result_dict["total_chunks_searched"],
            )

        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            # Return empty response
            response = RetrievalResponse(
                query=request.query,
                results=[],
                total_latency_ms=int((time.time() - start_time) * 1000),
                laws_searched=request.laws or [],
                total_chunks_searched=0,
            )

        # Update performance metrics
        self._update_metrics(response.total_latency_ms)

        return response

    def _retrieve_internal(
        self, query: str, law_filter: Optional[Set[str]], top_k: int, max_chars: int
    ) -> List[SearchResult]:
        """Internal retrieval logic without caching."""
        # Generate query embedding
        query_embedding = self.index_builder.model.encode(
            [query], convert_to_numpy=True
        )

        # Get dense vector results
        dense_results = self.index_builder.search(
            query_embedding[0], top_k=self.retrieval_config["max_results"]
        )

        # Convert to (score, index) format
        dense_scores = [
            (score, i)
            for i, (score, chunk) in enumerate(dense_results)
            if chunk in self.index_builder.chunks_metadata
        ]

        # Use hybrid retrieval for final ranking
        results = self.hybrid_retriever.retrieve(
            query=query, dense_scores=dense_scores, law_filter=law_filter, top_k=top_k
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
            truncated.rfind(". "), truncated.rfind("! "), truncated.rfind("? ")
        )

        if last_sentence > max_chars * 0.7:
            return truncated[: last_sentence + 1]

        # Find last word boundary
        last_space = truncated.rfind(" ")
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
                "cache_info": dict(self._cached_retrieve.cache_info()._asdict()),
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
            "total_chunks": (
                len(self.index_builder.chunks_metadata) if self.is_ready else 0
            ),
        }


# FastAPI app setup
if FastAPI is not None:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Lifespan context manager for FastAPI app."""
        global service
        try:
            service = RetrievalService()
            logger.info("Retrieval service started successfully")
            yield
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            raise
        finally:
            logger.info("Retrieval service shutting down")

    app = FastAPI(
        title="Regulation Retriever API",
        description="High-performance legal document retrieval service",
        version="1.0.0",
        lifespan=lifespan,
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
        max_chars: int = Field(
            1200, ge=100, le=5000, description="Maximum snippet length"
        )
        include_citation: bool = Field(True, description="Include citation metadata")

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
                include_citation=request.include_citation,
            )

            response = service.retrieve(internal_request)
            return response.to_dict()

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.get("/evidence/export")
    async def export_evidence(
        start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
        end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
        agents: Optional[List[str]] = Query(None, description="Filter by agent names"),
        limit: Optional[int] = Query(
            None, ge=1, le=10000, description="Maximum records to export"
        ),
        format: str = Query("csv", description="Export format (csv or json)"),
    ):
        """Export evidence logs to challenge CSV format."""
        try:
            # Parse dates
            parsed_start = None
            parsed_end = None
            if start_date:
                parsed_start = datetime.strptime(start_date, "%Y-%m-%d")
            if end_date:
                parsed_end = datetime.strptime(end_date, "%Y-%m-%d")

            # Initialize exporter
            exporter = EvidenceExporter()

            if format == "csv":
                # Generate temporary CSV file
                import tempfile

                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".csv", delete=False
                ) as tmp_file:
                    count = exporter.export_to_csv(
                        tmp_file.name, parsed_start, parsed_end, agents, limit
                    )

                    # Read file content
                    with open(tmp_file.name, "r") as f:
                        csv_content = f.read()

                    # Clean up
                    os.unlink(tmp_file.name)

                return Response(
                    content=csv_content,
                    media_type="text/csv",
                    headers={
                        "Content-Disposition": f"attachment; filename=evidence_export_{datetime.now().strftime('%Y%m%d')}.csv"
                    },
                )
            else:
                # Return JSON summary
                summary = exporter.get_export_summary(parsed_start, parsed_end, agents)
                return summary

        except Exception as e:
            logger.error(f"Export error: {e}")
            raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

    @app.get("/evidence/summary")
    async def evidence_summary(
        start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
        end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
        agents: Optional[List[str]] = Query(None, description="Filter by agent names"),
    ):
        """Get evidence export summary."""
        try:
            # Parse dates
            parsed_start = None
            parsed_end = None
            if start_date:
                parsed_start = datetime.strptime(start_date, "%Y-%m-%d")
            if end_date:
                parsed_end = datetime.strptime(end_date, "%Y-%m-%d")

            # Initialize exporter
            exporter = EvidenceExporter()
            summary = exporter.get_export_summary(parsed_start, parsed_end, agents)
            return summary

        except Exception as e:
            logger.error(f"Summary error: {e}")
            raise HTTPException(status_code=500, detail=f"Summary failed: {str(e)}")

    @app.get("/evidence")
    async def get_evidence(
        since: Optional[str] = Query(None, description="Start date (ISO8601)"),
        until: Optional[str] = Query(None, description="End date (ISO8601)"),
        agent: Optional[str] = Query(None, description="Filter by agent name"),
        feature_id: Optional[str] = Query(None, description="Filter by feature ID"),
        dataset_tag: Optional[str] = Query(None, description="Filter by dataset tag"),
        decision_flag: Optional[bool] = Query(
            None, description="Filter by decision flag"
        ),
        q: Optional[str] = Query(None, description="Search in title/reasoning"),
        limit: int = Query(50, ge=1, le=500, description="Number of records to return"),
        offset: int = Query(0, ge=0, description="Number of records to skip"),
        order: str = Query("timestamp_desc", description="Sort order"),
    ):
        """Get evidence records with filtering, pagination, and aggregates."""
        try:
            # Parse dates
            parsed_since = None
            parsed_until = None
            if since:
                parsed_since = datetime.fromisoformat(since)
            if until:
                parsed_until = datetime.fromisoformat(until)

            # Initialize exporter
            exporter = EvidenceExporter()

            # Get all records for filtering
            all_records = list(
                exporter.read_evidence_records(
                    start_date=parsed_since,
                    end_date=parsed_until,
                    agent_filter=[agent] if agent else None,
                )
            )

            # Apply additional filters
            filtered_records = []
            for record in all_records:
                # Feature ID filter
                if feature_id and record.get("feature_id") != feature_id:
                    continue

                # Dataset tag filter
                if dataset_tag and record.get("dataset_tag") != dataset_tag:
                    continue

                # Decision flag filter
                if (
                    decision_flag is not None
                    and record.get("decision_flag") != decision_flag
                ):
                    continue

                # Text search filter
                if q:
                    search_text = f"{record.get('feature_title', '')} {record.get('reasoning_text', '')}".lower()
                    if q.lower() not in search_text:
                        continue

                filtered_records.append(record)

            # Sort records
            if order == "timestamp_desc":
                filtered_records.sort(
                    key=lambda x: x.get("timestamp_iso", ""), reverse=True
                )
            elif order == "timestamp_asc":
                filtered_records.sort(key=lambda x: x.get("timestamp_iso", ""))
            elif order == "agent_name":
                filtered_records.sort(key=lambda x: x.get("agent_name", ""))

            # Apply pagination
            total_records = len(filtered_records)
            paginated_records = filtered_records[offset : offset + limit]

            # Calculate aggregates
            count_by_decision_flag = {"true": 0, "false": 0}
            count_by_agent = {}
            count_by_regulation = {}
            total_ms_values = []

            for record in filtered_records:
                # Decision flag counts
                decision = record.get("decision_flag", False)
                count_by_decision_flag["true" if decision else "false"] += 1

                # Agent counts
                agent_name = record.get("agent_name", "unknown")
                count_by_agent[agent_name] = count_by_agent.get(agent_name, 0) + 1

                # Regulation counts
                regulations = record.get("related_regulations", [])
                if isinstance(regulations, list):
                    for reg in regulations:
                        count_by_regulation[reg] = count_by_regulation.get(reg, 0) + 1

                # Timing values
                timings = record.get("timings_ms", {})
                if isinstance(timings, dict) and "total_ms" in timings:
                    total_ms_values.append(timings["total_ms"])

            # Calculate percentiles
            p50_ms = 0
            p95_ms = 0
            if total_ms_values:
                sorted_ms = sorted(total_ms_values)
                p50_idx = len(sorted_ms) // 2
                p95_idx = int(len(sorted_ms) * 0.95)
                p50_ms = sorted_ms[p50_idx] if p50_idx < len(sorted_ms) else 0
                p95_ms = sorted_ms[p95_idx] if p95_idx < len(sorted_ms) else 0

            # Top regulations
            top_regulations = sorted(
                count_by_regulation.items(), key=lambda x: x[1], reverse=True
            )[:10]

            return {
                "items": paginated_records,
                "total": total_records,
                "limit": limit,
                "offset": offset,
                "aggregates": {
                    "count_by_decision_flag": count_by_decision_flag,
                    "count_by_agent": count_by_agent,
                    "count_by_regulation": dict(top_regulations),
                    "p50_ms": p50_ms,
                    "p95_ms": p95_ms,
                },
            }

        except Exception as e:
            logger.error(f"Evidence query error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Evidence query failed: {str(e)}"
            )

    # MCP Endpoints
    if MCP_AVAILABLE:

        @app.post("/mcp/analyze", response_model=MCPResponse)
        async def mcp_analyze(request: MCPRequest):
            """MCP analysis endpoint."""
            if service is None:
                raise HTTPException(status_code=503, detail="Service not initialized")

            if not service.mcp_orchestrator:
                raise HTTPException(
                    status_code=503, detail="MCP orchestrator not available"
                )

            try:
                response = service.mcp_orchestrator.analyze(request)
                return response

            except Exception as e:
                logger.error(f"MCP analysis error: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Analysis failed: {str(e)}"
                )

        @app.get("/mcp/tools")
        async def mcp_tools():
            """Get registered MCP tools."""
            if service is None:
                raise HTTPException(status_code=503, detail="Service not initialized")

            if not service.mcp_orchestrator:
                raise HTTPException(
                    status_code=503, detail="MCP orchestrator not available"
                )

            try:
                tools = service.mcp_orchestrator.tool_registry.list_tools()
                return {"tools": [tool.dict() for tool in tools]}

            except Exception as e:
                logger.error(f"MCP tools error: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Failed to get tools: {str(e)}"
                )

        @app.get("/mcp/status", response_model=MCPStatus)
        async def mcp_status():
            """Get MCP service status."""
            if service is None:
                raise HTTPException(status_code=503, detail="Service not initialized")

            if not service.mcp_orchestrator:
                raise HTTPException(
                    status_code=503, detail="MCP orchestrator not available"
                )

            try:
                status = service.mcp_orchestrator.get_status()
                return status

            except Exception as e:
                logger.error(f"MCP status error: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Failed to get status: {str(e)}"
                )

    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        endpoints = {
            "health": "/health",
            "retrieve": "/retrieve",
            "evidence": "/evidence",
            "evidence_export": "/evidence/export",
            "evidence_summary": "/evidence/summary",
            "dashboard": "/dashboard",
            "docs": "/docs",
        }

        # Add MCP endpoints if available
        if MCP_AVAILABLE:
            endpoints.update(
                {
                    "mcp_analyze": "/mcp/analyze",
                    "mcp_tools": "/mcp/tools",
                    "mcp_status": "/mcp/status",
                }
            )

        return {
            "service": "Regulation Retriever API",
            "version": "1.0.0",
            "endpoints": endpoints,
        }

    @app.get("/dashboard")
    async def dashboard():
        """Evidence dashboard HTML page."""
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Evidence Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .filters { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .filters input, .filters select { margin: 5px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
                .filters button { background: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
                .filters button:hover { background: #0056b3; }
                .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
                .summary-card { background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .summary-card h3 { margin: 0 0 10px 0; color: #333; }
                .summary-card .value { font-size: 24px; font-weight: bold; color: #007bff; }
                .table-container { background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f8f9fa; font-weight: bold; }
                tr:hover { background-color: #f5f5f5; }
                .pagination { padding: 20px; text-align: center; }
                .pagination button { margin: 0 5px; padding: 8px 16px; border: 1px solid #ddd; background: white; cursor: pointer; }
                .pagination button:disabled { opacity: 0.5; cursor: not-allowed; }
                .loading { text-align: center; padding: 40px; color: #666; }
                .error { background: #f8d7da; color: #721c24; padding: 15px; border-radius: 4px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Evidence Dashboard</h1>
                    <p>Monitor compliance decisions and evidence across all agents</p>
                </div>
                
                <div class="filters">
                    <h3>Filters</h3>
                    <input type="date" id="since" placeholder="Start Date">
                    <input type="date" id="until" placeholder="End Date">
                    <select id="agent">
                        <option value="">All Agents</option>
                    </select>
                    <select id="decision">
                        <option value="">All Decisions</option>
                        <option value="true">Compliant</option>
                        <option value="false">Non-Compliant</option>
                    </select>
                    <input type="text" id="search" placeholder="Search in title/reasoning">
                    <button onclick="loadEvidence()">Apply Filters</button>
                    <button onclick="exportCSV()">Export CSV</button>
                </div>
                
                <div class="summary" id="summary">
                    <div class="summary-card">
                        <h3>Total Records</h3>
                        <div class="value" id="totalRecords">-</div>
                    </div>
                    <div class="summary-card">
                        <h3>Compliant</h3>
                        <div class="value" id="compliantCount">-</div>
                    </div>
                    <div class="summary-card">
                        <h3>Non-Compliant</h3>
                        <div class="value" id="nonCompliantCount">-</div>
                    </div>
                    <div class="summary-card">
                        <h3>P50 Latency</h3>
                        <div class="value" id="p50Latency">-</div>
                    </div>
                </div>
                
                <div class="table-container">
                    <div id="loading" class="loading">Loading evidence records...</div>
                    <div id="error" class="error" style="display: none;"></div>
                    <table id="evidenceTable" style="display: none;">
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Agent</th>
                                <th>Feature ID</th>
                                <th>Decision</th>
                                <th>Reasoning</th>
                                <th>Confidence</th>
                            </tr>
                        </thead>
                        <tbody id="evidenceBody">
                        </tbody>
                    </table>
                    <div class="pagination" id="pagination" style="display: none;">
                        <button onclick="previousPage()" id="prevBtn">Previous</button>
                        <span id="pageInfo">Page 1</span>
                        <button onclick="nextPage()" id="nextBtn">Next</button>
                    </div>
                </div>
            </div>
            
            <script>
                let currentPage = 0;
                let totalRecords = 0;
                let limit = 50;
                
                // Load evidence on page load
                window.onload = function() {
                    loadEvidence();
                };
                
                async function loadEvidence() {
                    const loading = document.getElementById('loading');
                    const error = document.getElementById('error');
                    const table = document.getElementById('evidenceTable');
                    const pagination = document.getElementById('pagination');
                    
                    loading.style.display = 'block';
                    error.style.display = 'none';
                    table.style.display = 'none';
                    pagination.style.display = 'none';
                    
                    try {
                        const params = new URLSearchParams();
                        const since = document.getElementById('since').value;
                        const until = document.getElementById('until').value;
                        const agent = document.getElementById('agent').value;
                        const decision = document.getElementById('decision').value;
                        const search = document.getElementById('search').value;
                        
                        if (since) params.append('since', since);
                        if (until) params.append('until', until);
                        if (agent) params.append('agent', agent);
                        if (decision) params.append('decision_flag', decision);
                        if (search) params.append('q', search);
                        
                        params.append('limit', limit);
                        params.append('offset', currentPage * limit);
                        params.append('order', 'timestamp_desc');
                        
                        const response = await fetch(`/evidence?${params}`);
                        const data = await response.json();
                        
                        if (response.ok) {
                            displayEvidence(data);
                            updateSummary(data.aggregates);
                        } else {
                            throw new Error(data.detail || 'Failed to load evidence');
                        }
                    } catch (err) {
                        error.textContent = 'Error loading evidence: ' + err.message;
                        error.style.display = 'block';
                    } finally {
                        loading.style.display = 'none';
                    }
                }
                
                function displayEvidence(data) {
                    const table = document.getElementById('evidenceTable');
                    const tbody = document.getElementById('evidenceBody');
                    const pagination = document.getElementById('pagination');
                    
                    tbody.innerHTML = '';
                    totalRecords = data.total;
                    
                    data.items.forEach(record => {
                        const row = tbody.insertRow();
                        row.insertCell(0).textContent = new Date(record.timestamp_iso).toLocaleString();
                        row.insertCell(1).textContent = record.agent_name || 'Unknown';
                        row.insertCell(2).textContent = record.feature_id || 'Unknown';
                        row.insertCell(3).textContent = record.decision_flag ? 'Compliant' : 'Non-Compliant';
                        row.insertCell(4).textContent = (record.reasoning_text || '').substring(0, 100) + '...';
                        row.insertCell(5).textContent = (record.confidence || 0).toFixed(2);
                    });
                    
                    table.style.display = 'table';
                    
                    // Update pagination
                    if (totalRecords > limit) {
                        pagination.style.display = 'block';
                        updatePagination();
                    }
                }
                
                function updateSummary(aggregates) {
                    document.getElementById('totalRecords').textContent = aggregates.count_by_decision_flag.true + aggregates.count_by_decision_flag.false;
                    document.getElementById('compliantCount').textContent = aggregates.count_by_decision_flag.true;
                    document.getElementById('nonCompliantCount').textContent = aggregates.count_by_decision_flag.false;
                    document.getElementById('p50Latency').textContent = aggregates.p50_ms + 'ms';
                }
                
                function updatePagination() {
                    const pageInfo = document.getElementById('pageInfo');
                    const prevBtn = document.getElementById('prevBtn');
                    const nextBtn = document.getElementById('nextBtn');
                    
                    const totalPages = Math.ceil(totalRecords / limit);
                    pageInfo.textContent = `Page ${currentPage + 1} of ${totalPages}`;
                    
                    prevBtn.disabled = currentPage === 0;
                    nextBtn.disabled = currentPage >= totalPages - 1;
                }
                
                function previousPage() {
                    if (currentPage > 0) {
                        currentPage--;
                        loadEvidence();
                    }
                }
                
                function nextPage() {
                    const totalPages = Math.ceil(totalRecords / limit);
                    if (currentPage < totalPages - 1) {
                        currentPage++;
                        loadEvidence();
                    }
                }
                
                async function exportCSV() {
                    try {
                        const params = new URLSearchParams();
                        const since = document.getElementById('since').value;
                        const until = document.getElementById('until').value;
                        const agent = document.getElementById('agent').value;
                        
                        if (since) params.append('start_date', since);
                        if (until) params.append('end_date', until);
                        if (agent) params.append('agents', agent);
                        
                        const response = await fetch(`/evidence/export?${params}&format=csv`);
                        if (response.ok) {
                            const blob = await response.blob();
                            const url = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = 'evidence_export.csv';
                            a.click();
                            window.URL.revokeObjectURL(url);
                        } else {
                            alert('Failed to export CSV');
                        }
                    } catch (err) {
                        alert('Error exporting CSV: ' + err.message);
                    }
                }
            </script>
        </body>
        </html>
        """
        return Response(content=html_content, media_type="text/html")

else:
    # Fallback for missing FastAPI
    logger.warning("FastAPI not available. Install with: pip install fastapi uvicorn")
    app = None
