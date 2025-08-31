#!/usr/bin/env python3

"""
Test and Fix Jurisdiction-Specific Reasoning
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_reasoning_engine import enhanced_compliance_analysis

def test_jurisdiction_specific_features():
    """Test jurisdiction-specific features with enhanced reasoning"""
    
    test_features = [
        {
            'title': 'Utah Social Media Age Verification',
            'description': 'Implement parental consent system for Utah minors to comply with Utah Social Media Regulation Act requirements',
            'jurisdiction': 'US_UT'
        },
        {
            'title': 'GDPR Data Processing Consent',
            'description': 'Collect explicit user consent for personal data processing and tracking activities in EU markets under GDPR',
            'jurisdiction': 'EU'
        },
        {
            'title': 'California SB976 Parental Controls',
            'description': 'Provide parental dashboard for time limits and addictive design restrictions for California minors under SB976',
            'jurisdiction': 'US_CA'
        },
        {
            'title': 'NCMEC Abuse Detection System',
            'description': 'Automated detection and reporting of child sexual abuse material to NCMEC as required by federal law',
            'jurisdiction': 'US'
        },
        {
            'title': 'Florida Minor Protection Dashboard',
            'description': 'Age verification and account restrictions for users under 14 in Florida per Online Protection for Minors Act',
            'jurisdiction': 'US_FL'
        },
        {
            'title': 'EU DSA Content Moderation',
            'description': 'Transparent content moderation system with appeal processes required under Digital Services Act',
            'jurisdiction': 'EU'
        }
    ]
    
    print("🧪 Testing Jurisdiction-Specific Enhanced Reasoning")
    print("=" * 70)
    
    for i, feature in enumerate(test_features, 1):
        print(f"\n📍 TEST {i}: {feature['jurisdiction']} - {feature['title']}")
        print("-" * 70)
        
        result = enhanced_compliance_analysis(
            feature['title'],
            feature['description'],
            feature['jurisdiction']
        )
        
        compliance = result['compliance_analysis']
        details = result['regulatory_details']
        
        print(f"🎯 VERDICT: {compliance['verdict']} (Confidence: {compliance['confidence']:.2f})")
        print(f"📋 REASONING: {compliance['reasoning']}")
        print(f"📚 REGULATIONS ({len(compliance['applicable_regulations'])}):")
        for reg in compliance['applicable_regulations']:
            print(f"   • {reg}")
        print(f"📖 CITATIONS ({len(details['citations'])}):")
        for citation in details['citations'][:3]:  # Show first 3
            print(f"   • {citation}")
        if len(details['citations']) > 3:
            print(f"   ... and {len(details['citations']) - 3} more")
        print(f"⚠️  RISK LEVEL: {details['risk_level']}")
        print(f"💡 RECOMMENDATIONS ({len(details['recommendations'])}):")
        for rec in details['recommendations'][:3]:  # Show first 3
            print(f"   {rec}")
        if len(details['recommendations']) > 3:
            print(f"   ... and {len(details['recommendations']) - 3} more")

if __name__ == "__main__":
    test_jurisdiction_specific_features()
