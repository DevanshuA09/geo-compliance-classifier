"""Test parsers for different file types."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile

from artifact_preprocessor.parsers import (
    parse_pdf, parse_docx, parse_markdown, parse_html, parse_txt
)
from artifact_preprocessor.schema import DocumentArtifact


class TestParsers:
    """Test suite for document parsers."""
    
    def test_parse_txt_success(self):
        """Test successful text file parsing."""
        content = "This is test content\nWith multiple lines"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            f.flush()
            
            result = parse_txt(Path(f.name))
            
        # Cleanup
        Path(f.name).unlink()
        
        assert isinstance(result, DocumentArtifact)
        assert result.doc_type == "txt"
        assert result.raw_text == content
        assert len(result.parse_warnings) == 0
    
    def test_parse_txt_missing_file(self):
        """Test text parser with missing file."""
        with pytest.raises(FileNotFoundError):
            parse_txt(Path("nonexistent.txt"))
    
    @patch('artifact_preprocessor.parsers.pdf_parser.PdfReader')
    def test_parse_pdf_success(self, mock_pdf_reader):
        """Test successful PDF parsing with PyPDF2."""
        # Mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "Sample PDF content"
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            result = parse_pdf(Path(f.name))
        
        # Cleanup
        Path(f.name).unlink()
        
        assert isinstance(result, DocumentArtifact)
        assert result.doc_type == "pdf"
        assert result.raw_text == "Sample PDF content"
        assert len(result.parse_warnings) == 0
    
    @patch('artifact_preprocessor.parsers.pdf_parser.PdfReader')
    @patch('artifact_preprocessor.parsers.pdf_parser.extract_text')
    def test_parse_pdf_fallback(self, mock_extract_text, mock_pdf_reader):
        """Test PDF parsing fallback to pdfminer.six."""
        # Mock PyPDF2 failure
        mock_pdf_reader.side_effect = Exception("PyPDF2 failed")
        
        # Mock pdfminer success
        mock_extract_text.return_value = "Fallback PDF content"
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            result = parse_pdf(Path(f.name))
        
        # Cleanup
        Path(f.name).unlink()
        
        assert result.raw_text == "Fallback PDF content"
        assert any("PyPDF2 failed" in w for w in result.parse_warnings)
    
    @patch('artifact_preprocessor.parsers.docx_parser.Document')
    def test_parse_docx_success(self, mock_document):
        """Test successful DOCX parsing."""
        # Mock document structure
        mock_para = Mock()
        mock_para.text = "Sample paragraph"
        
        mock_doc = Mock()
        mock_doc.paragraphs = [mock_para]
        mock_doc.tables = []
        mock_document.return_value = mock_doc
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            result = parse_docx(Path(f.name))
        
        # Cleanup
        Path(f.name).unlink()
        
        assert isinstance(result, DocumentArtifact)
        assert result.doc_type == "docx"
        assert result.raw_text == "Sample paragraph"
        assert len(result.parse_warnings) == 0
    
    def test_parse_markdown_plain_fallback(self):
        """Test Markdown parsing with plain text fallback."""
        content = "# Header\n\nSome **markdown** content"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(content)
            f.flush()
            
            result = parse_markdown(Path(f.name))
        
        # Cleanup
        Path(f.name).unlink()
        
        assert isinstance(result, DocumentArtifact)
        assert result.doc_type == "md"
        # Should contain the content (either processed or raw)
        assert "Header" in result.raw_text
        assert "markdown" in result.raw_text
    
    def test_parse_html_success(self):
        """Test HTML parsing."""
        content = "<html><body><h1>Title</h1><p>Content</p></body></html>"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(content)
            f.flush()
            
            result = parse_html(Path(f.name))
        
        # Cleanup
        Path(f.name).unlink()
        
        assert isinstance(result, DocumentArtifact)
        assert result.doc_type == "html"
        # Should extract text content
        assert "Title" in result.raw_text
        assert "Content" in result.raw_text
        # Should not contain HTML tags
        assert "<h1>" not in result.raw_text


class TestParserFixtures:
    """Test parsers with various document fixtures."""
    
    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        docs = {}
        
        # Text document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Feature: Test Feature\n\nDescription: This is a test feature.")
            docs['txt'] = Path(f.name)
        
        # Markdown document  
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("# Test Document\n\n## Objective\n\nTest the system.\n\n## Scope\n\nUnit testing.")
            docs['md'] = Path(f.name)
        
        # HTML document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write("<html><head><title>Test</title></head><body><h1>Feature Title</h1><p>Feature description here.</p></body></html>")
            docs['html'] = Path(f.name)
        
        yield docs
        
        # Cleanup
        for path in docs.values():
            path.unlink()
    
    def test_all_parsers_well_formed(self, sample_documents):
        """Test that all parsers handle well-formed inputs successfully."""
        results = {}
        
        # Test text parser
        results['txt'] = parse_txt(sample_documents['txt'])
        
        # Test markdown parser
        results['md'] = parse_markdown(sample_documents['md'])
        
        # Test HTML parser
        results['html'] = parse_html(sample_documents['html'])
        
        # Verify all parsed successfully
        for doc_type, result in results.items():
            assert isinstance(result, DocumentArtifact)
            assert result.doc_type == doc_type
            assert len(result.raw_text) > 0
            # Well-formed inputs should have no warnings
            assert len(result.parse_warnings) == 0
    
    def test_parser_content_extraction(self, sample_documents):
        """Test that parsers extract expected content."""
        # Test text content
        txt_result = parse_txt(sample_documents['txt'])
        assert "Test Feature" in txt_result.raw_text
        assert "test feature" in txt_result.raw_text
        
        # Test markdown content
        md_result = parse_markdown(sample_documents['md'])
        assert "Test Document" in md_result.raw_text
        assert "Objective" in md_result.raw_text
        assert "Scope" in md_result.raw_text
        
        # Test HTML content
        html_result = parse_html(sample_documents['html'])
        assert "Feature Title" in html_result.raw_text
        assert "Feature description" in html_result.raw_text
        # Should not contain HTML tags
        assert "<h1>" not in html_result.raw_text
