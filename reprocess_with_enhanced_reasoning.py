#!/usr/bin/env python3

"""
Reprocess Features with Enhanced Reasoning
Re-analyzes existing features using the enhanced reasoning engine
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_reasoning_engine import enhanced_compliance_analysis
from db import init_database

def reprocess_features_with_enhanced_reasoning(limit=10):
    """Reprocess existing features with enhanced reasoning"""
    
    print("🔄 Reprocessing Features with Enhanced Reasoning")
    print("=" * 60)
    
    # Connect to database
    conn = sqlite3.connect('compliance_decisions.db')
    cursor = conn.cursor()
    
    # Get features that need reprocessing (those with generic reasoning)
    cursor.execute("""
        SELECT id, feature_title, feature_description, jurisdiction, rationale
        FROM decisions 
        WHERE rationale LIKE '%general compliance requirements%' 
           OR rationale LIKE '%Platform General Terms%'
           OR implicated_regulations = '["Platform General Terms"]'
        ORDER BY id DESC 
        LIMIT ?
    """, (limit,))
    
    features_to_reprocess = cursor.fetchall()
    
    print(f"📁 Found {len(features_to_reprocess)} features needing enhanced analysis")
    
    for i, (feature_id, title, description, jurisdiction, old_reasoning) in enumerate(features_to_reprocess, 1):
        print(f"\n⚙️ Reprocessing {i}/{len(features_to_reprocess)}: {title[:50]}...")
        print(f"   🔍 Old reasoning: {old_reasoning[:60]}...")
        
        try:
            # Get enhanced analysis
            enhanced_result = enhanced_compliance_analysis(
                title, 
                description, 
                jurisdiction or 'GLOBAL'
            )
            
            compliance = enhanced_result['compliance_analysis']
            regulatory_details = enhanced_result['regulatory_details']
            
            # Update database with enhanced reasoning
            cursor.execute("""
                UPDATE decisions SET
                    rationale = ?,
                    implicated_regulations = ?,
                    citations = ?,
                    confidence_score = ?,
                    risk_tags = ?,
                    llm_output = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                compliance['reasoning'],
                str(compliance['applicable_regulations']),
                str(regulatory_details['citations']),
                compliance['confidence'],
                str(regulatory_details.get('risk_level', 'medium_risk')),
                str(enhanced_result),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                feature_id
            ))
            
            print(f"   ✅ Updated with enhanced reasoning")
            print(f"   📋 New reasoning: {compliance['reasoning'][:60]}...")
            print(f"   📚 Regulations: {len(compliance['applicable_regulations'])} identified")
            print(f"   📖 Citations: {len(regulatory_details['citations'])} added")
            
        except Exception as e:
            print(f"   ❌ Error processing feature {feature_id}: {str(e)}")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"\n✅ Reprocessing complete! {len(features_to_reprocess)} features updated")
    print("\n📊 Summary of improvements:")
    print("   • Detailed regulatory analysis")
    print("   • Specific legal citations")
    print("   • Risk-based reasoning")
    print("   • Compliance recommendations")

if __name__ == "__main__":
    # Initialize database
    init_database()
    
    # Reprocess features
    reprocess_features_with_enhanced_reasoning(15)  # Reprocess up to 15 features
