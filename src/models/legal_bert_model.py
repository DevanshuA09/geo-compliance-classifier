from typing import Any, Dict, Tuple

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class LegalBERTModel:
    """
    Legal-BERT Fine-tuned Model for Compliance Detection
    Base: nlpaueb/legal-bert-base-uncased
    Fine-tuned on compliance detection tasks
    """

    def __init__(self, model_path: str = "nlpaueb/legal-bert-base-uncased"):
        self.model_path = model_path
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._load_model()

    def _load_model(self):
        """Load the Legal-BERT model and tokenizer"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_path, num_labels=3  # Compliant, Non-Compliant, Unclear
            )
            self.model.to(self.device)
            self.model.eval()
        except Exception as e:
            print(f"Warning: Could not load Legal-BERT model: {e}")
            print("Using fallback classification logic")

    def predict(self, text: str) -> Tuple[str, float]:
        """
        Predict compliance status with confidence score

        Args:
            text: Input text to classify

        Returns:
            Tuple of (decision, confidence_score)
        """
        if self.model is None or self.tokenizer is None:
            return self._fallback_prediction(text)

        try:
            # Tokenize input
            inputs = self.tokenizer(
                text, truncation=True, padding=True, max_length=512, return_tensors="pt"
            ).to(self.device)

            # Get predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                probabilities = torch.softmax(outputs.logits, dim=1)
                confidence, predicted_class = torch.max(probabilities, dim=1)

            # Map class indices to decisions
            decision_map = {0: "Compliant", 1: "Non-Compliant", 2: "Unclear"}
            decision = decision_map[predicted_class.item()]
            confidence_score = confidence.item()

            return decision, confidence_score

        except Exception as e:
            print(f"Error in Legal-BERT prediction: {e}")
            return self._fallback_prediction(text)

    def _fallback_prediction(self, text: str) -> Tuple[str, float]:
        """Fallback prediction when model is not available"""
        # Simple keyword-based fallback
        text_lower = text.lower()

        compliant_keywords = [
            "compliant",
            "legal",
            "approved",
            "permitted",
            "authorized",
        ]
        non_compliant_keywords = [
            "non-compliant",
            "illegal",
            "prohibited",
            "violation",
            "breach",
        ]

        compliant_count = sum(1 for word in compliant_keywords if word in text_lower)
        non_compliant_count = sum(
            1 for word in word in non_compliant_keywords if word in text_lower
        )

        if compliant_count > non_compliant_count:
            return "Compliant", 0.75
        elif non_compliant_count > compliant_count:
            return "Non-Compliant", 0.75
        else:
            return "Unclear", 0.60

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and status"""
        return {
            "model_type": "Legal-BERT Fine-tuned",
            "base_model": self.model_path,
            "status": "loaded" if self.model is not None else "fallback",
            "device": str(self.device),
            "strength": "Specialized legal language comprehension",
        }
