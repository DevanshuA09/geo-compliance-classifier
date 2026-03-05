#!/usr/bin/env python3
"""
Comprehensive Test Script for All Three Agents

This script tests the Confidence Validator Agent, Evidence Verification Agent,
and Active Learning Agent together to ensure they work as an integrated system.
"""

import uuid
from datetime import datetime, timedelta

from src.agents import ActiveLearningAgent, ConfidenceValidatorAgent
from src.evidence import EvidenceVerificationAgent


def test_confidence_validator():
    """Test the Confidence Validator Agent"""
    print("🔍 Testing Confidence Validator Agent...")
    print("-" * 50)

    try:
        # Initialize the confidence validator
        validator = ConfidenceValidatorAgent()

        # Test case
        test_text = (
            "Social media platform requires age verification for users under 18 in Utah"
        )
        case_id = f"CASE-{uuid.uuid4().hex[:8]}"

        # Validate the case
        result = validator.validate_case(test_text, case_id)

        print(f"✅ Confidence Validator Test Passed")
        print(f"   Case ID: {result.case_id}")
        print(f"   Final Decision: {result.final_decision}")
        print(f"   Auto-Approved: {result.auto_approved}")
        print(f"   Agreement Level: {result.agreement_level}")
        print(f"   Ensemble Confidence: {result.ensemble_confidence:.2f}")

        return True

    except Exception as e:
        print(f"❌ Confidence Validator Test Failed: {e}")
        return False


def test_evidence_verifier():
    """Test the Evidence Verification Agent"""
    print("\n🔍 Testing Evidence Verification Agent...")
    print("-" * 50)

    try:
        # Initialize the evidence verifier
        verifier = EvidenceVerificationAgent()

        # Test case
        case_id = f"VERIFY-{uuid.uuid4().hex[:8]}"
        reasoning_text = (
            "Feature violates Utah age verification requirements for users under 18"
        )
        evidence_spans = [
            {
                "text": "Users under 18 must provide age verification in Utah",
                "source": "Utah Social Media Regulation Act",
                "section": "Section 3.2",
            }
        ]
        regulation_references = ["Utah Social Media Regulation Act"]

        # Verify the case
        result = verifier.verify_case(
            case_id, reasoning_text, evidence_spans, regulation_references
        )

        print(f"✅ Evidence Verifier Test Passed")
        print(f"   Case ID: {result.case_id}")
        print(f"   Final Decision: {result.final_decision}")
        print(f"   Auto-Approved: {result.auto_approved}")
        print(f"   Overall Score: {result.overall_score:.2f}")
        print(f"   Alignment Score: {result.reasoning_alignment.alignment_score:.2f}")

        return True

    except Exception as e:
        print(f"❌ Evidence Verifier Test Failed: {e}")
        return False


def test_active_learning_agent():
    """Test the Active Learning Agent"""
    print("\n🔍 Testing Active Learning Agent...")
    print("-" * 50)

    try:
        # Initialize the active learning agent
        agent = ActiveLearningAgent()

        # Test case
        case_id = f"CORR-{uuid.uuid4().hex[:8]}"

        # Log a human correction
        result = agent.log_human_correction(
            case_id=case_id,
            original_prediction="Compliant",
            corrected_label="Non-Compliant",
            reviewer_reasoning="Utah age verification requirements not met for users under 18",
            feature_characteristics={
                "geographic": {"state": "Utah", "country": "USA"},
                "demographic": {"age_min": 13, "age_max": 17},
                "regulation_type": "Age Verification",
            },
            confidence_score=0.85,
            model_used="Legal-BERT",
            correction_type="label_correction",
        )

        # Get system status
        status = agent.get_system_status()

        print(f"✅ Active Learning Agent Test Passed")
        print(f"   Case ID: {result}")
        print(f"   Total Corrections: {status['total_corrections']}")
        print(f"   Total Patterns: {status['total_patterns']}")
        print(f"   Ready for Retraining: {status['ready_for_retraining']}")

        return True

    except Exception as e:
        print(f"❌ Active Learning Agent Test Failed: {e}")
        return False


