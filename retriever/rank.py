"""
Hybrid retrieval with BM25 sparse search and dense vector fusion.
"""
import re
import math
import logging
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict, Counter
import time

try:
    import numpy as np
except ImportError:
    np = None

from retriever.models import TextChunk, SearchResult


logger = logging.getLogger(__name__)


class BM25Scorer:
    """BM25 implementation for sparse text retrieval."""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 with hyperparameters.
        
        Args:
            k1: Term frequency saturation parameter
            b: Length normalization parameter
        """
        self.k1 = k1
        self.b = b
        self.doc_frequencies = defaultdict(int)
        self.doc_lengths = []
        self.avg_doc_length = 0.0
        self.corpus_size = 0
        self.tokenized_docs = []
    
    def fit(self, documents: List[str]):
        """Build BM25 index from document corpus."""
        self.tokenized_docs = [self._tokenize(doc) for doc in documents]
        self.doc_lengths = [len(tokens) for tokens in self.tokenized_docs]
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)
        self.corpus_size = len(documents)
        
        # Calculate document frequencies
        for tokens in self.tokenized_docs:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_frequencies[token] += 1
        
        logger.info(f"Built BM25 index for {self.corpus_size} documents")
    
    def score(self, query: str, doc_indices: Optional[List[int]] = None) -> List[float]:
        """
        Score documents against query.
        
        Args:
            query: Search query
            doc_indices: Specific document indices to score (None for all)
            
        Returns:
            BM25 scores for documents
        """
        query_tokens = self._tokenize(query)
        
        if doc_indices is None:
            doc_indices = list(range(self.corpus_size))
        
        scores = []
        
        for doc_idx in doc_indices:
            if doc_idx >= len(self.tokenized_docs):
                scores.append(0.0)
                continue
                
            doc_tokens = self.tokenized_docs[doc_idx]
            doc_length = self.doc_lengths[doc_idx]
            
            score = 0.0
            token_counts = Counter(doc_tokens)
            
            for token in query_tokens:
                if token in token_counts:
                    tf = token_counts[token]
                    df = self.doc_frequencies[token]
                    
                    # IDF component
                    idf = math.log((self.corpus_size - df + 0.5) / (df + 0.5))
                    
                    # TF component with length normalization
                    tf_component = (tf * (self.k1 + 1)) / (
                        tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
                    )
                    
                    score += idf * tf_component
            
            scores.append(score)
        
        return scores
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization with legal text preprocessing."""
        # Convert to lowercase
        text = text.lower()
        
        # Handle legal citations and section numbers
        text = re.sub(r'§\\s*(\\d+[a-z]*(?:[.\\-]\\d+)*(?:\\([^)]+\\))*)', r'section_\\1', text)
        text = re.sub(r'art(?:icle)?[.]?\\s*(\\d+(?:\\(\\d+\\))*)', r'article_\\1', text)
        
        # Extract alphanumeric tokens
        tokens = re.findall(r'\\b[a-z0-9_]+\\b', text)
        
        # Filter out very short tokens and common stop words
        stop_words = {'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 
                     'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 
                     'that', 'the', 'to', 'was', 'will', 'with'}
        
        tokens = [token for token in tokens if len(token) > 2 and token not in stop_words]
        
        return tokens


class QueryExpander:
    """Expands queries with legal domain terms."""
    
    def __init__(self, expansion_terms: Dict[str, List[str]]):
        """Initialize with expansion term mappings."""
        self.expansion_terms = expansion_terms
    
    def expand_query(self, query: str) -> str:
        """Expand query with related legal terms."""
        expanded_terms = [query]
        query_lower = query.lower()
        
        for category, terms in self.expansion_terms.items():
            if any(term.lower() in query_lower for term in terms):
                expanded_terms.extend(terms)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in expanded_terms:
            if term.lower() not in seen:
                unique_terms.append(term)
                seen.add(term.lower())
        
        return " ".join(unique_terms)


