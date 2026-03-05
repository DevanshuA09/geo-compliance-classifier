#!/usr/bin/env python3
"""
Test script to verify all agents integrate properly with the centralized RAG system.
This script tests the refactored agents to ensure they use the unified RAG pipeline.
"""

import sys
import traceback
from pathlib import Path


def test_llm_rag_model_integration():
    """Test LLM RAG Model integration with centralized RAG system"""
    print("🔍 Testing LLM RAG Model Integration...")

    try:
        from src.models.llm_rag_model import LLMRAGModel

        # Test with centralized RAG
        model = LLMRAGModel(rag_base_url="http://localhost:8000")

        # Check model info
        model_info = model.get_model_info()
        print(f"  ✅ Model Type: {model_info['model_type']}")
        print(f"  ✅ RAG System: {model_info['rag_system']}")
        print(f"  ✅ RAG Base URL: {model_info['rag_base_url']}")

        # Test prediction (will use fallback if RAG unavailable)
        text = "The organization maintains compliance with GDPR requirements"
        decision, confidence = model.predict(text)
        print(f"  ✅ Prediction: {decision} (confidence: {confidence:.2f})")

        # Test explanation
        explanation = model.explain_decision(text)
        print(f"  ✅ RAG System Used: {explanation['rag_system_used']}")

        return True

    except Exception as e:
        print(f"  ❌ LLM RAG Model integration failed: {e}")
        traceback.print_exc()
        return False


def test_evidence_verifier_integration():
    """Test Evidence Verification Agent integration with centralized RAG system"""
    print("\n🔍 Testing Evidence Verification Agent Integration...")

    try:
        from src.evidence_verifier import EvidenceVerificationAgent

        # Test with centralized RAG
        agent = EvidenceVerificationAgent(rag_base_url="http://localhost:8000")

        # Check if RAG is available
        print(f"  ✅ RAG Available: {agent.rag_available}")
        print(f"  ✅ RAG Base URL: {agent.rag_base_url}")

        # Test verification (will use fallback if RAG unavailable)
        case_id = "TEST-RAG-001"
        reasoning = "This feature complies with GDPR requirements"
        evidence_spans = ["GDPR Article 7 consent mechanisms implemented"]
        regulation_references = ["GDPR"]

        result = agent.verify_case(
            case_id=case_id,
            reasoning=reasoning,
            evidence_spans=evidence_spans,
            regulation_references=regulation_references,
        )

        print(f"  ✅ Verification Complete: {result.final_decision}")
        print(f"  ✅ Auto-Approved: {result.auto_approved}")
        print(f"  ✅ Overall Score: {result.overall_score:.2f}")

        return True

    except Exception as e:
        print(f"  ❌ Evidence Verification Agent integration failed: {e}")
        traceback.print_exc()
        return False


def test_confidence_validator_integration():
    """Test Confidence Validator Agent integration with centralized RAG system"""
    print("\n🔍 Testing Confidence Validator Agent Integration...")

    try:
        from src.agents import ConfidenceValidatorAgent

        # Test with centralized RAG
        agent = ConfidenceValidatorAgent(rag_base_url="http://localhost:8000")

        # Check RAG base URL
        print(f"  ✅ RAG Base URL: {agent.rag_base_url}")

        # Test validation (will use fallback if RAG unavailable)
        text = "The platform implements age verification for users under 18"
        result = agent.validate_case(text, case_id="TEST-RAG-002")

        print(f"  ✅ Validation Complete: {result.ensemble_decision}")
        print(f"  ✅ Ensemble Confidence: {result.ensemble_confidence:.2f}")
        print(f"  ✅ Auto-Approved: {result.auto_approved}")
        print(f"  ✅ Agreement Level: {result.agreement_level}")

        # Check LLM+RAG model info
        llm_rag_info = result.predictions["LLM+RAG"].model_info
        print(f"  ✅ LLM+RAG RAG System: {llm_rag_info.get('rag_system', 'N/A')}")

        return True

    except Exception as e:
        print(f"  ❌ Confidence Validator Agent integration failed: {e}")
        traceback.print_exc()
        return False


def test_active_learning_integration():
    """Test Active Learning Agent integration with centralized RAG system"""
    print("\n🔍 Testing Active Learning Agent Integration...")

    try:
        from src.agents import ActiveLearningAgent

        # Test with centralized RAG
        agent = ActiveLearningAgent(rag_base_url="http://localhost:8000")

        # Check RAG system status
        rag_status = agent.get_rag_system_status()
        print(f"  ✅ RAG Available: {rag_status['rag_available']}")
        print(f"  ✅ RAG Base URL: {rag_status['rag_base_url']}")
        print(f"  ✅ RAG Client Initialized: {rag_status['rag_client_initialized']}")

        # Test pattern analysis with RAG (if available)
        if agent.patterns:
            pattern = agent.patterns[0]
            rag_analysis = agent.analyze_patterns_with_rag(pattern)
            print(f"  ✅ RAG Pattern Analysis: {rag_analysis['enhanced_analysis']}")
            if rag_analysis.get("regulatory_context"):
                print(
                    f"  ✅ Regulatory Context Found: {len(rag_analysis['regulatory_context'])} results"
                )
        else:
            print("  ⚠️ No patterns available for RAG analysis test")

        return True

    except Exception as e:
        print(f"  ❌ Active Learning Agent integration failed: {e}")
        traceback.print_exc()
        return False


def test_centralized_rag_system():
    """Test the centralized RAG system directly"""
    print("\n🔍 Testing Centralized RAG System...")

    try:
        from sdk.client import RegulationClient

        # Test RAG client
        client = RegulationClient(base_url="http://localhost:8000")

        # Test health check
        health = client.health()
        print(f"  ✅ RAG System Health: {health.get('status', 'unknown')}")

        # Test basic retrieval
        query = "age verification requirements"
        response = client.retrieve(query=query, top_k=2)

        print(f"  ✅ RAG Retrieval: {len(response.results)} results")
        if response.results:
            print(f"  ✅ Top Result: {response.results[0].law_name}")
            print(f"  ✅ Jurisdiction: {response.results[0].jurisdiction}")

        return True

    except Exception as e:
        print(f"  ❌ Centralized RAG system test failed: {e}")
        print("  ⚠️ This is expected if the RAG service is not running")
        return False


def main():
    """Run all integration tests"""
    print("🚀 Testing All Agents with Centralized RAG System")
    print("=" * 60)

    test_results = []

    # Test centralized RAG system first
    rag_system_ok = test_centralized_rag_system()
    test_results.append(("Centralized RAG System", rag_system_ok))

    # Test all agents
    test_results.append(("LLM RAG Model", test_llm_rag_model_integration()))
    test_results.append(
        ("Evidence Verification Agent", test_evidence_verifier_integration())
    )
    test_results.append(
        ("Confidence Validator Agent", test_confidence_validator_integration())
    )
    test_results.append(("Active Learning Agent", test_active_learning_integration()))

    # Summary
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 60)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All agents successfully integrated with centralized RAG system!")
        return True
    else:
        print("⚠️ Some integration issues detected. Check the logs above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
