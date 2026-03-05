#!/usr/bin/env python3
"""
RAG Document Retrieval Tool for MCP Server
Retrieves relevant documents using FAISS + BGE embeddings
"""

import sys
import json
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from src.rag.enhanced_rag import EnhancedRAG
    import logging
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    def main():
        try:
            # Read arguments from stdin
            input_data = json.loads(sys.stdin.read())
            query = input_data.get('query', '')
            top_k = input_data.get('top_k', 5)
            
            if not query:
                raise ValueError("Query is required")
            
            # Initialize RAG system
            rag = EnhancedRAG()
            
            # Retrieve documents
            results = rag.retrieve_and_rerank(query, top_k=top_k)
            
            # Format results
            documents = []
            scores = []
            
            for result in results:
                documents.append({
                    'content': result.get('content', ''),
                    'metadata': result.get('metadata', {}),
                    'source': result.get('metadata', {}).get('source', 'unknown')
                })
                scores.append(result.get('rerank_score', result.get('score', 0.0)))
            
            # Return results
            output = {
                'success': True,
                'documents': documents,
                'scores': scores,
                'query': query,
                'retrieved_count': len(documents)
            }
            
            print(json.dumps(output))
            
        except Exception as e:
            logger.error(f"Error in retrieve_docs: {e}")
            error_output = {
                'success': False,
                'error': str(e),
                'documents': [],
                'scores': []
            }
            print(json.dumps(error_output))
            sys.exit(1)
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    # Fallback if enhanced RAG is not available
    error_output = {
        'success': False,
        'error': f"RAG system not available: {e}",
        'documents': [],
        'scores': []
    }
    print(json.dumps(error_output))
    sys.exit(1)
