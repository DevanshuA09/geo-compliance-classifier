"""
Compliance Analyzer Module
Analyzes features against regulatory requirements and generates compliance mappings
"""

import json
import logging
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# Add RAG adapter import
try:
    sys.path.append(str(Path(__file__).parent.parent.parent))
    import uuid
    from datetime import datetime

    from src.evidence import log_compliance_decision
    from src.rag import RAGAdapter
except ImportError:
    RAGAdapter = None
    log_compliance_decision = None
    uuid = None
    datetime = None
    logger.warning("RAG adapter not available, using fallback knowledge base")


@dataclass
class ComplianceMatch:
    """Represents a compliance match between feature and regulation"""

    regulation_name: str
    regulation_type: str  # DMA, GDPR, COPPA, etc.
    jurisdiction: str
    matched_keywords: List[str]
    confidence_score: float  # 0.0 to 1.0
    compliance_status: str  # COMPLIANT, NON_COMPLIANT, PARTIAL, UNKNOWN
    evidence_text: List[str]
    requirements: List[str]


@dataclass
class FeatureAnalysis:
    """Complete compliance analysis for a single feature"""

    feature_name: str
    feature_description: str
    matches: List[ComplianceMatch]
    overall_compliance: str  # COMPLIANT, NON_COMPLIANT, PARTIAL, NEEDS_REVIEW
    confidence_level: str  # HIGH, MEDIUM, LOW
    flagged_for_review: bool
    missing_coverage: List[str]
    recommendations: List[str]


