"""Command-line interface for the Artifact Preprocessor Agent."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .expand_terms import CodenameExpander
from .extract import FieldExtractor
from .io_utils import (find_documents, load_features_csv, load_terminology_csv,
                       write_csv, write_jsonl)
from .logging_conf import get_logger, setup_logging
from .normalize import normalize_text
from .parsers import (parse_docx, parse_html, parse_markdown, parse_pdf,
                      parse_txt)
from .reporter import ProcessingReporter
from .schema import DocumentArtifact, FeatureRecord

logger = get_logger(__name__)


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(level=args.log_level, verbose=args.verbose)

    logger.info(f"Artifact Preprocessor Agent v{__version__}")
    logger.info(f"Processing with configuration: {vars(args)}")

    try:
        # Load inputs
        terminology = load_terminology_csv(Path(args.terms))
        features = load_features_csv(Path(args.features)) if args.features else []

        # Find documents
        documents = find_documents(Path(args.docs)) if args.docs else []

        # Initialize processors
        field_extractor = FieldExtractor()
        expander = CodenameExpander(terminology)
        reporter = ProcessingReporter()

        # Validate terminology
        term_warnings = expander.validate_terminology()
        if term_warnings:
            logger.warning(f"Terminology validation issues: {term_warnings}")

        # Process all inputs
        records = []

        # Process feature CSV data
        if features:
            logger.info(f"Processing {len(features)} features from CSV")
            for i, (feature_name, feature_description) in enumerate(features):
                record = process_feature_csv(
                    feature_name, feature_description, i, field_extractor, expander
                )
                records.append(record)

        # Process document files
        if documents:
            logger.info(f"Processing {len(documents)} documents")
            for doc_path in documents:
                try:
                    doc_artifact = parse_document(doc_path)
                    if doc_artifact.raw_text:
                        doc_records = process_document(
                            doc_artifact, field_extractor, expander
                        )
                        records.extend(doc_records)
                except Exception as e:
                    logger.error(f"Failed to process document {doc_path}: {e}")

        # Generate outputs
        output_dir = Path(args.out)
        output_dir.mkdir(parents=True, exist_ok=True)

        if records:
            # Write main outputs
            write_jsonl(records, output_dir / "preprocessed.jsonl")
            write_csv(records, output_dir / "preprocessed.csv")

            # Write expansion report
            write_expansion_report(records, output_dir / "expansion_report.csv")

            logger.info(f"Processed {len(records)} total records")
        else:
            logger.warning("No records were processed")

        # Generate processing report
        total_docs = len(documents) + (1 if features else 0)  # CSV counts as 1 doc
        reporter.generate_report(records, total_docs, len(terminology), output_dir)

        # Check success criteria
        success_rate = len(records) / max(total_docs, 1)
        if success_rate < 1.0:
            logger.warning(f"Parse success rate {success_rate:.1%} below 100%")
            return 1

        logger.info("Processing completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="Artifact Preprocessor Agent - Normalize PRD/TRD inputs and expand codenames",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process features CSV with terminology
  python -m artifact_preprocessor.cli --features data.csv --terms terms.csv --out ./out
  
  # Process documents with expansion
  python -m artifact_preprocessor.cli --docs ./docs --terms terms.csv --out ./out
  
  # Process both features and documents
  python -m artifact_preprocessor.cli \\
    --features data.csv --terms terms.csv --docs ./docs --out ./out
        """,
    )

    parser.add_argument(
        "--features",
        type=str,
        help="Path to features CSV file (columns: feature_name, feature_description)",
    )

    parser.add_argument(
        "--terms",
        type=str,
        required=True,
        help="Path to terminology CSV file (columns: term, explanation)",
    )

    parser.add_argument(
        "--docs",
        type=str,
        help="Path to documents directory (supports PDF, DOCX, MD, HTML, TXT)",
    )

    parser.add_argument(
        "--out", type=str, default="./out", help="Output directory (default: ./out)"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging (sets level to DEBUG)",
    )

    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    return parser


def parse_document(file_path: Path) -> DocumentArtifact:
    """Parse a document file based on its extension.

    Args:
        file_path: Path to document file

    Returns:
        DocumentArtifact with extracted content

    Raises:
        ValueError: If file type is not supported
    """
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return parse_pdf(file_path)
    elif suffix == ".docx":
        return parse_docx(file_path)
    elif suffix == ".md":
        return parse_markdown(file_path)
    elif suffix in [".html", ".htm"]:
        return parse_html(file_path)
    elif suffix == ".txt":
        return parse_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def process_feature_csv(
    feature_name: str,
    feature_description: str,
    index: int,
    field_extractor: FieldExtractor,
    expander: CodenameExpander,
) -> FeatureRecord:
    """Process a single feature from CSV data.

    Args:
        feature_name: Feature name
        feature_description: Feature description
        index: Feature index for ID generation
        field_extractor: Field extraction engine
        expander: Codename expansion engine

    Returns:
        Processed FeatureRecord
    """
    # Create feature ID
    feature_id = f"csv_feature_{index:04d}"

    # Combine name and description for processing
    combined_text = f"Feature: {feature_name}\n\nDescription: {feature_description}"
    normalized_text = normalize_text(combined_text)

    # Extract fields (minimal for CSV data)
    fields = {"feature_title": feature_name, "feature_description": feature_description}

    # Expand codenames
    text_hash, expanded_text, hits = expander.expand_text(normalized_text)
    expanded_hash, _, _ = expander.expand_text(expanded_text)

    # Create record
    record = FeatureRecord(
        feature_id=feature_id,
        doc_id="features_csv",
        source_path="features.csv",
        feature_title=fields.get("feature_title"),
        feature_description=fields.get("feature_description"),
        codename_hits=hits,
    )

    return record


def process_document(
    doc_artifact: DocumentArtifact,
    field_extractor: FieldExtractor,
    expander: CodenameExpander,
) -> List[FeatureRecord]:
    """Process a document artifact into feature records.

    Args:
        doc_artifact: Parsed document artifact
        field_extractor: Field extraction engine
        expander: Codename expansion engine

    Returns:
        List of FeatureRecord objects
    """
    # Normalize text
    normalized_text = normalize_text(doc_artifact.raw_text)

    # Extract fields
    fields = field_extractor.extract_fields(normalized_text)

    # Expand codenames
    text_hash, expanded_text, hits = expander.expand_text(normalized_text)
    expanded_hash, _, _ = expander.expand_text(expanded_text)

    # Create single record per document
    # In a more advanced version, this could split documents into multiple features
    feature_id = f"{doc_artifact.doc_id}_feature_001"

    record = FeatureRecord(
        feature_id=feature_id,
        doc_id=doc_artifact.doc_id,
        source_path=doc_artifact.source_path,
        date=fields.get("date"),
        feature_title=fields.get("feature_title"),
        feature_description=fields.get("feature_description"),
        objectives=fields.get("objectives"),
        user_segments=fields.get("user_segments"),
        geo_country=fields.get("geo_country"),
        geo_state=fields.get("geo_state"),
        codename_hits=hits,
    )

    return [record]


def write_expansion_report(records: List[FeatureRecord], output_path: Path) -> None:
    """Write expansion report CSV.

    Args:
        records: Processed records
        output_path: Output file path
    """
    import csv

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["feature_id", "term", "expansion", "count"])

        for record in records:
            for hit in record.codename_hits:
                writer.writerow([record.feature_id, hit.term, hit.expansion, hit.count])

    logger.info(f"Wrote expansion report to {output_path}")


if __name__ == "__main__":
    sys.exit(main())
