"""PDF parser using PyPDF2 and pdfminer.six as fallback."""

from pathlib import Path
from typing import List, Optional

from ..logging_conf import get_logger
from ..schema import DocumentArtifact

logger = get_logger(__name__)


def parse_pdf(file_path: Path) -> DocumentArtifact:
    """Parse PDF file and extract text.

    Args:
        file_path: Path to PDF file

    Returns:
        DocumentArtifact with extracted text
    """
    doc_id = file_path.stem
    warnings = []
    text = ""

    # Try PyPDF2 first
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(str(file_path))
        pages_text = []

        for page_num, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text() or ""
                pages_text.append(page_text)
            except Exception as e:
                warnings.append(f"Failed to extract page {page_num + 1}: {e}")

        text = "\n".join(pages_text).strip()

        if not text:
            warnings.append("PyPDF2 extracted no text, trying pdfminer.six")
        else:
            logger.debug(f"PyPDF2 extracted {len(text)} characters from {file_path}")

    except ImportError:
        warnings.append("PyPDF2 not available, trying pdfminer.six")
    except Exception as e:
        warnings.append(f"PyPDF2 failed: {e}, trying pdfminer.six")

    # Fallback to pdfminer.six if PyPDF2 failed or extracted no text
    if not text:
        try:
            from pdfminer.high_level import extract_text

            text = extract_text(str(file_path))
            logger.debug(
                f"pdfminer.six extracted {len(text)} characters from {file_path}"
            )

        except ImportError:
            warnings.append("pdfminer.six not available")
        except Exception as e:
            warnings.append(f"pdfminer.six failed: {e}")

    if not text:
        warnings.append("No text could be extracted from PDF")
        logger.warning(f"Failed to extract any text from {file_path}")

    return DocumentArtifact(
        doc_id=doc_id,
        doc_type="pdf",
        source_path=str(file_path),
        raw_text=text,
        parse_warnings=warnings,
    )
