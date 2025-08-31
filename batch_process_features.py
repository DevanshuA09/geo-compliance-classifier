#!/usr/bin/env python3

"""
Batch Feature Processing Script
Processes all features from feature_sample_data.csv through the complete workflow:
1. Feature preprocessing and expansion
2. Enhanced compliance analysis (with agents)
3. Database storage in canonical FeatureRecord format
4. Dashboard reflection

This demonstrates the end-to-end system with canonical schema consistency.
"""

import csv
import json
import sys
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from db import save_decision, get_decision_stats, list_recent_decisions, init_database

def extract_jurisdiction_from_description(description: str) -> str:
    """Extract jurisdiction from feature description"""
    description_lower = description.lower()
    
    # Specific jurisdiction mappings
    jurisdiction_keywords = {
        'utah': 'US_UT',
        'california': 'US_CA', 
        'florida': 'US_FL',
        'eu ': 'EU',
        'european union': 'EU',
        'digital services act': 'EU',
        'dsa': 'EU',
        'gdpr': 'EU',
        'canada': 'CA',
        'south korea': 'KR',
        'united states': 'US',
        'us federal': 'US',
        'ncmec': 'US',
        'sb976': 'US_CA',
        'ccpa': 'US_CA'
    }
    
    for keyword, jurisdiction in jurisdiction_keywords.items():
        if keyword in description_lower:
            return jurisdiction
    
    # Default to global if no specific jurisdiction found
    return 'GLOBAL'

def extract_domain_from_description(description: str) -> str:
    """Extract domain category from feature description"""
    description_lower = description.lower()
    
    domain_keywords = {
        'minor': 'child_safety',
        'child': 'child_safety', 
        'underage': 'child_safety',
        'parental': 'child_safety',
        'age': 'child_safety',
        'content': 'content_moderation',
        'moderation': 'content_moderation',
        'flagging': 'content_moderation',
        'visibility': 'content_moderation',
        'data retention': 'data_governance',
        'retention': 'data_governance',
        'privacy': 'privacy_protection',
        'tracking': 'privacy_protection',
        'personalization': 'algorithmic_systems',
        'recommendation': 'algorithmic_systems',
        'notification': 'user_engagement',
        'chat': 'communication',
        'video': 'media_sharing',
        'upload': 'media_sharing'
    }
    
    for keyword, domain in domain_keywords.items():
        if keyword in description_lower:
            return domain
    
    return 'platform_feature'

def extract_risk_tags_from_description(description: str) -> List[str]:
    """Extract risk tags from feature description"""
    description_lower = description.lower()
    risk_tags = []
    
    risk_keywords = {
        'minor': 'child_safety_risk',
        'underage': 'child_safety_risk',
        'abuse': 'high_risk_content',
        'sensitive': 'high_risk_content',
        'privacy': 'privacy_risk',
        'tracking': 'privacy_risk',
        'personal': 'data_protection_risk',
        'data': 'data_protection_risk',
        'cross-border': 'cross_jurisdiction_risk',
        'eu': 'regulatory_compliance_risk',
        'federal': 'regulatory_compliance_risk',
        'compliance': 'regulatory_compliance_risk'
    }
    
    for keyword, tag in risk_keywords.items():
        if keyword in description_lower and tag not in risk_tags:
            risk_tags.append(tag)
    
    return risk_tags

def extract_data_practices_from_description(description: str) -> List[str]:
    """Extract data practices from feature description"""
    description_lower = description.lower()
    practices = []
    
    practice_keywords = {
        'collect': 'data_collection',
        'track': 'user_tracking',
        'log': 'activity_logging',
        'detect': 'behavioral_analysis',
        'analyze': 'data_analysis',
        'store': 'data_storage',
        'monitor': 'user_monitoring',
        'profile': 'user_profiling',
        'segment': 'user_segmentation',
        'report': 'data_reporting',
        'audit': 'audit_logging'
    }
    
    for keyword, practice in practice_keywords.items():
        if keyword in description_lower and practice not in practices:
            practices.append(practice)
    
    return practices

