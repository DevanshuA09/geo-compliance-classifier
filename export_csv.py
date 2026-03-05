#!/usr/bin/env python3

"""
CSV Export Tool for Compliance Decisions
Exports all compliance analysis data to CSV format with enhanced reasoning
"""

import csv
import json
import sqlite3
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import init_database

def flatten_json_field(json_str: str, prefix: str = "") -> Dict[str, str]:
    """Flatten JSON fields for CSV export"""
    try:
        if json_str and json_str.strip():
            data = json.loads(json_str) if isinstance(json_str, str) else json_str
            flattened = {}
            
            if isinstance(data, list):
                # Handle list of items
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        for key, value in item.items():
                            flattened[f"{prefix}_{i}_{key}"] = str(value)
                    else:
                        flattened[f"{prefix}_{i}"] = str(item)
                # Also create a concatenated version
                flattened[f"{prefix}_concatenated"] = " | ".join([str(item) for item in data])
            elif isinstance(data, dict):
                # Handle dictionary
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        flattened[f"{prefix}_{key}"] = json.dumps(value)
                    else:
                        flattened[f"{prefix}_{key}"] = str(value)
            else:
                flattened[prefix] = str(data)
            
            return flattened
    except (json.JSONDecodeError, TypeError):
        return {prefix: str(json_str) if json_str else ""}
    
    return {prefix: ""}

def export_decisions_to_csv(output_file: str = None) -> str:
    """Export all compliance decisions to CSV format"""
    
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"compliance_decisions_export_{timestamp}.csv"
    
    print(f"📊 Exporting Compliance Decisions to CSV")
    print("=" * 60)
    
    # Connect to database
    conn = sqlite3.connect('compliance_decisions.db')
    conn.row_factory = sqlite3.Row  # Enable column access by name
    cursor = conn.cursor()
    
    # Get all decisions
    cursor.execute("""
        SELECT * FROM decisions 
        ORDER BY created_at DESC
    """)
    
    decisions = cursor.fetchall()
    
    if not decisions:
        print("❌ No decisions found in database")
        return None
    
    print(f"📁 Found {len(decisions)} decisions to export")
    
    # Prepare CSV data
    csv_rows = []
    
    for decision in decisions:
        # Convert row to dictionary
        row_dict = dict(decision)
        
        # Create base CSV row
        csv_row = {
            'id': row_dict.get('id', ''),
            'created_at': row_dict.get('created_at', ''),
            'updated_at': row_dict.get('updated_at', ''),
            'feature_id': row_dict.get('feature_id', ''),
            'doc_id': row_dict.get('doc_id', ''),
            'source_path': row_dict.get('source_path', ''),
            'date': row_dict.get('date', ''),
            'feature_title': row_dict.get('feature_title', ''),
            'feature_description': row_dict.get('feature_description', ''),
            'objectives': row_dict.get('objectives', ''),
            'user_segments': row_dict.get('user_segments', ''),
            'geo_country': row_dict.get('geo_country', ''),
            'geo_state': row_dict.get('geo_state', ''),
            'domain': row_dict.get('domain', ''),
            'label': row_dict.get('label', ''),
            'rationale': row_dict.get('rationale', ''),
            'confidence_score': row_dict.get('confidence_score', ''),
            'jurisdiction': row_dict.get('jurisdiction', ''),
            'law': row_dict.get('law', ''),
            'trigger': row_dict.get('trigger', ''),
            'require_compliance': row_dict.get('require_compliance', ''),
            'analysis_confidence': row_dict.get('analysis_confidence', ''),
            'human_override': row_dict.get('human_override', ''),
            'reviewer_notes': row_dict.get('reviewer_notes', ''),
        }
        
        # Handle JSON fields with flattening
        json_fields = [
            ('implicated_regulations', 'regulations'),
            ('data_practices', 'data_practices'),
            ('risk_tags', 'risk_tags'),
            ('codename_hits_json', 'codename_hits'),
            ('citations', 'citations'),
            ('llm_output', 'llm_output')
        ]
        
        for field_name, prefix in json_fields:
            field_value = row_dict.get(field_name, '')
            flattened = flatten_json_field(field_value, prefix)
            csv_row.update(flattened)
        
        csv_rows.append(csv_row)
    
    # Get all unique column names
    all_columns = set()
    for row in csv_rows:
        all_columns.update(row.keys())
    
    # Define column order (important fields first)
    priority_columns = [
        'id', 'created_at', 'updated_at', 'feature_title', 'feature_description', 
        'label', 'confidence_score', 'rationale', 'jurisdiction', 'geo_country', 'geo_state',
        'regulations_concatenated', 'citations_concatenated', 'domain', 'trigger',
        'human_override', 'reviewer_notes'
    ]
    
    # Order columns: priority first, then alphabetical
    ordered_columns = []
    for col in priority_columns:
        if col in all_columns:
            ordered_columns.append(col)
            all_columns.remove(col)
    
    # Add remaining columns alphabetically
    ordered_columns.extend(sorted(all_columns))
    
    # Write CSV file
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=ordered_columns)
        
        # Write header
        writer.writeheader()
        
        # Write data rows
        for row in csv_rows:
            # Ensure all columns are present
            complete_row = {col: row.get(col, '') for col in ordered_columns}
            writer.writerow(complete_row)
    
    # Close database connection
    conn.close()
    
    # Generate summary
    print(f"✅ Export completed successfully!")
    print(f"📄 File: {output_file}")
    print(f"📊 Records: {len(csv_rows)}")
    print(f"📋 Columns: {len(ordered_columns)}")
    
    # Show column breakdown
    print(f"\n📝 Column Summary:")
    print(f"   • Core fields: {len([c for c in ordered_columns if not '_' in c or c.endswith('_concatenated')])}")
    print(f"   • Regulation details: {len([c for c in ordered_columns if c.startswith('regulations_')])}")
    print(f"   • Citation details: {len([c for c in ordered_columns if c.startswith('citations_')])}")
    print(f"   • LLM output details: {len([c for c in ordered_columns if c.startswith('llm_output_')])}")
    
    return output_file

