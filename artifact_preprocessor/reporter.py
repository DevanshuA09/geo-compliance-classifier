"""Processing report generation."""

from pathlib import Path
from typing import Dict, List, Optional

from .logging_conf import get_logger
from .schema import FeatureRecord, CodenameHit

logger = get_logger(__name__)


class ProcessingReporter:
    """Generate processing reports with statistics and warnings."""
    
    def __init__(self):
        """Initialize the reporter."""
        self.stats = {
            'docs_found': 0,
            'docs_parsed': 0,
            'parse_success_rate': 0.0,
            'features_processed': 0,
            'total_warnings': 0,
            'expansion_coverage': 0.0,
            'unique_terms_found': 0,
            'total_term_occurrences': 0,
        }
        self.warnings = []
    
    def generate_report(
        self, 
        records: List[FeatureRecord],
        docs_found: int,
        terminology_size: int,
        output_dir: Path
    ) -> None:
        """Generate and save processing report.
        
        Args:
            records: Processed feature records
            docs_found: Total number of documents found
            terminology_size: Number of terms in terminology
            output_dir: Output directory
        """
        # Calculate statistics
        self._calculate_stats(records, docs_found, terminology_size)
        
        # Generate report content
        report_content = self._build_report_content(records)
        
        # Save report
        report_path = output_dir / "report.md"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Generated processing report: {report_path}")
    
    def _calculate_stats(
        self, 
        records: List[FeatureRecord], 
        docs_found: int,
        terminology_size: int
    ) -> None:
        """Calculate processing statistics.
        
        Args:
            records: Processed records
            docs_found: Number of documents found
            terminology_size: Size of terminology mapping
        """
        docs_parsed = len(set(record.doc_id for record in records))
        
        # Collect all warnings
        all_warnings = []
        for record in records:
            all_warnings.extend(record.parse_warnings)
        
        # Collect expansion statistics
        all_hits = []
        for record in records:
            all_hits.extend(record.codename_hits)
        
        unique_terms = set(hit.term for hit in all_hits)
        total_occurrences = sum(hit.count for hit in all_hits)
        
        self.stats.update({
            'docs_found': docs_found,
            'docs_parsed': docs_parsed,
            'parse_success_rate': docs_parsed / docs_found if docs_found > 0 else 0.0,
            'features_processed': len(records),
            'total_warnings': len(all_warnings),
            'expansion_coverage': len(unique_terms) / terminology_size if terminology_size > 0 else 0.0,
            'unique_terms_found': len(unique_terms),
            'total_term_occurrences': total_occurrences,
        })
        
        self.warnings = all_warnings
    
    def _build_report_content(self, records: List[FeatureRecord]) -> str:
        """Build the markdown report content.
        
        Args:
            records: Processed records
            
        Returns:
            Markdown report content
        """
        lines = [
            "# Artifact Preprocessor Processing Report",
            "",
            f"Generated on: {self._get_timestamp()}",
            "",
            "## Summary Statistics",
            "",
            f"- **Documents found:** {self.stats['docs_found']}",
            f"- **Documents parsed:** {self.stats['docs_parsed']}",
            f"- **Parse success rate:** {self.stats['parse_success_rate']:.1%}",
            f"- **Features processed:** {self.stats['features_processed']}",
            f"- **Total warnings:** {self.stats['total_warnings']}",
            "",
            "## Codename Expansion Statistics",
            "",
            f"- **Unique terms found:** {self.stats['unique_terms_found']}",
            f"- **Total term occurrences:** {self.stats['total_term_occurrences']}",
            f"- **Expansion coverage:** {self.stats['expansion_coverage']:.1%}",
            "",
        ]
        
        # Document type breakdown
        if records:
            doc_types = {}
            for record in records:
                doc_type = record.doc_type
                if doc_type not in doc_types:
                    doc_types[doc_type] = 0
                doc_types[doc_type] += 1
            
            lines.extend([
                "## Document Type Breakdown",
                "",
            ])
            for doc_type, count in sorted(doc_types.items()):
                lines.append(f"- **{doc_type.upper()}:** {count} documents")
            lines.append("")
        
        # Field extraction statistics
        if records:
            field_stats = self._calculate_field_stats(records)
            lines.extend([
                "## Field Extraction Statistics",
                "",
            ])
            for field_name, (filled, total) in sorted(field_stats.items()):
                percentage = (filled / total * 100) if total > 0 else 0
                lines.append(f"- **{field_name}:** {filled}/{total} ({percentage:.1f}%)")
            lines.append("")
        
        # Top terms found
        if records:
            term_counts = {}
            for record in records:
                for hit in record.codename_hits:
                    if hit.term not in term_counts:
                        term_counts[hit.term] = 0
                    term_counts[hit.term] += hit.count
            
            if term_counts:
                lines.extend([
                    "## Most Frequent Terms",
                    "",
                ])
                top_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                for term, count in top_terms:
                    lines.append(f"- **{term}:** {count} occurrences")
                lines.append("")
        
        # Warnings summary
        if self.warnings:
            lines.extend([
                "## Warnings and Issues",
                "",
            ])
            
            # Group warnings by type
            warning_groups = {}
            for warning in self.warnings:
                warning_type = self._categorize_warning(warning)
                if warning_type not in warning_groups:
                    warning_groups[warning_type] = []
                warning_groups[warning_type].append(warning)
            
            for warning_type, warnings in sorted(warning_groups.items()):
                lines.append(f"### {warning_type}")
                lines.append("")
                for warning in warnings[:5]:  # Limit to first 5 per category
                    lines.append(f"- {warning}")
                if len(warnings) > 5:
                    lines.append(f"- ... and {len(warnings) - 5} more")
                lines.append("")
        else:
            lines.extend([
                "## Warnings and Issues",
                "",
                "No warnings reported during processing.",
                "",
            ])
        
        # Success metrics
        lines.extend([
            "## Success Metrics",
            "",
            f"- **Parse Success Rate:** {self.stats['parse_success_rate']:.1%} " +
            ("✅" if self.stats['parse_success_rate'] >= 1.0 else "⚠️"),
            f"- **Field Extraction:** {self._get_overall_field_rate(records):.1%} average",
            f"- **Expansion Coverage:** {self.stats['expansion_coverage']:.1%}",
            "",
        ])
        
        return "\n".join(lines)
    
    def _calculate_field_stats(self, records: List[FeatureRecord]) -> Dict[str, tuple]:
        """Calculate field extraction statistics.
        
        Args:
            records: Processed records
            
        Returns:
            Dictionary mapping field names to (filled, total) counts
        """
        field_names = [
            'doc_title', 'version', 'authors', 'date',
            'feature_title', 'feature_description',
            'objectives', 'scope', 'user_segments', 'risk_safety',
            'privacy_data', 'age_gating', 'geo_regions', 'rollout', 'open_questions'
        ]
        
        stats = {}
        total_records = len(records)
        
        for field_name in field_names:
            filled_count = sum(1 for record in records if getattr(record, field_name, None))
            stats[field_name] = (filled_count, total_records)
        
        return stats
    
    def _get_overall_field_rate(self, records: List[FeatureRecord]) -> float:
        """Calculate overall field extraction rate.
        
        Args:
            records: Processed records
            
        Returns:
            Average field extraction rate as percentage
        """
        if not records:
            return 0.0
        
        field_stats = self._calculate_field_stats(records)
        rates = [filled / total for filled, total in field_stats.values() if total > 0]
        
        return (sum(rates) / len(rates) * 100) if rates else 0.0
    
    def _categorize_warning(self, warning: str) -> str:
        """Categorize a warning message.
        
        Args:
            warning: Warning message
            
        Returns:
            Warning category
        """
        warning_lower = warning.lower()
        
        if any(keyword in warning_lower for keyword in ['pdf', 'pypdf', 'pdfminer']):
            return "PDF Parsing Issues"
        elif any(keyword in warning_lower for keyword in ['docx', 'python-docx']):
            return "DOCX Parsing Issues"
        elif any(keyword in warning_lower for keyword in ['encoding', 'decode', 'unicode']):
            return "Encoding Issues"
        elif any(keyword in warning_lower for keyword in ['field', 'extract']):
            return "Field Extraction Issues"
        elif any(keyword in warning_lower for keyword in ['term', 'expansion']):
            return "Codename Expansion Issues"
        else:
            return "General Issues"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for report.
        
        Returns:
            Formatted timestamp string
        """
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
