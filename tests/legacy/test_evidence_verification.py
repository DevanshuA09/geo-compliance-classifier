#!/usr/bin/env python3
"""
Test script for Evidence Verification Agent with realistic scenarios

This script demonstrates successful evidence verification cases and shows
how the system handles different types of evidence and reasoning.
"""

from src.evidence import EvidenceVerificationAgent


def test_strong_alignment_case():
    """Test case with strong reasoning-evidence alignment"""
    print("🧪 Testing Strong Alignment Case")
    print("-" * 50)

    verifier = EvidenceVerificationAgent()

    # Create a case where reasoning directly references evidence
    reasoning = "The feature implements user consent mechanisms as required by GDPR Article 7, which mandates that organizations must obtain explicit user consent before processing personal data."

    evidence_spans = [
        {
            "text": "Organizations must obtain explicit user consent before processing personal data and shall implement data minimization practices.",
            "start_pos": 0,
            "end_pos": 100,
            "source": "GDPR_Article_7",
            "regulation_reference": "GDPR_Article_7",
            "confidence": 0.95,
        }
    ]

    regulation_references = ["GDPR_Article_7"]

    result = verifier.verify_case(
        case_id="STRONG-001",
        reasoning_text=reasoning,
        evidence_spans=evidence_spans,
        regulation_references=regulation_references,
    )

    print(f"Reasoning: {reasoning}")
    print(f"Evidence: {evidence_spans[0]['text']}")
    print(f"Final Decision: {result.final_decision}")
    print(f"Auto-Approved: {'Yes' if result.auto_approved else 'No'}")
    print(f"Overall Score: {result.overall_score:.2f}")
    print(f"Alignment Score: {result.reasoning_validation.alignment_score:.2f}")
    print(f"Regulation Valid: {'Yes' if result.regulation_mapping_valid else 'No'}")
    print(
        f"Evidence Quality: {sum(eq.quality_score for eq in result.evidence_quality) / len(result.evidence_quality):.2f}"
    )

    if result.flags:
        print("Flags:", "; ".join(result.flags))

    print(f"Notes: {result.notes}")
    print()


def test_specific_regulation_case():
    """Test case with specific regulation reference"""
    print("🧪 Testing Specific Regulation Case")
    print("-" * 50)

    verifier = EvidenceVerificationAgent()

    reasoning = "The system implements safety protocols as mandated by Section 3.2 of the Safety Standards Act, which requires emergency shutdown procedures and personal protective equipment."

    evidence_spans = [
        {
            "text": "All systems must implement safety protocols as required by Section 3.2 of the Safety Standards Act. These protocols shall include, but are not limited to: Emergency shutdown procedures, Personal protective equipment requirements, Training and certification requirements, Regular safety inspections and audits",
            "start_pos": 0,
            "end_pos": 200,
            "source": "Safety_Standards_Act",
            "regulation_reference": "Safety_Standards_Act",
            "confidence": 0.95,
        }
    ]

    regulation_references = ["Safety_Standards_Act"]

    result = verifier.verify_case(
        case_id="SPECIFIC-001",
        reasoning_text=reasoning,
        evidence_spans=evidence_spans,
        regulation_references=regulation_references,
    )

    print(f"Reasoning: {reasoning}")
    print(f"Evidence: {evidence_spans[0]['text'][:100]}...")
    print(f"Final Decision: {result.final_decision}")
    print(f"Auto-Approved: {'Yes' if result.auto_approved else 'No'}")
    print(f"Overall Score: {result.overall_score:.2f}")
    print(f"Alignment Score: {result.reasoning_validation.alignment_score:.2f}")
    print(f"Regulation Valid: {'Yes' if result.regulation_mapping_valid else 'No'}")
    print(
        f"Evidence Quality: {sum(eq.quality_score for eq in result.evidence_quality) / len(result.evidence_quality):.2f}"
    )

    if result.flags:
        print("Flags:", "; ".join(result.flags))

    print(f"Notes: {result.notes}")
    print()


