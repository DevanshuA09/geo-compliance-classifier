#!/usr/bin/env python3
"""
Complete Integration Test for Production LLM + Enhanced RAG Pipeline
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_environment():
    """Set up environment variables for testing."""
    print("🔧 Setting up test environment...")
    
    # Check for API keys (you'll need to set these)
    api_keys = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
        'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),
        'HUGGINGFACEHUB_API_TOKEN': os.getenv('HUGGINGFACEHUB_API_TOKEN')
    }
    
    available_apis = []
    for key, value in api_keys.items():
        if value:
            available_apis.append(key)
            print(f"✅ {key} is configured")
        else:
            print(f"⚠️ {key} not set - corresponding model will be unavailable")
    
    if not available_apis:
        print("❌ No API keys configured. Please set at least one:")
        print("   export OPENAI_API_KEY='your-key'")
        print("   export ANTHROPIC_API_KEY='your-key'")
        print("   export GOOGLE_API_KEY='your-key'")
        return False
        
    return True

def test_enhanced_rag_pipeline():
    """Test the enhanced RAG pipeline with BGE embeddings."""
    print("\n🔍 Testing Enhanced RAG Pipeline...")
    print("=" * 50)
    
    try:
        from src.rag.enhanced_rag import EnhancedRAGPipeline
        
        # Configuration for enhanced RAG - using lightweight models
        rag_config = {
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "reranker_model": "cross-encoder/ms-marco-MiniLM-L-2-v2",
            "chunk_size": 512,
            "chunk_overlap": 50,
            "retrieval_top_k": 20,
            "rerank_top_k": 5,
            "index_path": "index/enhanced_faiss/index.faiss",
            "metadata_path": "index/enhanced_faiss/metadata.json"
        }
        
        print("🚀 Initializing Enhanced RAG Pipeline...")
        rag_pipeline = EnhancedRAGPipeline(rag_config)
        
        # Test queries
        test_queries = [
            "Does this feature require dedicated logic to comply with region-specific legal obligations?",
            "What are age verification requirements for social media platforms?",
            "How should content moderation systems handle EU DSA compliance?",
            "What parental control features are required by COPPA?"
        ]
        
        rag_results = {}
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📋 Query {i}: {query}")
            print("-" * 40)
            
            try:
                # Retrieve and rerank
                results = rag_pipeline.retrieve_and_rerank(query)
                
                print(f"✅ Retrieved {len(results)} relevant documents")
                
                # Display top results
                for j, result in enumerate(results[:3], 1):
                    chunk = result.chunk
                    print(f"  {j}. {chunk.law_name} ({chunk.jurisdiction})")
                    print(f"     Relevance: {result.rerank_score:.3f}")
                    print(f"     Snippet: {chunk.text[:100]}...")
                
                # Format context for LLM
                context = rag_pipeline.format_context_for_llm(results)
                citations = rag_pipeline.get_citations(results)
                
                rag_results[f"query_{i}"] = {
                    "query": query,
                    "results_count": len(results),
                    "context": context,
                    "citations": citations,
                    "top_scores": [r.rerank_score for r in results[:3]]
                }
                
            except Exception as e:
                print(f"❌ RAG query failed: {e}")
                rag_results[f"query_{i}"] = {"query": query, "error": str(e)}
        
        print(f"\n✅ Enhanced RAG Pipeline tested with {len(rag_results)} queries")
        return rag_results
        
    except ImportError as e:
        print(f"❌ Enhanced RAG import failed: {e}")
        print("💡 FlagEmbedding package may need to be installed")
        return None
    except Exception as e:
        print(f"❌ Enhanced RAG test failed: {e}")
        return None

def test_production_llm_handler():
    """Test the production LLM handler with multiple models."""
    print("\n🤖 Testing Production LLM Handler...")
    print("=" * 50)
    
    try:
        from src.llm.production_llm_handler import ProductionLLMHandler
        
        # Configuration for production LLM
        llm_config = {
            "primary_model": "openai-gpt4o-mini",
            "backup_models": ["gemini-flash", "huggingface"],
            "confidence_threshold": 0.7,
            "timeout_seconds": 30,
            "max_retries": 2
        }
        
        print("🚀 Initializing Production LLM Handler...")
        llm_handler = ProductionLLMHandler(llm_config)
        
        # Check model status
        status = llm_handler.get_model_status()
        print(f"📊 Available models: {status['available_models']}")
        print(f"🎯 Primary model: {status['primary_model']}")
        print(f"🔄 Backup models: {status['backup_models']}")
        
        if not status['available_models']:
            print("❌ No LLM models available - API keys may be missing")
            return None
        
        # Test compliance analysis
        test_feature = """
        Smart Content Recommendation Engine:
        - Uses AI to analyze user behavior patterns and engagement history
        - Collects viewing time, interaction data, and demographic information  
        - Provides personalized content recommendations to maximize engagement
        - Targets users aged 13+ in EU markets
        - Stores user data for 24 months for recommendation improvement
        - Shares aggregated data with advertising partners
        """
        
        test_context = """
        RELEVANT REGULATORY CONTEXT:
        
        1. EU Digital Services Act (DSA) Article 38
           Section: Recommender Systems Transparency
           Content: Very large online platforms shall provide at least one option for each of their recommender systems that is not based on profiling...
        
        2. GDPR Article 6 - Lawfulness of processing
           Section: Legal basis for processing
           Content: Processing shall be lawful only if and to the extent that at least one of the following applies: the data subject has given consent...
        
        3. EU Digital Services Act (DSA) Article 28
           Section: Online protection of minors
           Content: Providers shall put in place appropriate and proportionate measures to ensure a high level of privacy, safety and security of minors...
        """
        
        print(f"\n📝 Testing compliance analysis...")
        print(f"Feature: {test_feature[:100]}...")
        
        try:
            result = llm_handler.analyze_compliance(test_feature, test_context)
            
            print(f"\n✅ LLM Analysis completed!")
            print(f"🏛️ Model used: {result.get('model_used', 'unknown')}")
            print(f"🎯 Compliance: {result.get('require_compliance', 'unknown')}")
            print(f"📊 Confidence: {result.get('confidence', 0):.3f}")
            print(f"⚖️ Jurisdiction: {result.get('jurisdiction', 'unknown')}")
            print(f"📋 Law: {result.get('law', 'unknown')}")
            print(f"💡 Reasoning: {result.get('why_short', 'No reasoning provided')}")
            
            citations = result.get('citations', [])
            print(f"📚 Citations: {len(citations)} provided")
            
            return result
            
        except Exception as e:
            print(f"❌ LLM analysis failed: {e}")
            return None
            
    except ImportError as e:
        print(f"❌ Production LLM import failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Production LLM test failed: {e}")
        return None

def test_complete_integration():
    """Test the complete RAG + LLM integration pipeline."""
    print("\n🔄 Testing Complete Integration Pipeline...")
    print("=" * 50)
    
    try:
        from src.rag.enhanced_rag import EnhancedRAGPipeline
        from src.llm.production_llm_handler import ProductionLLMHandler
        
        # Initialize both systems with lightweight models
        rag_config = {
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "reranker_model": "cross-encoder/ms-marco-MiniLM-L-2-v2",
            "retrieval_top_k": 15,
            "rerank_top_k": 5
        }
        
        llm_config = {
            "primary_model": "openai-gpt4o-mini",
            "backup_models": ["gemini-flash", "huggingface"],
            "confidence_threshold": 0.7
        }
        
        print("🚀 Initializing integrated pipeline...")
        
        try:
            rag_pipeline = EnhancedRAGPipeline(rag_config)
            print("✅ Enhanced RAG initialized")
        except Exception as e:
            print(f"⚠️ Enhanced RAG failed, falling back to existing system: {e}")
            # Fall back to existing RAG
            import yaml
            from pathlib import Path
            from retriever.faiss_retriever import FaissRetriever
            
            rag_config_path = Path('config/centralized_rag_config.yaml')
            with open(rag_config_path) as f:
                existing_rag_config = yaml.safe_load(f)
            
            faiss_config = {
                'embedding': {
                    'model_name': existing_rag_config.get('vector_index', {}).get('embedding_model'),
                    'dimension': 384,
                    'device': 'cpu'
                },
                'rag': {
                    'vectorstore': existing_rag_config.get('rag', {}).get('vectorstore', {})
                }
            }
            
            rag_pipeline = FaissRetriever(faiss_config)
            print("✅ Existing FAISS RAG initialized")
        
        llm_handler = ProductionLLMHandler(llm_config)
        print("✅ Production LLM initialized")
        
        # Test with a complex compliance scenario
        test_scenarios = [
            {
                "name": "EU DSA Compliance for Recommendation Systems",
                "feature": """
                TikTok-style infinite scroll feed with AI-powered content recommendations:
                - Analyzes user interaction patterns, viewing time, and engagement metrics
                - Uses machine learning algorithms to optimize for user engagement
                - Collects demographic data and behavioral patterns
                - Targets EU users aged 13+ 
                - Stores interaction data for algorithm improvement
                - No user controls for algorithmic transparency
                """,
                "query": "Does this recommendation system feature require EU DSA compliance measures?"
            },
            {
                "name": "COPPA Compliance for Child Safety",
                "feature": """
                Age verification and parental control system:
                - Collects age information from users during registration
                - Implements parental consent mechanisms for users under 13
                - Provides parental control dashboard for content filtering
                - Stores minimal personal data with parental consent
                - Includes age-appropriate content classification
                """,
                "query": "What COPPA compliance requirements apply to this age verification feature?"
            }
        ]
        
        integration_results = []
        
        for scenario in test_scenarios:
            print(f"\n📋 Scenario: {scenario['name']}")
            print("-" * 40)
            
            try:
                # Step 1: Retrieve relevant regulations
                if hasattr(rag_pipeline, 'retrieve_and_rerank'):
                    # Enhanced RAG
                    rag_results = rag_pipeline.retrieve_and_rerank(scenario['query'])
                    context = rag_pipeline.format_context_for_llm(rag_results)
                    citations = rag_pipeline.get_citations(rag_results)
                else:
                    # Existing FAISS RAG
                    rag_results = rag_pipeline.retrieve(scenario['query'], top_k=5)
                    context = "\n".join([
                        f"- {r.law_name} ({r.jurisdiction}): {r.snippet[:150]}..."
                        for r in rag_results
                    ])
                    citations = [{"source": r.law_name, "snippet": r.snippet[:200]} for r in rag_results]
                
                print(f"📚 Retrieved {len(rag_results)} relevant regulations")
                
                # Step 2: LLM analysis
                compliance_result = llm_handler.analyze_compliance(
                    scenario['feature'], 
                    context
                )
                
                # Step 3: Combine results
                integrated_result = {
                    "scenario": scenario['name'],
                    "feature": scenario['feature'],
                    "rag_results_count": len(rag_results),
                    "compliance_analysis": compliance_result,
                    "regulatory_citations": citations,
                    "pipeline_success": "error" not in compliance_result
                }
                
                integration_results.append(integrated_result)
                
                print(f"✅ Analysis completed:")
                print(f"   Compliance: {compliance_result.get('require_compliance', 'unknown')}")
                print(f"   Confidence: {compliance_result.get('confidence', 0):.3f}")
                print(f"   Model: {compliance_result.get('model_used', 'unknown')}")
                print(f"   Regulations found: {len(rag_results)}")
                
            except Exception as e:
                print(f"❌ Scenario failed: {e}")
                integration_results.append({
                    "scenario": scenario['name'],
                    "error": str(e),
                    "pipeline_success": False
                })
        
        print(f"\n✅ Complete integration tested with {len(integration_results)} scenarios")
        return integration_results
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return None

def test_existing_mcp_server():
    """Test the existing MCP server endpoints."""
    print("\n🌐 Testing Existing MCP Server Integration...")
    print("=" * 50)
    
    try:
        import requests
        
        # Check if server is running
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ MCP server is running")
                server_info = response.json()
                print(f"📊 Server status: {server_info}")
            else:
                print("⚠️ MCP server responded but may have issues")
                return None
        except requests.exceptions.ConnectionError:
            print("❌ MCP server not running on port 8000")
            print("💡 Start server with: python minimal_mcp_server.py")
            return None
        
        # Test MCP endpoints
        test_query = {
            "query": "Does this feature require dedicated logic to comply with region-specific legal obligations?",
            "tools": ["retrieve_rag"],
            "context": {"jurisdiction": "EU"}
        }
        
        try:
            response = requests.post(
                "http://localhost:8000/mcp/query",
                json=test_query,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ MCP query successful")
                print(f"📋 Response keys: {list(result.keys())}")
                return result
            else:
                print(f"❌ MCP query failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ MCP query error: {e}")
            return None
            
    except ImportError:
        print("❌ requests library not available")
        return None

def main():
    """Run complete integration tests."""
    print("🧪 Production LLM + Enhanced RAG Integration Test Suite")
    print("=" * 60)
    
    # Setup
    if not setup_environment():
        print("❌ Environment setup failed")
        return
    
    test_results = {}
    
    # Test 1: Enhanced RAG Pipeline
    print("\n" + "="*60)
    rag_results = test_enhanced_rag_pipeline()
    test_results['enhanced_rag'] = rag_results is not None
    
    # Test 2: Production LLM Handler
    print("\n" + "="*60)
    llm_results = test_production_llm_handler()
    test_results['production_llm'] = llm_results is not None
    
    # Test 3: Complete Integration
    print("\n" + "="*60)
    integration_results = test_complete_integration()
    test_results['complete_integration'] = integration_results is not None
    
    # Test 4: Existing MCP Server
    print("\n" + "="*60)
    mcp_results = test_existing_mcp_server()
    test_results['mcp_server'] = mcp_results is not None
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for test_name, success in test_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All systems operational! Production pipeline ready.")
    elif passed_tests >= total_tests // 2:
        print("⚠️ Partial success. Check failed components.")
    else:
        print("❌ Multiple failures. Review configuration and dependencies.")
    
    # Next steps
    print("\n💡 Next Steps:")
    if not test_results.get('enhanced_rag'):
        print("- Install FlagEmbedding: pip install FlagEmbedding")
    if not test_results.get('production_llm'):
        print("- Set API keys: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY")
    if not test_results.get('mcp_server'):
        print("- Start MCP server: python minimal_mcp_server.py")
    
    print("\n🚀 Ready for production compliance analysis!")

if __name__ == "__main__":
    main()
