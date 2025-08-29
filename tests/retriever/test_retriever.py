"""
Test suite for the Regulation Retriever Agent.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
import json

from ingest.loader import DocumentLoader
from ingest.chunker import TextChunker, ChunkingConfig
from retriever.models import LegalDocument, TextChunk, Jurisdiction
from retriever.rank import BM25Scorer, HybridRetriever


@pytest.fixture
def sample_legal_texts():
    """Create sample legal text files for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Sample EU DSA text
    eu_text = """
Article 28
Risk assessment

1. Providers of very large online platforms and very large online search engines shall assess, 
at least once a year, any systemic risks stemming from the functioning and use of their service 
in the Union. That assessment shall be specific to their services and shall take into account 
how algorithmic systems may contribute to any of the systemic risks.

2. The assessment shall include an analysis of the risk of:
(a) dissemination of illegal content through their services;
(b) any negative effects for the exercise of fundamental rights, in particular the rights to 
human dignity, respect for private and family life, the protection of personal data, freedom 
of expression and information, the right to non-discrimination and the rights of the child.
    """
    
    # Sample Florida HB3 text
    fl_text = """
§501.1736 Social media platforms; requirements for minor users

(1) DEFINITIONS.—As used in this section:
(a) "Minor" means an individual under 18 years of age.
(b) "Social media platform" means a form of electronic communication through which users may 
create profiles, share information, and view and interact with user-generated content.

(2) PROHIBITED CONDUCT.—A social media platform shall:
(a) Prohibit a minor who is younger than 14 years of age from creating an account.
(b) Require parental consent for a minor who is 14 or 15 years of age to create an account.
    """
    
    # Write test files
    eu_file = Path(temp_dir) / "eudsa_test.txt"
    fl_file = Path(temp_dir) / "florida_test.txt"
    
    with open(eu_file, 'w', encoding='utf-8') as f:
        f.write(eu_text)
    
    with open(fl_file, 'w', encoding='utf-8') as f:
        f.write(fl_text)
    
    # Create test config
    config = {
        'sources': {
            'EUDSA_TEST': {
                'law_id': 'EUDSA_TEST',
                'law_name': 'EU Digital Services Act (Test)',
                'jurisdiction': 'EU',
                'file_path': str(eu_file),
                'section_patterns': ['Article \\d+']
            },
            'FL_TEST': {
                'law_id': 'FL_TEST',
                'law_name': 'Florida Test Law',
                'jurisdiction': 'US-FL',
                'file_path': str(fl_file),
                'section_patterns': ['§\\d+\\.\\d+']
            }
        },
        'chunking': {
            'min_chars': 200,
            'max_chars': 400,
            'overlap_ratio': 0.15,
            'preserve_sections': True
        }
    }
    
    config_file = Path(temp_dir) / "test_config.yaml"
    import yaml
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f)
    
    yield temp_dir, str(config_file)
    
    # Cleanup
    shutil.rmtree(temp_dir)


def test_document_loader(sample_legal_texts):
    """Test document loading and section detection."""
    temp_dir, config_file = sample_legal_texts
    
    loader = DocumentLoader(config_file)
    
    # Test loading single document
    doc = loader.load_document('EUDSA_TEST')
    
    assert doc.law_id == 'EUDSA_TEST'
    assert doc.jurisdiction == Jurisdiction.EU
    assert 'Article 28' in doc.content
    assert doc.total_lines > 0
    
    # Test section detection
    sections = loader.detect_sections('EUDSA_TEST', doc.content)
    
    assert len(sections) > 0
    assert any('Article 28' in section[0] for section in sections)
    
    # Test loading all documents
    all_docs = loader.load_all_documents()
    assert len(all_docs) == 2
    
    law_ids = {doc.law_id for doc in all_docs}
    assert law_ids == {'EUDSA_TEST', 'FL_TEST'}


def test_text_chunker(sample_legal_texts):
    """Test text chunking with section preservation."""
    temp_dir, config_file = sample_legal_texts
    
    loader = DocumentLoader(config_file)
    doc = loader.load_document('FL_TEST')
    
    chunking_config = ChunkingConfig(min_chars=100, max_chars=300, overlap_ratio=0.1)
    chunker = TextChunker(chunking_config)
    
    chunks = chunker.chunk_document(doc)
    
    assert len(chunks) > 0
    
    # Test chunk properties
    for chunk in chunks:
        assert isinstance(chunk, TextChunk)
        assert chunk.law_id == 'FL_TEST'
        assert chunk.jurisdiction == 'US-FL'
        assert len(chunk.content) <= chunking_config.max_chars
        assert chunk.start_line <= chunk.end_line
        assert chunk.char_start <= chunk.char_end
    
    # Test section labels
    section_labels = {chunk.section_label for chunk in chunks}
    assert any('501.1736' in label for label in section_labels)


