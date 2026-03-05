#!/usr/bin/env python3
"""
Test script for ensemble logic demonstration

This script shows how the Confidence Validator Agent handles different scenarios
and demonstrates the ensemble decision-making process.
"""

import os

from src.agents import ConfidenceValidatorAgent


def test_unanimous_agreement():
    """Test case where all models agree with high confidence"""
    print("🧪 Testing Unanimous Agreement Scenario")
    print("-" * 50)

    text = "The organization is fully compliant with all applicable regulations and maintains certified compliance status."

    validator = ConfidenceValidatorAgent()
    result = validator.validate_case(text, "UNANIMOUS-001")

    print(f"Text: {text}")
    print(
        f"Final Decision: {result.ensemble_decision} (Confidence: {result.ensemble_confidence:.2f})"
    )
    print(f"Auto-Approved: {'Yes' if result.auto_approved else 'No'}")
    print(f"Agreement Level: {result.agreement_level}")

    for model_name, prediction in result.predictions.items():
        print(f"  {model_name}: {prediction.decision} ({prediction.confidence:.2f})")

    print()


def test_majority_vote():
    """Test case where majority of models agree"""
    print("🧪 Testing Majority Vote Scenario")
    print("-" * 50)

    text = "The company maintains compliance with safety standards but requires additional review for environmental regulations."

    validator = ConfidenceValidatorAgent()
    result = validator.validate_case(text, "MAJORITY-001")

    print(f"Text: {text}")
    print(
        f"Final Decision: {result.ensemble_decision} (Confidence: {result.ensemble_confidence:.2f})"
    )
    print(f"Auto-Approved: {'Yes' if result.auto_approved else 'No'}")
    print(f"Agreement Level: {result.agreement_level}")

    for model_name, prediction in result.predictions.items():
        print(f"  {model_name}: {prediction.decision} ({prediction.confidence:.2f})")

    print()


def test_legal_bert_tiebreaker():
    """Test case where Legal-BERT acts as tiebreaker"""
    print("🧪 Testing Legal-BERT Tiebreaker Scenario")
    print("-" * 50)

    text = "The compliance status is ambiguous and requires legal interpretation."

    validator = ConfidenceValidatorAgent()
    result = validator.validate_case(text, "TIEBREAKER-001")

    print(f"Text: {text}")
    print(
        f"Final Decision: {result.ensemble_decision} (Confidence: {result.ensemble_confidence:.2f})"
    )
    print(f"Auto-Approved: {'Yes' if result.auto_approved else 'No'}")
    print(f"Agreement Level: {result.agreement_level}")

    for model_name, prediction in result.predictions.items():
        print(f"  {model_name}: {prediction.decision} ({prediction.confidence:.2f})")

    if result.flags:
        print("Flags:")
        for flag in result.flags:
            print(f"  - {flag}")

    print()


def test_low_confidence():
    """Test case with low confidence across all models"""
    print("🧪 Testing Low Confidence Scenario")
    print("-" * 50)

    text = "The situation is complex and may involve multiple regulatory frameworks."

    validator = ConfidenceValidatorAgent()
    result = validator.validate_case(text, "LOW-CONF-001")

    print(f"Text: {text}")
    print(
        f"Final Decision: {result.ensemble_decision} (Confidence: {result.ensemble_confidence:.2f})"
    )
    print(f"Auto-Approved: {'Yes' if result.auto_approved else 'No'}")
    print(f"Agreement Level: {result.agreement_level}")

    for model_name, prediction in result.predictions.items():
        print(f"  {model_name}: {prediction.decision} ({prediction.confidence:.2f})")

    print()


def test_confidence_thresholds():
    """Test different confidence threshold configurations"""
    print("🧪 Testing Confidence Threshold Configurations")
    print("-" * 50)

    text = "The organization maintains compliance with industry standards."

    # Test with default thresholds
    validator_default = ConfidenceValidatorAgent()
    result_default = validator_default.validate_case(text, "THRESHOLD-001")

    print("Default thresholds (0.85):")
    print(f"  Decision: {result_default.ensemble_decision}")
    print(f"  Confidence: {result_default.ensemble_confidence:.2f}")
    print(f"  Auto-Approved: {'Yes' if result_default.auto_approved else 'No'}")

    # Test with lower thresholds
    validator_lower = ConfidenceValidatorAgent()
    validator_lower.confidence_threshold = 0.70
    validator_lower.auto_approval_threshold = 0.70
    result_lower = validator_lower.validate_case(text, "THRESHOLD-002")

    print("\nLower thresholds (0.70):")
    print(f"  Decision: {result_lower.ensemble_decision}")
    print(f"  Confidence: {result_lower.ensemble_confidence:.2f}")
    print(f"  Auto-Approved: {'Yes' if result_lower.auto_approved else 'No'}")

    print()


def main():
    """Run all test scenarios"""
    print("🔍 Ensemble Logic Test Suite")
    print("=" * 60)

    # Run test scenarios
    test_unanimous_agreement()
    test_majority_vote()
    test_legal_bert_tiebreaker()
    test_low_confidence()
    test_confidence_thresholds()

    print("✅ All tests completed!")
    print("\nKey Insights:")
    print("  • Unanimous agreement with high confidence → Auto-approval")
    print("  • Majority vote → Use majority decision")
    print("  • No clear majority → Legal-BERT tiebreaker")
    print("  • Low confidence → Flag for manual review")
    print("  • Thresholds configurable for different use cases")


if __name__ == "__main__":
    main()
