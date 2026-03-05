#!/usr/bin/env python3
"""
TikTok Feature Generator Agent

Generates realistic TikTok-style product features with geo-regulation compliance labels.
This module creates synthetic training data for compliance classification models.
"""

import json
import logging
import os
import random
import sys
import uuid
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add RAG adapter import
try:
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from src.evidence import log_compliance_decision
    from src.rag import RAGAdapter
except ImportError:
    RAGAdapter = None
    log_compliance_decision = None
    logger.warning("RAG adapter not available, using fallback compliance rules")


@dataclass
class GeneratedFeature:
    """Schema for generated TikTok features with compliance metadata."""

    feature_id: str
    title: str
    description: str
    domain: str
    geo_country: str
    geo_state: Optional[str]
    age_min: int
    age_max: int
    data_practices: List[str]
    addictive_features: List[str]
    safety_controls: List[str]
    label: str  # Compliant | Partially Compliant | Non-Compliant
    rationale: str
    implicated_regs: List[str]
    risk_tags: List[str]
    source_seed: str
    confidence_score: float
    generation_timestamp: str


class FeatureTemplateLibrary:
    """Comprehensive library of TikTok feature templates across all product domains."""

    def __init__(self):
        self.templates = {
            "recommendations": [
                {
                    "base_title": "Infinite Scroll for Shorts",
                    "base_description": "Continuous video feed with infinite scrolling for seamless content discovery",
                    "data_practices": [
                        "viewing_history",
                        "engagement_patterns",
                        "device_info",
                    ],
                    "addictive_features": ["infinite_scroll", "autoplay"],
                    "safety_controls": [],
                    "risk_level": "high",
                    "variations": {
                        "age_restrictions": [13, 16, 18],
                        "opt_in_required": [True, False],
                        "time_limits": [True, False],
                    },
                },
                {
                    "base_title": "Personalized Study Feed",
                    "base_description": "AI-curated educational content based on learning preferences and academic interests",
                    "data_practices": [
                        "educational_preferences",
                        "time_spent_learning",
                        "quiz_results",
                    ],
                    "addictive_features": [],
                    "safety_controls": ["content_filtering", "time_limits"],
                    "risk_level": "low",
                    "variations": {
                        "data_collection": ["minimal", "moderate", "extensive"],
                        "personalization_level": ["basic", "advanced"],
                    },
                },
                {
                    "base_title": "Viral Trend Recommendations",
                    "base_description": "Algorithm that promotes trending content and challenges to maximize engagement",
                    "data_practices": [
                        "social_graph",
                        "engagement_patterns",
                        "viral_participation",
                    ],
                    "addictive_features": ["push_notifications", "algorithmic_ranking"],
                    "safety_controls": [],
                    "risk_level": "medium",
                    "variations": {
                        "notification_frequency": ["low", "medium", "high"],
                        "trend_sensitivity": ["conservative", "aggressive"],
                    },
                },
                {
                    "base_title": "Auto-play Next Video",
                    "base_description": "Automatic progression to next recommended video without user interaction",
                    "data_practices": ["viewing_patterns", "content_preferences"],
                    "addictive_features": ["autoplay", "seamless_transition"],
                    "safety_controls": [],
                    "risk_level": "high",
                    "variations": {
                        "default_enabled": [True, False],
                        "pause_between_videos": [0, 3, 5],
                    },
                },
                {
                    "base_title": "Friend Activity Feed",
                    "base_description": "Real-time updates showing friends' activities, likes, and comments",
                    "data_practices": [
                        "social_connections",
                        "friend_activity",
                        "interaction_history",
                    ],
                    "addictive_features": ["real_time_updates", "social_validation"],
                    "safety_controls": ["privacy_controls"],
                    "risk_level": "medium",
                    "variations": {
                        "update_frequency": ["instant", "hourly", "daily"],
                        "visibility_settings": ["public", "friends_only", "private"],
                    },
                },
            ],
            "advertising": [
                {
                    "base_title": "Contextual Product Placement",
                    "base_description": "AI-driven product recommendations integrated naturally within video content",
                    "data_practices": [
                        "purchase_history",
                        "browsing_behavior",
                        "demographic_data",
                    ],
                    "addictive_features": ["targeted_advertising"],
                    "safety_controls": ["ad_transparency"],
                    "risk_level": "medium",
                    "variations": {
                        "targeting_precision": ["broad", "narrow", "hyper_targeted"],
                        "disclosure_prominence": ["subtle", "clear", "prominent"],
                    },
                },
                {
                    "base_title": "Location-Based Local Ads",
                    "base_description": "Geo-targeted advertisements for local businesses and services",
                    "data_practices": [
                        "location_data",
                        "local_preferences",
                        "visit_history",
                    ],
                    "addictive_features": [],
                    "safety_controls": ["location_controls"],
                    "risk_level": "low",
                    "variations": {
                        "location_precision": ["city", "neighborhood", "exact"],
                        "data_retention": ["session", "short_term", "long_term"],
                    },
                },
                {
                    "base_title": "Influencer Sponsored Content",
                    "base_description": "Branded content promotion through creator partnerships with disclosure",
                    "data_practices": ["creator_preferences", "engagement_history"],
                    "addictive_features": ["social_influence"],
                    "safety_controls": ["sponsorship_disclosure"],
                    "risk_level": "medium",
                    "variations": {
                        "disclosure_timing": [
                            "pre_content",
                            "during_content",
                            "post_content",
                        ],
                        "influence_tracking": ["basic", "detailed"],
                    },
                },
            ],
            "live_streaming": [
                {
                    "base_title": "Live Stream Discovery",
                    "base_description": "Real-time promotion of live streams based on user interests and social connections",
                    "data_practices": [
                        "live_viewing_history",
                        "creator_follows",
                        "interaction_patterns",
                    ],
                    "addictive_features": ["live_notifications", "fomo_triggers"],
                    "safety_controls": ["age_verification"],
                    "risk_level": "high",
                    "variations": {
                        "notification_urgency": ["low", "medium", "high"],
                        "age_restrictions": [13, 16, 18],
                    },
                },
                {
                    "base_title": "Virtual Gift Economy",
                    "base_description": "In-app currency system for viewers to send virtual gifts to streamers",
                    "data_practices": [
                        "payment_info",
                        "gifting_history",
                        "spending_patterns",
                    ],
                    "addictive_features": ["virtual_economy", "social_status"],
                    "safety_controls": ["spending_limits", "parental_controls"],
                    "risk_level": "high",
                    "variations": {
                        "spending_limits": ["none", "daily", "monthly"],
                        "parental_oversight": [
                            "none",
                            "notifications",
                            "approval_required",
                        ],
                    },
                },
                {
                    "base_title": "Age-Gated Adult Content",
                    "base_description": "Restricted live streaming categories requiring age verification",
                    "data_practices": ["age_verification_data", "content_preferences"],
                    "addictive_features": [],
                    "safety_controls": ["strict_age_verification", "content_warnings"],
                    "risk_level": "low",
                    "variations": {
                        "verification_method": [
                            "document_upload",
                            "credit_card",
                            "third_party",
                        ],
                        "content_warnings": ["minimal", "detailed", "comprehensive"],
                    },
                },
            ],
            "messaging": [
                {
                    "base_title": "Minor Direct Messaging",
                    "base_description": "Private messaging system allowing communication with users under 18",
                    "data_practices": [
                        "message_content",
                        "contact_lists",
                        "conversation_history",
                    ],
                    "addictive_features": [],
                    "safety_controls": ["message_filtering", "parental_oversight"],
                    "risk_level": "high",
                    "variations": {
                        "filtering_strictness": ["basic", "moderate", "strict"],
                        "parental_visibility": ["none", "summaries", "full_access"],
                    },
                },
                {
                    "base_title": "Group Chat Creation",
                    "base_description": "Feature allowing users to create and manage group conversations",
                    "data_practices": [
                        "group_membership",
                        "admin_actions",
                        "shared_content",
                    ],
                    "addictive_features": ["group_dynamics"],
                    "safety_controls": ["group_moderation", "reporting_tools"],
                    "risk_level": "medium",
                    "variations": {
                        "group_size_limits": [10, 50, 100],
                        "moderation_level": [
                            "user_driven",
                            "ai_assisted",
                            "human_moderated",
                        ],
                    },
                },
                {
                    "base_title": "Disappearing Messages",
                    "base_description": "Time-limited messages that auto-delete after specified duration",
                    "data_practices": ["message_metadata", "deletion_logs"],
                    "addictive_features": [],
                    "safety_controls": ["screenshot_detection"],
                    "risk_level": "medium",
                    "variations": {
                        "deletion_timeframes": ["10s", "1min", "1hour", "1day"],
                        "screenshot_policies": ["allow", "notify", "prevent"],
                    },
                },
            ],
            "privacy": [
                {
                    "base_title": "Data Download Portal",
                    "base_description": "User interface for requesting and downloading personal data archives",
                    "data_practices": ["data_access_logs", "download_history"],
                    "addictive_features": [],
                    "safety_controls": ["identity_verification", "secure_delivery"],
                    "risk_level": "low",
                    "variations": {
                        "processing_time": ["instant", "24hours", "30days"],
                        "data_completeness": ["basic", "comprehensive", "forensic"],
                    },
                },
                {
                    "base_title": "Granular Privacy Controls",
                    "base_description": "Detailed settings for controlling data sharing and profile visibility",
                    "data_practices": ["privacy_preferences", "settings_history"],
                    "addictive_features": [],
                    "safety_controls": [
                        "default_private_settings",
                        "clear_explanations",
                    ],
                    "risk_level": "low",
                    "variations": {
                        "granularity_level": ["basic", "intermediate", "expert"],
                        "default_settings": ["open", "balanced", "private"],
                    },
                },
                {
                    "base_title": "Automatic Data Deletion",
                    "base_description": "Scheduled deletion of user data after specified retention periods",
                    "data_practices": ["retention_schedules", "deletion_logs"],
                    "addictive_features": [],
                    "safety_controls": ["user_notification", "recovery_period"],
                    "risk_level": "low",
                    "variations": {
                        "retention_periods": ["30days", "1year", "3years"],
                        "deletion_scope": [
                            "activity_only",
                            "profile_data",
                            "everything",
                        ],
                    },
                },
            ],
            "safety": [
                {
                    "base_title": "CSAM Detection System",
                    "base_description": "AI-powered system for identifying and reporting child sexual abuse material",
                    "data_practices": [
                        "content_hashes",
                        "detection_metadata",
                        "report_logs",
                    ],
                    "addictive_features": [],
                    "safety_controls": [
                        "automated_reporting",
                        "human_review",
                        "law_enforcement_cooperation",
                    ],
                    "risk_level": "low",
                    "variations": {
                        "detection_sensitivity": [
                            "conservative",
                            "balanced",
                            "aggressive",
                        ],
                        "reporting_speed": ["immediate", "batched", "reviewed"],
                    },
                },
                {
                    "base_title": "Cyberbullying Detection",
                    "base_description": "Machine learning system to identify and prevent harassment and bullying",
                    "data_practices": [
                        "comment_analysis",
                        "behavioral_patterns",
                        "report_history",
                    ],
                    "addictive_features": [],
                    "safety_controls": [
                        "automatic_intervention",
                        "counseling_resources",
                    ],
                    "risk_level": "low",
                    "variations": {
                        "intervention_threshold": ["low", "medium", "high"],
                        "response_actions": [
                            "warning",
                            "timeout",
                            "account_suspension",
                        ],
                    },
                },
                {
                    "base_title": "Crisis Intervention Alerts",
                    "base_description": "System to detect self-harm content and provide mental health resources",
                    "data_practices": [
                        "content_analysis",
                        "intervention_logs",
                        "resource_engagement",
                    ],
                    "addictive_features": [],
                    "safety_controls": ["immediate_support", "professional_referrals"],
                    "risk_level": "low",
                    "variations": {
                        "detection_scope": [
                            "text_only",
                            "images",
                            "videos",
                            "all_content",
                        ],
                        "response_level": [
                            "resources_only",
                            "outreach",
                            "emergency_contact",
                        ],
                    },
                },
            ],
            "growth": [
                {
                    "base_title": "Gamified Achievement System",
                    "base_description": "Points, badges, and levels to incentivize platform engagement",
                    "data_practices": [
                        "achievement_progress",
                        "engagement_metrics",
                        "competition_data",
                    ],
                    "addictive_features": [
                        "gamification",
                        "social_competition",
                        "variable_rewards",
                    ],
                    "safety_controls": [],
                    "risk_level": "high",
                    "variations": {
                        "reward_frequency": ["rare", "moderate", "frequent"],
                        "social_visibility": ["private", "friends", "public"],
                    },
                },
                {
                    "base_title": "Daily Login Streaks",
                    "base_description": "Reward system for consecutive daily app usage with escalating benefits",
                    "data_practices": [
                        "login_patterns",
                        "streak_data",
                        "reward_history",
                    ],
                    "addictive_features": [
                        "habit_formation",
                        "loss_aversion",
                        "escalating_rewards",
                    ],
                    "safety_controls": [],
                    "risk_level": "high",
                    "variations": {
                        "streak_reset_policy": [
                            "strict",
                            "forgiving",
                            "weekend_exempt",
                        ],
                        "reward_escalation": [
                            "linear",
                            "exponential",
                            "milestone_based",
                        ],
                    },
                },
                {
                    "base_title": "Social Proof Metrics",
                    "base_description": "Public display of likes, shares, and follower counts to drive engagement",
                    "data_practices": ["engagement_metrics", "social_validation_data"],
                    "addictive_features": ["social_validation", "public_metrics"],
                    "safety_controls": ["hide_metrics_option"],
                    "risk_level": "medium",
                    "variations": {
                        "metrics_visibility": [
                            "always_visible",
                            "toggleable",
                            "hidden_by_default",
                        ],
                        "metrics_granularity": [
                            "exact_counts",
                            "ranges",
                            "qualitative",
                        ],
                    },
                },
            ],
        }

    def get_template(self, domain: str) -> Dict:
        """Get a random template from the specified domain."""
        if domain not in self.templates:
            domain = random.choice(list(self.templates.keys()))
        return random.choice(self.templates[domain])

    def get_all_domains(self) -> List[str]:
        """Get list of all available domains."""
        return list(self.templates.keys())

    def mutate_template(self, template: Dict, target_label: str = None) -> Dict:
        """Apply mutations to template based on target compliance label."""
        mutated = template.copy()

        # Apply variations if available
        if "variations" in template:
            for variation_type, options in template["variations"].items():
                mutated[variation_type] = random.choice(options)

        # Adjust features based on target label
        if target_label == "Non-Compliant":
            # Add more risky features
            if "addictive_features" in mutated:
                additional_risks = [
                    "push_notifications",
                    "variable_rewards",
                    "social_pressure",
                ]
                mutated["addictive_features"].extend(
                    random.sample(additional_risks, k=random.randint(1, 2))
                )

            # Remove some safety controls
            if "safety_controls" in mutated and mutated["safety_controls"]:
                mutated["safety_controls"] = mutated["safety_controls"][
                    : -random.randint(0, len(mutated["safety_controls"]) // 2)
                ]

        elif target_label == "Compliant":
            # Add safety controls
            safety_additions = [
                "parental_controls",
                "age_verification",
                "content_filtering",
                "user_controls",
            ]
            mutated["safety_controls"] = mutated.get(
                "safety_controls", []
            ) + random.sample(safety_additions, k=random.randint(1, 2))

        return mutated


class ComplianceRuleEngine:
    """Rule-based compliance evaluation engine for geo-regulations."""

    def __init__(self):
        self.rules = self._initialize_rules()

    def _initialize_rules(self) -> Dict:
        """Initialize compliance rules for different jurisdictions."""
        return {
            "US-FL": {
                "name": "Florida Online Protections for Minors (HB 3)",
                "banned_under_14": True,
                "consent_required_14_15": True,
                "addictive_triggers": [
                    "infinite_scroll",
                    "autoplay",
                    "push_notifications",
                    "public_metrics",
                    "variable_rewards",
                    "fomo_triggers",
                    "live_notifications",
                    "virtual_economy",
                ],
                "required_controls": ["parental_controls", "age_verification"],
                "mitigations": ["time_limits", "default_off", "parental_oversight"],
            },
            "US-CA": {
                "name": "California Protecting Our Kids from Social Media Addiction Act",
                "parental_consent_required": True,
                "default_safety_required": True,
                "algorithmic_triggers": [
                    "algorithmic_ranking",
                    "personalization",
                    "targeted_advertising",
                    "push_notifications",
                    "recommendation_algorithms",
                    "engagement_optimization",
                ],
                "required_controls": [
                    "opt_in_required",
                    "transparency_required",
                    "user_controls",
                ],
                "mitigations": ["clear_disclosure", "user_choice", "safety_defaults"],
            },
            "EU": {
                "name": "EU Digital Services Act (DSA)",
                "transparency_required": True,
                "profiling_controls_required": True,
                "recommender_triggers": [
                    "algorithmic_ranking",
                    "personalization",
                    "content_curation",
                    "behavioral_tracking",
                    "preference_analysis",
                    "targeted_content",
                    "infinite_scroll",
                    "autoplay",
                    "push_notifications",
                    "variable_rewards",
                ],
                "required_controls": [
                    "disable_profiling_option",
                    "transparent_moderation",
                    "accessible_documentation",
                ],
                "mitigations": [
                    "user_choice",
                    "clear_explanations",
                    "appeal_processes",
                ],
            },
            "US-2258A": {
                "name": "US Federal CSAM Reporting Requirements (18 U.S.C. §2258A)",
                "reporting_required": True,
                "preservation_required": True,
                "content_triggers": [
                    "user_generated_content",
                    "image_sharing",
                    "video_sharing",
                    "messaging",
                    "live_streaming",
                    "content_upload",
                ],
                "required_controls": [
                    "ncmec_reporting",
                    "preservation_systems",
                    "human_review",
                    "automated_detection",
                ],
                "mitigations": [
                    "automated_detection",
                    "law_enforcement_cooperation",
                    "content_filtering",
                ],
            },
        }

    def evaluate_compliance(
        self, feature: Dict, geo_country: str, geo_state: str = None
    ) -> Tuple[str, str, List[str]]:
        """Evaluate feature compliance and return label, rationale, and implicated regulations."""

        # Determine applicable jurisdiction
        jurisdiction = self._get_jurisdiction(geo_country, geo_state)
        if jurisdiction not in self.rules:
            return "Compliant", "No specific regulations apply to this jurisdiction", []

        rules = self.rules[jurisdiction]
        violations = []
        mitigations = []

        # Extract feature characteristics
        addictive_features = feature.get("addictive_features", [])
        data_practices = feature.get("data_practices", [])
        safety_controls = feature.get("safety_controls", [])
        age_min = feature.get("age_min", 18)

        # Check for violations based on jurisdiction
        if jurisdiction == "US-FL":
            # Florida-specific checks
            if age_min < 14:
                violations.append("Targets users under 14 (banned in Florida)")

            if age_min >= 14 and age_min < 16:
                if not any(
                    control in safety_controls
                    for control in ["parental_controls", "parental_consent"]
                ):
                    violations.append("Missing parental consent for 14-15 age group")

            # Check for addictive features
            for trigger in rules.get("addictive_triggers", []):
                if trigger in addictive_features:
                    violations.append(f"Uses addictive feature: {trigger}")

        elif jurisdiction == "US-CA":
            # California-specific checks
            if any(
                trigger in addictive_features + data_practices
                for trigger in rules.get("algorithmic_triggers", [])
            ):
                if not any(
                    control in safety_controls
                    for control in ["opt_in_required", "user_controls"]
                ):
                    violations.append(
                        "Algorithmic features without proper user controls"
                    )

        elif jurisdiction == "EU":
            # EU DSA checks
            if any(
                trigger in addictive_features + data_practices
                for trigger in rules.get("recommender_triggers", [])
            ):
                if not any(
                    control in safety_controls
                    for control in [
                        "disable_profiling_option",
                        "transparent_moderation",
                    ]
                ):
                    violations.append(
                        "Recommender systems without transparency/control options"
                    )

        elif jurisdiction == "US-2258A":
            # Federal CSAM reporting checks
            if any(
                trigger in data_practices + addictive_features
                for trigger in rules.get("content_triggers", [])
            ):
                if not any(
                    control in safety_controls
                    for control in [
                        "ncmec_reporting",
                        "automated_detection",
                        "content_filtering",
                    ]
                ):
                    violations.append(
                        "User-generated content without CSAM detection/reporting"
                    )

        # Check for mitigations
        mitigation_controls = rules.get("mitigations", [])
        for mitigation in mitigation_controls:
            if mitigation in safety_controls:
                mitigations.append(mitigation)

        # Determine final label
        if not violations:
            return (
                "Compliant",
                f"Feature meets all {rules['name']} requirements",
                [jurisdiction],
            )

        # Check if mitigations address violations
        mitigation_score = len(mitigations)
        violation_count = len(violations)

        if not violations:
            return (
                "Compliant",
                f"Feature meets all {rules['name']} requirements",
                [jurisdiction],
            )

        # Partial compliance logic: some violations but also some mitigations
        if mitigations and (mitigation_score >= violation_count // 2):
            rationale = f"Partial compliance with {rules['name']}: {violation_count} violations partially mitigated by {', '.join(mitigations[:2])}"
            if len(mitigations) > 2:
                rationale += f" and {len(mitigations) - 2} other controls"
            return "Partially Compliant", rationale, [jurisdiction]

        # Non-compliant
        violation_summary = "; ".join(violations[:3])
        if len(violations) > 3:
            violation_summary += f" and {len(violations) - 3} other issues"

        return (
            "Non-Compliant",
            f"Violates {rules['name']}: {violation_summary}",
            [jurisdiction],
        )

    def _get_jurisdiction(self, country: str, state: str = None) -> str:
        """Determine jurisdiction code from geographic information."""
        if country == "USA":
            if state in ["Florida", "FL"]:
                return "US-FL"
            elif state in ["California", "CA"]:
                return "US-CA"
            else:
                return "US-2258A"  # Federal regulations apply
        elif country in [
            "Germany",
            "France",
            "Netherlands",
            "EU",
        ] or country.startswith("EU"):
            return "EU"
        else:
            return "US-2258A"  # Default to federal regulations


class TikTokFeatureGenerator:
    """Main generator class for creating synthetic TikTok features with compliance labels."""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.seed = seed
        self.rag_adapter = RAGAdapter() if RAGAdapter else None
        self.template_library = FeatureTemplateLibrary()
        self.compliance_engine = ComplianceRuleEngine()
        self.generated_features = []

    def analyze_seed_data(self, filepath: str) -> Dict:
        """Analyze corrections.json to learn patterns and distributions."""
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.warning(
                f"Seed file {filepath} not found. Using default distributions."
            )
            return self._get_default_distributions()

        analysis = {
            "total_records": len(data),
            "label_distribution": Counter(item["corrected_label"] for item in data),
            "geo_distribution": Counter(),
            "regulation_distribution": Counter(
                item["feature_characteristics"]["regulation_type"] for item in data
            ),
            "age_ranges": [],
            "domains_inferred": Counter(),
        }

        # Analyze geographic distribution
        for item in data:
            geo = item["feature_characteristics"]["geographic"]
            if "country" in geo:
                country_state = f"{geo['country']}"
                if "state" in geo:
                    country_state += f"-{geo['state']}"
                analysis["geo_distribution"][country_state] += 1

        # Analyze age ranges
        for item in data:
            demo = item["feature_characteristics"]["demographic"]
            age_range = (demo.get("age_min", 13), demo.get("age_max", 65))
            analysis["age_ranges"].append(age_range)

        # Infer domains from feature types
        domain_mapping = {
            "Social Media": "recommendations",
            "User Registration": "privacy",
            "Data Collection": "privacy",
            "Industrial Process": "safety",
            "Construction Project": "safety",
            "Legal Documentation": "privacy",
            "User Controls": "privacy",
        }

        for item in data:
            feature_type = item["feature_characteristics"].get(
                "feature_type", "Unknown"
            )
            domain = domain_mapping.get(feature_type, "recommendations")
            analysis["domains_inferred"][domain] += 1

        logger.info(f"Analyzed {analysis['total_records']} seed records")
        return analysis

    def _get_default_distributions(self) -> Dict:
        """Return default distributions when seed data is unavailable."""
        return {
            "label_distribution": Counter(
                {"Non-Compliant": 60, "Compliant": 25, "Partially Compliant": 15}
            ),
            "geo_distribution": Counter(
                {"USA-CA": 30, "USA-FL": 25, "EU": 25, "USA": 20}
            ),
            "regulation_distribution": Counter(
                {
                    "Age Verification": 20,
                    "Data Protection": 18,
                    "Privacy": 15,
                    "Safety": 15,
                    "Parental Consent": 12,
                    "Privacy Policy": 10,
                    "Privacy Rights": 10,
                }
            ),
            "domains_inferred": Counter(
                {
                    "recommendations": 25,
                    "advertising": 15,
                    "live_streaming": 15,
                    "messaging": 15,
                    "privacy": 15,
                    "safety": 10,
                    "growth": 5,
                }
            ),
        }

    def generate_features(
        self,
        n: int,
        geo_filters: List[str] = None,
        target_mix: Dict[str, float] = None,
        domain_focus: List[str] = None,
    ) -> List[GeneratedFeature]:
        """Generate n features with specified constraints."""

        if target_mix is None:
            target_mix = {
                "Compliant": 0.3,
                "Partially Compliant": 0.3,
                "Non-Compliant": 0.4,
            }

        if geo_filters is None:
            geo_filters = ["USA-CA", "USA-FL", "EU", "USA"]

        if domain_focus is None:
            domain_focus = self.template_library.get_all_domains()

        # Calculate target counts for each label
        target_counts = {label: int(n * ratio) for label, ratio in target_mix.items()}

        # Adjust for rounding
        total_assigned = sum(target_counts.values())
        if total_assigned < n:
            # Add remaining to most frequent label
            max_label = max(target_mix.keys(), key=lambda k: target_mix[k])
            target_counts[max_label] += n - total_assigned

        logger.info(
            f"Generating {n} features with target distribution: {target_counts}"
        )

        generated = []
        label_counts = {label: 0 for label in target_mix.keys()}

        for i in range(n):
            # Determine target label for this feature
            remaining_labels = [
                label
                for label, count in label_counts.items()
                if count < target_counts[label]
            ]

            if remaining_labels:
                target_label = random.choice(remaining_labels)
            else:
                target_label = random.choice(list(target_mix.keys()))

            # Generate feature
            feature = self._generate_single_feature(
                feature_id=f"GEN-{i:04d}",
                target_label=target_label,
                geo_filters=geo_filters,
                domain_focus=domain_focus,
            )

            generated.append(feature)
            label_counts[feature.label] += 1

        self.generated_features.extend(generated)
        logger.info(
            f"Generated {len(generated)} features. Final distribution: {label_counts}"
        )

        return generated

    def _generate_single_feature(
        self,
        feature_id: str,
        target_label: str,
        geo_filters: List[str],
        domain_focus: List[str],
    ) -> GeneratedFeature:
        """Generate a single feature with specified constraints."""

        # Select domain and template
        domain = random.choice(domain_focus)
        template = self.template_library.get_template(domain)

        # Mutate template based on target label
        mutated_template = self.template_library.mutate_template(template, target_label)

        # Select geography
        geo_info = self._select_geography(geo_filters)

        # Select age range
        age_min, age_max = self._select_age_range(target_label, geo_info)

        # Build feature characteristics
        feature_data = {
            "addictive_features": mutated_template.get("addictive_features", []),
            "data_practices": mutated_template.get("data_practices", []),
            "safety_controls": mutated_template.get("safety_controls", []),
            "age_min": age_min,
            "age_max": age_max,
        }

        # Add target-specific adjustments
        feature_data = self._adjust_for_target_label(feature_data, target_label)

        # Evaluate compliance using RAG if available, otherwise fallback
        if self.rag_adapter:
            compliance_result = self._validate_compliance_with_rag(feature_data)
            self._log_compliance_evidence(feature_data, compliance_result)
            label = compliance_result["label"]
            rationale = compliance_result["rationale"]
            implicated_regs = compliance_result["implicated_regs"]
        else:
            label, rationale, implicated_regs = (
                self.compliance_engine.evaluate_compliance(
                    feature_data, geo_info["country"], geo_info.get("state")
                )
            )

        # Generate risk tags
        risk_tags = self._generate_risk_tags(feature_data, mutated_template)

        # Create feature object
        feature = GeneratedFeature(
            feature_id=feature_id,
            title=mutated_template["base_title"],
            description=mutated_template["base_description"],
            domain=domain,
            geo_country=geo_info["country"],
            geo_state=geo_info.get("state"),
            age_min=age_min,
            age_max=age_max,
            data_practices=feature_data["data_practices"],
            addictive_features=feature_data["addictive_features"],
            safety_controls=feature_data["safety_controls"],
            label=label,
            rationale=rationale,
            implicated_regs=implicated_regs,
            risk_tags=risk_tags,
            source_seed=f"template_{domain}",
            confidence_score=round(random.uniform(0.7, 0.95), 2),
            generation_timestamp=datetime.now().isoformat(),
        )

        return feature

    def _select_geography(self, geo_filters: List[str]) -> Dict[str, str]:
        """Select geographic information from available filters."""
        geo_choice = random.choice(geo_filters)

        if geo_choice == "US-CA":
            return {"country": "USA", "state": "California"}
        elif geo_choice == "US-FL":
            return {"country": "USA", "state": "Florida"}
        elif geo_choice == "EU":
            return {"country": random.choice(["Germany", "France", "Netherlands"])}
        else:  # USA or other
            return {
                "country": "USA",
                "state": random.choice(["Texas", "New York", "Illinois"]),
            }

    def _select_age_range(self, target_label: str, geo_info: Dict) -> Tuple[int, int]:
        """Select age range based on target label and geography."""

        # High-risk age ranges for certain labels
        if target_label == "Non-Compliant":
            # More likely to include problematic age ranges
            ranges = [(13, 17), (14, 16), (13, 15), (16, 18), (18, 25)]
        elif target_label == "Partially Compliant":
            ranges = [(14, 17), (16, 18), (18, 25), (13, 18)]
        else:  # Compliant
            ranges = [(18, 65), (21, 65), (16, 18), (18, 25)]

        return random.choice(ranges)

    def _adjust_for_target_label(self, feature_data: Dict, target_label: str) -> Dict:
        """Adjust feature characteristics to increase likelihood of target label."""

        if target_label == "Non-Compliant":
            # Add risky features, remove safeguards
            risky_additions = [
                "push_notifications",
                "variable_rewards",
                "infinite_scroll",
                "social_pressure",
            ]
            feature_data["addictive_features"].extend(
                random.sample(risky_additions, k=random.randint(1, 3))
            )

            # Remove some safety controls
            if feature_data["safety_controls"]:
                remove_count = random.randint(
                    0, len(feature_data["safety_controls"]) // 2
                )
                for _ in range(remove_count):
                    if feature_data["safety_controls"]:
                        feature_data["safety_controls"].pop()

        elif target_label == "Partially Compliant":
            # Add both risky features AND mitigations
            risky_additions = [
                "push_notifications",
                "algorithmic_ranking",
                "behavioral_tracking",
            ]
            feature_data["addictive_features"].extend(
                random.sample(risky_additions, k=random.randint(1, 2))
            )

            # Add some mitigations
            safety_additions = [
                "user_controls",
                "transparent_moderation",
                "time_limits",
                "user_choice",
            ]
            feature_data["safety_controls"].extend(
                random.sample(safety_additions, k=random.randint(1, 3))
            )

        elif target_label == "Compliant":
            # Add safety controls, reduce risky features
            safety_additions = [
                "parental_controls",
                "age_verification",
                "user_controls",
                "content_filtering",
            ]
            feature_data["safety_controls"].extend(
                random.sample(safety_additions, k=random.randint(1, 3))
            )

            # Remove some addictive features
            if feature_data["addictive_features"]:
                remove_count = random.randint(
                    0, len(feature_data["addictive_features"]) // 2
                )
                for _ in range(remove_count):
                    if feature_data["addictive_features"]:
                        feature_data["addictive_features"].pop()

        # Remove duplicates
        feature_data["addictive_features"] = list(
            set(feature_data["addictive_features"])
        )
        feature_data["safety_controls"] = list(set(feature_data["safety_controls"]))
        feature_data["data_practices"] = list(set(feature_data["data_practices"]))

        return feature_data

    def _generate_risk_tags(self, feature_data: Dict, template: Dict) -> List[str]:
        """Generate risk tags based on feature characteristics."""
        risk_tags = []

        # Risk based on age targeting
        age_min = feature_data.get("age_min", 18)
        if age_min < 14:
            risk_tags.append("child_targeting")
        elif age_min < 18:
            risk_tags.append("minor_targeting")

        # Risk based on addictive features
        if any(
            feature in feature_data.get("addictive_features", [])
            for feature in ["infinite_scroll", "variable_rewards", "social_pressure"]
        ):
            risk_tags.append("addiction_risk")

        # Risk based on data practices
        if any(
            practice in feature_data.get("data_practices", [])
            for practice in ["location_data", "biometric_data", "behavioral_tracking"]
        ):
            risk_tags.append("privacy_risk")

        # Risk based on template risk level
        if template.get("risk_level") == "high":
            risk_tags.append("high_risk_feature")

        return risk_tags

    def save_features(self, features: List[GeneratedFeature], output_dir: str):
        """Save generated features to JSONL and CSV formats."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Convert to dictionaries
        feature_dicts = [asdict(feature) for feature in features]

        # Save as JSONL
        jsonl_path = output_path / "generated_features.jsonl"
        with open(jsonl_path, "w") as f:
            for feature_dict in feature_dicts:
                f.write(json.dumps(feature_dict) + "\n")

        # Save as CSV (flatten lists to strings)
        csv_data = []
        for feature_dict in feature_dicts:
            csv_row = feature_dict.copy()
            # Convert lists to comma-separated strings
            for key, value in csv_row.items():
                if isinstance(value, list):
                    csv_row[key] = ", ".join(map(str, value))
            csv_data.append(csv_row)

        # Create CSV manually to ensure compatibility
        csv_path = output_path / "generated_features.csv"
        with open(csv_path, "w") as f:
            if csv_data:
                # Write header
                headers = list(csv_data[0].keys())
                f.write(",".join(headers) + "\n")

                # Write data
                for row in csv_data:
                    values = [
                        str(row.get(header, "")).replace(",", ";") for header in headers
                    ]
                    f.write(",".join(f'"{value}"' for value in values) + "\n")

        logger.info(f"Saved {len(features)} features to {output_dir}")
        return jsonl_path, csv_path

    def generate_distribution_report(
        self, features: List[GeneratedFeature], output_dir: str
    ):
        """Generate a comprehensive distribution report."""
        output_path = Path(output_dir)

        # Analyze distributions
        label_dist = Counter(f.label for f in features)
        geo_dist = Counter(
            f"{f.geo_country}-{f.geo_state}" if f.geo_state else f.geo_country
            for f in features
        )
        domain_dist = Counter(f.domain for f in features)
        reg_dist = Counter()
        for f in features:
            for reg in f.implicated_regs:
                reg_dist[reg] += 1

        # Generate report
        report = f"""# TikTok Feature Generation Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Features: {len(features)}
Generation Seed: {self.seed}

## Label Distribution
{dict(label_dist)}

## Geographic Distribution
{dict(geo_dist)}

## Domain Distribution
{dict(domain_dist)}

## Regulation Distribution
{dict(reg_dist)}

## Sample Features by Label

### Compliant Examples
"""

        # Add sample features for each label
        for label in ["Compliant", "Partially Compliant", "Non-Compliant"]:
            report += f"### {label} Examples\n"
            label_features = [f for f in features if f.label == label][:3]

            for i, feature in enumerate(label_features, 1):
                report += f"""
{i}. **{feature.title}** ({feature.geo_country})
   - Domain: {feature.domain}
   - Age Range: {feature.age_min}-{feature.age_max}
   - Rationale: {feature.rationale}
   - Risk Tags: {', '.join(feature.risk_tags)}
"""

        # Save report
        report_path = output_path / "distribution_report.md"
        with open(report_path, "w") as f:
            f.write(report)

        logger.info(f"Distribution report saved to {report_path}")
        return report_path

    def _validate_compliance_with_rag(self, feature_data: Dict) -> Dict:
        """Validate compliance using centralized RAG system."""
        try:
            # Query RAG for regulatory context
            query = (
                f"{feature_data.get('title', '')} {feature_data.get('description', '')}"
            )
            regulatory_context = self.rag_adapter.retrieve_regulatory_context(
                query=query, max_results=3
            )

            # Analyze compliance based on RAG results
            compliance_status = self._analyze_rag_compliance(
                regulatory_context, feature_data
            )

            return {
                "label": compliance_status["label"],
                "rationale": compliance_status["rationale"],
                "implicated_regs": compliance_status["regulations"],
                "confidence_score": compliance_status["confidence"],
            }
        except Exception as e:
            logger.warning(f"RAG compliance validation failed: {e}, using fallback")
            return self._validate_compliance_fallback(feature_data)

    def _analyze_rag_compliance(
        self, regulatory_context: List[Dict], feature_data: Dict
    ) -> Dict:
        """Analyze compliance based on RAG-retrieved regulatory context."""
        # Simple compliance analysis based on RAG results
        if not regulatory_context:
            return {
                "label": "Unknown",
                "rationale": "No regulatory context available",
                "regulations": [],
                "confidence": 0.5,
            }

        # Count compliance indicators
        compliance_indicators = 0
        risk_indicators = 0
        regulations = []

        for context in regulatory_context:
            regulations.append(context.get("regulation", "Unknown"))
            text = context.get("text", "").lower()

            # Check for compliance indicators
            if any(
                term in text
                for term in ["compliance", "compliant", "permitted", "allowed"]
            ):
                compliance_indicators += 1
            if any(
                term in text
                for term in ["violation", "prohibited", "restricted", "banned"]
            ):
                risk_indicators += 1

        # Determine compliance label
        if compliance_indicators > risk_indicators:
            label = "Compliant"
            rationale = f'Regulatory context indicates compliance with {", ".join(regulations[:2])}'
        elif risk_indicators > compliance_indicators:
            label = "Non-Compliant"
            rationale = f'Regulatory context indicates potential violations of {", ".join(regulations[:2])}'
        else:
            label = "Partially Compliant"
            rationale = f'Mixed regulatory signals for {", ".join(regulations[:2])}'

        confidence = min(0.9, 0.5 + (len(regulatory_context) * 0.1))

        return {
            "label": label,
            "rationale": rationale,
            "regulations": regulations,
            "confidence": confidence,
        }

    def _validate_compliance_fallback(self, feature_data: Dict) -> Dict:
        """Fallback compliance validation using existing rule engine."""
        label, rationale, implicated_regs = self.compliance_engine.evaluate_compliance(
            feature_data, "USA", None
        )
        return {
            "label": label,
            "rationale": rationale,
            "implicated_regs": implicated_regs,
            "confidence_score": 0.8,
        }

    def _log_compliance_evidence(self, feature_data: Dict, compliance_result: Dict):
        """Log compliance decision evidence using centralized logger."""
        if log_compliance_decision:
            evidence_data = {
                "request_id": str(uuid.uuid4()),
                "timestamp_iso": datetime.now().isoformat(),
                "agent_name": "tiktok_feature_generator",
                "decision_flag": compliance_result["label"] == "Compliant",
                "reasoning_text": compliance_result["rationale"],
                "feature_id": feature_data.get("feature_id", "unknown"),
                "feature_title": feature_data.get("title", "unknown"),
                "related_regulations": compliance_result["implicated_regs"],
                "confidence": compliance_result.get("confidence_score", 0.0),
                "retrieval_metadata": {
                    "agent_specific": "feature_generation",
                    "compliance_validation": True,
                },
                "timings_ms": {
                    "generation_ms": 0  # Will be populated if timing is tracked
                },
            }
            log_compliance_decision(evidence_data)
        else:
            # Fallback to local logging
            evidence = {
                "feature_id": feature_data.get("feature_id", "unknown"),
                "decision": compliance_result["label"],
                "reasoning": compliance_result["rationale"],
                "regulations": compliance_result["implicated_regs"],
                "timestamp": datetime.now().isoformat(),
            }
            logger.info(f"Compliance evidence logged (local): {evidence}")


def main():
    """Example usage and testing."""
    print("🚀 TikTok Feature Generator Agent")
    print("=" * 50)

    # Initialize generator
    generator = TikTokFeatureGenerator(seed=42)

    # Analyze seed data
    seed_analysis = generator.analyze_seed_data("active_learning_data/corrections.json")
    print(f"📊 Seed analysis: {seed_analysis['total_records']} records analyzed")

    # Generate features
    features = generator.generate_features(
        n=50,
        geo_filters=["USA-CA", "USA-FL", "EU"],
        target_mix={"Compliant": 0.3, "Partially Compliant": 0.3, "Non-Compliant": 0.4},
    )

    # Save outputs
    output_dir = "generated_features"
    generator.save_features(features, output_dir)
    generator.generate_distribution_report(features, output_dir)

    # Show example results
    print("\n🎯 Example Generated Features:")
    for feature in features[:3]:
        print(f'[{feature.geo_country}] "{feature.title}" → {feature.label}')
        print(f"   Reason: {feature.rationale}")
        print(f"   Regulations: {', '.join(feature.implicated_regs)}")
        print()

    print(f"✅ Generated {len(features)} features successfully!")


if __name__ == "__main__":
    main()
