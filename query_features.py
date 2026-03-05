#!/usr/bin/env python3
"""
Simple Feature Artifact Query Tool
Query your compliance system for feature-related legal requirements
"""

import json
import sys
from pathlib import Path
from retriever.faiss_retriever import FaissRetriever

def create_config():
    """Create configuration for FAISS retriever."""
    return {
        'embedding': {
            'model_name': 'sentence-transformers/all-MiniLM-L6-v2',
            'dimension': 384
        },
        'rag': {
            'vectorstore': {
                'index_path': 'index/faiss/index.faiss',
                'id_map_path': 'index/faiss/id_map.jsonl',
                'metric': 'ip',
                'normalize': True
            }
        }
    }

def query_features(query, top_k=5):
    """Query the feature compliance system."""
    try:
        print(f'🔍 Querying: "{query}"')
        print('Initializing FAISS retriever...')
        
        config = create_config()
        retriever = FaissRetriever(config)
        print('✅ FAISS retriever initialized successfully!')
        
        results = retriever.retrieve(query, top_k=top_k)
        
        print(f'\n📊 Found {len(results)} results:')
        for i, result in enumerate(results, 1):
            print(f'\n[{i}] {result.law_name} ({result.jurisdiction})')
            print(f'    Section: {result.section_label}')
            print(f'    Score: {result.score:.3f}')
            print(f'    Text: {result.snippet[:300]}...')
            
        return results
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function for command line usage."""
    if len(sys.argv) < 2:
        print("Usage: python query_features.py 'your query here' [number_of_results]")
        print("\nExample queries:")
        print("  python query_features.py 'Does this feature require dedicated logic to comply with region-specific legal obligations?'")
        print("  python query_features.py 'How many features have we rolled out to ensure compliance with this regulation?' 10")
        print("\nOr run interactively:")
        print("  python query_features.py")
        return
    
    if len(sys.argv) == 1:
        # Interactive mode
        print("🎯 Feature Artifact Query Tool")
        print("Enter your queries (type 'quit' to exit):")
        print("-" * 50)
        
        while True:
            try:
                query = input("\n🔍 Query: ").strip()
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                if not query:
                    continue
                    
                top_k = input("📊 Number of results (default 5): ").strip()
                top_k = int(top_k) if top_k.isdigit() else 5
                
                query_features(query, top_k)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    else:
        # Command line mode
        query = sys.argv[1]
        top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        
        query_features(query, top_k)

if __name__ == "__main__":
    main()
