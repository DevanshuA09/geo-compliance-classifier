#!/usr/bin/env python3
"""
CLI for TikTok Feature Generator Agent

Usage:
python -m featuregen.cli --n 200 --geo EU,US-CA,US-FL --label_mix 0.4,0.3,0.3 --seed 42 --out ./out
"""

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from ignored.tiktok_feature_generator import TikTokFeatureGenerator


def parse_label_mix(label_mix_str: str) -> dict:
    """Parse label mix string into dictionary."""
    try:
        values = [float(x.strip()) for x in label_mix_str.split(",")]
        if len(values) != 3:
            raise ValueError("Label mix must have exactly 3 values")
        if abs(sum(values) - 1.0) > 0.01:
            raise ValueError("Label mix values must sum to 1.0")

        return {
            "Compliant": values[0],
            "Partially Compliant": values[1],
            "Non-Compliant": values[2],
        }
    except (ValueError, IndexError) as e:
        raise argparse.ArgumentTypeError(f"Invalid label mix format: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic TikTok features with geo-compliance labels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 100 features with default distribution
  python -m featuregen.cli --n 100 --out ./output
  
  # Generate 200 features for specific geos with custom label mix
  python -m featuregen.cli --n 200 --geo EU,US-CA,US-FL --label_mix 0.4,0.3,0.3 --out ./output
  
  # Generate features with specific seed for reproducibility
  python -m featuregen.cli --n 50 --seed 42 --out ./output --verbose
        """,
    )

    parser.add_argument(
        "--n",
        type=int,
        default=100,
        help="Number of features to generate (default: 100)",
    )

    parser.add_argument(
        "--geo",
        type=str,
        default="EU,US-CA,US-FL,USA",
        help="Comma-separated list of geo filters (default: EU,US-CA,US-FL,USA)",
    )

    parser.add_argument(
        "--label_mix",
        type=parse_label_mix,
        default="0.3,0.3,0.4",
        help="Label distribution as compliant,partial,non-compliant ratios (default: 0.3,0.3,0.4)",
    )

    parser.add_argument(
        "--domains",
        type=str,
        default=None,
        help="Comma-separated list of domains to focus on (optional)",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )

    parser.add_argument(
        "--out",
        type=str,
        default="./generated_features",
        help="Output directory (default: ./generated_features)",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging
    import logging

    level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")

    print("🚀 TikTok Feature Generator Agent")
    print("=" * 50)
    print(f"📊 Generating {args.n} features")
    print(f"🌍 Geographic filters: {args.geo}")
    print(f"🏷️  Label mix: {args.label_mix}")
    print(f"🎲 Seed: {args.seed}")
    print(f"📁 Output: {args.out}")
    print()

    # Parse arguments
    geo_filters = [g.strip() for g in args.geo.split(",")]
    domain_focus = None
    if args.domains:
        domain_focus = [d.strip() for d in args.domains.split(",")]

    # Initialize generator
    generator = TikTokFeatureGenerator(seed=args.seed)

    # Analyze seed data
    try:
        seed_analysis = generator.analyze_seed_data(
            "active_learning_data/corrections.json"
        )
        print(f"📚 Analyzed {seed_analysis['total_records']} seed records")
    except Exception as e:
        print(f"⚠️  Could not load seed data: {e}")
        print("📚 Using default distributions")

    # Generate features
    try:
        features = generator.generate_features(
            n=args.n,
            geo_filters=geo_filters,
            target_mix=args.label_mix,
            domain_focus=domain_focus,
        )

        # Save outputs
        jsonl_path, csv_path = generator.save_features(features, args.out)
        report_path = generator.generate_distribution_report(features, args.out)

        print(f"✅ Successfully generated {len(features)} features")
        print(f"📄 JSONL: {jsonl_path}")
        print(f"📄 CSV: {csv_path}")
        print(f"📄 Report: {report_path}")

        # Show example results
        print(f"\n🎯 Example Generated Features:")
        for i, feature in enumerate(features[:3], 1):
            geo_str = f"{feature.geo_country}"
            if feature.geo_state:
                geo_str += f"-{feature.geo_state}"

            print(f'{i}. [{geo_str}] "{feature.title}" → {feature.label}')
            print(
                f"   Reason: {feature.rationale[:80]}{'...' if len(feature.rationale) > 80 else ''}"
            )
            print(f"   Regulations: {', '.join(feature.implicated_regs)}")
            print()

        # Final statistics
        label_counts = {}
        for feature in features:
            label_counts[feature.label] = label_counts.get(feature.label, 0) + 1

        print(f"📊 Final Distribution:")
        for label, count in label_counts.items():
            percentage = (count / len(features)) * 100
            print(f"   {label}: {count} ({percentage:.1f}%)")

        return 0

    except Exception as e:
        print(f"❌ Generation failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
