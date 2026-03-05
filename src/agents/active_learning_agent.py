import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

try:
    from ..evidence import log_compliance_decision
    from ..rag import RAGAdapter
except ImportError:
    from rag_adapter import RAGAdapter

    try:
        from evidence_logger import log_compliance_decision
    except ImportError:
        log_compliance_decision = None


@dataclass
class HumanCorrection:
    """Individual human correction with metadata"""

    case_id: str
    timestamp: datetime
    original_prediction: str
    corrected_label: str
    reviewer_reasoning: str
    feature_characteristics: Dict[str, Any]
    confidence_score: float
    model_used: str
    correction_type: str = "label_correction"
    impact_score: float = 0.0
    regulatory_context: List[str] = field(default_factory=list)


@dataclass
class CorrectionPattern:
    """Identified pattern of systematic misclassifications"""

    pattern_id: str
    pattern_type: str
    description: str
    affected_cases: List[str]
    frequency: int
    severity_score: float
    keywords: List[str] = field(default_factory=list)
    geographic_factors: List[str] = field(default_factory=list)
    demographic_factors: List[str] = field(default_factory=list)


@dataclass
class WeeklyMetrics:
    """Weekly performance metrics"""

    week_start: datetime
    week_end: datetime
    human_reviews_logged: int
    corrections_applied: int
    patterns_identified: int
    retraining_triggered: int
    human_review_reduction: float
    notes: str
    target_met: bool


