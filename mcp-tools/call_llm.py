#!/usr/bin/env python3
"""
LLM Call Tool for MCP Server
Calls primary or backup LLM models
"""

import sys
import json
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from src.llm.production_llm_handler import ProductionLLMHandler
    import logging
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    async def main():
        try:
            # Read arguments from stdin
            input_data = json.loads(sys.stdin.read())
            prompt = input_data.get('prompt', '')
            context = input_data.get('context', '')
            model_type = input_data.get('model_type', 'primary')  # 'primary' or 'backup'
            
            if not prompt:
                raise ValueError("Prompt is required")
            
            # Initialize LLM handler
            llm_handler = ProductionLLMHandler()
            
            # Combine prompt and context
            full_prompt = f"{prompt}\n\nContext:\n{context}" if context else prompt
            
            # Call appropriate model
            if model_type == 'backup':
                # Force backup model (Gemini)
                response = await llm_handler.call_backup_llm(full_prompt)
                model_used = 'gemini-1.5-flash'
            else:
                # Use primary model with fallback
                response = await llm_handler.call_llm(full_prompt)
                model_used = getattr(llm_handler, 'last_model_used', 'unknown')
            
            # Estimate token usage (rough approximation)
            tokens_used = len(full_prompt.split()) + len(str(response).split())
            
            # Return results
            output = {
                'success': True,
                'response': response,
                'model_used': model_used,
                'tokens_used': tokens_used,
                'model_type': model_type
            }
            
            print(json.dumps(output))
            
        except Exception as e:
            logger.error(f"Error in call_llm: {e}")
            error_output = {
                'success': False,
                'error': str(e),
                'response': '',
                'model_used': 'none',
                'tokens_used': 0
            }
            print(json.dumps(error_output))
            sys.exit(1)
    
    if __name__ == "__main__":
        import asyncio
        asyncio.run(main())
        
except ImportError as e:
    # Fallback if LLM handler is not available
    error_output = {
        'success': False,
        'error': f"LLM system not available: {e}",
        'response': '',
        'model_used': 'none',
        'tokens_used': 0
    }
    print(json.dumps(error_output))
    sys.exit(1)