class HybridRetriever:
    """Combines BM25 sparse and dense vector retrieval."""
    
    def __init__(self, 
                 bm25_weight: float = 0.3,
                 dense_weight: float = 0.7,
                 expansion_terms: Optional[Dict[str, List[str]]] = None):
        """
        Initialize hybrid retriever.
        
        Args:
            bm25_weight: Weight for BM25 scores
            dense_weight: Weight for dense vector scores
            expansion_terms: Query expansion mappings
        """
        self.bm25_weight = bm25_weight
        self.dense_weight = dense_weight
        self.bm25 = BM25Scorer()
        self.expander = QueryExpander(expansion_terms or {})
        self.chunks = []
        
        # Validate weights
        if abs(bm25_weight + dense_weight - 1.0) > 1e-6:
            logger.warning(f"Weights don't sum to 1.0: {bm25_weight} + {dense_weight}")
    
    def fit(self, chunks: List[TextChunk]):
        """Build retrieval indices from chunks."""
        self.chunks = chunks
        documents = [chunk.content for chunk in chunks]
        self.bm25.fit(documents)
        logger.info(f"Fitted hybrid retriever with {len(chunks)} chunks")
    
    def retrieve(self, 
                 query: str,
                 dense_scores: List[Tuple[float, int]],
                 law_filter: Optional[Set[str]] = None,
                 top_k: int = 5) -> List[SearchResult]:
        """
        Hybrid retrieval with score fusion.
        
        Args:
            query: Search query
            dense_scores: List of (dense_score, chunk_index) from vector search
            law_filter: Set of law_ids to filter by
            top_k: Number of results to return
            
        Returns:
            Ranked search results
        """
        start_time = time.time()
        
        # Expand query
        expanded_query = self.expander.expand_query(query)
        
        # Get dense scores as dict
        dense_score_dict = {idx: score for score, idx in dense_scores}
        
        # Filter chunks by law if specified
        if law_filter:
            candidate_indices = [
                i for i, chunk in enumerate(self.chunks) 
                if chunk.law_id in law_filter
            ]
        else:
            candidate_indices = list(range(len(self.chunks)))
        
        # Get BM25 scores for candidate chunks
        bm25_scores = self.bm25.score(expanded_query, candidate_indices)
        
        # Combine scores using weighted fusion
        combined_results = []
        
        for i, chunk_idx in enumerate(candidate_indices):
            chunk = self.chunks[chunk_idx]
            
            # Get individual scores
            bm25_score = bm25_scores[i] if i < len(bm25_scores) else 0.0
            dense_score = dense_score_dict.get(chunk_idx, 0.0)
            
            # Normalize scores (simple min-max scaling)
            normalized_bm25 = self._normalize_score(bm25_score, [s for s in bm25_scores if s > 0])
            normalized_dense = dense_score  # Already normalized by FAISS
            
            # Weighted combination
            combined_score = (
                self.bm25_weight * normalized_bm25 + 
                self.dense_weight * normalized_dense
            )
            
            result = SearchResult(
                law_id=chunk.law_id,
                law_name=chunk.law_name,
                jurisdiction=chunk.jurisdiction,
                section_label=chunk.section_label,
                score=combined_score,
                snippet=self._create_snippet(chunk.content),
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                source_path=chunk.source_path,
                latency_ms=0,  # Will be set later
                dense_score=dense_score,
                sparse_score=bm25_score
            )
            
            combined_results.append(result)
        
        # Sort by combined score and take top_k
        combined_results.sort(key=lambda x: x.score, reverse=True)
        top_results = combined_results[:top_k]
        
        # Set latency for all results
        latency_ms = int((time.time() - start_time) * 1000)
        for result in top_results:
            result.latency_ms = latency_ms
        
        return top_results
    
    def _normalize_score(self, score: float, score_list: List[float]) -> float:
        """Normalize score using min-max scaling."""
        if not score_list or len(score_list) == 1:
            return 1.0 if score > 0 else 0.0
        
        min_score = min(score_list)
        max_score = max(score_list)
        
        if max_score == min_score:
            return 1.0 if score > 0 else 0.0
        
        return (score - min_score) / (max_score - min_score)
    
    def _create_snippet(self, content: str, max_chars: int = 1200) -> str:
        """Create snippet from content with proper boundaries."""
        if len(content) <= max_chars:
            return content
        
        # Try to break at sentence boundaries
        sentences = re.split(r'[.!?]\\s+', content[:max_chars + 100])
        
        snippet = ""
        for sentence in sentences[:-1]:  # Exclude last partial sentence
            if len(snippet + sentence) <= max_chars:
                snippet += sentence + ". "
            else:
                break
        
        if not snippet:
            # Fallback to character limit
            snippet = content[:max_chars]
            # Try to end at word boundary
            last_space = snippet.rfind(' ')
            if last_space > max_chars * 0.8:
                snippet = snippet[:last_space]
            snippet += "..."
        
        return snippet.strip()
