#!/usr/bin/env python3
"""
Compliance Analysis Tool for MCP Server
Performs compliance analysis using RAG + LLM pipeline
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
    from src.rag.enhanced_rag import EnhancedRAG
    import logging
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    async def main():
        try:
            # Read arguments from stdin
            input_data = json.loads(sys.stdin.read())
            feature_data = input_data.get('feature_data', {})
            jurisdiction = input_data.get('jurisdiction', 'EU')
            
            if not feature_data:
                raise ValueError("Feature data is required")
            
            # Initialize components
            llm_handler = ProductionLLMHandler()
            rag = EnhancedRAG()
            
            # Convert feature data to text for analysis
            feature_text = json.dumps(feature_data, indent=2)
            
            # Create compliance analysis query
            query = f"Analyze compliance for {jurisdiction} jurisdiction: {feature_text}"
            
            # Retrieve relevant regulatory documents
            retrieved_docs = rag.retrieve_and_rerank(query, top_k=5)
            
            # Build context from retrieved documents
            context = "\n\n".join([
                f"Document: {doc.get('metadata', {}).get('source', 'Unknown')}\n{doc.get('content', '')}"
                for doc in retrieved_docs[:3]  # Use top 3 documents
            ])
            
            # Create compliance analysis prompt
            compliance_prompt = f"""
You are a compliance expert analyzing a software feature for regulatory compliance.

JURISDICTION: {jurisdiction}

FEATURE TO ANALYZE:
{feature_text}

RELEVANT REGULATIONS:
{context}

Please analyze the feature for compliance and provide your response in the following JSON format:

{{
    "verdict": "COMPLIANT|NON_COMPLIANT|ABSTAIN",
    "confidence": 0.0-1.0,
    "reasoning": "Detailed explanation of the analysis",
    "citations": ["List of specific regulations or articles referenced"],
    "recommendations": ["List of recommendations if non-compliant"],
    "risk_level": "LOW|MEDIUM|HIGH|CRITICAL"
}}

Be thorough and cite specific regulations. If uncertain, use ABSTAIN verdict.
"""
            
            # Get LLM analysis
            llm_response = await llm_handler.analyze_compliance(
                compliance_prompt,
                feature_data
            )
            
            # Parse LLM response
            try:
                if isinstance(llm_response, dict):
                    analysis_result = llm_response
                else:
                    # Try to extract JSON from response text
                    import re
                    json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                    if json_match:
                        analysis_result = json.loads(json_match.group())
                    else:
                        raise ValueError("Could not parse LLM response as JSON")
                        
            except (json.JSONDecodeError, ValueError):
                # Fallback analysis
                analysis_result = {
                    "verdict": "ABSTAIN",
                    "confidence": 0.5,
                    "reasoning": f"LLM analysis completed but response parsing failed. Raw response: {llm_response}",
                    "citations": [doc.get('metadata', {}).get('source', 'Unknown') for doc in retrieved_docs[:2]],
                    "recommendations": ["Manual review recommended due to parsing error"],
                    "risk_level": "MEDIUM"
                }
            
            # Add metadata
            output = {
                'success': True,
                'verdict': analysis_result.get('verdict', 'ABSTAIN'),
                'confidence': float(analysis_result.get('confidence', 0.5)),
                'reasoning': analysis_result.get('reasoning', ''),
                'citations': analysis_result.get('citations', []),
                'recommendations': analysis_result.get('recommendations', []),
                'risk_level': analysis_result.get('risk_level', 'MEDIUM'),
                'jurisdiction': jurisdiction,
                'documents_used': len(retrieved_docs),
                'model_used': getattr(llm_handler, 'last_model_used', 'unknown')
            }
            
            print(json.dumps(output))
            
        except Exception as e:
            logger.error(f"Error in check_compliance: {e}")
            error_output = {
                'success': False,
                'error': str(e),
                'verdict': 'ABSTAIN',
                'confidence': 0.0,
                'reasoning': f'Analysis failed: {e}',
                'citations': [],
                'recommendations': ['Manual review required due to system error'],
                'risk_level': 'HIGH'
            }
            print(json.dumps(error_output))
            sys.exit(1)
    
    if __name__ == "__main__":
        import asyncio
        asyncio.run(main())
        
except ImportError as e:
    # Fallback if components are not available
    error_output = {
        'success': False,
        'error': f"Compliance analysis system not available: {e}",
        'verdict': 'ABSTAIN',
        'confidence': 0.0,
        'reasoning': f'System components not available: {e}',
        'citations': [],
        'recommendations': ['System setup required'],
        'risk_level': 'HIGH'
    }
    print(json.dumps(error_output))
    sys.exit(1)
