"""
Vector index builder with FAISS and embedding generation.
"""

import json
import logging
import pickle
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

try:
    import faiss
except ImportError:
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from ingest.chunker import ChunkingConfig, TextChunker
from ingest.loader import DocumentLoader
from retriever.models import IndexStats, TextChunk

logger = logging.getLogger(__name__)


class VectorIndexBuilder:
    """Builds and manages FAISS vector index for legal documents."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize builder with configuration."""
        import yaml

        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.embedding_config = self.config["embedding"]
        self.index_config = self.config["index"]
        self.chunking_config = ChunkingConfig(**self.config["chunking"])

        # Initialize components
        self.loader = DocumentLoader(config_path)
        self.chunker = TextChunker(self.chunking_config)
        self.model = None
        self.index = None
        self.chunks_metadata = []

        # Ensure required dependencies
        if faiss is None:
            raise ImportError(
                "faiss-cpu is required. Install with: pip install faiss-cpu"
            )
        if SentenceTransformer is None:
            raise ImportError(
                "sentence-transformers is required. Install with: pip install sentence-transformers"
            )

    def build_index(self, index_dir: str = "index") -> IndexStats:
        """
        Build complete vector index from legal documents.

        Returns:
            Index statistics and build metrics
        """
        start_time = time.time()
        index_path = Path(index_dir)
        index_path.mkdir(exist_ok=True)

        logger.info("Starting index build process...")

        # Load and chunk all documents
        documents = self.loader.load_all_documents()
        all_chunks = []

        for doc in documents:
            chunks = self.chunker.chunk_document(doc)
            all_chunks.extend(chunks)

        logger.info(
            f"Generated {len(all_chunks)} total chunks from {len(documents)} documents"
        )

        # Initialize embedding model
        self._load_embedding_model()

        # Generate embeddings
        embeddings = self._generate_embeddings(all_chunks)

        # Build FAISS index
        self._build_faiss_index(embeddings)

        # Store metadata
        self.chunks_metadata = all_chunks

        # Persist index and metadata
        self._save_index(index_path)

        build_time = time.time() - start_time

        # Calculate index size
        index_size_mb = self._calculate_index_size(index_path)

        stats = IndexStats(
            total_documents=len(documents),
            total_chunks=len(all_chunks),
            embedding_dimension=self.index_config["dimension"],
            index_size_mb=index_size_mb,
            laws_indexed=[doc.law_id for doc in documents],
            build_time_seconds=build_time,
        )

        logger.info(f"Index build completed in {build_time:.2f}s")
        logger.info(f"Index size: {index_size_mb:.2f} MB")

        return stats

    def load_index(self, index_dir: str = "index") -> bool:
        """Load existing index from disk."""
        index_path = Path(index_dir)

        if not index_path.exists():
            logger.error(f"Index directory not found: {index_path}")
            return False

        try:
            # Load FAISS index
            faiss_path = index_path / "faiss" / "index.faiss"
            if faiss_path.exists():
                self.index = faiss.read_index(str(faiss_path))
            else:
                logger.error("FAISS index file not found")
                return False

            # Load metadata
            metadata_path = index_path / "faiss" / "id_map.jsonl"
            if metadata_path.exists():
                self.chunks_metadata = []
                with open(metadata_path, "r", encoding="utf-8") as f:
                    for line in f:
                        meta = json.loads(line)
                        # Create TextChunk with proper field mapping
                        chunk = TextChunk(
                            chunk_id=meta.get("id", str(meta.get("row", 0))),
                            law_id=meta.get("law_id", "Unknown"),
                            law_name=meta.get("law_name", "Unknown"),
                            jurisdiction=meta.get("jurisdiction", "Unknown"),
                            section_label=meta.get("section_label", ""),
                            section_path=meta.get("section_label", ""),
                            content=meta.get("text", ""),
                            start_line=meta.get("meta", {}).get("start_line", 0),
                            end_line=meta.get("meta", {}).get("end_line", 0),
                            source_path=meta.get("source_path", ""),
                            char_start=meta.get("meta", {}).get("start_char", 0),
                            char_end=meta.get("meta", {}).get("end_char", 0),
                        )
                        self.chunks_metadata.append(chunk)
            else:
                logger.error("Metadata file not found")
                return False

            # Load embedding model
            self._load_embedding_model()

            logger.info(f"Loaded index with {len(self.chunks_metadata)} chunks")
            return True

        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False

    def _load_embedding_model(self):
        """Load sentence transformer model."""
        model_name = self.embedding_config["model_name"]
        device = self.embedding_config["device"]

        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name, device=device)

    def _generate_embeddings(self, chunks: List[TextChunk]) -> np.ndarray:
        """Generate embeddings for all chunks."""
        logger.info("Generating embeddings...")

        # Extract text content
        texts = [chunk.content for chunk in chunks]

        # Generate embeddings in smaller batches for memory efficiency
        batch_size = 8  # Reduced from 32 to avoid memory issues
        embeddings = []

        try:
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i : i + batch_size]
                logger.info(
                    f"Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}"
                )

                batch_embeddings = self.model.encode(
                    batch_texts,
                    convert_to_numpy=True,
                    show_progress_bar=False,  # Disable progress bar to reduce output
                )
                embeddings.append(batch_embeddings)

                # Force garbage collection after each batch
                import gc

                gc.collect()

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

        embeddings_array = np.vstack(embeddings)
        logger.info(f"Generated embeddings shape: {embeddings_array.shape}")

        return embeddings_array

    def _build_faiss_index(self, embeddings: np.ndarray):
        """Build FAISS index from embeddings."""
        logger.info("Building FAISS index...")

        dimension = embeddings.shape[1]

        # Use IndexFlatIP for cosine similarity (inner product after normalization)
        self.index = faiss.IndexFlatIP(dimension)

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)

        # Add embeddings to index
        self.index.add(embeddings)

        logger.info(f"Built FAISS index with {self.index.ntotal} vectors")

    def _save_index(self, index_path: Path):
        """Save index and metadata to disk."""
        logger.info(f"Saving index to {index_path}")

        # Create FAISS subdirectory
        faiss_dir = index_path / "faiss"
        faiss_dir.mkdir(exist_ok=True)

        # Save FAISS index
        faiss_path = faiss_dir / "index.faiss"
        faiss.write_index(self.index, str(faiss_path))

        # Save metadata as JSONL for easier access
        id_map_path = faiss_dir / "id_map.jsonl"
        with open(id_map_path, "w", encoding="utf-8") as f:
            for i, chunk in enumerate(self.chunks_metadata):
                meta = {
                    "row": i,
                    "id": chunk.chunk_id,
                    "text": chunk.content,
                    "law_id": chunk.law_id,
                    "law_name": chunk.law_name,
                    "section_label": chunk.section_label,
                    "jurisdiction": chunk.jurisdiction,
                    "source_path": chunk.source_path,
                    "meta": {
                        "start_char": chunk.char_start,
                        "end_char": chunk.char_end,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                    },
                }
                f.write(json.dumps(meta) + "\n")

        # Also save legacy pickle format for backward compatibility
        metadata_path = index_path / "chunks_metadata.pkl"
        with open(metadata_path, "rb") as f:
            pickle.dump(self.chunks_metadata, f)

        # Save configuration
        config_path = index_path / "index_config.pkl"
        index_info = {
            "embedding_config": self.embedding_config,
            "index_config": self.index_config,
            "chunking_config": self.chunking_config.__dict__,
        }
        with open(config_path, "wb") as f:
            pickle.dump(index_info, f)

    def _calculate_index_size(self, index_path: Path) -> float:
        """Calculate total index size in MB."""
        total_size = 0
        for file_path in index_path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)

    def search(
        self, query_embedding: np.ndarray, top_k: int = 5
    ) -> List[Tuple[float, TextChunk]]:
        """
        Search index for similar chunks.

        Args:
            query_embedding: Normalized query embedding
            top_k: Number of results to return

        Returns:
            List of (score, chunk) tuples
        """
        if self.index is None:
            raise ValueError("Index not loaded. Call load_index() first.")

        # Normalize query embedding
        query_embedding = query_embedding.reshape(1, -1)
        faiss.normalize_L2(query_embedding)

        # Search index
        scores, indices = self.index.search(query_embedding, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0:  # Valid index
                chunk = self.chunks_metadata[idx]
                results.append((float(score), chunk))

        return results


def main():
    """Main function to build the vector index."""
    logging.basicConfig(level=logging.INFO)
    import argparse

    parser = argparse.ArgumentParser(description="Build FAISS vector index")
    parser.add_argument(
        "--rebuild", action="store_true", help="Rebuild index even if exists"
    )
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    args = parser.parse_args()

    builder = VectorIndexBuilder(args.config)

    # Check if index exists
    if not args.rebuild and Path("index/faiss/index.faiss").exists():
        print("Index already exists. Use --rebuild to overwrite.")
        return

    stats = builder.build_index()

    print(f"Index built successfully!")
    print(f"Total chunks: {stats.total_chunks}")
    print(f"Total documents: {stats.total_documents}")
    print(f"Build time: {stats.build_time_seconds:.2f}s")
    print(f"Index saved to: index/faiss/")

    return stats


if __name__ == "__main__":
    main()
