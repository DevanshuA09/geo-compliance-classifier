#!/usr/bin/env python3
"""
Demo script for the Confidence Validator Agent

This script demonstrates how the agent validates compliance predictions
using three different models and applies ensemble logic.
"""

import os
import sys

from src.agents import ConfidenceValidatorAgent


def main():
    """Main demo function"""
    print("🔍 Confidence Validator Agent Demo")
    print("=" * 50)

    # Initialize the validator agent
    # Note: Set OPENAI_API_KEY environment variable for LLM+RAG model
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print(
            "⚠️  Warning: OPENAI_API_KEY not set. LLM+RAG model will use fallback mode."
        )

    validator = ConfidenceValidatorAgent(openai_api_key=openai_api_key)

    # Display model status
    print("\n📊 Model Status:")
    model_status = validator.get_model_status()
    for model_name, status in model_status.items():
        print(f"  {model_name}: {status.get('status', 'Unknown')}")

    # Sample compliance cases for testing
    test_cases = [
        {
            "id": "CASE-001",
            "text": "The organization maintains full compliance with all applicable data protection regulations and regularly conducts compliance audits to ensure ongoing adherence to legal requirements.",
            "description": "Clear compliance statement",
        },
        {
            "id": "CASE-002",
            "text": "The company violated multiple safety regulations and failed to implement required safety protocols, resulting in significant penalties and enforcement actions.",
            "description": "Clear non-compliance statement",
        },
        {
            "id": "CASE-003",
            "text": "The project requires further assessment to determine compliance status with environmental regulations. Additional review may be necessary.",
            "description": "Unclear compliance status",
        },
        {
            "id": "CASE-004",
            "text": "Our financial reporting procedures are certified compliant with SEC requirements and we maintain all necessary documentation for regulatory review.",
            "description": "Financial compliance statement",
        },
        {
            "id": "CASE-005",
            "text": "The data processing activities may or may not comply with GDPR requirements depending on the specific use case and data subject consent.",
            "description": "Ambiguous compliance case",
        },
    ]

    print(f"\n🧪 Testing with {len(test_cases)} sample cases...")
    print("-" * 50)

    # Process each test case
    for case in test_cases:
        print(f"\n📋 {case['id']}: {case['description']}")
        print(f"Text: {case['text'][:80]}...")

        # Validate the case
        result = validator.validate_case(case["text"], case["id"])

        # Display results
        print(
            f"✅ Final Decision: {result.ensemble_decision} (Confidence: {result.ensemble_confidence:.2f})"
        )
        print(f"🔄 Auto-Approved: {'Yes' if result.auto_approved else 'No'}")
        print(f"🤝 Agreement Level: {result.agreement_level}")

        # Show individual model predictions
        print("  Model Predictions:")
        for model_name, prediction in result.predictions.items():
            status_emoji = (
                "✅"
                if prediction.confidence >= 0.85
                else "⚠️" if prediction.confidence >= 0.70 else "❌"
            )
            print(
                f"    {status_emoji} {model_name}: {prediction.decision} ({prediction.confidence:.2f})"
            )

        # Show flags if any
        if result.flags:
            print("  🚩 Flags:")
            for flag in result.flags:
                print(f"    - {flag}")

        print(f"  📝 Notes: {result.notes}")

    # Generate summary report
    print("\n📈 Generating Summary Report...")
    summary_df = validator.get_validation_summary()

    if not summary_df.empty:
        print("\n📊 Validation Summary:")
        print(summary_df.to_string(index=False))

    # Export results to markdown
    try:
        markdown_file = validator.export_results_markdown()
        print(f"\n💾 Results exported to: {markdown_file}")
    except Exception as e:
        print(f"\n❌ Error exporting results: {e}")

    # Final statistics
    total_cases = len(validator.validation_history)
    auto_approved = sum(1 for r in validator.validation_history if r.auto_approved)
    manual_review = total_cases - auto_approved

    print(f"\n📊 Final Statistics:")
    print(f"  Total Cases Processed: {total_cases}")
    print(f"  Auto-Approved: {auto_approved}")
    print(f"  Manual Review Required: {manual_review}")
    print(f"  Auto-Approval Rate: {(auto_approved/total_cases)*100:.1f}%")

    print("\n🎯 Demo Complete!")
    print("\nThe Confidence Validator Agent has successfully:")
    print("  ✓ Collected predictions from three different models")
    print("  ✓ Applied ensemble logic for decision aggregation")
    print("  ✓ Auto-approved high-confidence unanimous decisions")
    print("  ✓ Flagged cases requiring manual review")
    print("  ✓ Provided transparent reasoning and traceability")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()
