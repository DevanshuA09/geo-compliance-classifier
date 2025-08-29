"""Markdown and HTML parsers."""

from pathlib import Path
from typing import List

from ..io_utils import read_text_file
from ..logging_conf import get_logger
from ..schema import DocumentArtifact

logger = get_logger(__name__)


def parse_markdown(file_path: Path) -> DocumentArtifact:
    """Parse Markdown file and extract text.
    
    Args:
        file_path: Path to Markdown file
        
    Returns:
        DocumentArtifact with extracted text
    """
    doc_id = file_path.stem
    warnings = []
    text = ""
    
    try:
        # First try with markdown library
        try:
            import markdown
            
            raw_content = read_text_file(file_path)
            md = markdown.Markdown(extensions=['meta', 'toc', 'tables'])
            html = md.convert(raw_content)
            
            # Extract plain text from the HTML
            text = _html_to_text(html)
            logger.debug(f"Markdown library extracted {len(text)} characters from {file_path}")
            
        except ImportError:
            warnings.append("markdown library not available, using plain text fallback")
            text = read_text_file(file_path)
        
    except Exception as e:
        warnings.append(f"Failed to parse Markdown: {e}")
        logger.warning(f"Failed to parse {file_path}: {e}")
    
    if not text:
        warnings.append("No text could be extracted from Markdown")
    
    return DocumentArtifact(
        doc_id=doc_id,
        doc_type="md",
        source_path=str(file_path),
        raw_text=text,
        parse_warnings=warnings
    )


def parse_html(file_path: Path) -> DocumentArtifact:
    """Parse HTML file and extract text.
    
    Args:
        file_path: Path to HTML file
        
    Returns:
        DocumentArtifact with extracted text
    """
    doc_id = file_path.stem
    warnings = []
    text = ""
    
    try:
        raw_content = read_text_file(file_path)
        text = _html_to_text(raw_content)
        logger.debug(f"Extracted {len(text)} characters from {file_path}")
        
    except Exception as e:
        warnings.append(f"Failed to parse HTML: {e}")
        logger.warning(f"Failed to parse {file_path}: {e}")
    
    if not text:
        warnings.append("No text could be extracted from HTML")
    
    return DocumentArtifact(
        doc_id=doc_id,
        doc_type="html",
        source_path=str(file_path),
        raw_text=text,
        parse_warnings=warnings
    )


def _html_to_text(html_content: str) -> str:
    """Convert HTML to plain text using BeautifulSoup.
    
    Args:
        html_content: Raw HTML content
        
    Returns:
        Plain text content
    """
    try:
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and normalize whitespace
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
        
    except ImportError:
        # Fallback: simple HTML tag removal using regex
        import re
        text = re.sub(r'<[^>]+>', '', html_content)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