class ComplianceKnowledgeBase:
    """Knowledge base of regulatory requirements and patterns"""

    def __init__(self):
        self.regulations = self._initialize_regulations()
        self.compliance_patterns = self._initialize_patterns()
        self.jurisdiction_mapping = self._initialize_jurisdictions()

    def _initialize_regulations(self) -> Dict:
        """Initialize regulatory knowledge base"""
        return {
            "DMA": {
                "full_name": "Digital Markets Act",
                "jurisdiction": "EU",
                "key_requirements": [
                    "gatekeeper obligations",
                    "interoperability requirements",
                    "data portability",
                    "alternative app stores",
                    "choice screens",
                    "bundling restrictions",
                    "self-preferencing prohibition",
                    "data combination restrictions",
                ],
                "keywords": [
                    "gatekeeper",
                    "interoperability",
                    "portability",
                    "alternative store",
                    "choice screen",
                    "bundling",
                    "self-preferencing",
                    "data combination",
                    "core platform services",
                    "systematic non-compliance",
                ],
                "reporting_requirements": [
                    "Annual compliance report",
                    "Quarterly metrics reporting",
                    "Incident reporting within 24 hours",
                ],
            },
            "GDPR": {
                "full_name": "General Data Protection Regulation",
                "jurisdiction": "EU",
                "key_requirements": [
                    "data protection by design",
                    "privacy by default",
                    "consent management",
                    "data subject rights",
                    "data minimization",
                    "purpose limitation",
                    "storage limitation",
                    "breach notification",
                ],
                "keywords": [
                    "privacy",
                    "consent",
                    "data subject",
                    "processing",
                    "controller",
                    "processor",
                    "breach",
                    "dpo",
                    "impact assessment",
                    "lawful basis",
                    "legitimate interest",
                    "essential cookies",
                    "opt-in",
                    "opt-out",
                ],
                "reporting_requirements": [
                    "Breach notification within 72 hours",
                    "Annual privacy report",
                    "DPO contact details",
                ],
            },
            "COPPA": {
                "full_name": "Children's Online Privacy Protection Act",
                "jurisdiction": "US",
                "key_requirements": [
                    "parental consent",
                    "age verification",
                    "data minimization for children",
                    "safe harbor provisions",
                    "notice requirements",
                ],
                "keywords": [
                    "children",
                    "parental consent",
                    "age verification",
                    "under 13",
                    "safe harbor",
                    "notice",
                    "deletion",
                    "disclosure",
                ],
                "reporting_requirements": [
                    "Annual safe harbor certification",
                    "Incident reporting",
                ],
            },
            "DSA": {
                "full_name": "Digital Services Act",
                "jurisdiction": "EU",
                "key_requirements": [
                    "content moderation",
                    "risk assessment",
                    "transparency reporting",
                    "illegal content removal",
                    "crisis response mechanism",
                ],
                "keywords": [
                    "content moderation",
                    "risk assessment",
                    "transparency",
                    "illegal content",
                    "crisis response",
                    "notice and action",
                    "trusted flaggers",
                    "out-of-court dispute",
                ],
                "reporting_requirements": [
                    "Annual transparency report",
                    "Risk assessment updates",
                ],
            },
            "CCPA": {
                "full_name": "California Consumer Privacy Act",
                "jurisdiction": "California, US",
                "key_requirements": [
                    "consumer rights",
                    "data disclosure",
                    "opt-out mechanisms",
                    "non-discrimination",
                    "third-party sharing",
                ],
                "keywords": [
                    "consumer rights",
                    "disclosure",
                    "opt-out",
                    "sale of data",
                    "third party",
                    "categories of data",
                    "business purpose",
                    "service provider",
                    "non-discrimination",
                ],
                "reporting_requirements": [
                    "Privacy policy updates",
                    "Consumer request metrics",
                ],
            },
        }

    def _initialize_patterns(self) -> Dict:
        """Initialize compliance detection patterns"""
        return {
            "compliance_signals": {
                "positive": [
                    r"\bcompl(y|ies|iant|iance)\b",
                    r"\badhere(s|nce)\b",
                    r"\bconform(s|ance)\b",
                    r"\bmeet(s)?\s+requirements\b",
                    r"\baccording to\b",
                    r"\bin line with\b",
                    r"\bper\s+regulation\b",
                ],
                "negative": [
                    r"\bnon.?compliant\b",
                    r"\bviolat(es|ion)\b",
                    r"\bbreach(es)?\b",
                    r"\bfail(s)?\s+to\s+meet\b",
                    r"\bnot\s+compliant\b",
                ],
                "partial": [
                    r"\bpartial(ly)?\s+compliant\b",
                    r"\bwork(ing)?\s+towards?\b",
                    r"\bprogress(ing)?\b",
                    r"\bunder\s+development\b",
                ],
            },
            "geographic_indicators": {
                "EU": [r"\bEU\b", r"\bEuropean\s+Union\b", r"\bEurope(an)?\b"],
                "US": [r"\bUS\b", r"\bUnited\s+States\b", r"\bAmerica(n)?\b"],
                "California": [r"\bCalifornia\b", r"\bCA\b"],
                "Global": [r"\bglobal(ly)?\b", r"\bworldwide\b", r"\binternational\b"],
            },
            "age_indicators": [
                r"\b(under|below)\s*(\d+)\b",
                r"\b(\d+)\s*years?\s*old\b",
                r"\bminor(s)?\b",
                r"\bchild(ren)?\b",
                r"\badult(s)?\b",
            ],
            "feature_types": {
                "data_processing": [
                    r"\bdata\s+(processing|collection|storage)\b",
                    r"\bpersonal\s+data\b",
                    r"\buser\s+information\b",
                ],
                "content_moderation": [
                    r"\bcontent\s+(moderation|filtering|removal)\b",
                    r"\buser\s+generated\s+content\b",
                    r"\bCommunity\s+Guidelines\b",
                ],
                "advertising": [
                    r"\badvertising\b",
                    r"\bads?\b",
                    r"\btargeted\s+advertising\b",
                    r"\bpersonalized\s+ads\b",
                ],
                "user_controls": [
                    r"\bprivacy\s+controls\b",
                    r"\buser\s+settings\b",
                    r"\baccount\s+controls\b",
                    r"\bpermissions\b",
                ],
            },
        }

    def _initialize_jurisdictions(self) -> Dict:
        """Map jurisdictions to applicable regulations"""
        return {
            "EU": ["DMA", "GDPR", "DSA"],
            "US": ["COPPA"],
            "California": ["CCPA", "COPPA"],
            "Global": ["GDPR", "COPPA"],  # Regulations that often apply globally
        }