def test_multiple_evidence_case():
    """Test case with multiple evidence spans"""
    print("🧪 Testing Multiple Evidence Case")
    print("-" * 50)

    verifier = EvidenceVerificationAgent()

    reasoning = "The feature complies with both data protection and safety requirements by implementing consent mechanisms and safety protocols."

    evidence_spans = [
        {
            "text": "Organizations must obtain explicit user consent before processing personal data and shall implement data minimization practices.",
            "start_pos": 0,
            "end_pos": 100,
            "source": "GDPR_Article_7",
            "regulation_reference": "GDPR_Article_7",
            "confidence": 0.90,
        },
        {
            "text": "All systems must implement safety protocols as required by Section 3.2 of the Safety Standards Act.",
            "start_pos": 0,
            "end_pos": 80,
            "source": "Safety_Standards_Act",
            "regulation_reference": "Safety_Standards_Act",
            "confidence": 0.90,
        },
    ]

    regulation_references = ["GDPR_Article_7", "Safety_Standards_Act"]

    result = verifier.verify_case(
        case_id="MULTIPLE-001",
        reasoning_text=reasoning,
        evidence_spans=evidence_spans,
        regulation_references=regulation_references,
    )

    print(f"Reasoning: {reasoning}")
    print(f"Evidence Spans: {len(evidence_spans)}")
    for i, span in enumerate(evidence_spans):
        print(f"  {i+1}. {span['text'][:60]}...")

    print(f"Final Decision: {result.final_decision}")
    print(f"Auto-Approved: {'Yes' if result.auto_approved else 'No'}")
    print(f"Overall Score: {result.overall_score:.2f}")
    print(f"Alignment Score: {result.reasoning_validation.alignment_score:.2f}")
    print(f"Regulation Valid: {'Yes' if result.regulation_mapping_valid else 'No'}")
    print(
        f"Evidence Quality: {sum(eq.quality_score for eq in result.evidence_quality) / len(result.evidence_quality):.2f}"
    )

    if result.flags:
        print("Flags:", "; ".join(result.flags))

    print(f"Notes: {result.notes}")
    print()


def test_weak_evidence_case():
    """Test case with weak evidence to demonstrate flagging"""
    print("🧪 Testing Weak Evidence Case")
    print("-" * 50)

    verifier = EvidenceVerificationAgent()

    reasoning = "The feature may comply with environmental standards through general best practices."

    evidence_spans = [
        {
            "text": "Environmental impact assessments are generally required for new projects, but specific requirements may vary depending on the scope and potential environmental impact of the project.",
            "start_pos": 0,
            "end_pos": 120,
            "source": "Environmental_Protection_Act",
            "regulation_reference": "Environmental_Protection_Act",
            "confidence": 0.50,
        }
    ]

    regulation_references = ["Environmental_Protection_Act"]

    result = verifier.verify_case(
        case_id="WEAK-001",
        reasoning_text=reasoning,
        evidence_spans=evidence_spans,
        regulation_references=regulation_references,
    )

    print(f"Reasoning: {reasoning}")
    print(f"Evidence: {evidence_spans[0]['text']}")
    print(f"Final Decision: {result.final_decision}")
    print(f"Auto-Approved: {'Yes' if result.auto_approved else 'No'}")
    print(f"Overall Score: {result.overall_score:.2f}")
    print(f"Alignment Score: {result.reasoning_validation.alignment_score:.2f}")
    print(f"Regulation Valid: {'Yes' if result.regulation_mapping_valid else 'No'}")
    print(
        f"Evidence Quality: {sum(eq.quality_score for eq in result.evidence_quality) / len(result.evidence_quality):.2f}"
    )

    if result.flags:
        print("Flags:", "; ".join(result.flags))

    print(f"Notes: {result.notes}")
    print()


def main():
    """Run all test scenarios"""
    print("🔍 Evidence Verification Test Suite")
    print("=" * 60)

    # Run test scenarios
    test_strong_alignment_case()
    test_specific_regulation_case()
    test_multiple_evidence_case()
    test_weak_evidence_case()

    print("✅ All tests completed!")
    print("\nKey Insights:")
    print("  • Strong alignment + valid regulations + quality evidence → Auto-approval")
    print("  • Weak evidence or misalignment → Manual review required")
    print("  • Multiple evidence spans can strengthen cases")
    print("  • Regulation mapping validation prevents false references")


if __name__ == "__main__":
    main()
