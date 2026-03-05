#!/usr/bin/env python3
"""
Test script for database integration
"""

import sys
from pathlib import Path
import json

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from db import (
    init_database, save_decision, update_with_human_override,
    list_recent_decisions, get_decision_stats, search_decisions
)

def test_database_integration():
    """Test all database functions"""
    
    print("🧪 Testing Database Integration")
    print("=" * 50)
    
    # Test 1: Initialize database
    print("1. Testing database initialization...")
    success = init_database()
    if success:
        print("✅ Database initialized successfully")
    else:
        print("❌ Database initialization failed")
        return
    
    # Test 2: Save sample decisions
    print("\n2. Testing decision saving...")
    
    sample_decisions = [
        {
            'feature_id': 'test_feature_1',
            'feature_text': 'Smart content recommendation system using AI to analyze user behavior',
            'jurisdiction': 'EU',
            'law': 'GDPR',
            'trigger': 'automated_profiling',
            'verdict': 'NON_COMPLIANT',
            'confidence': 0.85,
            'citations': ['GDPR Article 22', 'GDPR Article 6'],
            'llm_output': {
                'reasoning': 'Automated decision-making requires explicit consent',
                'risk_level': 'HIGH'
            }
        },
        {
            'feature_id': 'test_feature_2',
            'feature_text': 'Basic user authentication with email and password',
            'jurisdiction': 'US',
            'law': 'CCPA',
            'trigger': 'data_collection',
            'verdict': 'COMPLIANT',
            'confidence': 0.92,
            'citations': ['CCPA Section 1798.100'],
            'llm_output': {
                'reasoning': 'Basic authentication is compliant with proper consent',
                'risk_level': 'LOW'
            }
        },
        {
            'feature_id': 'test_feature_3',
            'feature_text': 'Location tracking for delivery services',
            'jurisdiction': 'CA',
            'law': 'PIPEDA',
            'trigger': 'location_data',
            'verdict': 'ABSTAIN',
            'confidence': 0.65,
            'citations': ['PIPEDA Principle 3'],
            'llm_output': {
                'reasoning': 'Requires review of consent mechanisms',
                'risk_level': 'MEDIUM'
            }
        }
    ]
    
    decision_ids = []
    for i, decision in enumerate(sample_decisions):
        decision_id = save_decision(decision)
        if decision_id:
            decision_ids.append(decision_id)
            print(f"✅ Saved decision {i+1} with ID: {decision_id}")
        else:
            print(f"❌ Failed to save decision {i+1}")
    
    if not decision_ids:
        print("❌ No decisions saved, cannot continue tests")
        return
    
    # Test 3: List recent decisions
    print("\n3. Testing decision retrieval...")
    
    recent_decisions = list_recent_decisions(limit=10)
    print(f"✅ Retrieved {len(recent_decisions)} recent decisions")
    
    if recent_decisions:
        for decision in recent_decisions[-3:]:  # Show last 3
            print(f"   - ID {decision['id']}: {decision['feature_text'][:50]}...")
    
    # Test 4: Update with human override
    print("\n4. Testing human override...")
    
    if decision_ids:
        test_id = decision_ids[0]
        success = update_with_human_override(
            test_id,
            'YES',
            'Human reviewer determined compliance is required',
            'test_reviewer'
        )
        
        if success:
            print(f"✅ Updated decision {test_id} with human override")
        else:
            print(f"❌ Failed to update decision {test_id}")
    
    # Test 5: Get statistics
    print("\n5. Testing statistics...")
    
    stats = get_decision_stats()
    print(f"✅ Statistics retrieved:")
    print(f"   - Total decisions: {stats['total_decisions']}")
    print(f"   - Compliant: {stats['compliant']}")
    print(f"   - Non-compliant: {stats['non_compliant']}")
    print(f"   - Abstain: {stats['abstain']}")
    print(f"   - Human overrides: {stats['human_overrides']}")
    
    # Test 6: Search functionality
    print("\n6. Testing search...")
    
    search_results = search_decisions('authentication', limit=5)
    print(f"✅ Search found {len(search_results)} results for 'authentication'")
    
    # Test 7: Filtering
    print("\n7. Testing filtering...")
    
    eu_decisions = list_recent_decisions(limit=50, jurisdiction='EU')
    print(f"✅ Found {len(eu_decisions)} decisions for EU jurisdiction")
    
    gdpr_decisions = list_recent_decisions(limit=50, law='GDPR')
    print(f"✅ Found {len(gdpr_decisions)} decisions for GDPR law")
    
    print("\n" + "=" * 50)
    print("🎉 Database integration test completed!")
    
    # Show sample data
    if recent_decisions:
        print("\n📋 Sample Decision Data:")
        sample = recent_decisions[0]
        print(json.dumps({
            'id': sample['id'],
            'feature_text': sample['feature_text'][:100] + "...",
            'jurisdiction': sample['jurisdiction'],
            'law': sample['law'],
            'require_compliance': sample['require_compliance'],
            'confidence': sample['confidence'],
            'human_override': sample['human_override'],
            'created_at': sample['created_at']
        }, indent=2))

if __name__ == "__main__":
    try:
        test_database_integration()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
