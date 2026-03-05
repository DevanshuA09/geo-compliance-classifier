#!/usr/bin/env python3
"""
Demo script for the Evidence Verification Agent

This script demonstrates how the agent validates reasoning against evidence spans
and regulation texts to ensure defensible compliance decisions.
"""

import os

from src.evidence_verifier import EvidenceVerificationAgent


def main():
    """Main demo function"""
    print("🔍 Evidence Verification Agent Demo")
    print("=" * 60)

    # Initialize the evidence verifier
    verifier = EvidenceVerificationAgent()

    # Display available regulations
    print("\n📚 Available Regulations:")
    for reg_name, reg_data in verifier.regulation_database.items():
        print(f"  📖 {reg_name} ({len(reg_data['content'])} chars)")

    # Sample test cases for evidence verification
    test_cases = [
        {
            "id": "EVIDENCE-001",
            "reasoning": "The feature complies with data protection regulations by implementing user consent mechanisms and data minimization principles.",
            "evidence_spans": [
                {
                    "text": "Organizations must obtain explicit user consent before processing personal data and shall implement data minimization practices.",
                    "start_pos": 0,
                    "end_pos": 100,
                    "source": "GDPR_Article_7",
                    "regulation_reference": "GDPR",
                    "confidence": 0.95,
                }
            ],
            "regulation_references": ["GDPR"],
            "description": "Strong alignment with specific regulation",
        },
        {
            "id": "EVIDENCE-002",
            "reasoning": "This feature violates safety regulations by not implementing required safety protocols.",
            "evidence_spans": [
                {
                    "text": "All systems must implement safety protocols as required by Section 3.2 of the Safety Standards Act.",
                    "start_pos": 0,
                    "end_pos": 80,
                    "source": "Safety_Standards_Act",
                    "regulation_reference": "Safety Standards Act",
                    "confidence": 0.90,
                }
            ],
            "regulation_references": ["Safety Standards Act"],
            "description": "Clear violation with specific regulation reference",
        },
        {
            "id": "EVIDENCE-003",
            "reasoning": "The feature may or may not comply with environmental regulations depending on implementation details.",
            "evidence_spans": [
                {
                    "text": "Environmental impact assessments are generally required for new projects, but specific requirements may vary.",
                    "start_pos": 0,
                    "end_pos": 90,
                    "source": "Environmental_Protection_Act",
                    "regulation_reference": "Environmental Protection Act",
                    "confidence": 0.60,
                }
            ],
            "regulation_references": ["Environmental Protection Act"],
            "description": "Ambiguous compliance with generic language",
        },
        {
            "id": "EVIDENCE-004",
            "reasoning": "This feature is fully compliant with financial reporting requirements and maintains all necessary documentation.",
            "evidence_spans": [
                {
                    "text": "Financial institutions shall maintain accurate records and submit quarterly reports as mandated by Section 15 of the Financial Services Act.",
                    "start_pos": 0,
                    "end_pos": 120,
                    "source": "Financial_Services_Act",
                    "regulation_reference": "Financial Services Act",
                    "confidence": 0.95,
                },
                {
                    "text": "All documentation must be retained for a minimum of 7 years as per regulatory requirements.",
                    "start_pos": 0,
                    "end_pos": 70,
                    "source": "Record_Keeping_Regulations",
                    "regulation_reference": "Record Keeping Regulations",
                    "confidence": 0.85,
                },
            ],
            "regulation_references": [
                "Financial Services Act",
                "Record Keeping Regulations",
            ],
            "description": "Multiple strong evidence spans with specific regulations",
        },
        {
            "id": "EVIDENCE-005",
            "reasoning": "The feature implements advanced security measures that exceed regulatory requirements.",
            "evidence_spans": [
                {
                    "text": "Security measures should be appropriate for the risk level and may include encryption and access controls.",
                    "start_pos": 0,
                    "end_pos": 90,
                    "source": "Cybersecurity_Framework",
                    "regulation_reference": "Cybersecurity Framework",
                    "confidence": 0.70,
                }
            ],
            "regulation_references": ["Cybersecurity Framework"],
            "description": "Weak evidence with generic language",
        },
    ]

    print(f"\n🧪 Testing with {len(test_cases)} evidence verification cases...")
    print("-" * 60)

    # Process each test case
    for case in test_cases:
        print(f"\n📋 {case['id']}: {case['description']}")
        print(f"Reasoning: {case['reasoning'][:80]}...")

        # Verify the case
        result = verifier.verify_case(
            case_id=case["id"],
            reasoning_text=case["reasoning"],
            evidence_spans=case["evidence_spans"],
            regulation_references=case["regulation_references"],
        )

        # Display results
        print(f"✅ Final Decision: {result.final_decision}")
        print(f"🔄 Auto-Approved: {'Yes' if result.auto_approved else 'No'}")
        print(f"📊 Overall Score: {result.overall_score:.2f}")

        # Show alignment details
        print(
            f"  🤝 Reasoning-Evidence Alignment: {result.reasoning_validation.alignment_score:.2f}"
        )
        print(
            f"  📖 Regulation Mapping Valid: {'Yes' if result.regulation_mapping_valid else 'No'}"
        )

        # Show evidence quality
        avg_quality = sum(eq.quality_score for eq in result.evidence_quality) / max(
            1, len(result.evidence_quality)
        )
        print(f"  🎯 Evidence Quality: {avg_quality:.2f}")

        # Show individual evidence spans
        print("  📝 Evidence Spans:")
        for eq in result.evidence_quality:
            status_emoji = (
                "✅"
                if eq.quality_score >= 0.8
                else "⚠️" if eq.quality_score >= 0.6 else "❌"
            )
            print(
                f"    {status_emoji} {eq.span.source}: {eq.quality_level} ({eq.quality_score:.2f})"
            )
            print(f"      - {eq.quality_notes}")

        # Show flags if any
        if result.flags:
            print("  🚩 Flags:")
            for flag in result.flags:
                print(f"    - {flag}")

        print(f"  📋 Notes: {result.notes}")

    # Generate verification summary
    print("\n📈 Generating Verification Summary...")
    summary = verifier.get_verification_summary()
    print(summary)

    # Export results to markdown
    try:
        markdown_file = verifier.export_verification_results()
        print(f"\n💾 Results exported to: {markdown_file}")
    except Exception as e:
        print(f"\n❌ Error exporting results: {e}")

    # Final statistics
    total_cases = len(verifier.verification_history)
    auto_approved = sum(1 for r in verifier.verification_history if r.auto_approved)
    manual_review = total_cases - auto_approved

    print(f"\n📊 Final Statistics:")
    print(f"  Total Cases Processed: {total_cases}")
    print(f"  Auto-Approved: {auto_approved}")
    print(f"  Manual Review Required: {manual_review}")
    print(f"  Auto-Approval Rate: {(auto_approved/total_cases)*100:.1f}%")

    print("\n🎯 Demo Complete!")
    print("\nThe Evidence Verification Agent has successfully:")
    print("  ✓ Validated reasoning-evidence alignment")
    print("  ✓ Verified regulation mappings against actual texts")
    print("  ✓ Assessed evidence quality and specificity")
    print("  ✓ Auto-approved strongly aligned cases")
    print("  ✓ Flagged problematic cases for manual review")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()
