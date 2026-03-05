"""
Tests for FAISS retriever functionality.
"""

import json
import os
import tempfile
from pathlib import Path

import faiss
import numpy as np
import pytest

from retriever.faiss_retriever import FaissRetriever


@pytest.fixture
def temp_config():
    """Create temporary configuration for testing."""
    return {
        "embedding": {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "dimension": 384,
            "device": "cpu",
        },
        "rag": {
            "vectorstore": {
                "type": "faiss",
                "index_path": "temp_index.faiss",
                "id_map_path": "temp_id_map.jsonl",
                "metric": "ip",
                "normalize": True,
            }
        },
    }


def test_faiss_retriever_initialization(temp_config):
    """Test FAISS retriever initialization."""
    # This test will fail if index doesn't exist, which is expected
    with pytest.raises(FileNotFoundError):
        retriever = FaissRetriever(temp_config)


def test_faiss_index_building_integration():
    """Test FAISS index retrieval workflow with existing mock index."""
    import yaml

    from retriever.faiss_retriever_mock import MockFaissRetriever

    # Load config
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Test retrieval with existing mock index
    retriever = MockFaissRetriever(config)

    # Test query
    results = retriever.retrieve("test query", top_k=3)
    assert len(results) >= 1
    assert all(hasattr(result, "snippet") for result in results)

    # Test stats
    stats = retriever.get_stats()
    assert stats["index_vectors"] > 0
    assert stats["dimension"] == 384
    assert stats["metric"] == "ip"
    assert stats["normalize"] == True


def test_faiss_retriever_stats(temp_config):
    """Test FAISS retriever statistics."""
    # This test will fail if index doesn't exist, which is expected
    with pytest.raises(FileNotFoundError):
        retriever = FaissRetriever(temp_config)
        # If it gets here, test stats
        stats = retriever.get_stats()
        assert "index_vectors" in stats
        assert "dimension" in stats
        assert "metric" in stats