def test_integrated_workflow():
    """Test an integrated workflow using all three agents"""
    print("\n🔍 Testing Integrated Workflow...")
    print("-" * 50)

    try:
        # Initialize all agents
        validator = ConfidenceValidatorAgent()
        verifier = EvidenceVerificationAgent()
        learner = ActiveLearningAgent()

        # Test case
        test_text = (
            "Social media platform requires age verification for users under 18 in Utah"
        )
        case_id = f"INTEGRATED-{uuid.uuid4().hex[:8]}"

        print(f"📋 Processing Case: {case_id}")
        print(f"   Text: {test_text}")

        # Step 1: Confidence Validation
        print(f"\n🔍 Step 1: Confidence Validation")
        validation_result = validator.validate_case(test_text, case_id)
        print(f"   Decision: {validation_result.final_decision}")
        print(f"   Confidence: {validation_result.ensemble_confidence:.2f}")
        print(f"   Auto-Approved: {validation_result.auto_approved}")

        # Step 2: Evidence Verification
        print(f"\n🔍 Step 2: Evidence Verification")
        reasoning_text = f"Feature classified as {validation_result.final_decision} with confidence {validation_result.ensemble_confidence:.2f}"
        evidence_spans = [
            {
                "text": "Users under 18 must provide age verification in Utah",
                "source": "Utah Social Media Regulation Act",
                "section": "Section 3.2",
            }
        ]
        regulation_references = ["Utah Social Media Regulation Act"]

        verification_result = verifier.verify_case(
            case_id, reasoning_text, evidence_spans, regulation_references
        )
        print(f"   Decision: {verification_result.final_decision}")
        print(f"   Score: {verification_result.overall_score:.2f}")
        print(f"   Auto-Approved: {verification_result.auto_approved}")

        # Step 3: Active Learning (if human review needed)
        if not validation_result.auto_approved or not verification_result.auto_approved:
            print(f"\n🔍 Step 3: Active Learning (Human Review)")

            # Simulate human correction
            human_correction = learner.log_human_correction(
                case_id=case_id,
                original_prediction=validation_result.final_decision,
                corrected_label="Non-Compliant",  # Human decides it's non-compliant
                reviewer_reasoning="Utah age verification requirements not properly implemented",
                feature_characteristics={
                    "geographic": {"state": "Utah", "country": "USA"},
                    "demographic": {"age_min": 13, "age_max": 17},
                    "regulation_type": "Age Verification",
                },
                confidence_score=validation_result.ensemble_confidence,
                model_used="Ensemble",
                correction_type="label_correction",
            )

            print(f"   Human Correction Logged: {human_correction}")

            # Check if pattern analysis was triggered
            status = learner.get_system_status()
            print(f"   Total Corrections: {status['total_corrections']}")
            print(f"   Patterns Identified: {status['total_patterns']}")

        print(f"\n✅ Integrated Workflow Test Passed")
        return True

    except Exception as e:
        print(f"❌ Integrated Workflow Test Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main test function"""
    print("🧪 Comprehensive Test Suite for All Three Agents")
    print("=" * 70)

    # Test results
    results = {}

    # Test each agent individually
    results["confidence_validator"] = test_confidence_validator()
    results["evidence_verifier"] = test_evidence_verifier()
    results["active_learning"] = test_active_learning_agent()

    # Test integrated workflow
    results["integrated_workflow"] = test_integrated_workflow()

    # Summary
    print(f"\n📊 Test Results Summary")
    print("=" * 50)

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")

    print(f"\n   Overall: {passed}/{total} tests passed")

    if passed == total:
        print(f"\n🎉 All tests passed! The system is fully operational.")
        print(f"   ✅ Confidence Validator Agent: Working")
        print(f"   ✅ Evidence Verification Agent: Working")
        print(f"   ✅ Active Learning Agent: Working")
        print(f"   ✅ Integrated Workflow: Working")
    else:
        print(f"\n⚠️  Some tests failed. Please check the implementation.")

    print(
        f"\n🚀 System Status: {'FULLY OPERATIONAL' if passed == total else 'NEEDS ATTENTION'}"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback

        traceback.print_exc()
