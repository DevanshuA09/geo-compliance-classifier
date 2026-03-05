"""
Comprehensive integration tests for the centralized RAG system.
"""

import os
import sys
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.agents import (ActiveLearningAgent, ConfidenceValidatorAgent,
                             EvidenceVerificationAgent)
    from core.rag import CentralizedRAGClient, CentralizedRAGService

    IMPORTS_SUCCESS = True
except ImportError as e:
    print(f"❌ Import failed: {e}")
    IMPORTS_SUCCESS = False


def test_centralized_rag_client():
    """Test the centralized RAG client."""
    print("\n🔍 Testing Centralized RAG Client...")

    try:
        # Test client initialization
        client = CentralizedRAGClient(base_url="http://localhost:8000")
        print("✅ Centralized RAG client initialized successfully")

        # Test availability check
        is_available = client.is_available()
        print(f"📡 RAG service available: {is_available}")

        # Test health check
        health = client.health()
        print(f"🏥 Health status: {health}")

        # Test system info
        info = client.get_system_info()
        print(f"ℹ️  System info: {info}")

        return True

    except Exception as e:
        print(f"❌ Centralized RAG client test failed: {e}")
        return False


def test_evidence_verification_agent():
    """Test the Evidence Verification Agent with centralized RAG."""
    print("\n🔍 Testing Evidence Verification Agent...")

    try:
        # Initialize agent
        agent = EvidenceVerificationAgent(rag_base_url="http://localhost:8000")
        print("✅ Evidence Verification Agent initialized successfully")

        # Test evidence verification
        text = "This organization complies with all applicable regulations and maintains proper documentation."
        regulation_refs = ["GENERAL_COMPLIANCE", "DATA_PROTECTION"]

        mappings = agent.verify_evidence(text, regulation_refs)
        print(f"✅ Evidence verification completed: {len(mappings)} mappings")

        # Test verification stats
        stats = agent.get_verification_stats()
        print(f"📊 Verification stats: {stats}")

        # Test RAG integration status
        rag_status = agent.get_rag_system_status()
        print(f"🔗 RAG integration status: {rag_status}")

        return True

    except Exception as e:
        print(f"❌ Evidence Verification Agent test failed: {e}")
        return False


def test_active_learning_agent():
    """Test the Active Learning Agent with centralized RAG."""
    print("\n🔍 Testing Active Learning Agent...")

    try:
        # Initialize agent
        agent = ActiveLearningAgent(rag_base_url="http://localhost:8000")
        print("✅ Active Learning Agent initialized successfully")

        # Test recording corrections
        correction_id = agent.record_correction(
            text="Sample compliance text",
            original_prediction="Compliant",
            corrected_prediction="Non-Compliant",
            confidence=0.9,
            reviewer_notes="Regulatory violation identified",
        )
        print(f"✅ Correction recorded: {correction_id}")

        # Test recording feedback
        feedback_id = agent.record_feedback(
            text="Another compliance example",
            original_prediction="Unclear",
            corrected_prediction="Compliant",
            confidence=0.8,
            reviewer_notes="Clear compliance indicators present",
        )
        print(f"✅ Feedback recorded: {feedback_id}")

        # Test pattern analysis
        result = agent.analyze_patterns()
        print(f"✅ Pattern analysis completed: {result.patterns_identified} patterns")

        # Test learning stats
        stats = agent.get_learning_stats()
        print(f"📊 Learning stats: {stats}")

        # Test RAG system status
        rag_status = agent.get_rag_system_status()
        print(f"🔗 RAG integration status: {rag_status}")

        return True

    except Exception as e:
        print(f"❌ Active Learning Agent test failed: {e}")
        return False


def test_rag_service_integration():
    """Test the centralized RAG service integration."""
    print("\n🔍 Testing Centralized RAG Service Integration...")

    try:
        # Test service initialization
        service = CentralizedRAGService()
        print("✅ Centralized RAG service initialized successfully")

        # Test health check
        health = service.health_check()
        print(f"🏥 Service health: {health}")

        # Test performance stats
        stats = service.get_performance_stats()
        print(f"📊 Performance stats: {stats}")

        return True

    except Exception as e:
        print(f"❌ RAG service integration test failed: {e}")
        return False


def test_end_to_end_workflow():
    """Test end-to-end workflow with all agents."""
    print("\n🔍 Testing End-to-End Workflow...")

    try:
        # Initialize all agents
        evidence_agent = EvidenceVerificationAgent(rag_base_url="http://localhost:8000")
        learning_agent = ActiveLearningAgent(rag_base_url="http://localhost:8000")

        print("✅ All agents initialized successfully")

        # Test text
        test_text = "The organization maintains compliance with all applicable regulations and conducts regular audits."

        # Step 1: Evidence verification
        regulation_refs = ["GENERAL_COMPLIANCE", "AUDIT_REQUIREMENTS"]
        evidence_mappings = evidence_agent.verify_evidence(test_text, regulation_refs)
        print(f"✅ Evidence verification: {len(evidence_mappings)} mappings")

        # Step 2: Active learning (record correction)
        correction_id = learning_agent.record_correction(
            text=test_text,
            original_prediction="Unclear",
            corrected_prediction="Compliant",
            confidence=0.9,
            reviewer_notes="Clear compliance indicators present",
        )
        print(f"✅ Correction recorded: {correction_id}")

        # Step 3: Pattern analysis
        learning_result = learning_agent.analyze_patterns()
        print(f"✅ Pattern analysis: {learning_result.patterns_identified} patterns")

        print("✅ End-to-end workflow completed successfully")
        return True

    except Exception as e:
        print(f"❌ End-to-end workflow test failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print("🚀 Starting Centralized RAG System Integration Tests")
    print("=" * 60)

    if not IMPORTS_SUCCESS:
        print("❌ Cannot run tests due to import failures")
        return False

    test_results = []

    # Test individual components
    test_results.append(("Centralized RAG Client", test_centralized_rag_client()))
    test_results.append(
        ("Evidence Verification Agent", test_evidence_verification_agent())
    )
    test_results.append(("Active Learning Agent", test_active_learning_agent()))
    test_results.append(("RAG Service Integration", test_rag_service_integration()))

    # Test end-to-end workflow
    test_results.append(("End-to-End Workflow", test_end_to_end_workflow()))

    # Print summary
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

    success_rate = (passed / total) * 100
    print(f"📈 Success Rate: {success_rate:.1f}%")

    if success_rate >= 80:
        print("🎉 Integration tests completed successfully!")
        return True
    else:
        print("⚠️  Some integration tests failed. Check the output above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
