#!/usr/bin/env python3
"""
Test script for enhanced MCP tools
"""

import json
import sys
from pathlib import Path

def test_enhanced_compliance_analysis():
    """Test the enhanced compliance analysis tool"""
    print("Testing Enhanced Compliance Analysis...")
    
    # Load demo data
    with open('demo_data.json', 'r') as f:
        demo_data = json.load(f)
    
    sample_feature = demo_data['sample_features'][0]
    
    test_input = {
        'feature_data': sample_feature,
        'jurisdiction': 'EU'
    }
    
    print(f"Input: {json.dumps(test_input, indent=2)}")
    print("=" * 50)
    
    # Import and run the tool directly
    try:
        from pathlib import Path
        import subprocess
        
        tool_path = Path(__file__).parent / "mcp-tools/enhanced_compliance_analysis.py"
        
        result = subprocess.run(
            [sys.executable, str(tool_path)],
            input=json.dumps(test_input),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                print("SUCCESS!")
                print(json.dumps(output, indent=2))
            except json.JSONDecodeError:
                print("Output was not valid JSON:")
                print(result.stdout)
        else:
            print("FAILED!")
            print("STDERR:", result.stderr)
            print("STDOUT:", result.stdout)
            
    except Exception as e:
        print(f"Exception: {e}")

def test_evidence_backed_retrieval():
    """Test the evidence-backed retrieval tool"""
    print("\n" + "=" * 60)
    print("Testing Evidence-Backed Retrieval...")
    
    with open('demo_data.json', 'r') as f:
        demo_data = json.load(f)
    
    sample_feature = demo_data['sample_features'][1]  # Location services
    
    test_input = {
        'feature_data': sample_feature,
        'jurisdiction': 'EU',
        'max_results': 5
    }
    
    print(f"Input: {json.dumps(test_input, indent=2)}")
    print("=" * 50)
    
    try:
        from pathlib import Path
        import subprocess
        
        tool_path = Path(__file__).parent / "mcp-tools/evidence_backed_retrieval.py"
        
        result = subprocess.run(
            [sys.executable, str(tool_path)],
            input=json.dumps(test_input),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                print("SUCCESS!")
                print(json.dumps(output, indent=2))
            except json.JSONDecodeError:
                print("Output was not valid JSON:")
                print(result.stdout)
        else:
            print("FAILED!")
            print("STDERR:", result.stderr)
            
    except Exception as e:
        print(f"Exception: {e}")

def test_orchestrator():
    """Test the enhanced MCP orchestrator"""
    print("\n" + "=" * 60)
    print("Testing Enhanced MCP Orchestrator...")
    
    with open('demo_data.json', 'r') as f:
        demo_data = json.load(f)
    
    sample_feature = demo_data['sample_features'][2]  # Biometric auth
    
    test_input = {
        'action': 'comprehensive_analysis',
        'feature_data': sample_feature,
        'jurisdiction': 'US'
    }
    
    print(f"Input: {json.dumps(test_input, indent=2)}")
    print("=" * 50)
    
    try:
        from pathlib import Path
        import subprocess
        
        tool_path = Path(__file__).parent / "mcp-tools/enhanced_mcp_orchestrator.py"
        
        result = subprocess.run(
            [sys.executable, str(tool_path)],
            input=json.dumps(test_input),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                print("SUCCESS!")
                print(json.dumps(output, indent=2))
            except json.JSONDecodeError:
                print("Output was not valid JSON:")
                print(result.stdout)
        else:
            print("FAILED!")
            print("STDERR:", result.stderr)
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("Enhanced MCP Tools Test Suite")
    print("=" * 60)
    
    try:
        test_enhanced_compliance_analysis()
        test_evidence_backed_retrieval()
        test_orchestrator()
        
        print("\n" + "=" * 60)
        print("Test suite completed!")
        
    except KeyboardInterrupt:
        print("\nTest suite interrupted by user")
    except Exception as e:
        print(f"\nTest suite failed with error: {e}")
