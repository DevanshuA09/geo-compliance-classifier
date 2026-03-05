"""Parser modules for different file types."""

from .docx_parser import parse_docx
from .md_html_parser import parse_html, parse_markdown
from .pdf_parser import parse_pdf
from .txt_parser import parse_txt

__all__ = ["parse_pdf", "parse_docx", "parse_markdown", "parse_html", "parse_txt"]
