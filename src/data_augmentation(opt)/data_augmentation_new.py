#!/usr/bin/env python3
"""
Feature Data Augmentation for Geo-Compliance Classification

This script generates synthetic feature descriptions in the same format as feature_sample_data.csv:
- feature_name: Short descriptive name
- feature_description: Detailed description using internal codenames and compliance terminology

Generates realistic social media platform features with:
- Internal codenames (ASL, GH, CDS, T5, etc.)
- Compliance requirements for various jurisdictions
- Technical implementation details
- Safety and privacy considerations
"""

import csv
import os
import random
from collections import defaultdict
from typing import List, Tuple

# Set random seed for reproducibility
random.seed(42)


class FeatureDataGenerator:
    """Generate synthetic feature data in the same format as feature_sample_data.csv"""

    def __init__(self):
        # Load terminology from the existing terminology.csv
        self.codenames = {
            "NR": "Not recommended",
            "PF": "Personalized feed",
            "GH": "Geo-handler",
            "CDS": "Compliance Detection System",
            "DRT": "Data retention threshold",
            "LCP": "Local compliance policy",
            "Redline": "Flag for legal review",
            "Softblock": "User limitation applied silently",
            "Spanner": "Rule engine",
            "ShadowMode": "Non-user-impact analytics deployment",
            "T5": "Tier 5 sensitivity data",
            "ASL": "Age-sensitive logic",
            "Glow": "Compliance-flagging status",
            "NSP": "Non-shareable policy",
            "Jellybean": "Parental control system",
            "EchoTrace": "Log tracing mode",
            "BB": "Baseline Behavior",
            "Snowcap": "Child safety policy framework",
            "FR": "Feature rollout status",
            "IMT": "Internal monitoring trigger",
        }

        self.jurisdictions = {
            "US": ["Utah", "California", "Florida", "Texas", "New York", "Washington"],
            "EU": ["Germany", "France", "Netherlands", "Italy", "Spain", "Belgium"],
            "Other": [
                "Canada",
                "United Kingdom",
                "Australia",
                "South Korea",
                "Japan",
                "Brazil",
            ],
        }

        self.regulations = {
            "Utah": "Utah Social Media Regulation Act",
            "California": "California's SB976",
            "Florida": "Florida's Online Protections for Minors law",
            "Texas": "Texas SCOPE Act",
            "EU": "EU Digital Services Act",
            "Germany": "German Network Enforcement Act",
            "US Federal": "COPPA compliance requirements",
            "GDPR": "General Data Protection Regulation",
        }

        self.feature_types = [
            "login restriction",
            "content filtering",
            "parental control",
            "age verification",
            "data retention",
            "notification system",
            "content moderation",
            "user safety",
            "privacy protection",
            "analytics tracking",
            "feed customization",
            "chat feature",
            "video feature",
            "social feature",
            "monetization feature",
            "profile feature",
        ]

        self.feature_actions = [
            "blocking",
            "limiting",
            "monitoring",
            "filtering",
            "restricting",
            "enabling",
            "disabling",
            "tracking",
            "logging",
            "flagging",
            "scanning",
            "detecting",
            "controlling",
            "managing",
            "routing",
            "triggering",
            "enforcing",
            "auditing",
        ]

        self.compliance_reasons = [
            "age verification requirements",
            "parental consent obligations",
            "data protection standards",
            "content safety measures",
            "privacy transparency",
            "minor protection laws",
            "content reporting requirements",
            "user safety protocols",
            "geographical compliance",
            "retention policy enforcement",
        ]

    def generate_feature_name(self) -> str:
        """Generate a realistic feature name"""
        components = [
            random.choice(self.feature_types),
            "with",
            random.choice(list(self.codenames.keys())),
            "and",
            random.choice(list(self.codenames.keys())),
            "for",
            random.choice(
                [
                    f"{random.choice(self.jurisdictions['US'])} minors",
                    f"{random.choice(self.jurisdictions['EU'])} users",
                    f"{random.choice(self.jurisdictions['Other'])} compliance",
                    "underage users",
                    "teen safety",
                    "parental controls",
                ]
            ),
        ]

        # Sometimes use simpler names
        if random.random() < 0.4:
            components = [
                random.choice(
                    [
                        random.choice(list(self.codenames.keys())),
                        f"{random.choice(self.feature_actions)} {random.choice(self.feature_types)}",
                    ]
                ),
                random.choice(
                    [
                        "auto-flagging",
                        "enforcement",
                        "detection",
                        "controls",
                        "monitoring",
                    ]
                ),
            ]

        return " ".join(components)

    def generate_feature_description(self, feature_name: str) -> str:
        """Generate a detailed feature description with codenames and compliance context"""

        # Choose jurisdiction and regulation
        region = random.choice(["US", "EU", "Other"])
        if region == "US":
            jurisdiction = random.choice(self.jurisdictions["US"])
            regulation = self.regulations.get(jurisdiction, "state privacy laws")
        elif region == "EU":
            jurisdiction = random.choice(self.jurisdictions["EU"])
            regulation = random.choice(
                [self.regulations["EU"], self.regulations["GDPR"]]
            )
        else:
            jurisdiction = random.choice(self.jurisdictions["Other"])
            regulation = "local data protection requirements"

        # Choose compliance context
        compliance_context = random.choice(
            [
                f"To comply with the {regulation}",
                f"In line with {jurisdiction} {random.choice(self.compliance_reasons)}",
                f"To meet the {random.choice(self.compliance_reasons)} of the {regulation}",
                f"As part of compliance with {regulation}",
                f"To support {regulation}",
            ]
        )

        # Choose technical implementation
        codename1 = random.choice(list(self.codenames.keys()))
        codename2 = random.choice(list(self.codenames.keys()))
        codename3 = random.choice(list(self.codenames.keys()))

        technical_details = [
            f"The system uses {codename1} to {random.choice(['detect', 'segment', 'filter', 'route', 'monitor'])} {random.choice(['user accounts', 'content', 'behaviors', 'violations', 'activities'])}",
            f"Routes enforcement through {codename2} to apply only within {jurisdiction} boundaries",
            f"Uses {codename3} for {random.choice(['auditability', 'traceability', 'monitoring', 'compliance validation', 'safety checks'])}",
            f"Operating in {random.choice(['ShadowMode', 'Spanner', 'EchoTrace'])} during {random.choice(['initial rollout', 'testing phase', 'validation period'])}",
        ]

        # Additional implementation details
        additional_details = [
            f"The feature {random.choice(['activates', 'triggers', 'applies', 'enforces'])} during {random.choice(['restricted hours', 'specific conditions', 'policy violations', 'safety events'])}",
            f"Logs activity using {random.choice(['EchoTrace', 'CDS', 'FR', 'IMT'])} for {random.choice(['auditability', 'compliance tracking', 'safety monitoring'])}",
            f"This allows {random.choice(['parental control', 'safety measures', 'compliance enforcement', 'privacy protection'])} to be {random.choice(['enacted', 'implemented', 'maintained'])} without {random.choice(['user-facing alerts', 'service disruption', 'privacy concerns'])}",
            f"The design ensures {random.choice(['minimal disruption', 'compliance accuracy', 'user safety', 'privacy protection'])} while meeting the {random.choice(['strict requirements', 'regulatory standards', 'safety protocols'])} imposed by the law",
        ]

        # Build description
        description_parts = [
            compliance_context + ",",
            random.choice(
                [
                    f"we are implementing a {random.choice(self.feature_types)} for {random.choice(['users under 18', 'minor accounts', 'teen users', 'underage profiles'])}.",
                    f"this feature {random.choice(['scans', 'monitors', 'filters', 'controls', 'manages'])} {random.choice(['uploads', 'content', 'user activity', 'interactions', 'behaviors'])} and {random.choice(['flags', 'blocks', 'restricts', 'routes', 'logs'])} {random.choice(['suspected materials', 'policy violations', 'safety risks', 'compliance issues'])}.",
                    f"the app will {random.choice(['disable', 'enable', 'restrict', 'monitor', 'control'])} {random.choice(['PF', 'content sharing', 'messaging features', 'social features'])} by default for {random.choice(['users under 18', 'minor accounts', 'teen profiles'])} located in {jurisdiction}.",
                ]
            ),
            random.choice(technical_details) + ".",
            random.choice(additional_details) + ".",
            random.choice(
                [
                    f"{random.choice(['Regional', 'Geographic', 'Compliance'])} {random.choice(['thresholds', 'parameters', 'controls'])} are governed by {random.choice(['LCP', 'DRT', 'Spanner'])} parameters in the backend.",
                    f"{random.choice(['Glow', 'Redline', 'FR'])} flags ensure {random.choice(['compliance visibility', 'safety monitoring', 'audit tracking'])} during rollout phases.",
                    f"The logic runs in {random.choice(['real-time', 'batch mode', 'continuous mode'])}, supports {random.choice(['human validation', 'automated review', 'compliance checks'])}, and logs {random.choice(['detection metadata', 'compliance events', 'safety metrics'])} for internal audits.",
                ]
            ),
        ]

        return " ".join(description_parts)

    def generate_features(self, count: int = 50) -> List[Tuple[str, str]]:
        """Generate a list of synthetic features"""
        features = []

        for _ in range(count):
            feature_name = self.generate_feature_name()
            feature_description = self.generate_feature_description(feature_name)
            features.append((feature_name, feature_description))

        return features

    def save_to_csv(self, features: List[Tuple[str, str]], filepath: str):
        """Save features to CSV file in the same format as feature_sample_data.csv"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["feature_name", "feature_description"])
            for feature_name, feature_description in features:
                writer.writerow([feature_name, feature_description])

        print(f"💾 Saved {len(features)} features to {filepath}")

    def generate_augmentation_report(self, features: List[Tuple[str, str]]) -> str:
        """Generate a report about the generated features"""
        codename_usage = defaultdict(int)
        jurisdiction_usage = defaultdict(int)

        for name, description in features:
            # Count codename usage
            for codename in self.codenames.keys():
                if codename in description:
                    codename_usage[codename] += 1

            # Count jurisdiction mentions
            for jurisdictions in self.jurisdictions.values():
                for jurisdiction in jurisdictions:
                    if jurisdiction in description:
                        jurisdiction_usage[jurisdiction] += 1

        report = f"""# Feature Data Augmentation Report