class ComplianceAnalyzer:
    """Main analyzer class for feature compliance assessment"""

    def __init__(self, knowledge_base: Optional[ComplianceKnowledgeBase] = None):
        self.kb = knowledge_base or ComplianceKnowledgeBase()
        self.analysis_cache = {}
        self.rag_adapter = RAGAdapter() if RAGAdapter else None

    def analyze_feature(
        self, feature_name: str, feature_description: str
    ) -> FeatureAnalysis:
        """
        Analyze a single feature for regulatory compliance

        Args:
            feature_name: Name of the feature
            feature_description: Description of the feature

        Returns:
            FeatureAnalysis object with compliance assessment
        """

        # Check cache first
        cache_key = f"{feature_name}:{hash(feature_description)}"
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]

        logger.debug(f"Analyzing feature: {feature_name}")

        # Find regulatory matches
        matches = self._find_regulatory_matches(feature_description)

        # Determine overall compliance status
        overall_compliance, confidence_level = self._determine_overall_compliance(
            matches
        )

        # Check for missing coverage
        missing_coverage = self._identify_missing_coverage(feature_description, matches)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            feature_description, matches, missing_coverage
        )

        # Log analysis evidence
        self._log_analysis_evidence(feature_name, matches, overall_compliance)

        # Determine if flagged for review
        flagged_for_review = self._should_flag_for_review(
            matches, confidence_level, missing_coverage
        )

        analysis = FeatureAnalysis(
            feature_name=feature_name,
            feature_description=feature_description,
            matches=matches,
            overall_compliance=overall_compliance,
            confidence_level=confidence_level,
            flagged_for_review=flagged_for_review,
            missing_coverage=missing_coverage,
            recommendations=recommendations,
        )

        # Cache result
        self.analysis_cache[cache_key] = analysis

        return analysis

    def analyze_features_batch(
        self, features_df: pd.DataFrame
    ) -> List[FeatureAnalysis]:
        """
        Analyze multiple features in batch

        Args:
            features_df: DataFrame with 'feature_name' and 'feature_description' columns

        Returns:
            List of FeatureAnalysis objects
        """

        required_columns = ["feature_name", "feature_description"]
        if not all(col in features_df.columns for col in required_columns):
            raise ValueError(f"DataFrame must contain columns: {required_columns}")

        results = []
        for _, row in features_df.iterrows():
            analysis = self.analyze_feature(
                row["feature_name"], row["feature_description"]
            )
            results.append(analysis)

        logger.info(f"Analyzed {len(results)} features")
        return results

    def _find_regulatory_matches(self, description: str) -> List[ComplianceMatch]:
        """Find regulatory matches for a feature description"""

        matches = []
        description_lower = description.lower()

        for reg_code, reg_info in self.kb.regulations.items():
            # Check for keyword matches
            matched_keywords = []
            for keyword in reg_info["keywords"]:
                if keyword.lower() in description_lower:
                    matched_keywords.append(keyword)

            # Check for regulation-specific patterns
            pattern_matches = self._check_regulation_patterns(description, reg_code)
            matched_keywords.extend(pattern_matches)

            if matched_keywords:
                # Calculate confidence score based on matches
                confidence_score = self._calculate_confidence_score(
                    matched_keywords, reg_info["keywords"], description
                )

                # Determine compliance status
                compliance_status = self._determine_compliance_status(
                    description, reg_code
                )

                # Extract evidence text
                evidence_text = self._extract_evidence_text(
                    description, matched_keywords
                )

                match = ComplianceMatch(
                    regulation_name=reg_info["full_name"],
                    regulation_type=reg_code,
                    jurisdiction=reg_info["jurisdiction"],
                    matched_keywords=list(set(matched_keywords)),  # Remove duplicates
                    confidence_score=confidence_score,
                    compliance_status=compliance_status,
                    evidence_text=evidence_text,
                    requirements=reg_info["key_requirements"],
                )

                matches.append(match)

        return matches

    def _check_regulation_patterns(
        self, description: str, regulation_type: str
    ) -> List[str]:
        """Check for regulation-specific patterns"""

        pattern_matches = []

        # Check geographic patterns
        for jurisdiction, patterns in self.kb.compliance_patterns[
            "geographic_indicators"
        ].items():
            for pattern in patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    # Check if jurisdiction matches regulation
                    if regulation_type in self.kb.jurisdiction_mapping.get(
                        jurisdiction, []
                    ):
                        pattern_matches.append(f"geographic_indicator_{jurisdiction}")

        # Check age-related patterns (especially for COPPA)
        if regulation_type == "COPPA":
            for pattern in self.kb.compliance_patterns["age_indicators"]:
                if re.search(pattern, description, re.IGNORECASE):
                    pattern_matches.append("age_related")

        # Check feature type patterns
        for feature_type, patterns in self.kb.compliance_patterns[
            "feature_types"
        ].items():
            for pattern in patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    pattern_matches.append(f"feature_type_{feature_type}")

        return pattern_matches

    def _calculate_confidence_score(
        self, matched_keywords: List[str], all_keywords: List[str], description: str
    ) -> float:
        """Calculate confidence score for regulatory match"""

        # Base score from keyword matches
        keyword_score = len(matched_keywords) / len(all_keywords)

        # Bonus for explicit compliance language
        compliance_bonus = 0.0
        for pattern in self.kb.compliance_patterns["compliance_signals"]["positive"]:
            if re.search(pattern, description, re.IGNORECASE):
                compliance_bonus += 0.2

        # Penalty for negative compliance signals
        compliance_penalty = 0.0
        for pattern in self.kb.compliance_patterns["compliance_signals"]["negative"]:
            if re.search(pattern, description, re.IGNORECASE):
                compliance_penalty += 0.3

        # Final score
        final_score = min(
            1.0, max(0.0, keyword_score + compliance_bonus - compliance_penalty)
        )

        return round(final_score, 2)

    def _determine_compliance_status(
        self, description: str, regulation_type: str
    ) -> str:
        """Determine compliance status based on description analysis"""

        # Check for explicit compliance signals
        for pattern in self.kb.compliance_patterns["compliance_signals"]["positive"]:
            if re.search(pattern, description, re.IGNORECASE):
                return "COMPLIANT"

        # Check for negative signals
        for pattern in self.kb.compliance_patterns["compliance_signals"]["negative"]:
            if re.search(pattern, description, re.IGNORECASE):
                return "NON_COMPLIANT"

        # Check for partial compliance
        for pattern in self.kb.compliance_patterns["compliance_signals"]["partial"]:
            if re.search(pattern, description, re.IGNORECASE):
                return "PARTIAL"

        # Default to unknown if no clear signals
        return "UNKNOWN"

    def _extract_evidence_text(
        self, description: str, keywords: List[str]
    ) -> List[str]:
        """Extract relevant evidence text from description"""

        evidence = []
        sentences = re.split(r"[.!?]+", description)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Ignore very short sentences
                # Check if sentence contains any matched keywords
                for keyword in keywords:
                    if keyword.lower() in sentence.lower():
                        evidence.append(sentence)
                        break

        return evidence[:3]  # Limit to top 3 evidence pieces

    def _determine_overall_compliance(
        self, matches: List[ComplianceMatch]
    ) -> Tuple[str, str]:
        """Determine overall compliance status and confidence level"""

        if not matches:
            return "NEEDS_REVIEW", "LOW"

        # Count compliance statuses
        statuses = [match.compliance_status for match in matches]

        if all(status == "COMPLIANT" for status in statuses):
            overall = "COMPLIANT"
        elif any(status == "NON_COMPLIANT" for status in statuses):
            overall = "NON_COMPLIANT"
        elif any(status == "PARTIAL" for status in statuses):
            overall = "PARTIAL"
        else:
            overall = "NEEDS_REVIEW"

        # Determine confidence level
        avg_confidence = sum(match.confidence_score for match in matches) / len(matches)

        if avg_confidence >= 0.8:
            confidence = "HIGH"
        elif avg_confidence >= 0.5:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        return overall, confidence

    def _identify_missing_coverage(
        self, description: str, matches: List[ComplianceMatch]
    ) -> List[str]:
        """Identify potentially missing regulatory coverage"""

        missing = []
        matched_regulations = {match.regulation_type for match in matches}

        # Check for geographic indicators without matching regulations
        description_lower = description.lower()

        # EU indicators without EU regulations
        eu_indicators = any(
            re.search(pattern, description, re.IGNORECASE)
            for pattern in self.kb.compliance_patterns["geographic_indicators"]["EU"]
        )
        if eu_indicators and not any(
            reg in matched_regulations for reg in ["DMA", "GDPR", "DSA"]
        ):
            missing.extend(["DMA", "GDPR", "DSA"])

        # US indicators without US regulations
        us_indicators = any(
            re.search(pattern, description, re.IGNORECASE)
            for pattern in self.kb.compliance_patterns["geographic_indicators"]["US"]
        )
        if us_indicators and "COPPA" not in matched_regulations:
            missing.append("COPPA")

        # Age-related features without COPPA
        age_related = any(
            re.search(pattern, description, re.IGNORECASE)
            for pattern in self.kb.compliance_patterns["age_indicators"]
        )
        if age_related and "COPPA" not in matched_regulations:
            missing.append("COPPA")

        return list(set(missing))  # Remove duplicates

    def _generate_recommendations(
        self,
        description: str,
        matches: List[ComplianceMatch],
        missing_coverage: List[str],
    ) -> List[str]:
        """Generate compliance recommendations"""

        recommendations = []

        # Recommendations for missing coverage
        if missing_coverage:
            recommendations.append(
                f"Review feature for potential {', '.join(missing_coverage)} compliance requirements"
            )

        # Recommendations based on compliance status
        non_compliant_matches = [
            m for m in matches if m.compliance_status == "NON_COMPLIANT"
        ]
        if non_compliant_matches:
            for match in non_compliant_matches:
                recommendations.append(
                    f"Address {match.regulation_name} non-compliance issues"
                )

        partial_matches = [m for m in matches if m.compliance_status == "PARTIAL"]
        if partial_matches:
            for match in partial_matches:
                recommendations.append(
                    f"Complete {match.regulation_name} compliance implementation"
                )

        # Recommendations for unknown status
        unknown_matches = [m for m in matches if m.compliance_status == "UNKNOWN"]
        if unknown_matches:
            recommendations.append(
                "Clarify compliance status with explicit compliance statements"
            )

        # Low confidence recommendations
        low_confidence_matches = [m for m in matches if m.confidence_score < 0.5]
        if low_confidence_matches:
            recommendations.append("Provide more detailed compliance documentation")

        return recommendations[:5]  # Limit to top 5 recommendations

    def _should_flag_for_review(
        self,
        matches: List[ComplianceMatch],
        confidence_level: str,
        missing_coverage: List[str],
    ) -> bool:
        """Determine if feature should be flagged for manual review"""

        # Flag if no matches found
        if not matches:
            return True

        # Flag if low confidence
        if confidence_level == "LOW":
            return True

        # Flag if missing coverage identified
        if missing_coverage:
            return True

        # Flag if any non-compliant matches
        if any(match.compliance_status == "NON_COMPLIANT" for match in matches):
            return True

        # Flag if conflicting compliance statuses
        statuses = {match.compliance_status for match in matches}
        if len(statuses) > 1 and "NON_COMPLIANT" in statuses:
            return True

        return False

    def get_coverage_statistics(self, analyses: List[FeatureAnalysis]) -> Dict:
        """Generate coverage statistics for analyzed features"""

        total_features = len(analyses)

        # Compliance status distribution
        status_counts = {}
        for analysis in analyses:
            status = analysis.overall_compliance
            status_counts[status] = status_counts.get(status, 0) + 1

        # Confidence level distribution
        confidence_counts = {}
        for analysis in analyses:
            confidence = analysis.confidence_level
            confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1

        # Regulation coverage
        regulation_coverage = {}
        for analysis in analyses:
            for match in analysis.matches:
                reg_type = match.regulation_type
                regulation_coverage[reg_type] = regulation_coverage.get(reg_type, 0) + 1

        # Flagged features
        flagged_count = sum(1 for analysis in analyses if analysis.flagged_for_review)

        # Missing coverage analysis
        missing_coverage_counts = {}
        for analysis in analyses:
            for missing_reg in analysis.missing_coverage:
                missing_coverage_counts[missing_reg] = (
                    missing_coverage_counts.get(missing_reg, 0) + 1
                )

        return {
            "total_features": total_features,
            "compliance_status_distribution": status_counts,
            "confidence_level_distribution": confidence_counts,
            "regulation_coverage": regulation_coverage,
            "flagged_for_review": flagged_count,
            "flagged_percentage": (
                round((flagged_count / total_features) * 100, 1)
                if total_features > 0
                else 0
            ),
            "missing_coverage_analysis": missing_coverage_counts,
            "compliant_percentage": (
                round((status_counts.get("COMPLIANT", 0) / total_features) * 100, 1)
                if total_features > 0
                else 0
            ),
        }

    def _get_rag_regulatory_context(
        self, query: str, jurisdiction: str = None
    ) -> List[Dict]:
        """Get regulatory context using centralized RAG system."""
        if not self.rag_adapter:
            return []

        try:
            return self.rag_adapter.retrieve_regulatory_context(
                query=query, jurisdiction=jurisdiction, max_results=5
            )
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            return []

    def _log_analysis_evidence(
        self, feature_name: str, matches: List[ComplianceMatch], overall_compliance: str
    ):
        """Log compliance analysis evidence using centralized logger."""
        if log_compliance_decision:
            evidence_data = {
                "request_id": str(uuid.uuid4()),
                "timestamp_iso": datetime.now().isoformat(),
                "agent_name": "compliance_analyzer",
                "decision_flag": overall_compliance == "Compliant",
                "reasoning_text": f"Analysis completed with {len(matches)} compliance matches",
                "feature_id": feature_name,
                "feature_title": feature_name,
                "related_regulations": [match.regulation for match in matches],
                "confidence": sum(match.confidence for match in matches)
                / max(len(matches), 1),
                "retrieval_metadata": {
                    "agent_specific": "compliance_analysis",
                    "analysis_top_k": 5,
                    "matches_count": len(matches),
                },
                "timings_ms": {
                    "analysis_ms": 0  # Will be populated if timing is tracked
                },
            }
            log_compliance_decision(evidence_data)
        else:
            # Fallback to local logging
            evidence = {
                "feature_name": feature_name,
                "overall_compliance": overall_compliance,
                "matches_count": len(matches),
                "timestamp": datetime.now().isoformat(),
            }
            logger.info(f"Compliance analysis evidence logged (local): {evidence}")
