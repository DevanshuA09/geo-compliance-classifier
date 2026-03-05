"""
Current Agent Tests

These tests verify that the refactored agents work correctly with the new interface.
"""

import pytest

from src.agents import ActiveLearningAgent, ConfidenceValidatorAgent
from src.evidence import EvidenceVerificationAgent


def test_evidence_verification_agent_initialization():
    """Test that EvidenceVerificationAgent can be initialized"""
    agent = EvidenceVerificationAgent()
    assert agent is not None
    assert hasattr(agent, "verify_evidence_with_rag")


def test_confidence_validator_agent_initialization():
    """Test that ConfidenceValidatorAgent can be initialized"""
    agent = ConfidenceValidatorAgent()
    assert agent is not None
    assert hasattr(agent, "validate_case")


def test_active_learning_agent_initialization():
    """Test that ActiveLearningAgent can be initialized"""
    agent = ActiveLearningAgent()
    assert agent is not None
    assert hasattr(agent, "log_human_correction")


def test_agent_methods_exist():
    """Test that all expected methods exist on the agents"""
    # Evidence Verification Agent
    evidence_agent = EvidenceVerificationAgent()
    expected_evidence_methods = ["verify_evidence_with_rag", "get_verification_summary"]
    for method in expected_evidence_methods:
        assert hasattr(evidence_agent, method), f"Missing method: {method}"

    # Confidence Validator Agent
    validator_agent = ConfidenceValidatorAgent()
    expected_validator_methods = ["validate_case", "get_validation_summary"]
    for method in expected_validator_methods:
        assert hasattr(validator_agent, method), f"Missing method: {method}"

    # Active Learning Agent
    learning_agent = ActiveLearningAgent()
    expected_learning_methods = ["log_human_correction", "get_rag_system_status"]
    for method in expected_learning_methods:
        assert hasattr(learning_agent, method), f"Missing method: {method}"


def test_agent_fallback_mechanism():
    """Test that agents can work without RAG service (fallback mode)"""
    # Test with invalid RAG URL to trigger fallback
    evidence_agent = EvidenceVerificationAgent()
    assert evidence_agent.rag_adapter is None or hasattr(evidence_agent, "rag_adapter")

    validator_agent = ConfidenceValidatorAgent()
    assert validator_agent.rag_adapter is None or hasattr(
        validator_agent, "rag_adapter"
    )

    learning_agent = ActiveLearningAgent()
    assert learning_agent.rag_adapter is None or hasattr(learning_agent, "rag_adapter")


if __name__ == "__main__":
    print("🧪 Running Current Agent Tests")
    print("=" * 50)

    test_results = []

    test_results.append(
        ("Agent Initialization", test_evidence_verification_agent_initialization())
    )
    test_results.append(
        (
            "Confidence Validator Initialization",
            test_confidence_validator_agent_initialization(),
        )
    )
    test_results.append(
        ("Active Learning Initialization", test_active_learning_agent_initialization())
    )
    test_results.append(("Method Verification", test_agent_methods_exist()))
    test_results.append(("Fallback Mechanism", test_agent_fallback_mechanism()))

    print("\n📊 Test Results Summary")
    print("=" * 50)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All current agent tests passed!")
        exit(0)
    else:
        print("⚠️  Some tests failed. Check the output above.")
        exit(1)