def test_bm25_scorer():
    """Test BM25 sparse retrieval."""
    documents = [
        "age verification requirements for social media platforms",
        "parental consent for minors under 16 years old",
        "systemic risk assessment for very large platforms",
        "content moderation and illegal content removal"
    ]
    
    bm25 = BM25Scorer()
    bm25.fit(documents)
    
    # Test query scoring
    query = "age verification minors"
    scores = bm25.score(query)
    
    assert len(scores) == len(documents)
    assert all(isinstance(score, float) for score in scores)
    
    # First document should have highest score (contains both "age" and "verification")
    max_score_idx = scores.index(max(scores))
    assert max_score_idx == 0


def test_search_models():
    """Test search result models."""
    from retriever.models import SearchResult, RetrievalRequest, RetrievalResponse
    
    # Test RetrievalRequest validation
    request = RetrievalRequest(
        query="test query",
        laws=["EUDSA"],
        top_k=5,
        max_chars=1000
    )
    
    assert request.query == "test query"
    assert request.laws == ["EUDSA"]
    
    # Test invalid requests
    with pytest.raises(ValueError):
        RetrievalRequest(query="", top_k=5)
    
    with pytest.raises(ValueError):
        RetrievalRequest(query="test", top_k=0)
    
    # Test SearchResult
    result = SearchResult(
        law_id="EUDSA",
        law_name="EU Digital Services Act",
        jurisdiction="EU",
        section_label="Article 28",
        score=0.85,
        snippet="Risk assessment requirements...",
        start_line=100,
        end_line=120,
        source_path="eudsa.txt",
        latency_ms=250
    )
    
    result_dict = result.to_dict()
    assert result_dict['score'] == 0.85
    assert result_dict['law_id'] == "EUDSA"
    
    # Test JSON serialization
    json_str = result.to_json()
    parsed = json.loads(json_str)
    assert parsed['score'] == 0.85


def test_hybrid_retriever():
    """Test hybrid retrieval with mock data."""
    # Create mock chunks
    chunks = [
        TextChunk(
            chunk_id="test_1",
            law_id="EUDSA",
            law_name="EU DSA",
            jurisdiction="EU",
            section_label="Article 28",
            section_path="Article 28",
            content="risk assessment systemic risks platforms",
            start_line=1,
            end_line=5,
            source_path="test.txt",
            char_start=0,
            char_end=50
        ),
        TextChunk(
            chunk_id="test_2",
            law_id="FL_HB3",
            law_name="Florida HB3",
            jurisdiction="US-FL",
            section_label="§501.1736",
            section_path="§501.1736",
            content="parental consent minor verification age",
            start_line=10,
            end_line=15,
            source_path="test.txt",
            char_start=60,
            char_end=110
        )
    ]
    
    retriever = HybridRetriever(bm25_weight=0.5, dense_weight=0.5)
    retriever.fit(chunks)
    
    # Mock dense scores (score, chunk_index)
    dense_scores = [(0.8, 0), (0.6, 1)]
    
    # Test retrieval
    results = retriever.retrieve(
        query="risk assessment platforms",
        dense_scores=dense_scores,
        top_k=2
    )
    
    assert len(results) <= 2
    assert all(isinstance(result, SearchResult) for result in results)
    
    # Results should be sorted by combined score
    if len(results) > 1:
        assert results[0].score >= results[1].score


@pytest.mark.asyncio
async def test_api_models():
    """Test API request/response models."""
    try:
        from fastapi.testclient import TestClient
        from retriever.service import app
        
        if app is not None:
            client = TestClient(app)
            
            # Test health endpoint
            response = client.get("/health")
            # Note: Will fail without proper service initialization, but tests structure
            assert response.status_code in [200, 503]  # 503 if service not ready
            
            # Test root endpoint
            response = client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert "service" in data
    
    except ImportError:
        # Skip test if FastAPI not available
        pytest.skip("FastAPI not available for testing")


def test_query_tokenization():
    """Test BM25 tokenization for legal text."""
    bm25 = BM25Scorer()
    
    # Test legal citation tokenization
    legal_text = "Section §501.1736(2)(a) requires parental consent for Art. 28 compliance"
    tokens = bm25._tokenize(legal_text)
    
    # Should preserve section numbers and article references
    assert "section_501" in " ".join(tokens) or "501" in tokens
    assert "article_28" in " ".join(tokens) or "article" in tokens
    assert "parental" in tokens
    assert "consent" in tokens
    
    # Should filter stop words
    assert "for" not in tokens
    assert "the" not in tokens


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
