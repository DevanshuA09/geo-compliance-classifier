"""
Evidence Exporter for Challenge CSV Generation

Converts JSONL evidence logs to challenge-compatible CSV format with filtering,
transformation, and export capabilities.
"""

import argparse
import csv
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class EvidenceExporter:
    """
    Exports evidence logs to challenge CSV format.

    Features:
    - JSONL to CSV conversion
    - Date range filtering
    - Agent filtering
    - Schema transformation
    - Multiple output formats
    """

    def __init__(self, evidence_dir: str = "data/evidence"):
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

        # Challenge CSV schema
        self.csv_schema = [
            "feature_id",
            "decision_flag",  # needs_geo_specific_logic
            "reasoning_text",
            "agent_name",
            "timestamp_iso",
            "confidence",
            "related_regulations",
            "retrieval_metadata",
            "feature_title",
            "pipeline_version",
            "environment",
        ]

    def list_evidence_files(self) -> List[Path]:
        """List all available evidence files."""
        if not self.evidence_dir.exists():
            return []

        files = list(self.evidence_dir.glob("*.jsonl"))
        return sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)

    def read_evidence_records(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        agent_filter: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Read evidence records with filtering.

        Args:
            start_date: Filter records from this date
            end_date: Filter records until this date
            agent_filter: List of agent names to include
            limit: Maximum number of records to return

        Yields:
            Evidence records as dictionaries
        """
        files = self.list_evidence_files()
        record_count = 0

        for file_path in files:
            if limit and record_count >= limit:
                break

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if limit and record_count >= limit:
                            break

                        try:
                            record = json.loads(line.strip())

                            # Apply filters
                            if not self._passes_filters(
                                record, start_date, end_date, agent_filter
                            ):
                                continue

                            yield record
                            record_count += 1

                        except json.JSONDecodeError as e:
                            logger.warning(
                                f"Invalid JSON in {file_path}:{line_num}: {e}"
                            )
                            continue

            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                continue

    def _passes_filters(
        self,
        record: Dict[str, Any],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        agent_filter: Optional[List[str]],
    ) -> bool:
        """Check if record passes all filters."""
        # Date filter
        if start_date or end_date:
            try:
                record_timestamp = datetime.fromisoformat(
                    record.get("timestamp_iso", "")
                )

                if start_date and record_timestamp < start_date:
                    return False
                if end_date and record_timestamp > end_date:
                    return False
            except (ValueError, TypeError):
                return False

        # Agent filter
        if agent_filter and record.get("agent_name") not in agent_filter:
            return False

        return True

    def transform_to_challenge_schema(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform evidence record to challenge CSV schema.

        Args:
            record: Original evidence record

        Returns:
            Transformed record for CSV export
        """
        # Extract related regulations
        related_regs = record.get("related_regulations", [])
        if isinstance(related_regs, list):
            regulations_str = "; ".join(str(reg) for reg in related_regs)
        else:
            regulations_str = str(related_regs) if related_regs else ""

        # Extract retrieval metadata
        retrieval_meta = record.get("retrieval_metadata", {})
        if isinstance(retrieval_meta, dict):
            # Flatten key metadata for CSV
            meta_parts = []
            for key, value in retrieval_meta.items():
                if isinstance(value, (str, int, float, bool)):
                    meta_parts.append(f"{key}:{value}")
                elif isinstance(value, list):
                    meta_parts.append(f"{key}:{len(value)}")
            retrieval_meta_str = "; ".join(meta_parts)
        else:
            retrieval_meta_str = str(retrieval_meta) if retrieval_meta else ""

        # Transform decision_flag to needs_geo_specific_logic
        decision_flag = record.get("decision_flag", False)
        needs_geo_logic = not decision_flag  # Inverse logic for challenge

        return {
            "feature_id": record.get("feature_id", "unknown"),
            "decision_flag": needs_geo_logic,  # needs_geo_specific_logic
            "reasoning_text": record.get("reasoning_text", ""),
            "agent_name": record.get("agent_name", "unknown"),
            "timestamp_iso": record.get("timestamp_iso", ""),
            "confidence": record.get("confidence", 0.0),
            "related_regulations": regulations_str,
            "retrieval_metadata": retrieval_meta_str,
            "feature_title": record.get("feature_title", ""),
            "pipeline_version": record.get("pipeline_version", ""),
            "environment": record.get("environment", ""),
        }

    def transform_to_test_dataset_schema(
        self, record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transform evidence record to test dataset CSV schema.

        Args:
            record: Original evidence record

        Returns:
            Transformed record for test dataset CSV export
        """
        # Extract related regulations
        related_regs = record.get("related_regulations", [])
        if isinstance(related_regs, list):
            regulations_str = "; ".join(str(reg) for reg in related_regs)
        else:
            regulations_str = str(related_regs) if related_regs else ""

        # Extract retrieved IDs and scores
        retrieval_meta = record.get("retrieval_metadata", {})
        retrieved_ids = []
        scores = []

        if isinstance(retrieval_meta, dict):
            if "retrieved_ids" in retrieval_meta:
                retrieved_ids = (
                    retrieval_meta["retrieved_ids"]
                    if isinstance(retrieval_meta["retrieved_ids"], list)
                    else []
                )
            if "scores" in retrieval_meta:
                scores = (
                    retrieval_meta["scores"]
                    if isinstance(retrieval_meta["scores"], list)
                    else []
                )

        # Extract timing information
        timings = record.get("timings_ms", {})
        total_ms = timings.get("total_ms", 0) if isinstance(timings, dict) else 0
        embed_ms = timings.get("embed_ms", 0) if isinstance(timings, dict) else 0
        search_ms = timings.get("search_ms", 0) if isinstance(timings, dict) else 0
        llm_ms = timings.get("llm_ms", 0) if isinstance(timings, dict) else 0

        # Extract error information
        error_info = record.get("error_info", {})
        error_type = error_info.get("type", "") if isinstance(error_info, dict) else ""
        error_message = (
            error_info.get("message", "") if isinstance(error_info, dict) else ""
        )

        # Extract model information
        model_meta = record.get("model_metadata", {})
        llm_model_name = (
            model_meta.get("llm_model_name", "") if isinstance(model_meta, dict) else ""
        )
        prompt_template_id = (
            model_meta.get("prompt_template_id", "")
            if isinstance(model_meta, dict)
            else ""
        )

        # Extract embedding information
        embedder_name = (
            retrieval_meta.get("embedder_name", "")
            if isinstance(retrieval_meta, dict)
            else ""
        )
        embed_dim = (
            retrieval_meta.get("embed_dim", "")
            if isinstance(retrieval_meta, dict)
            else ""
        )
        vectorstore_type = (
            retrieval_meta.get("vectorstore_type", "")
            if isinstance(retrieval_meta, dict)
            else ""
        )
        metric = (
            retrieval_meta.get("metric", "") if isinstance(retrieval_meta, dict) else ""
        )
        normalize = (
            retrieval_meta.get("normalize", "")
            if isinstance(retrieval_meta, dict)
            else ""
        )
        top_k = (
            retrieval_meta.get("top_k", "") if isinstance(retrieval_meta, dict) else ""
        )

        return {
            "request_id": record.get("request_id", ""),
            "timestamp_iso": record.get("timestamp_iso", ""),
            "agent_name": record.get("agent_name", ""),
            "feature_id": record.get("feature_id", ""),
            "feature_title": record.get("feature_title", ""),
            "dataset_tag": record.get("dataset_tag", ""),
            "decision_flag": record.get("decision_flag", False),
            "reasoning_text": record.get("reasoning_text", ""),
            "related_regulations": regulations_str,
            "confidence": record.get("confidence", 0.0),
            "llm_model_name": llm_model_name,
            "prompt_template_id": prompt_template_id,
            "embedder_name": embedder_name,
            "embed_dim": embed_dim,
            "vectorstore_type": vectorstore_type,
            "metric": metric,
            "normalize": normalize,
            "top_k": top_k,
            "retrieved_ids": "; ".join(map(str, retrieved_ids)),
            "scores": "; ".join(map(str, scores)),
            "total_ms": total_ms,
            "embed_ms": embed_ms,
            "search_ms": search_ms,
            "llm_ms": llm_ms,
            "error_type": error_type,
            "error_message_redacted": error_message,
        }

    def export_to_csv(
        self,
        output_path: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        agent_filter: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> int:
        """
        Export evidence records to CSV file.

        Args:
            output_path: Path for output CSV file
            start_date: Filter records from this date
            end_date: Filter records until this date
            agent_filter: List of agent names to include
            limit: Maximum number of records to export

        Returns:
            Number of records exported
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        exported_count = 0

        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.csv_schema)
            writer.writeheader()

            for record in self.read_evidence_records(
                start_date, end_date, agent_filter, limit
            ):
                transformed_record = self.transform_to_challenge_schema(record)
                writer.writerow(transformed_record)
                exported_count += 1

        logger.info(f"Exported {exported_count} records to {output_path}")
        return exported_count

    def export_test_dataset_csv(
        self,
        output_path: str,
        dataset_tag: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        agent_filter: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> int:
        """
        Export evidence records to test dataset CSV format.

        Args:
            output_path: Path for output CSV file
            dataset_tag: Filter by dataset tag
            start_date: Filter records from this date
            end_date: Filter records until this date
            agent_filter: List of agent names to include
            limit: Maximum number of records to export

        Returns:
            Number of records exported
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Test dataset CSV schema
        test_schema = [
            "request_id",
            "timestamp_iso",
            "agent_name",
            "feature_id",
            "feature_title",
            "dataset_tag",
            "decision_flag",
            "reasoning_text",
            "related_regulations",
            "confidence",
            "llm_model_name",
            "prompt_template_id",
            "embedder_name",
            "embed_dim",
            "vectorstore_type",
            "metric",
            "normalize",
            "top_k",
            "retrieved_ids",
            "scores",
            "total_ms",
            "embed_ms",
            "search_ms",
            "llm_ms",
            "error_type",
            "error_message_redacted",
        ]

        exported_count = 0

        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=test_schema)
            writer.writeheader()

            for record in self.read_evidence_records(
                start_date, end_date, agent_filter, limit
            ):
                # Apply dataset tag filter
                if dataset_tag and record.get("dataset_tag") != dataset_tag:
                    continue

                transformed_record = self.transform_to_test_dataset_schema(record)
                writer.writerow(transformed_record)
                exported_count += 1

        logger.info(f"Exported {exported_count} test dataset records to {output_path}")
        return exported_count

    def export_to_dataframe(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        agent_filter: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Export evidence records to pandas DataFrame.

        Args:
            start_date: Filter records from this date
            end_date: Filter records until this date
            agent_filter: List of agent names to include
            limit: Maximum number of records to export

        Returns:
            DataFrame with evidence records
        """
        records = []
        for record in self.read_evidence_records(
            start_date, end_date, agent_filter, limit
        ):
            transformed_record = self.transform_to_challenge_schema(record)
            records.append(transformed_record)

        df = pd.DataFrame(records)
        logger.info(f"Exported {len(df)} records to DataFrame")
        return df

    def get_export_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        agent_filter: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get summary statistics for export.

        Args:
            start_date: Filter records from this date
            end_date: Filter records until this date
            agent_filter: List of agent names to include

        Returns:
            Summary statistics
        """
        total_records = 0
        agent_counts = {}
        decision_counts = {"true": 0, "false": 0}
        date_range = {"earliest": None, "latest": None}

        for record in self.read_evidence_records(start_date, end_date, agent_filter):
            total_records += 1

            # Agent counts
            agent = record.get("agent_name", "unknown")
            agent_counts[agent] = agent_counts.get(agent, 0) + 1

            # Decision counts
            decision = record.get("decision_flag", False)
            decision_counts["true" if decision else "false"] += 1

            # Date range
            try:
                timestamp = datetime.fromisoformat(record.get("timestamp_iso", ""))
                if date_range["earliest"] is None or timestamp < date_range["earliest"]:
                    date_range["earliest"] = timestamp
                if date_range["latest"] is None or timestamp > date_range["latest"]:
                    date_range["latest"] = timestamp
            except (ValueError, TypeError):
                pass

        return {
            "total_records": total_records,
            "agent_distribution": agent_counts,
            "decision_distribution": decision_counts,
            "date_range": {
                "earliest": (
                    date_range["earliest"].isoformat()
                    if date_range["earliest"]
                    else None
                ),
                "latest": (
                    date_range["latest"].isoformat() if date_range["latest"] else None
                ),
            },
            "filters_applied": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "agent_filter": agent_filter,
            },
        }


def main():
    """CLI interface for evidence export."""
    parser = argparse.ArgumentParser(
        description="Export evidence logs to challenge CSV format"
    )
    parser.add_argument(
        "--output", "-o", default="evidence_export.csv", help="Output CSV file path"
    )
    parser.add_argument("--start-date", "-s", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", "-e", help="End date (YYYY-MM-DD)")
    parser.add_argument("--agents", "-a", nargs="+", help="Filter by agent names")
    parser.add_argument("--limit", "-l", type=int, help="Maximum records to export")
    parser.add_argument("--summary", action="store_true", help="Show export summary")
    parser.add_argument(
        "--format", choices=["csv", "dataframe"], default="csv", help="Output format"
    )
    parser.add_argument(
        "--test-dataset", action="store_true", help="Export in test dataset format"
    )
    parser.add_argument(
        "--dataset-tag", help="Filter by dataset tag for test dataset export"
    )

    args = parser.parse_args()

    # Parse dates
    start_date = None
    end_date = None
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")

    # Initialize exporter
    exporter = EvidenceExporter()

    # Show summary if requested
    if args.summary:
        summary = exporter.get_export_summary(start_date, end_date, args.agents)
        print("Export Summary:")
        print(f"  Total records: {summary['total_records']}")
        print(f"  Agent distribution: {summary['agent_distribution']}")
        print(f"  Decision distribution: {summary['decision_distribution']}")
        print(
            f"  Date range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}"
        )
        return

    # Export data
    if args.format == "csv":
        if args.test_dataset:
            count = exporter.export_test_dataset_csv(
                args.output,
                args.dataset_tag,
                start_date,
                end_date,
                args.agents,
                args.limit,
            )
            print(f"Exported {count} test dataset records to {args.output}")
        else:
            count = exporter.export_to_csv(
                args.output, start_date, end_date, args.agents, args.limit
            )
            print(f"Exported {count} records to {args.output}")
    else:
        df = exporter.export_to_dataframe(start_date, end_date, args.agents, args.limit)
        print(f"Exported {len(df)} records to DataFrame")
        print(df.head())


if __name__ == "__main__":
    main()