class ActiveLearningAgent:
    """Active Learning Agent for reducing human review effort"""

    def __init__(
        self, data_dir: str = "active_learning_data", rag_adapter: RAGAdapter = None
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # Data storage
        self.corrections: List[HumanCorrection] = []
        self.patterns: List[CorrectionPattern] = []
        self.weekly_metrics: List[WeeklyMetrics] = []

        # Configuration
        self.correction_threshold = 50
        self.target_reduction_rate = 0.15
        self.pattern_analysis_threshold = 10

        # RAG integration
        self.rag_adapter = rag_adapter or RAGAdapter()

        # Load existing data
        self._load_data()

        # Analytics components
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words="english")
        self.pattern_clustering = KMeans(n_clusters=5, random_state=42)

    def get_regulatory_context(self, text: str, max_results: int = 3) -> List[str]:
        """Get regulatory context using centralized RAG system."""
        try:
            results = self.rag_adapter.retrieve_regulatory_context(
                text, max_results=max_results
            )
            return [r["text"] for r in results]
        except Exception as e:
            print(f"Failed to get regulatory context: {e}")
            return []

    def get_rag_system_status(self) -> Dict[str, Any]:
        """Get RAG system status."""
        return self.rag_adapter.get_system_status()

    def _load_data(self):
        """Load existing data from storage"""
        corrections_file = self.data_dir / "corrections.json"
        if corrections_file.exists():
            try:
                with open(corrections_file, "r") as f:
                    corrections_data = json.load(f)
                    for corr_data in corrections_data:
                        corr = HumanCorrection(
                            case_id=corr_data["case_id"],
                            timestamp=datetime.fromisoformat(corr_data["timestamp"]),
                            original_prediction=corr_data["original_prediction"],
                            corrected_label=corr_data["corrected_label"],
                            reviewer_reasoning=corr_data["reviewer_reasoning"],
                            feature_characteristics=corr_data[
                                "feature_characteristics"
                            ],
                            confidence_score=corr_data["confidence_score"],
                            model_used=corr_data["model_used"],
                            correction_type=corr_data["correction_type"],
                            impact_score=corr_data.get("impact_score", 0.0),
                        )
                        self.corrections.append(corr)
            except Exception as e:
                print(f"Warning: Could not load corrections: {e}")

    def _save_data(self):
        """Save data to storage"""
        corrections_file = self.data_dir / "corrections.json"
        corrections_data = []
        for corr in self.corrections:
            corr_data = {
                "case_id": corr.case_id,
                "timestamp": corr.timestamp.isoformat(),
                "original_prediction": corr.original_prediction,
                "corrected_label": corr.corrected_label,
                "reviewer_reasoning": corr.reviewer_reasoning,
                "feature_characteristics": corr.feature_characteristics,
                "confidence_score": corr.confidence_score,
                "model_used": corr.model_used,
                "correction_type": corr.correction_type,
                "impact_score": corr.impact_score,
            }
            corrections_data.append(corr_data)

        with open(corrections_file, "w") as f:
            json.dump(corrections_data, f, indent=2)

    def log_human_correction(
        self,
        case_id: str,
        original_prediction: str,
        corrected_label: str,
        reviewer_reasoning: str,
        feature_characteristics: Dict[str, Any],
        confidence_score: float,
        model_used: str,
        correction_type: str = "label_correction",
    ) -> str:
        """Log a human correction with full metadata"""

        # Calculate impact score
        impact_score = self._calculate_impact_score(
            original_prediction,
            corrected_label,
            confidence_score,
            feature_characteristics,
            reviewer_reasoning,
        )

        # Create correction record
        correction = HumanCorrection(
            case_id=case_id,
            timestamp=datetime.now(),
            original_prediction=original_prediction,
            corrected_label=corrected_label,
            reviewer_reasoning=reviewer_reasoning,
            feature_characteristics=feature_characteristics,
            confidence_score=confidence_score,
            model_used=model_used,
            correction_type=correction_type,
            impact_score=impact_score,
        )

        # Add to corrections list
        self.corrections.append(correction)

        # Save data
        self._save_data()

        # Check if pattern analysis should be triggered
        if len(self.corrections) >= self.pattern_analysis_threshold:
            self._analyze_correction_patterns()

        # Check if retraining should be triggered
        if len(self.corrections) >= self.correction_threshold:
            self._trigger_retraining()

        # Log evidence for active learning decision
        if log_compliance_decision:
            evidence_data = {
                "request_id": str(uuid.uuid4()),
                "timestamp_iso": datetime.now().isoformat(),
                "agent_name": "active_learning_agent",
                "decision_flag": corrected_label != "Non-Compliant",
                "reasoning_text": f"Human correction logged: {original_prediction} → {corrected_label} - {reviewer_reasoning}",
                "feature_id": case_id,
                "feature_title": f"Active Learning Correction {case_id}",
                "related_regulations": [],  # Will be populated from RAG if available
                "confidence": confidence_score,
                "retrieval_metadata": {
                    "agent_specific": "active_learning",
                    "correction_type": correction_type,
                    "impact_score": impact_score,
                    "model_used": model_used,
                    "corrections_count": len(self.corrections),
                    "pattern_analysis_triggered": len(self.corrections)
                    >= self.pattern_analysis_threshold,
                    "retraining_triggered": len(self.corrections)
                    >= self.correction_threshold,
                },
                "timings_ms": {
                    "correction_logging_ms": 0  # Will be populated if timing is tracked
                },
            }
            log_compliance_decision(evidence_data)

        return case_id

    def _calculate_impact_score(
        self,
        original_prediction: str,
        corrected_label: str,
        confidence_score: float,
        feature_characteristics: Dict[str, Any],
        reviewer_reasoning: str,
    ) -> float:
        """Calculate the impact score for a correction"""
        impact_score = 0.0

        # High confidence errors are more impactful
        if confidence_score > 0.8:
            impact_score += 0.3
        elif confidence_score > 0.6:
            impact_score += 0.2
        else:
            impact_score += 0.1

        # Label changes are more impactful than confidence adjustments
        if original_prediction != corrected_label:
            impact_score += 0.4
        else:
            impact_score += 0.1

        # Geographic or demographic factors increase impact
        if (
            "geographic" in feature_characteristics
            or "demographic" in feature_characteristics
        ):
            impact_score += 0.2

        # Regulatory compliance errors are high impact
        if (
            "compliance" in reviewer_reasoning.lower()
            or "regulation" in reviewer_reasoning.lower()
        ):
            impact_score += 0.3

        return min(1.0, impact_score)

    def _analyze_correction_patterns(self):
        """Analyze corrections to identify systematic patterns"""
        if len(self.corrections) < self.pattern_analysis_threshold:
            return

        # Extract text features for clustering
        correction_texts = []
        for corr in self.corrections:
            text = f"{corr.original_prediction} {corr.corrected_label} {corr.reviewer_reasoning}"
            correction_texts.append(text)

        if not correction_texts:
            return

        try:
            # Vectorize text
            text_vectors = self.vectorizer.fit_transform(correction_texts)

            # Cluster corrections
            clusters = self.pattern_clustering.fit_predict(text_vectors)

            # Get number of clusters from the fitted model
            n_clusters = self.pattern_clustering.n_clusters

            # Analyze each cluster for patterns
            for cluster_id in range(n_clusters):
                cluster_corrections = [
                    corr
                    for i, corr in enumerate(self.corrections)
                    if clusters[i] == cluster_id
                ]

                if len(cluster_corrections) < 3:
                    continue

                pattern = self._identify_cluster_pattern(
                    cluster_id, cluster_corrections
                )
                if pattern:
                    self.patterns.append(pattern)

            # Save updated patterns
            self._save_data()

        except Exception as e:
            print(f"Warning: Pattern analysis failed: {e}")

    def _identify_cluster_pattern(
        self, cluster_id: int, cluster_corrections: List[HumanCorrection]
    ) -> Optional[CorrectionPattern]:
        """Identify specific pattern within a cluster"""
        if len(cluster_corrections) < 3:
            return None

        # Analyze common characteristics
        keywords = self._extract_common_keywords(cluster_corrections)
        geographic_factors = self._extract_geographic_factors(cluster_corrections)
        demographic_factors = self._extract_demographic_factors(cluster_corrections)

        # Determine pattern type
        pattern_type = self._classify_pattern_type(
            keywords, geographic_factors, demographic_factors
        )

        # Calculate severity score
        severity_score = self._calculate_pattern_severity(cluster_corrections)

        # Create pattern description
        description = self._generate_pattern_description(
            pattern_type, keywords, geographic_factors, demographic_factors
        )

        pattern = CorrectionPattern(
            pattern_id=f"PATTERN-{cluster_id:03d}",
            pattern_type=pattern_type,
            description=description,
            affected_cases=[corr.case_id for corr in cluster_corrections],
            frequency=len(cluster_corrections),
            severity_score=severity_score,
            keywords=keywords,
            geographic_factors=geographic_factors,
            demographic_factors=demographic_factors,
        )

        return pattern

    def _extract_common_keywords(self, corrections: List[HumanCorrection]) -> List[str]:
        """Extract common keywords from corrections"""
        all_text = " ".join(
            [
                f"{corr.original_prediction} {corr.corrected_label} {corr.reviewer_reasoning}"
                for corr in corrections
            ]
        ).lower()

        # Extract regulatory and compliance keywords
        keywords = re.findall(
            r"\b(compliance|regulation|legal|requirement|mandatory|prohibited|consent|privacy|data|safety|environmental)\b",
            all_text,
        )

        return list(set(keywords))

    def _extract_geographic_factors(
        self, corrections: List[HumanCorrection]
    ) -> List[str]:
        """Extract geographic factors from corrections"""
        geographic_factors = []

        for corr in corrections:
            if "geographic" in corr.feature_characteristics:
                geo_data = corr.feature_characteristics["geographic"]
                if isinstance(geo_data, dict):
                    for key, value in geo_data.items():
                        if value and str(value) not in geographic_factors:
                            geographic_factors.append(str(value))

        return geographic_factors

    def _extract_demographic_factors(
        self, corrections: List[HumanCorrection]
    ) -> List[str]:
        """Extract demographic factors from corrections"""
        demographic_factors = []

        for corr in corrections:
            if "demographic" in corr.feature_characteristics:
                demo_data = corr.feature_characteristics["demographic"]
                if isinstance(demo_data, dict):
                    for key, value in demo_data.items():
                        if value and str(value) not in demographic_factors:
                            demographic_factors.append(str(value))

        return demographic_factors

    def _classify_pattern_type(
        self,
        keywords: List[str],
        geographic_factors: List[str],
        demographic_factors: List[str],
    ) -> str:
        """Classify the type of pattern"""
        if geographic_factors and demographic_factors:
            return "geographic_age"
        elif keywords and any("compliance" in k.lower() for k in keywords):
            return "keyword_blindspot"
        else:
            return "confidence_mismatch"

    def _calculate_pattern_severity(self, corrections: List[HumanCorrection]) -> float:
        """Calculate severity score for a pattern"""
        if not corrections:
            return 0.0

        # Average impact score
        avg_impact = sum(corr.impact_score for corr in corrections)
        avg_impact = avg_impact / len(corrections)

        # Frequency factor
        frequency_factor = min(1.0, len(corrections) / 20.0)

        # Confidence factor (high confidence errors are more severe)
        avg_confidence = sum(corr.confidence_score for corr in corrections)
        avg_confidence = avg_confidence / len(corrections)
        confidence_factor = avg_confidence

        severity = (avg_impact + frequency_factor + confidence_factor) / 3
        return min(1.0, severity)

    def _generate_pattern_description(
        self,
        pattern_type: str,
        keywords: List[str],
        geographic_factors: List[str],
        demographic_factors: List[str],
    ) -> str:
        """Generate human-readable pattern description"""
        if pattern_type == "geographic_age":
            return f"Systematic errors involving geographic factors ({', '.join(geographic_factors)}) and demographic factors ({', '.join(demographic_factors)})"
        elif pattern_type == "keyword_blindspot":
            return f"Keyword blindspot pattern involving terms: {', '.join(keywords)}"
        else:
            return "Confidence mismatch pattern indicating systematic overconfidence"

    def _trigger_retraining(self):
        """Trigger model retraining when sufficient corrections are available"""
        if len(self.corrections) < self.correction_threshold:
            return

        print(f"Retraining triggered after {len(self.corrections)} corrections")
        # This would integrate with your model training pipeline

        # For now, just log the trigger
        print("Retraining workflow would be executed here")

    def calculate_weekly_metrics(self, week_start: datetime) -> WeeklyMetrics:
        """Calculate weekly performance metrics"""
        week_end = week_start + timedelta(days=7)

        # Filter corrections for the week
        week_corrections = [
            corr for corr in self.corrections if week_start <= corr.timestamp < week_end
        ]

        # Calculate metrics
        human_reviews_logged = len(week_corrections)
        corrections_applied = len(
            [c for c in week_corrections if c.correction_type == "label_correction"]
        )

        # Count patterns identified in this week (simplified approach)
        patterns_identified = 0
        for pattern in self.patterns:
            # Check if any of the affected cases were created this week
            for case_id in pattern.affected_cases:
                # Find the correction for this case
                for corr in week_corrections:
                    if corr.case_id == case_id:
                        patterns_identified += 1
                        break
                if patterns_identified > 0:
                    break

        retraining_triggered = 0  # Simplified for now

        # Calculate review reduction (simplified)
        human_review_reduction = 0.0  # Would calculate based on baseline
        target_met = False

        # Generate notes
        notes = self._generate_weekly_notes(
            week_corrections,
            patterns_identified,
            retraining_triggered,
            human_review_reduction,
        )

        metrics = WeeklyMetrics(
            week_start=week_start,
            week_end=week_end,
            human_reviews_logged=human_reviews_logged,
            corrections_applied=corrections_applied,
            patterns_identified=patterns_identified,
            retraining_triggered=retraining_triggered,
            human_review_reduction=human_review_reduction,
            notes=notes,
            target_met=target_met,
        )

        self.weekly_metrics.append(metrics)
        return metrics

    def _generate_weekly_notes(
        self,
        week_corrections: List[HumanCorrection],
        patterns_identified: int,
        retraining_triggered: int,
        review_reduction: float,
    ) -> str:
        """Generate notes for weekly metrics"""
        notes = []

        if patterns_identified > 0:
            notes.append(f"Identified {patterns_identified} new correction patterns")

        if retraining_triggered > 0:
            notes.append(f"Triggered {retraining_triggered} retraining workflows")

        if review_reduction > 0:
            notes.append(f"Human review rate reduced by {review_reduction:.1%}")
        else:
            notes.append(f"Human review rate increased by {abs(review_reduction):.1%}")

        if not notes:
            notes.append("No significant changes this week")

        return "; ".join(notes)

    def get_weekly_summary_table(self) -> str:
        """Generate weekly summary table in markdown format"""
        if not self.weekly_metrics:
            return "No weekly metrics available."

        # Sort by week start
        sorted_metrics = sorted(self.weekly_metrics, key=lambda x: x.week_start)

        # Create markdown table
        markdown = "## Weekly Active Learning Metrics\n\n"
        markdown += "| Week | Human Reviews Logged | Corrections Applied | Patterns Identified | Retraining Triggered | Human Review Reduction (%) | Notes |\n"
        markdown += "|------|---------------------|---------------------|---------------------|----------------------|----------------------------|-------|\n"

        for metrics in sorted_metrics:
            week_str = metrics.week_start.strftime("%Y-%m-%d")
            reduction_str = f"{metrics.human_review_reduction:.1%}"
            target_emoji = "✅" if metrics.target_met else "⚠️"

            markdown += f"| {week_str} | {metrics.human_reviews_logged} | {metrics.corrections_applied} | {metrics.patterns_identified} | {metrics.retraining_triggered} | {reduction_str} | {target_emoji} {metrics.notes} |\n"

        return markdown

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "total_corrections": len(self.corrections),
            "total_patterns": len(self.patterns),
            "correction_threshold": self.correction_threshold,
            "target_reduction_rate": self.target_reduction_rate,
            "ready_for_retraining": len(self.corrections) >= self.correction_threshold,
        }
