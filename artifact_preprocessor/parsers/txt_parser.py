"""Plain text parser."""

from pathlib import Path

from ..io_utils import read_text_file
from ..logging_conf import get_logger
from ..schema import DocumentArtifact

logger = get_logger(__name__)


def parse_txt(file_path: Path) -> DocumentArtifact:
    """Parse plain text file.

    Args:
        file_path: Path to text file

    Returns:
        DocumentArtifact with extracted text
    """
    doc_id = file_path.stem
    warnings = []
    text = ""

    try:
        text = read_text_file(file_path)
        logger.debug(f"Read {len(text)} characters from {file_path}")

    except Exception as e:
        warnings.append(f"Failed to read text file: {e}")
        logger.warning(f"Failed to read {file_path}: {e}")

    if not text:
        warnings.append("No text could be read from file")

    return DocumentArtifact(
        doc_id=doc_id,
        doc_type="txt",
        source_path=str(file_path),
        raw_text=text,
        parse_warnings=warnings,
    )
