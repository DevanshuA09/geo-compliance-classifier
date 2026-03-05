#!/usr/bin/env python3

"""
Debug CSV parsing
"""

import csv

def debug_csv():
    """Debug CSV file parsing"""
    print("🔍 Debugging CSV file parsing...")
    
    with open("feature_sample_data.csv", 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        print(f"Column names: {reader.fieldnames}")
        
        for i, row in enumerate(reader):
            if i < 3:  # Show first 3 rows
                print(f"Row {i+1}: {row}")
            else:
                break

if __name__ == "__main__":
    debug_csv()
