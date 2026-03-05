from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from src.models import LegalBERTModel, LLMRAGModel, RulesBasedClassifier

try:
    from ..evidence import log_compliance_decision
    from ..rag import RAGAdapter
except ImportError:
    from rag_adapter import RAGAdapter

    try:
        from evidence_logger import log_compliance_decision
    except ImportError:
        log_compliance_decision = None
import uuid
from datetime import datetime

import pandas as pd


@dataclass
class ModelPrediction:
    """Individual model prediction with metadata"""

    model_name: str
    decision: str
    confidence: float
    reasoning: str = ""
    model_info: Dict[str, Any] = None
    regulatory_context: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Complete validation result for a case"""

    case_id: str
    timestamp: str
    text: str
    predictions: Dict[str, ModelPrediction]
    ensemble_decision: str
    ensemble_confidence: float
    auto_approved: bool
    flags: List[str]
    notes: str
    majority_vote: str
    agreement_level: str


class ConfidenceValidatorAgent:
    """
    Confidence Validator Agent for Compliance Predictions

    Ensures reliable compliance predictions by cross-validating outputs from multiple models:
    1. Legal-BERT Fine-tuned (Primary)
    2. Rules-Based Classifier (Hybrid)
    3. General-Purpose LLM with RAG (Context-Enhanced)
    """

    def __init__(self, openai_api_key: str = None, rag_adapter: RAGAdapter = None):
        self.models = {
            "Legal-BERT": LegalBERTModel(),
            "Rules-Based": RulesBasedClassifier(),
            "LLM+RAG": LLMRAGModel(api_key=openai_api_key),
        }
        self.validation_history = []
        self.confidence_threshold = 0.85
        self.auto_approval_threshold = 0.85

        # RAG integration
        self.rag_adapter = rag_adapter or RAGAdapter()

    def validate_case(self, text: str, case_id: str = None) -> ValidationResult:
        """
        Validate a compliance case using all three models

        Args:
            text: Text to analyze for compliance
            case_id: Optional case identifier

        Returns:
            ValidationResult with ensemble decision and metadata
        """
        if case_id is None:
            case_id = str(uuid.uuid4())[:8]

        # Collect predictions from all models
        predictions = {}
        for model_name, model in self.models.items():
            try:
                decision, confidence = model.predict(text)
                reasoning = self._get_model_reasoning(model, text)
                model_info = model.get_model_info()

                predictions[model_name] = ModelPrediction(
                    model_name=model_name,
                    decision=decision,
                    confidence=confidence,
                    reasoning=reasoning,
                    model_info=model_info,
                )
            except Exception as e:
                print(f"Error getting prediction from {model_name}: {e}")
                # Create fallback prediction
                predictions[model_name] = ModelPrediction(
                    model_name=model_name,
                    decision="Unclear",
                    confidence=0.50,
                    reasoning=f"Error occurred: {str(e)}",
                    model_info={"status": "error"},
                )

        # Apply ensemble logic
        ensemble_decision, ensemble_confidence, flags, notes = (
            self._apply_ensemble_logic(predictions)
        )

        # Determine if auto-approved
        auto_approved = self._should_auto_approve(predictions, ensemble_confidence)

        # Create validation result
        result = ValidationResult(
            case_id=case_id,
            timestamp=datetime.now().isoformat(),
            text=(
                text[:200] + "..." if len(text) > 200 else text
            ),  # Truncate for display
            predictions=predictions,
            ensemble_decision=ensemble_decision,
            ensemble_confidence=ensemble_confidence,
            auto_approved=auto_approved,
            flags=flags,
            notes=notes,
            majority_vote=self._get_majority_vote(predictions),
            agreement_level=self._get_agreement_level(predictions),
        )

        # Store in history
        self.validation_history.append(result)

        # Log evidence for confidence validation decision
        if log_compliance_decision:
            evidence_data = {
                "request_id": str(uuid.uuid4()),
                "timestamp_iso": datetime.now().isoformat(),
                "agent_name": "confidence_validator",
                "decision_flag": ensemble_decision != "Non-Compliant",
                "reasoning_text": f"Confidence validation: {ensemble_decision} - {notes}",
                "feature_id": case_id,
                "feature_title": f"Confidence Validation {case_id}",
                "related_regulations": [],  # Will be populated from RAG if available
                "confidence": ensemble_confidence,
                "retrieval_metadata": {
                    "agent_specific": "confidence_validation",
                    "models_count": len(predictions),
                    "agreement_level": self._get_agreement_level(predictions),
                    "majority_vote": self._get_majority_vote(predictions),
                    "auto_approved": auto_approved,
                },
                "timings_ms": {
                    "validation_ms": 0  # Will be populated if timing is tracked
                },
            }
            log_compliance_decision(evidence_data)

        return result

    def validate_case_with_rag(
        self, text: str, case_id: str = None
    ) -> ValidationResult:
        """Validate case with enhanced RAG context."""
        # Get regulatory context via RAG
        regulatory_context = self.rag_adapter.retrieve_regulatory_context(
            text, max_results=3
        )

        # Enhance text with regulatory context
        enhanced_text = f"{text}\n\nRegulatory Context:\n" + "\n".join(
            [f"- {ctx['text']}" for ctx in regulatory_context]
        )

        # Use enhanced text for validation
        return self.validate_case(enhanced_text, case_id)

    def get_rag_system_status(self) -> Dict[str, Any]:
        """Get RAG system status."""
        return self.rag_adapter.get_system_status()

    def _get_model_reasoning(self, model: Any, text: str) -> str:
        """Get reasoning from model if available"""
        try:
            if hasattr(model, "explain_decision"):
                explanation = model.explain_decision(text)
                if isinstance(explanation, dict):
                    return str(explanation.get("reasoning", "No reasoning provided"))
                return str(explanation)
            return "No reasoning method available"
        except Exception:
            return "Error retrieving reasoning"

    def _apply_ensemble_logic(
        self, predictions: Dict[str, ModelPrediction]
    ) -> Tuple[str, float, List[str], str]:
        """Apply ensemble logic to determine final decision"""
        decisions = [pred.decision for pred in predictions.values()]
        confidences = [pred.confidence for pred in predictions.values()]

        # Check for unanimous agreement
        if len(set(decisions)) == 1:
            # All models agree
            avg_confidence = sum(confidences) / len(confidences)
            if avg_confidence >= self.confidence_threshold:
                return (
                    decisions[0],
                    avg_confidence,
                    [],
                    "Unanimous agreement with high confidence",
                )
            else:
                return (
                    decisions[0],
                    avg_confidence,
                    ["Low confidence despite agreement"],
                    "Unanimous agreement but low confidence",
                )

        # Check for majority vote
        decision_counts = {}
        for decision in decisions:
            decision_counts[decision] = decision_counts.get(decision, 0) + 1

        majority_decision = max(decision_counts.items(), key=lambda x: x[1])

        if majority_decision[1] >= 2:  # At least 2 models agree
            # Calculate confidence for majority decision
            majority_confidences = [
                pred.confidence
                for pred in predictions.values()
                if pred.decision == majority_decision[0]
            ]
            avg_majority_confidence = sum(majority_confidences) / len(
                majority_confidences
            )

            # Check if minority model has high confidence
            minority_models = [
                pred
                for pred in predictions.values()
                if pred.decision != majority_decision[0]
            ]

            flags = []
            notes = f"Majority vote: {majority_decision[0]} ({majority_decision[1]}/3 models)"

            for minority in minority_models:
                if minority.confidence > 0.80:
                    flags.append(
                        f"High-confidence minority: {minority.model_name} ({minority.decision}, {minority.confidence:.2f})"
                    )
                    notes += f". Minority disagreement from {minority.model_name}"

            return majority_decision[0], avg_majority_confidence, flags, notes

        # No clear majority - use Legal-BERT as tiebreaker
        legal_bert_pred = predictions.get("Legal-BERT")
        if legal_bert_pred:
            flags = ["No clear majority - using Legal-BERT as tiebreaker"]
            notes = (
                "No majority agreement. Legal-BERT used as domain-specific tiebreaker."
            )
            return legal_bert_pred.decision, legal_bert_pred.confidence, flags, notes

        # Fallback
        return "Unclear", 0.50, ["All models disagree"], "No clear decision possible"

    def _should_auto_approve(
        self, predictions: Dict[str, ModelPrediction], ensemble_confidence: float
    ) -> bool:
        """Determine if case should be auto-approved"""
        decisions = [pred.decision for pred in predictions.values()]
        confidences = [pred.confidence for pred in predictions.values()]

        # Check for unanimous agreement with high confidence
        if (
            len(set(decisions)) == 1
            and ensemble_confidence >= self.auto_approval_threshold
        ):
            return True

        # Check if all models have high confidence
        if all(conf >= self.confidence_threshold for conf in confidences):
            return True

        return False

    def _get_majority_vote(self, predictions: Dict[str, ModelPrediction]) -> str:
        """Get the majority vote decision"""
        decisions = [pred.decision for pred in predictions.values()]
        decision_counts = {}
        for decision in decisions:
            decision_counts[decision] = decision_counts.get(decision, 0) + 1

        if decision_counts:
            return max(decision_counts.items(), key=lambda x: x[1])[0]
        return "Unclear"

    def _get_agreement_level(self, predictions: Dict[str, ModelPrediction]) -> str:
        """Get the level of agreement between models"""
        decisions = [pred.decision for pred in predictions.values()]
        unique_decisions = len(set(decisions))

        if unique_decisions == 1:
            return "Unanimous"
        elif unique_decisions == 2:
            return "Majority"
        else:
            return "Disagreement"

    def get_validation_summary(self) -> pd.DataFrame:
        """Get summary of all validations in DataFrame format"""
        if not self.validation_history:
            return pd.DataFrame()

        summary_data = []
        for result in self.validation_history:
            row = {
                "Case ID": result.case_id,
                "Timestamp": result.timestamp,
                "Legal-BERT Decision (Conf.)": f"{result.predictions['Legal-BERT'].decision} ({result.predictions['Legal-BERT'].confidence:.2f})",
                "Rules-Based Decision (Conf.)": f"{result.predictions['Rules-Based'].decision} ({result.predictions['Rules-Based'].confidence:.2f})",
                "LLM+RAG Decision (Conf.)": f"{result.predictions['LLM+RAG'].decision} ({result.predictions['LLM+RAG'].confidence:.2f})",
                "Final Ensemble Decision": result.ensemble_decision,
                "Ensemble Confidence": f"{result.ensemble_confidence:.2f}",
                "Auto-Approved": "Yes" if result.auto_approved else "No",
                "Agreement Level": result.agreement_level,
                "Flags": "; ".join(result.flags) if result.flags else "None",
                "Notes": result.notes,
            }
            summary_data.append(row)

        return pd.DataFrame(summary_data)

    def export_results_markdown(self, filename: str = None) -> str:
        """Export validation results in markdown format"""
        if filename is None:
            filename = (
                f"compliance_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            )

        markdown_content = "# Compliance Validation Results\n\n"
        markdown_content += (
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        markdown_content += f"Total Cases: {len(self.validation_history)}\n\n"

        # Summary table
        df = self.get_validation_summary()
        if not df.empty:
            markdown_content += "## Validation Summary\n\n"
            markdown_content += df.to_markdown(index=False)
            markdown_content += "\n\n"

        # Detailed results
        markdown_content += "## Detailed Results\n\n"
        for result in self.validation_history:
            markdown_content += f"### Case {result.case_id}\n\n"
            markdown_content += f"**Text:** {result.text}\n\n"
            markdown_content += f"**Timestamp:** {result.timestamp}\n\n"
            markdown_content += f"**Final Decision:** {result.ensemble_decision} (Confidence: {result.ensemble_confidence:.2f})\n\n"
            markdown_content += (
                f"**Auto-Approved:** {'Yes' if result.auto_approved else 'No'}\n\n"
            )

            # Model predictions
            markdown_content += "**Model Predictions:**\n\n"
            for model_name, prediction in result.predictions.items():
                markdown_content += f"- **{model_name}:** {prediction.decision} (Confidence: {prediction.confidence:.2f})\n"
                if prediction.reasoning:
                    markdown_content += f"  - Reasoning: {prediction.reasoning}\n"
            markdown_content += "\n"

            # Flags and notes
            if result.flags:
                markdown_content += "**Flags:**\n"
                for flag in result.flags:
                    markdown_content += f"- {flag}\n"
                markdown_content += "\n"

            if result.notes:
                markdown_content += f"**Notes:** {result.notes}\n\n"

            markdown_content += "---\n\n"

        # Save to file
        with open(filename, "w") as f:
            f.write(markdown_content)

        return filename

    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all models"""
        status = {}
        for model_name, model in self.models.items():
            try:
                status[model_name] = model.get_model_info()
            except Exception as e:
                status[model_name] = {"status": "error", "error": str(e)}
        return status
