#!/usr/bin/env python3
"""
System Status Tool for MCP Server
Returns status of all system components
"""

import sys
import json
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def check_component_status():
    """Check status of all system components"""
    status = {
        'llm_handler': False,
        'rag_system': False,
        'index_available': False,
        'env_configured': False,
        'python_packages': False
    }
    
    # Check LLM Handler
    try:
        from src.llm.production_llm_handler import ProductionLLMHandler
        status['llm_handler'] = True
    except ImportError:
        pass
    
    # Check RAG System
    try:
        from src.rag.enhanced_rag import EnhancedRAG
        status['rag_system'] = True
    except ImportError:
        pass
    
    # Check FAISS Index
    index_path = project_root / 'index'
    if index_path.exists() and (index_path / 'faiss').exists():
        status['index_available'] = True
    
    # Check Environment Configuration
    env_path = project_root / '.env'
    if env_path.exists():
        status['env_configured'] = True
    
    # Check Required Packages
    try:
        import sentence_transformers
        import faiss
        import openai
        import google.generativeai
        status['python_packages'] = True
    except ImportError:
        pass
    
    return status

def get_system_metrics():
    """Get system performance metrics"""
    import psutil
    import time
    
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'timestamp': time.time()
    }

def main():
    try:
        # Read arguments from stdin (not used for status check)
        input_data = json.loads(sys.stdin.read())
        
        # Get component status
        component_status = check_component_status()
        
        # Get system metrics
        try:
            system_metrics = get_system_metrics()
        except ImportError:
            system_metrics = {
                'cpu_percent': 'unavailable',
                'memory_percent': 'unavailable',
                'disk_usage': 'unavailable',
                'timestamp': 'unavailable'
            }
        
        # Calculate overall health
        healthy_components = sum(component_status.values())
        total_components = len(component_status)
        health_percentage = (healthy_components / total_components) * 100
        
        overall_status = 'healthy' if health_percentage >= 80 else 'degraded' if health_percentage >= 50 else 'unhealthy'
        
        # Return status
        output = {
            'success': True,
            'overall_status': overall_status,
            'health_percentage': health_percentage,
            'components': component_status,
            'system_metrics': system_metrics,
            'project_root': str(project_root),
            'python_version': sys.version
        }
        
        print(json.dumps(output))
        
    except Exception as e:
        error_output = {
            'success': False,
            'error': str(e),
            'overall_status': 'error',
            'health_percentage': 0,
            'components': {},
            'system_metrics': {}
        }
        print(json.dumps(error_output))
        sys.exit(1)

if __name__ == "__main__":
    main()