def extract_regulations_from_description(description: str) -> List[str]:
    """Extract implicated regulations from feature description"""
    description_lower = description.lower()
    regulations = []
    
    regulation_keywords = {
        'utah social media regulation act': 'Utah Social Media Regulation Act',
        'sb976': 'California SB976',
        'ccpa': 'California Consumer Privacy Act',
        'gdpr': 'EU General Data Protection Regulation',
        'digital services act': 'EU Digital Services Act',
        'dsa': 'EU Digital Services Act',
        'ncmec': 'US NCMEC Reporting Requirements',
        'federal law': 'US Federal Child Protection Laws',
        'florida.*protection.*minor': 'Florida Online Protections for Minors'
    }
    
    for keyword, regulation in regulation_keywords.items():
        if keyword in description_lower and regulation not in regulations:
            regulations.append(regulation)
    
    return regulations

def enhanced_compliance_analysis_mock(feature_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mock enhanced compliance analysis with agentic workflow
    In production, this would call the actual MCP tools
    """
    description = feature_data['feature_description']
    jurisdiction = feature_data['geo_country']
    
    # Simulate compliance analysis based on content
    description_lower = description.lower()
    
    # Determine compliance verdict based on content analysis
    if any(term in description_lower for term in ['minor', 'underage', 'child', 'abuse']):
        if any(term in description_lower for term in ['consent', 'parental', 'protection', 'safety']):
            verdict = 'COMPLIANT'
            confidence = 0.85
            reasoning = 'Feature includes appropriate safeguards for minors with consent mechanisms'
        else:
            verdict = 'NON_COMPLIANT' 
            confidence = 0.78
            reasoning = 'Feature affects minors but lacks explicit consent or safety mechanisms'
    elif 'privacy' in description_lower or 'data' in description_lower:
        if 'consent' in description_lower or 'opt-in' in description_lower:
            verdict = 'COMPLIANT'
            confidence = 0.82
            reasoning = 'Data processing includes user consent mechanisms'
        else:
            verdict = 'NON_COMPLIANT'
            confidence = 0.75
            reasoning = 'Data processing requires explicit user consent under applicable regulations'
    else:
        verdict = 'COMPLIANT'
        confidence = 0.70
        reasoning = 'Feature appears to meet general compliance requirements'
    
    # Extract citations based on jurisdiction and content
    regulations = extract_regulations_from_description(description)
    if not regulations:
        if jurisdiction.startswith('US'):
            regulations = ['General US Privacy Laws']
        elif jurisdiction == 'EU':
            regulations = ['EU General Compliance Framework']
        else:
            regulations = ['Platform General Terms']
    
    # Simulate comprehensive analysis response
    return {
        'success': True,
        'analysis_type': 'comprehensive_agentic',
        'compliance_analysis': {
            'verdict': verdict,
            'confidence': confidence,
            'reasoning': reasoning,
            'applicable_regulations': regulations
        },
        'confidence_validation': {
            'final_confidence': confidence,
            'ensemble_agreement': min(confidence + 0.1, 1.0),
            'validation_notes': 'Multi-agent confidence validation completed'
        },
        'evidence_verification': {
            'evidence_quality_score': 0.85,
            'regulatory_references': [{'regulation': reg, 'confidence': 0.8} for reg in regulations],
            'verification_status': 'verified'
        },
        'active_learning': {
            'uncertainty_score': 1.0 - confidence,
            'requires_human_review': confidence < 0.8,
            'learning_feedback': 'Pattern stored for future analysis'
        },
        'timestamp': datetime.now().isoformat()
    }

def create_canonical_feature_record(feature_name: str, feature_description: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """Create a canonical FeatureRecord format entry"""
    
    # Extract geographic and domain information
    jurisdiction = extract_jurisdiction_from_description(feature_description)
    geo_country = jurisdiction.split('_')[0] if '_' in jurisdiction else jurisdiction
    geo_state = jurisdiction.split('_')[1] if '_' in jurisdiction else None
    domain = extract_domain_from_description(feature_description)
    
    # Extract compliance information
    compliance_analysis = analysis_result['compliance_analysis']
    verdict = compliance_analysis['verdict']
    confidence = compliance_analysis['confidence']
    reasoning = compliance_analysis['reasoning']
    regulations = compliance_analysis['applicable_regulations']
    
    # Map verdict to label
    label_mapping = {
        'COMPLIANT': 'compliant',
        'NON_COMPLIANT': 'non-compliant',
        'ABSTAIN': 'partially-compliant'
    }
    label = label_mapping.get(verdict, 'partially-compliant')
    
    # Generate feature ID
    feature_id = f"feature_{feature_name.lower().replace(' ', '_').replace('-', '_')}"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create canonical FeatureRecord
    canonical_record = {
        # Core canonical FeatureRecord fields
        'feature_id': feature_id,
        'doc_id': f"batch_processing_{timestamp}",
        'source_path': 'feature_sample_data.csv',
        'date': datetime.now().strftime('%Y-%m-%d'),
        'feature_title': feature_name,
        'feature_description': feature_description,
        'objectives': f"Implement {feature_name} with compliance requirements",
        'user_segments': 'Platform users with geographic and age-based targeting',
        'geo_country': geo_country if geo_country != 'GLOBAL' else None,
        'geo_state': geo_state,
        'domain': domain,
        'label': label,
        'implicated_regulations': regulations,
        'data_practices': extract_data_practices_from_description(feature_description),
        'rationale': reasoning,
        'risk_tags': extract_risk_tags_from_description(feature_description),
        'confidence_score': float(confidence),
        'codename_hits_json': [],  # Would be populated by terminology extraction
        
        # Analysis-specific fields for compatibility
        'jurisdiction': jurisdiction,
        'law': regulations[0] if regulations else 'GENERAL',
        'trigger': 'batch_processing_analysis',
        'verdict': verdict,
        'confidence': confidence,
        'citations': regulations,
        'reasoning': reasoning,
        'llm_output': {
            'tool_used': 'enhanced_compliance_analysis',
            'full_response': analysis_result,
            'processing_method': 'batch_workflow',
            'timestamp': datetime.now().isoformat()
        }
    }
    
    return canonical_record

def process_feature_batch(csv_file_path: str) -> List[Dict[str, Any]]:
    """Process all features from CSV file through the complete workflow"""
    
    print("🚀 Starting Batch Feature Processing")
    print("=" * 60)
    
    # Initialize database
    init_database()
    
    # Read CSV file
    features = []
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            features.append({
                'name': row['feature_name'],
                'description': row['feature_description']
            })
    
    print(f"📁 Loaded {len(features)} features from {csv_file_path}")
    
    processed_results = []
    decision_ids = []
    
    for i, feature in enumerate(features, 1):
        print(f"\n⚙️ Processing Feature {i}/{len(features)}: {feature['name'][:50]}...")
        
        try:
            # Step 1: Enhanced Compliance Analysis (Mock)
            print(f"   🔍 Running enhanced compliance analysis...")
            analysis_result = enhanced_compliance_analysis_mock({
                'feature_name': feature['name'],
                'feature_description': feature['description'],
                'geo_country': extract_jurisdiction_from_description(feature['description'])
            })
            
            # Step 2: Create Canonical FeatureRecord
            print(f"   📋 Creating canonical FeatureRecord...")
            canonical_record = create_canonical_feature_record(
                feature['name'], 
                feature['description'], 
                analysis_result
            )
            
            # Step 3: Save to Database
            print(f"   💾 Saving to database...")
            decision_id = save_decision(canonical_record)
            
            if decision_id:
                decision_ids.append(decision_id)
                processed_results.append({
                    'feature_name': feature['name'],
                    'decision_id': decision_id,
                    'verdict': canonical_record['verdict'],
                    'confidence': canonical_record['confidence'],
                    'jurisdiction': canonical_record['jurisdiction'],
                    'success': True
                })
                print(f"   ✅ Saved with ID: {decision_id}")
            else:
                processed_results.append({
                    'feature_name': feature['name'],
                    'success': False,
                    'error': 'Database save failed'
                })
                print(f"   ❌ Failed to save to database")
            
            # Brief pause to avoid overwhelming the system
            time.sleep(0.1)
            
        except Exception as e:
            print(f"   ❌ Error processing feature: {e}")
            processed_results.append({
                'feature_name': feature['name'],
                'success': False,
                'error': str(e)
            })
    
    return processed_results, decision_ids

def generate_processing_report(results: List[Dict[str, Any]], decision_ids: List[int]):
    """Generate a comprehensive processing report"""
    
    print("\n" + "=" * 60)
    print("📊 BATCH PROCESSING REPORT")
    print("=" * 60)
    
    # Summary statistics
    total_features = len(results)
    successful_features = len([r for r in results if r.get('success', False)])
    failed_features = total_features - successful_features
    
    print(f"📈 Processing Summary:")
    print(f"   Total Features: {total_features}")
    print(f"   Successfully Processed: {successful_features}")
    print(f"   Failed: {failed_features}")
    print(f"   Success Rate: {(successful_features/total_features)*100:.1f}%")
    
    # Verdict distribution
    verdicts = {}
    jurisdictions = {}
    
    for result in results:
        if result.get('success'):
            verdict = result.get('verdict', 'UNKNOWN')
            jurisdiction = result.get('jurisdiction', 'UNKNOWN')
            
            verdicts[verdict] = verdicts.get(verdict, 0) + 1
            jurisdictions[jurisdiction] = jurisdictions.get(jurisdiction, 0) + 1
    
    print(f"\n🎯 Compliance Verdicts:")
    for verdict, count in verdicts.items():
        print(f"   {verdict}: {count}")
    
    print(f"\n🌍 Jurisdiction Distribution:")
    for jurisdiction, count in jurisdictions.items():
        print(f"   {jurisdiction}: {count}")
    
    # Database statistics
    print(f"\n💾 Database Status:")
    db_stats = get_decision_stats()
    for key, value in db_stats.items():
        if key != 'jurisdiction_breakdown':
            print(f"   {key.replace('_', ' ').title()}: {value}")
    
    # Recent decisions sample
    print(f"\n📋 Recent Decisions (Sample):")
    recent_decisions = list_recent_decisions(limit=5)
    for decision in recent_decisions:
        print(f"   ID {decision['id']}: {decision.get('feature_title', 'N/A')[:40]}... -> {decision.get('label', 'N/A')}")
    
    # Failed features
    if failed_features > 0:
        print(f"\n❌ Failed Features:")
        for result in results:
            if not result.get('success', False):
                print(f"   {result['feature_name']}: {result.get('error', 'Unknown error')}")
    
    print(f"\n🎉 Batch processing complete! {successful_features} features now in database.")
    print("   You can view them in the Streamlit dashboard History tab.")

def main():
    """Main execution function"""
    
    # Path to the CSV file
    csv_file = "feature_sample_data.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ Error: CSV file '{csv_file}' not found!")
        print("   Make sure feature_sample_data.csv is in the current directory.")
        return
    
    try:
        # Process all features
        results, decision_ids = process_feature_batch(csv_file)
        
        # Generate comprehensive report
        generate_processing_report(results, decision_ids)
        
        # Save processing results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"batch_processing_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump({
                'processing_timestamp': datetime.now().isoformat(),
                'total_features': len(results),
                'successful_features': len([r for r in results if r.get('success', False)]),
                'decision_ids': decision_ids,
                'detailed_results': results
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        print(f"\n🚀 Next Steps:")
        print(f"   1. Run: streamlit run app.py")
        print(f"   2. Navigate to the 'History' tab")
        print(f"   3. View all processed features with canonical FeatureRecord format")
        print(f"   4. Use search/filter to explore the compliance decisions")
        print(f"   5. Review any features requiring human override")
        
    except Exception as e:
        print(f"❌ Critical error during batch processing: {e}")
        return

if __name__ == "__main__":
    main()
