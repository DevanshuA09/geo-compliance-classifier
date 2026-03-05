#!/usr/bin/env python3

"""
Process Sample Features with Enhanced Reasoning
Demonstrates the improved reasoning for your existing features
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_reasoning_engine import enhanced_compliance_analysis
from db import save_decision, init_database

def process_sample_features_enhanced():
    """Process some real features from your dataset with enhanced reasoning"""
    
    print("🚀 Processing Sample Features with Enhanced Reasoning")
    print("=" * 70)
    
    # Sample features from your dataset with proper jurisdiction mapping
    sample_features = [
        {
            'title': 'Utah Social Media Age Verification System',
            'description': 'Parental consent system for Utah minors requiring verification before account creation, including time restrictions and parental access controls as required by Utah Social Media Regulation Act',
            'jurisdiction': 'US_UT'
        },
        {
            'title': 'GDPR Consent Collection for EU Users',
            'description': 'Explicit consent collection system for EU users covering data processing, tracking, and personalization activities with granular consent options and withdrawal mechanisms',
            'jurisdiction': 'EU'
        },
        {
            'title': 'California SB976 Minor Protection Suite',
            'description': 'Comprehensive parental control dashboard with time limits, addictive design restrictions, and notification controls for California users under 18 as mandated by SB976',
            'jurisdiction': 'US_CA'
        },
        {
            'title': 'NCMEC Automated Reporting System',
            'description': 'Machine learning system for detecting and automatically reporting child sexual abuse material to NCMEC with evidence preservation and law enforcement cooperation',
            'jurisdiction': 'US'
        },
        {
            'title': 'Florida Age Verification for Social Media',
            'description': 'Age verification system preventing account creation for users under 14 in Florida with parental consent requirements and educational materials about social media risks',
            'jurisdiction': 'US_FL'
        },
        {
            'title': 'EU Digital Services Act Compliance Dashboard',
            'description': 'Transparent content moderation system with user appeal processes, risk assessments, and external auditing capabilities required under EU Digital Services Act',
            'jurisdiction': 'EU'
        }
    ]
    
    # Initialize database
    init_database()
    
    processed_results = []
    
    for i, feature in enumerate(sample_features, 1):
        print(f"\n🔍 Processing {i}/{len(sample_features)}: {feature['title']}")
        print("-" * 60)
        
        try:
            # Get enhanced analysis
            enhanced_result = enhanced_compliance_analysis(
                feature['title'],
                feature['description'],
                feature['jurisdiction']
            )
            
            compliance = enhanced_result['compliance_analysis']
            regulatory_details = enhanced_result['regulatory_details']
            
            print(f"   🎯 VERDICT: {compliance['verdict']} (Confidence: {compliance['confidence']:.2f})")
            print(f"   📚 REGULATIONS: {len(compliance['applicable_regulations'])} identified")
            for reg in compliance['applicable_regulations']:
                print(f"      • {reg}")
            
            print(f"   📖 CITATIONS: {len(regulatory_details['citations'])} specific citations")
            for citation in regulatory_details['citations'][:2]:
                print(f"      • {citation}")
            if len(regulatory_details['citations']) > 2:
                print(f"      ... and {len(regulatory_details['citations']) - 2} more")
            
            print(f"   ⚠️  RISK LEVEL: {regulatory_details['risk_level']}")
            print(f"   💡 RECOMMENDATIONS: {len(regulatory_details['recommendations'])} provided")
            
            # Create canonical record
            canonical_record = {
                'feature_id': f"enhanced_sample_{i}",
                'doc_id': f"enhanced_reasoning_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'source_path': 'enhanced_reasoning_demo',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'feature_title': feature['title'],
                'feature_description': feature['description'],
                'objectives': f"Demonstrate enhanced compliance analysis for {feature['title']}",
                'user_segments': 'Platform users with jurisdiction-specific requirements',
                'geo_country': feature['jurisdiction'].split('_')[0] if '_' in feature['jurisdiction'] else feature['jurisdiction'],
                'geo_state': feature['jurisdiction'].split('_')[1] if '_' in feature['jurisdiction'] else None,
                'domain': 'compliance_demonstration',
                'label': 'compliant' if compliance['verdict'] == 'COMPLIANT' else 'non-compliant',
                'implicated_regulations': compliance['applicable_regulations'],
                'data_practices': ['enhanced_analysis', 'regulatory_compliance'],
                'rationale': compliance['reasoning'],
                'risk_tags': [regulatory_details['risk_level'], 'enhanced_reasoning'],
                'confidence_score': float(compliance['confidence']),
                'codename_hits_json': [],
                'jurisdiction': feature['jurisdiction'],
                'law': compliance['applicable_regulations'][0] if compliance['applicable_regulations'] else 'GENERAL',
                'trigger': 'enhanced_reasoning_demonstration',
                'verdict': compliance['verdict'],
                'confidence': compliance['confidence'],
                'citations': regulatory_details['citations'],
                'reasoning': compliance['reasoning'],
                'recommendations': regulatory_details['recommendations'],
                'llm_output': {
                    'tool_used': 'enhanced_reasoning_engine',
                    'full_response': enhanced_result,
                    'processing_method': 'enhanced_demonstration',
                    'risk_level': regulatory_details['risk_level'],
                    'regulatory_details': regulatory_details,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            # Save to database
            decision_id = save_decision(canonical_record)
            print(f"   💾 Saved to database with ID: {decision_id}")
            
            processed_results.append({
                'feature': feature,
                'analysis': enhanced_result,
                'decision_id': decision_id
            })
            
        except Exception as e:
            print(f"   ❌ Error processing feature: {str(e)}")
    
    print(f"\n✅ Enhanced Processing Complete!")
    print(f"📊 Processed {len(processed_results)} features successfully")
    print("\n🎉 Key Improvements Demonstrated:")
    print("   • Specific regulatory identification")
    print("   • Detailed legal citations") 
    print("   • Risk-based confidence scoring")
    print("   • Actionable compliance recommendations")
    print("   • Jurisdiction-aware analysis")
    
    return processed_results

if __name__ == "__main__":
    process_sample_features_enhanced()
