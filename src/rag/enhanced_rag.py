"""
Enhanced RAG Pipeline with Lightweight Embeddings and Reranker
"""

import json
import logging
import numpy as np
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
import faiss
from sentence_transformers import SentenceTransformer, CrossEncoder
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Document chunk with metadata."""
    text: str
    law_name: str
    jurisdiction: str
    section_label: str
    source_path: str
    chunk_id: str
    start_line: int = 0
    end_line: int = 0


@dataclass
class RetrievedResult:
    """Result from retrieval with ranking."""
    chunk: DocumentChunk
    retrieval_score: float
    rerank_score: float = 0.0
    final_rank: int = 0


class EnhancedRAGPipeline:
    """Production RAG pipeline with BGE embeddings and reranking."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the enhanced RAG pipeline."""
        if config is None:
            config = {}
            
        self.config = config
        
        # Model configurations - using lighter models for faster setup
        self.embedding_model_name = config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
        self.reranker_model_name = config.get("reranker_model", "cross-encoder/ms-marco-MiniLM-L-2-v2")        # Retrieval parameters - use environment variables with defaults
        self.chunk_size = config.get("chunk_size", 512)
        self.chunk_overlap = config.get("chunk_overlap", 50)
        self.retrieval_top_k = config.get(
            "retrieval_top_k", 
            int(os.getenv("RETRIEVAL_TOP_K", "20"))
        )
        self.rerank_top_k = config.get(
            "rerank_top_k", 
            int(os.getenv("RERANK_TOP_K", "5"))
        )
        
        # Index paths
        self.index_path = config.get("index_path", "index/enhanced_faiss/index.faiss")
        self.metadata_path = config.get("metadata_path", "index/enhanced_faiss/metadata.json")
        
        # Initialize models
        self.embedding_model = None
        self.reranker = None
        self.index = None
        self.chunk_metadata = []
        
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize lighter embedding and reranking models for faster setup."""
        try:
            logger.info(f"🔧 Loading lightweight embedding model: {self.embedding_model_name}")
            # Use sentence-transformers instead of BGE for faster loading
            from sentence_transformers import SentenceTransformer, CrossEncoder
            
            self.embedding_model = SentenceTransformer(
                self.embedding_model_name,
                device='cpu'  # Use CPU for compatibility
            )
            logger.info("✅ Lightweight embedding model loaded")
            
            logger.info(f"🔧 Loading lightweight reranker: {self.reranker_model_name}")
            self.reranker = CrossEncoder(self.reranker_model_name)
            logger.info("✅ Lightweight reranker loaded")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize models: {e}")
            raise
            
    def _load_or_build_index(self):
        """Load existing index or build new one."""
        if Path(self.index_path).exists() and Path(self.metadata_path).exists():
            logger.info("📂 Loading existing enhanced index...")
            self._load_index()
        else:
            logger.info("🏗️ Building new enhanced index...")
            self._build_index()
            
    def _load_index(self):
        """Load existing FAISS index and metadata."""
        try:
            self.index = faiss.read_index(self.index_path)
            
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                metadata_list = json.load(f)
                self.chunk_metadata = [
                    DocumentChunk(**item) for item in metadata_list
                ]
            
            logger.info(f"✅ Loaded index with {self.index.ntotal} vectors and {len(self.chunk_metadata)} chunks")
            
        except Exception as e:
            logger.error(f"❌ Failed to load index: {e}")
            raise
            
    def _build_index(self):
        """Build new FAISS index with BGE embeddings."""
        logger.info("🔨 Building enhanced FAISS index with BGE embeddings...")
        
        # Load legal documents
        legal_texts_dir = Path("legal_texts")
        chunks = []
        
        for text_file in legal_texts_dir.glob("*.txt"):
            logger.info(f"📖 Processing {text_file.name}")
            chunks.extend(self._chunk_document(text_file))
        
        if not chunks:
            raise ValueError("No documents found to index")
            
        logger.info(f"📊 Total chunks to index: {len(chunks)}")
        
        # Generate embeddings using sentence-transformers
        texts = [chunk.text for chunk in chunks]
        logger.info("🧮 Generating lightweight embeddings...")
        
        embeddings = self.embedding_model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        logger.info(f"🏗️ Building FAISS index with dimension {dimension}")
        
        # Use IndexFlatIP for inner product (cosine similarity)
        self.index = faiss.IndexFlatIP(dimension)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings.astype('float32'))
        
        # Save index and metadata
        Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        
        # Save metadata
        self.chunk_metadata = chunks
        metadata_list = [
            {
                'text': chunk.text,
                'law_name': chunk.law_name,
                'jurisdiction': chunk.jurisdiction, 
                'section_label': chunk.section_label,
                'source_path': chunk.source_path,
                'chunk_id': chunk.chunk_id,
                'start_line': chunk.start_line,
                'end_line': chunk.end_line
            }
            for chunk in chunks
        ]
        
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_list, f, indent=2, ensure_ascii=False)
            
        logger.info(f"✅ Enhanced index built and saved with {self.index.ntotal} vectors")
        
    def _chunk_document(self, file_path: Path) -> List[DocumentChunk]:
        """Chunk a document into overlapping segments."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract metadata from filename and content
            law_name = self._extract_law_name(file_path.stem)
            jurisdiction = self._extract_jurisdiction(content, file_path.stem)
            
            chunks = []
            lines = content.split('\n')
            
            # Create overlapping chunks
            i = 0
            chunk_num = 0
            
            while i < len(lines):
                chunk_lines = []
                char_count = 0
                start_line = i
                
                # Build chunk up to size limit
                while i < len(lines) and char_count < self.chunk_size:
                    line = lines[i].strip()
                    if line:  # Skip empty lines
                        chunk_lines.append(line)
                        char_count += len(line) + 1
                    i += 1
                
                if chunk_lines:
                    chunk_text = ' '.join(chunk_lines)
                    
                    chunk = DocumentChunk(
                        text=chunk_text,
                        law_name=law_name,
                        jurisdiction=jurisdiction,
                        section_label=f"Chunk_{chunk_num}",
                        source_path=str(file_path),
                        chunk_id=f"{file_path.stem}_{chunk_num}",
                        start_line=start_line,
                        end_line=i-1
                    )
                    
                    chunks.append(chunk)
                    chunk_num += 1
                    
                    # Apply overlap
                    overlap_lines = min(self.chunk_overlap // 50, len(chunk_lines))
                    i = max(start_line + len(chunk_lines) - overlap_lines, start_line + 1)
                    
            logger.info(f"📝 Created {len(chunks)} chunks from {file_path.name}")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Failed to chunk {file_path}: {e}")
            return []
            
    def _extract_law_name(self, filename: str) -> str:
        """Extract law name from filename."""
        name_mapping = {
            'EUDSA': 'EU Digital Services Act (DSA)',
            'GDPR_Article_7': 'GDPR Article 7',
            'NCMEC_reporting': '18 U.S.C. §2258A - Reporting requirements',
            'Environmental_Protection_Act': 'Environmental Protection Act',
            'Safety_Standards_Act': 'Safety Standards Act',
            'Cali': 'California Privacy Regulations',
            'Florida_text': 'Florida Privacy Regulations'
        }
        return name_mapping.get(filename, filename.replace('_', ' ').title())
        
    def _extract_jurisdiction(self, content: str, filename: str) -> str:
        """Extract jurisdiction from content or filename."""
        content_lower = content.lower()
        filename_lower = filename.lower()
        
        if any(term in content_lower for term in ['european union', 'eu ', 'gdpr', 'dsa']):
            return 'EU'
        elif any(term in content_lower for term in ['united states', 'u.s.', 'usc', 'coppa']):
            return 'US'
        elif any(term in filename_lower for term in ['cali', 'california']):
            return 'US-CA'
        elif any(term in filename_lower for term in ['florida', 'fl']):
            return 'US-FL'
        else:
            return 'Unknown'
            
    def retrieve_and_rerank(self, query: str) -> List[RetrievedResult]:
        """Main retrieval and reranking pipeline."""
        
        # Ensure index is loaded
        if self.index is None:
            self._load_or_build_index()
            
        logger.info(f"🔍 Processing query: {query[:100]}...")
        
        # Step 1: Generate query embedding using sentence-transformers
        query_embedding = self.embedding_model.encode(
            [query],
            convert_to_numpy=True,
            show_progress_bar=False
        )
        
        # Normalize for cosine similarity
        faiss.normalize_L2(query_embedding)
        
        # Step 2: Retrieve top-k candidates
        scores, indices = self.index.search(
            query_embedding.astype('float32'),
            self.retrieval_top_k
        )
        
        # Step 3: Prepare candidates for reranking
        candidates = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.chunk_metadata):
                chunk = self.chunk_metadata[idx]
                result = RetrievedResult(
                    chunk=chunk,
                    retrieval_score=float(score)
                )
                candidates.append(result)
                
        logger.info(f"📊 Retrieved {len(candidates)} candidates")
        
        if not candidates:
            return []
            
        # Step 4: Rerank with CrossEncoder
        logger.info("🔄 Reranking results...")
        
        # Prepare pairs for reranking
        pairs = [[query, candidate.chunk.text] for candidate in candidates]
        
        # Get reranking scores using CrossEncoder
        rerank_scores = self.reranker.predict(pairs)
        
        # Update candidates with rerank scores
        for candidate, rerank_score in zip(candidates, rerank_scores):
            candidate.rerank_score = float(rerank_score)
            
        # Step 5: Sort by rerank score and take top-k
        candidates.sort(key=lambda x: x.rerank_score, reverse=True)
        final_results = candidates[:self.rerank_top_k]
        
        # Assign final ranks
        for i, result in enumerate(final_results):
            result.final_rank = i + 1
            
        logger.info(f"✅ Reranked to top {len(final_results)} results")
        
        return final_results
        
    def format_context_for_llm(self, results: List[RetrievedResult]) -> str:
        """Format retrieved results as context for LLM."""
        if not results:
            return "No relevant regulatory context found."
            
        context_parts = []
        context_parts.append("RELEVANT REGULATORY CONTEXT:\n")
        
        for i, result in enumerate(results, 1):
            chunk = result.chunk
            context_parts.append(
                f"{i}. {chunk.law_name} ({chunk.jurisdiction})\n"
                f"   Section: {chunk.section_label}\n"
                f"   Relevance Score: {result.rerank_score:.3f}\n"
                f"   Content: {chunk.text}\n"
                f"   Source: {chunk.source_path}\n"
            )
            
        return "\n".join(context_parts)
        
    def get_citations(self, results: List[RetrievedResult]) -> List[Dict[str, str]]:
        """Extract citations from results."""
        citations = []
        for result in results:
            chunk = result.chunk
            citations.append({
                "source": f"{chunk.law_name} ({chunk.jurisdiction})",
                "snippet": chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
                "section": chunk.section_label,
                "relevance_score": result.rerank_score
            })
        return citations
