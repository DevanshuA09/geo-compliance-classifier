import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class ComplianceRule:
    """Individual compliance rule with pattern and decision"""

    name: str
    pattern: str
    decision: str
    confidence: float
    description: str


class RulesBasedClassifier:
    """
    Rules-Based Classifier for Compliance Detection
    Pattern matching compliance keywords and explicit rule triggers
    Strength: Interpretable and reliable on clear-cut cases
    """

    def __init__(self):
        self.rules = self._initialize_rules()
        self.compliance_keywords = self._initialize_keywords()

    def _initialize_rules(self) -> List[ComplianceRule]:
        """Initialize compliance rules with patterns and decisions"""
        return [
            ComplianceRule(
                name="Explicit Compliance",
                pattern=r"\b(compliant|compliance|legal|approved|permitted|authorized)\b",
                decision="Compliant",
                confidence=0.95,
                description="Explicit compliance language detected",
            ),
            ComplianceRule(
                name="Explicit Non-Compliance",
                pattern=r"\b(non.?compliant|illegal|prohibited|violation|breach|unauthorized)\b",
                decision="Non-Compliant",
                confidence=0.95,
                description="Explicit non-compliance language detected",
            ),
            ComplianceRule(
                name="Regulatory Reference",
                pattern=r"\b(regulation|statute|law|act|code|standard)\b",
                decision="Compliant",
                confidence=0.85,
                description="Regulatory framework reference detected",
            ),
            ComplianceRule(
                name="Penalty Language",
                pattern=r"\b(penalty|fine|sanction|enforcement|violation)\b",
                decision="Non-Compliant",
                confidence=0.80,
                description="Penalty or enforcement language detected",
            ),
            ComplianceRule(
                name="Certification Language",
                pattern=r"\b(certified|certification|accredited|licensed|registered)\b",
                decision="Compliant",
                confidence=0.90,
                description="Certification or accreditation language detected",
            ),
            ComplianceRule(
                name="Risk Assessment",
                pattern=r"\b(risk|assessment|evaluation|review|audit)\b",
                decision="Unclear",
                confidence=0.70,
                description="Risk assessment language detected",
            ),
        ]

    def _initialize_keywords(self) -> Dict[str, List[str]]:
        """Initialize keyword categories for scoring"""
        return {
            "compliant": [
                "compliant",
                "compliance",
                "legal",
                "approved",
                "permitted",
                "authorized",
                "valid",
                "proper",
                "correct",
                "adequate",
            ],
            "non_compliant": [
                "non-compliant",
                "illegal",
                "prohibited",
                "violation",
                "breach",
                "unauthorized",
                "invalid",
                "improper",
                "incorrect",
                "inadequate",
            ],
            "uncertain": [
                "unclear",
                "uncertain",
                "ambiguous",
                "unclear",
                "depends",
                "case-by-case",
                "context-dependent",
                "review required",
            ],
        }

    def predict(self, text: str) -> Tuple[str, float]:
        """
        Predict compliance status using rule-based classification

        Args:
            text: Input text to classify

        Returns:
            Tuple of (decision, confidence_score)
        """
        text_lower = text.lower()

        # Apply rule-based classification
        rule_matches = self._apply_rules(text_lower)

        # Calculate keyword-based scoring
        keyword_scores = self._calculate_keyword_scores(text_lower)

        # Combine rule-based and keyword-based approaches
        final_decision, final_confidence = self._combine_approaches(
            rule_matches, keyword_scores
        )

        return final_decision, final_confidence

    def _apply_rules(self, text: str) -> List[ComplianceRule]:
        """Apply all compliance rules to the text"""
        matches = []

        for rule in self.rules:
            if re.search(rule.pattern, text, re.IGNORECASE):
                matches.append(rule)

        return matches

    def _calculate_keyword_scores(self, text: str) -> Dict[str, float]:
        """Calculate keyword-based scores for each category"""
        scores = {}

        for category, keywords in self.compliance_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text)
            # Normalize score based on text length and keyword frequency
            scores[category] = min(1.0, count / max(1, len(text.split()) * 0.1))

        return scores

    def _combine_approaches(
        self, rule_matches: List[ComplianceRule], keyword_scores: Dict[str, float]
    ) -> Tuple[str, float]:
        """Combine rule-based and keyword-based approaches for final decision"""

        if not rule_matches and not any(
            score > 0.1 for score in keyword_scores.values()
        ):
            return "Unclear", 0.50

        # If we have strong rule matches, use them
        if rule_matches:
            # Find the highest confidence rule match
            best_rule = max(rule_matches, key=lambda x: x.confidence)

            # If multiple rules agree, boost confidence
            if len(rule_matches) > 1:
                agreeing_rules = [
                    r for r in rule_matches if r.decision == best_rule.decision
                ]
                if len(agreeing_rules) > 1:
                    confidence_boost = min(0.1, len(agreeing_rules) * 0.02)
                    final_confidence = min(1.0, best_rule.confidence + confidence_boost)
                else:
                    final_confidence = best_rule.confidence
            else:
                final_confidence = best_rule.confidence

            return best_rule.decision, final_confidence

        # Fall back to keyword-based scoring
        if keyword_scores["compliant"] > keyword_scores["non_compliant"]:
            if keyword_scores["compliant"] > 0.3:
                return "Compliant", min(0.85, keyword_scores["compliant"])
            else:
                return "Unclear", 0.60
        elif keyword_scores["non_compliant"] > keyword_scores["compliant"]:
            if keyword_scores["non_compliant"] > 0.3:
                return "Non-Compliant", min(0.85, keyword_scores["non_compliant"])
            else:
                return "Unclear", 0.60
        else:
            return "Unclear", 0.50

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and status"""
        return {
            "model_type": "Rules-Based Classifier",
            "status": "active",
            "rule_count": len(self.rules),
            "strength": "Interpretable and reliable on clear-cut cases",
        }

    def explain_decision(self, text: str) -> Dict[str, Any]:
        """Explain the decision-making process for transparency"""
        text_lower = text.lower()
        rule_matches = self._apply_rules(text_lower)
        keyword_scores = self._calculate_keyword_scores(text_lower)

        return {
            "applied_rules": [rule.name for rule in rule_matches],
            "keyword_scores": keyword_scores,
            "reasoning": f"Applied {len(rule_matches)} rules and keyword scoring",
        }
