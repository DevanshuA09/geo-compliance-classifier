#!/usr/bin/env python3
"""
Demo script for the Active Learning Agent

This script demonstrates how the agent tracks human corrections,
identifies patterns, and triggers retraining to reduce human review effort.
"""

import uuid
from datetime import datetime, timedelta

from src.agents import ActiveLearningAgent


def main():
    """Main demo function"""
    print("🔄 Active Learning Agent Demo")
    print("=" * 60)

    # Initialize the active learning agent
    agent = ActiveLearningAgent()

    # Display current status
    status = agent.get_system_status()
    print(f"\n📊 Current System Status:")
    print(f"  Total Corrections: {status['total_corrections']}")
    print(f"  Total Patterns: {status['total_patterns']}")
    print(f"  Correction Threshold: {status['correction_threshold']}")
    print(f"  Target Reduction Rate: {status['target_reduction_rate']:.1%}")
    print(
        f"  Ready for Retraining: {'Yes' if status['ready_for_retraining'] else 'No'}"
    )

    # Sample human corrections for testing
    sample_corrections = [
        {
            "case_id": f"CORR-{uuid.uuid4().hex[:8]}",
            "original_prediction": "Compliant",
            "corrected_label": "Non-Compliant",
            "reviewer_reasoning": "Feature violates Utah age verification requirements for users under 18",
            "feature_characteristics": {
                "geographic": {"state": "Utah", "country": "USA"},
                "demographic": {"age_min": 13, "age_max": 17},
                "regulation_type": "Age Verification",
                "feature_type": "Social Media",
            },
            "confidence_score": 0.85,
            "model_used": "Legal-BERT",
            "correction_type": "label_correction",
        },
        {
            "case_id": f"CORR-{uuid.uuid4().hex[:8]}",
            "original_prediction": "Compliant",
            "corrected_label": "Non-Compliant",
            "reviewer_reasoning": "Missing GDPR consent mechanisms for data processing",
            "feature_characteristics": {
                "geographic": {"region": "EU", "country": "Germany"},
                "demographic": {"age_min": 18, "age_max": 65},
                "regulation_type": "Data Protection",
                "feature_type": "User Registration",
            },
            "confidence_score": 0.78,
            "model_used": "Rules-Based",
            "correction_type": "label_correction",
        },
        {
            "case_id": f"CORR-{uuid.uuid4().hex[:8]}",
            "original_prediction": "Non-Compliant",
            "corrected_label": "Compliant",
            "reviewer_reasoning": "Feature correctly implements California privacy requirements",
            "feature_characteristics": {
                "geographic": {"state": "California", "country": "USA"},
                "demographic": {"age_min": 18, "age_max": 100},
                "regulation_type": "Privacy",
                "feature_type": "Data Collection",
            },
            "confidence_score": 0.92,
            "model_used": "LLM+RAG",
            "correction_type": "label_correction",
        },
        {
            "case_id": f"CORR-{uuid.uuid4().hex[:8]}",
            "original_prediction": "Compliant",
            "corrected_label": "Non-Compliant",
            "reviewer_reasoning": "Safety protocols not implemented for hazardous material handling",
            "feature_characteristics": {
                "geographic": {"state": "Texas", "country": "USA"},
                "demographic": {"age_min": 21, "age_max": 65},
                "regulation_type": "Safety",
                "feature_type": "Industrial Process",
            },
            "confidence_score": 0.88,
            "model_used": "Legal-BERT",
            "correction_type": "label_correction",
        },
        {
            "case_id": f"CORR-{uuid.uuid4().hex[:8]}",
            "original_prediction": "Unclear",
            "corrected_label": "Non-Compliant",
            "reviewer_reasoning": "Environmental impact assessment required but not conducted",
            "feature_characteristics": {
                "geographic": {"state": "Oregon", "country": "USA"},
                "demographic": {"age_min": 18, "age_max": 100},
                "regulation_type": "Environmental",
                "feature_type": "Construction Project",
            },
            "confidence_score": 0.65,
            "model_used": "Rules-Based",
            "correction_type": "label_correction",
        },
    ]

    print(f"\n🧪 Testing with {len(sample_corrections)} sample corrections...")
    print("-" * 60)

    # Log each correction
    for i, correction_data in enumerate(sample_corrections, 1):
        print(f"\n📝 Logging Correction {i}: {correction_data['case_id']}")
        print(
            f"Original: {correction_data['original_prediction']} → Corrected: {correction_data['corrected_label']}"
        )
        print(f"Reasoning: {correction_data['reviewer_reasoning'][:80]}...")
        print(f"Confidence: {correction_data['confidence_score']:.2f}")
        print(f"Model: {correction_data['model_used']}")

        # Log the correction
        case_id = agent.log_human_correction(
            case_id=correction_data["case_id"],
            original_prediction=correction_data["original_prediction"],
            corrected_label=correction_data["corrected_label"],
            reviewer_reasoning=correction_data["reviewer_reasoning"],
            feature_characteristics=correction_data["feature_characteristics"],
            confidence_score=correction_data["confidence_score"],
            model_used=correction_data["model_used"],
            correction_type=correction_data["correction_type"],
        )

        print(f"✅ Correction logged successfully")

    # Display updated status
    print(f"\n📊 Updated System Status:")
    updated_status = agent.get_system_status()
    print(f"  Total Corrections: {updated_status['total_corrections']}")
    print(f"  Total Patterns: {updated_status['total_patterns']}")
    print(
        f"  Ready for Retraining: {'Yes' if updated_status['ready_for_retraining'] else 'No'}"
    )

    # Display identified patterns
    if agent.patterns:
        print(f"\n🔍 Identified Correction Patterns:")
        for pattern in agent.patterns:
            print(f"  📊 {pattern.pattern_id}: {pattern.description}")
            print(f"     Type: {pattern.pattern_type}")
            print(f"     Frequency: {pattern.frequency} cases")
            print(f"     Severity: {pattern.severity_score:.2f}")
            if pattern.keywords:
                print(f"     Keywords: {', '.join(pattern.keywords)}")
            if pattern.geographic_factors:
                print(f"     Geographic: {', '.join(pattern.geographic_factors)}")
            print()

    # Calculate weekly metrics
    print(f"\n📈 Calculating Weekly Metrics...")
    week_start = datetime.now() - timedelta(days=7)
    weekly_metrics = agent.calculate_weekly_metrics(week_start)

    print(f"📅 Week of {weekly_metrics.week_start.strftime('%Y-%m-%d')}:")
    print(f"  Human Reviews Logged: {weekly_metrics.human_reviews_logged}")
    print(f"  Corrections Applied: {weekly_metrics.corrections_applied}")
    print(f"  Patterns Identified: {weekly_metrics.patterns_identified}")
    print(f"  Retraining Triggered: {weekly_metrics.retraining_triggered}")
    print(f"  Human Review Reduction: {weekly_metrics.human_review_reduction:.1%}")
    print(f"  Target Met: {'Yes' if weekly_metrics.target_met else 'No'}")
    print(f"  Notes: {weekly_metrics.notes}")

    # Generate weekly summary table
    print(f"\n📊 Weekly Summary Table:")
    summary_table = agent.get_weekly_summary_table()
    print(summary_table)

    # Display system insights
    print(f"\n💡 System Insights:")
    if updated_status["total_corrections"] >= 10:
        print(f"  ✅ Sufficient corrections for pattern analysis")
    else:
        print(
            f"  ⏳ Need {10 - updated_status['total_corrections']} more corrections for pattern analysis"
        )

    if updated_status["ready_for_retraining"]:
        print(f"  🚀 Ready to trigger model retraining!")
    else:
        print(
            f"  ⏳ Need {updated_status['correction_threshold'] - updated_status['total_corrections']} more corrections for retraining"
        )

    print(f"\n🎯 Demo Complete!")
    print(f"\nThe Active Learning Agent has successfully:")
    print(f"  ✓ Logged human corrections with full metadata")
    print(f"  ✓ Identified systematic misclassification patterns")
    print(f"  ✓ Calculated weekly performance metrics")
    print(f"  ✓ Prepared for automatic retraining workflows")
    print(f"  ✓ Tracked progress toward 15% weekly reduction target")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()
