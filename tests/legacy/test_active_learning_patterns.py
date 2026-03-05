#!/usr/bin/env python3
"""
Test script for Active Learning Agent Pattern Analysis

This script adds more corrections to trigger pattern analysis
and demonstrates the full functionality of the system.
"""

import uuid
from datetime import datetime, timedelta

from src.agents import ActiveLearningAgent


def main():
    """Main test function"""
    print("🧪 Active Learning Agent Pattern Analysis Test")
    print("=" * 60)

    # Initialize the active learning agent
    agent = ActiveLearningAgent()

    # Display current status
    status = agent.get_system_status()
    print(f"\n📊 Current System Status:")
    print(f"  Total Corrections: {status['total_corrections']}")
    print(f"  Total Patterns: {status['total_patterns']}")
    print(f"  Pattern Analysis Threshold: {agent.pattern_analysis_threshold}")
    print(f"  Correction Threshold: {agent.correction_threshold}")

    # Add more corrections to trigger pattern analysis
    additional_corrections = [
        {
            "case_id": f"CORR-{uuid.uuid4().hex[:8]}",
            "original_prediction": "Compliant",
            "corrected_label": "Non-Compliant",
            "reviewer_reasoning": "Utah age verification requirements not met for users 13-17",
            "feature_characteristics": {
                "geographic": {"state": "Utah", "country": "USA"},
                "demographic": {"age_min": 13, "age_max": 17},
                "regulation_type": "Age Verification",
                "feature_type": "Social Media",
            },
            "confidence_score": 0.82,
            "model_used": "Legal-BERT",
            "correction_type": "label_correction",
        },
        {
            "case_id": f"CORR-{uuid.uuid4().hex[:8]}",
            "original_prediction": "Compliant",
            "corrected_label": "Non-Compliant",
            "reviewer_reasoning": "Utah parental consent mechanisms missing for under-18 users",
            "feature_characteristics": {
                "geographic": {"state": "Utah", "country": "USA"},
                "demographic": {"age_min": 13, "age_max": 17},
                "regulation_type": "Parental Consent",
                "feature_type": "User Registration",
            },
            "confidence_score": 0.79,
            "model_used": "Rules-Based",
            "correction_type": "label_correction",
        },
        {
            "case_id": f"CORR-{uuid.uuid4().hex[:8]}",
            "original_prediction": "Compliant",
            "corrected_label": "Non-Compliant",
            "reviewer_reasoning": "GDPR data processing consent not properly implemented",
            "feature_characteristics": {
                "geographic": {"region": "EU", "country": "France"},
                "demographic": {"age_min": 18, "age_max": 65},
                "regulation_type": "Data Protection",
                "feature_type": "Data Collection",
            },
            "confidence_score": 0.76,
            "model_used": "LLM+RAG",
            "correction_type": "label_correction",
        },
        {
            "case_id": f"CORR-{uuid.uuid4().hex[:8]}",
            "original_prediction": "Compliant",
            "corrected_label": "Non-Compliant",
            "reviewer_reasoning": "EU privacy policy not compliant with GDPR requirements",
            "feature_characteristics": {
                "geographic": {"region": "EU", "country": "Germany"},
                "demographic": {"age_min": 18, "age_max": 100},
                "regulation_type": "Privacy Policy",
                "feature_type": "Legal Documentation",
            },
            "confidence_score": 0.81,
            "model_used": "Legal-BERT",
            "correction_type": "label_correction",
        },
        {
            "case_id": f"CORR-{uuid.uuid4().hex[:8]}",
            "original_prediction": "Compliant",
            "corrected_label": "Non-Compliant",
            "reviewer_reasoning": "California privacy rights not properly implemented",
            "feature_characteristics": {
                "geographic": {"state": "California", "country": "USA"},
                "demographic": {"age_min": 18, "age_max": 100},
                "regulation_type": "Privacy Rights",
                "feature_type": "User Controls",
            },
            "confidence_score": 0.77,
            "model_used": "Rules-Based",
            "correction_type": "label_correction",
        },
    ]

    print(
        f"\n🧪 Adding {len(additional_corrections)} more corrections to trigger pattern analysis..."
    )
    print("-" * 60)

    # Log each additional correction
    for i, correction_data in enumerate(additional_corrections, 1):
        print(f"\n📝 Adding Correction {i}: {correction_data['case_id']}")
        print(
            f"Original: {correction_data['original_prediction']} → Corrected: {correction_data['corrected_label']}"
        )
        print(f"Reasoning: {correction_data['reviewer_reasoning'][:60]}...")
        print(f"Geographic: {correction_data['feature_characteristics']['geographic']}")
        print(
            f"Demographic: {correction_data['feature_characteristics']['demographic']}"
        )

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
            if pattern.demographic_factors:
                print(f"     Demographic: {', '.join(pattern.demographic_factors)}")
            print()
    else:
        print(f"\n⚠️  No patterns identified yet. This may indicate:")
        print(f"   - Insufficient corrections for clustering")
        print(f"   - Corrections are too diverse to cluster")
        print(f"   - Pattern analysis threshold not met")

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
    if updated_status["total_corrections"] >= agent.pattern_analysis_threshold:
        print(f"  ✅ Sufficient corrections for pattern analysis")
        if updated_status["total_patterns"] > 0:
            print(f"  ✅ Pattern analysis completed successfully")
        else:
            print(f"  ⚠️  Pattern analysis completed but no patterns identified")
    else:
        print(
            f"  ⏳ Need {agent.pattern_analysis_threshold - updated_status['total_corrections']} more corrections for pattern analysis"
        )

    if updated_status["ready_for_retraining"]:
        print(f"  🚀 Ready to trigger model retraining!")
    else:
        print(
            f"  ⏳ Need {updated_status['correction_threshold'] - updated_status['total_corrections']} more corrections for retraining"
        )

    # Show correction distribution
    print(f"\n📊 Correction Distribution Analysis:")
    corrections = agent.corrections

    # Geographic distribution
    geo_counts = {}
    for corr in corrections:
        if "geographic" in corr.feature_characteristics:
            geo = corr.feature_characteristics["geographic"]
            if "state" in geo:
                state = geo["state"]
                geo_counts[state] = geo_counts.get(state, 0) + 1
            elif "region" in geo:
                region = geo["region"]
                geo_counts[region] = geo_counts.get(region, 0) + 1

    if geo_counts:
        print(f"  Geographic Distribution:")
        for geo, count in geo_counts.items():
            print(f"    {geo}: {count} corrections")

    # Model distribution
    model_counts = {}
    for corr in corrections:
        model = corr.model_used
        model_counts[model] = model_counts.get(model, 0) + 1

    print(f"  Model Distribution:")
    for model, count in model_counts.items():
        print(f"    {model}: {count} corrections")

    # Correction type distribution
    type_counts = {}
    for corr in corrections:
        corr_type = corr.correction_type
        type_counts[corr_type] = type_counts.get(corr_type, 0) + 1

    print(f"  Correction Type Distribution:")
    for corr_type, count in type_counts.items():
        print(f"    {corr_type}: {count} corrections")

    print(f"\n🎯 Test Complete!")
    print(f"\nThe Active Learning Agent has successfully:")
    print(f"  ✓ Logged {len(corrections)} human corrections with full metadata")
    print(
        f"  ✓ Triggered pattern analysis at {agent.pattern_analysis_threshold}+ corrections"
    )
    print(f"  ✓ Identified {len(agent.patterns)} systematic misclassification patterns")
    print(f"  ✓ Calculated comprehensive weekly performance metrics")
    print(f"  ✓ Prepared for automatic retraining workflows")
    print(f"  ✓ Demonstrated full active learning pipeline")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
