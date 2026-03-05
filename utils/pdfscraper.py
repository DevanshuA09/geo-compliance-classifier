"""PDF scraper: extract text from PDF files using PyPDF2.

Usage:
    python pdfscraper.py --pdf /path/to/file.pdf [--out out.txt]
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

try:
    from PyPDF2 import PdfReader
except Exception as e:  # pragma: no cover
    raise ImportError("PyPDF2 is required. Install with `pip install PyPDF2`.") from e


def extract_text_from_pdf(path: str | Path) -> str:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    reader = PdfReader(str(path))
    texts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        texts.append(text)

    return "\n".join(texts).strip()


def _main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Extract text from PDF using PyPDF2")
    p.add_argument("--pdf", required=True, help="Path to the PDF file")
    p.add_argument(
        "--out", help="Optional output text file; if omitted prints to stdout"
    )
    args = p.parse_args(argv)

    text = extract_text_from_pdf(args.pdf)

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(text, encoding="utf-8")
        print(f"Wrote extracted text to: {out_path}")
    else:
        print(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