def export_enhanced_summary_csv(output_file: str = None) -> str:
    """Export a simplified summary CSV with key enhanced reasoning fields"""
    
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"compliance_summary_{timestamp}.csv"
    
    print(f"\n📋 Creating Enhanced Summary CSV")
    print("=" * 50)
    
    # Connect to database
    conn = sqlite3.connect('compliance_decisions.db')
    cursor = conn.cursor()
    
    # Get key fields for summary
    cursor.execute("""
        SELECT 
            id,
            created_at,
            feature_title,
            feature_description,
            label,
            confidence_score,
            rationale,
            jurisdiction,
            geo_country,
            geo_state,
            domain,
            implicated_regulations,
            citations,
            human_override,
            trigger
        FROM decisions 
        ORDER BY created_at DESC
    """)
    
    decisions = cursor.fetchall()
    
    # Prepare summary CSV
    summary_rows = []
    
    for decision in decisions:
        # Parse JSON fields for display
        regulations = "None"
        citations = "None"
        
        try:
            if decision[11]:  # implicated_regulations
                regs_data = json.loads(decision[11]) if isinstance(decision[11], str) else decision[11]
                regulations = " | ".join(regs_data) if isinstance(regs_data, list) else str(regs_data)
        except:
            regulations = str(decision[11]) if decision[11] else "None"
        
        try:
            if decision[12]:  # citations
                cites_data = json.loads(decision[12]) if isinstance(decision[12], str) else decision[12]
                citations = " | ".join(cites_data) if isinstance(cites_data, list) else str(cites_data)
        except:
            citations = str(decision[12]) if decision[12] else "None"
        
        summary_row = {
            'ID': decision[0],
            'Created': decision[1],
            'Feature Title': decision[2],
            'Feature Description': decision[3][:200] + "..." if len(decision[3]) > 200 else decision[3],
            'Compliance Label': decision[4],
            'Confidence Score': decision[5],
            'Reasoning Summary': decision[6][:300] + "..." if len(decision[6]) > 300 else decision[6],
            'Jurisdiction': decision[7],
            'Country': decision[8],
            'State': decision[9],
            'Domain': decision[10],
            'Applicable Regulations': regulations,
            'Legal Citations': citations,
            'Human Override': decision[13] if decision[13] else "No",
            'Analysis Type': decision[14]
        }
        
        summary_rows.append(summary_row)
    
    # Write summary CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = list(summary_rows[0].keys()) if summary_rows else []
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(summary_rows)
    
    conn.close()
    
    print(f"✅ Summary export completed!")
    print(f"📄 File: {output_file}")
    print(f"📊 Records: {len(summary_rows)}")
    
    return output_file

def main():
    """Main export function"""
    
    print("🚀 Compliance Decisions CSV Export Tool")
    print("=" * 70)
    
    # Initialize database
    init_database()
    
    # Export full detailed CSV
    full_csv = export_decisions_to_csv()
    
    # Export summary CSV  
    summary_csv = export_enhanced_summary_csv()
    
    print(f"\n🎉 Export Complete!")
    print(f"📊 Generated Files:")
    print(f"   1. Full Export: {full_csv}")
    print(f"   2. Summary Export: {summary_csv}")
    print(f"\n💡 Files include enhanced reasoning, specific regulations, and legal citations!")

if __name__ == "__main__":
    main()