Generated: {len(features)} synthetic features

## Codename Usage Distribution
"""
        for codename, count in sorted(
            codename_usage.items(), key=lambda x: x[1], reverse=True
        ):
            report += (
                f"- **{codename}**: {count} features ({self.codenames[codename]})\n"
            )

        report += f"""
## Jurisdiction Coverage
"""
        for jurisdiction, count in sorted(
            jurisdiction_usage.items(), key=lambda x: x[1], reverse=True
        ):
            if count > 0:
                report += f"- **{jurisdiction}**: {count} features\n"

        report += f"""
## Feature Categories Generated
- Age verification and parental controls
- Content moderation and safety
- Data retention and privacy
- Geographic compliance enforcement
- User behavior monitoring
- Feed and recommendation controls

## Quality Measures
- Realistic internal codename usage
- Jurisdiction-specific compliance references
- Technical implementation details
- Safety and privacy considerations
- Regulatory framework alignment
"""

        return report


def main():
    """Main feature generation pipeline"""
    print("🚀 Feature Data Generation Pipeline")
    print("=" * 60)

    # Initialize generator
    generator = FeatureDataGenerator()

    # Generate features
    print("🔄 Generating synthetic features...")
    features = generator.generate_features(count=100)  # Generate 100 features

    # Save to CSV
    output_path = "generated_output/augmented_features.csv"
    generator.save_to_csv(features, output_path)

    # Generate report
    report = generator.generate_augmentation_report(features)
    report_path = "generated_output/feature_generation_report.md"

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, "w") as f:
        f.write(report)

    print(f"✅ Generated {len(features)} features")
    print(f"📄 Report saved to: {report_path}")
    print(f"📁 Features saved to: {output_path}")

    # Display sample features
    print("\n🔍 Sample Generated Features:")
    print("-" * 40)
    for i, (name, description) in enumerate(features[:3]):
        print(f"\n**Feature {i+1}:** {name}")
        print(f"**Description:** {description[:200]}...")

    return features


if __name__ == "__main__":
    main()
