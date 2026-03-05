#!/usr/bin/env python3
"""
Quick Production Test - Focus on LLM and existing RAG integration
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_quick_production_pipeline():
    """Test the production pipeline with existing components."""
    print("🚀 Quick Production Pipeline Test")
    print("=" * 50)
    
    # Check environment
    openai_key = os.getenv('OPENAI_API_KEY')
    google_key = os.getenv('GOOGLE_API_KEY')
    hf_token = os.getenv('HUGGINGFACEHUB_API_TOKEN')
    
    print(f"OpenAI API: {'✅' if openai_key else '❌'}")
    print(f"Google API: {'✅' if google_key else '❌'}")
    print(f"HF Token: {'✅' if hf_token else '❌'}")
    
    if not (openai_key or google_key):
        print("❌ No LLM APIs available")
        return False
    
    # Test 1: Production LLM Handler
    print("\n🤖 Testing Production LLM...")
    try:
        from src.llm.production_llm_handler import ProductionLLMHandler
        
        llm_config = {
            "primary_model": "openai-gpt4o-mini",
            "backup_models": ["gemini-flash", "huggingface"],
            "confidence_threshold": 0.7
        }
        
        llm_handler = ProductionLLMHandler(llm_config)
        status = llm_handler.get_model_status()
        print(f"Available models: {status['available_models']}")
        
        # Quick test
        test_feature = "AI content recommendation system for social media users aged 13+"
        test_context = "EU DSA requires transparency for recommendation systems targeting minors"
        
        result = llm_handler.analyze_compliance(test_feature, test_context)
        
        print(f"✅ LLM Test Result:")
        print(f"   Model: {result.get('model_used', 'unknown')}")
        print(f"   Compliance: {result.get('require_compliance', 'unknown')}")
        print(f"   Confidence: {result.get('confidence', 0):.3f}")
        
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        return False
    
    # Test 2: Existing RAG System
    print("\n📚 Testing Existing RAG System...")
    try:
        import yaml
        from pathlib import Path
        from retriever.faiss_retriever import FaissRetriever
        
        # Load existing RAG config
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
        
        rag_retriever = FaissRetriever(faiss_config)
        print("✅ Existing RAG system loaded")
        
        # Test retrieval
        query = "age verification requirements for minors on social platforms"
        results = rag_retriever.retrieve(query, top_k=3)
        
        print(f"✅ RAG Test Result:")
        print(f"   Retrieved: {len(results)} documents")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.law_name} ({result.jurisdiction}) - Score: {result.score:.3f}")
        
    except Exception as e:
        print(f"❌ RAG test failed: {e}")
        return False
    
    # Test 3: Complete Integration
    print("\n🔄 Testing Complete Integration...")
    try:
        # Combine RAG + LLM
        query = "content moderation requirements for EU social media platforms"
        rag_results = rag_retriever.retrieve(query, top_k=5)
        
        # Format context
        context = "REGULATORY CONTEXT:\n" + "\n".join([
            f"- {r.law_name} ({r.jurisdiction}): {r.snippet[:150]}..."
            for r in rag_results
        ])
        
        feature_description = """
        Automated content moderation system that:
        - Scans user-generated content for harmful material
        - Uses AI to classify content risks
        - Automatically removes policy violations
        - Targets EU users including minors
        - Stores content analysis data for 12 months
        """
        
        # LLM analysis with RAG context
        compliance_result = llm_handler.analyze_compliance(feature_description, context)
        
        print(f"✅ Integration Test Result:")
        print(f"   RAG Documents: {len(rag_results)}")
        print(f"   LLM Model: {compliance_result.get('model_used', 'unknown')}")
        print(f"   Compliance: {compliance_result.get('require_compliance', 'unknown')}")
        print(f"   Confidence: {compliance_result.get('confidence', 0):.3f}")
        print(f"   Jurisdiction: {compliance_result.get('jurisdiction', 'unknown')}")
        print(f"   Law: {compliance_result.get('law', 'unknown')}")
        print(f"   Reasoning: {compliance_result.get('why_short', 'N/A')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def test_mcp_server_integration():
    """Test integration with existing MCP server."""
    print("\n🌐 Testing MCP Server Integration...")
    try:
        import requests
        
        # Check if server is running
        try:
            response = requests.get("http://localhost:8000/health", timeout=3)
            print("✅ MCP server is running")
        except:
            print("⚠️ MCP server not running - start with: python minimal_mcp_server.py")
            return False
        
        # Test MCP query
        test_query = {
            "query": "Analyze content recommendation system for GDPR compliance",
            "tools": ["retrieve_rag"],
            "context": {"jurisdiction": "EU", "regulation": "GDPR"}
        }
        
        response = requests.post(
            "http://localhost:8000/mcp/query",
            json=test_query,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ MCP query successful")
            print(f"   Response keys: {list(result.keys())}")
            return True
        else:
            print(f"❌ MCP query failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ MCP test failed: {e}")
        return False

def main():
    """Run quick production tests."""
    print("⚡ Quick Production Test Suite")
    print("=" * 40)
    
    success = test_quick_production_pipeline()
    
    if success:
        print("\n🎉 Production pipeline is working!")
        
        # Optional: Test MCP server if running
        mcp_success = test_mcp_server_integration()
        
        print("\n📊 Summary:")
        print(f"✅ Core Pipeline: {'PASS' if success else 'FAIL'}")
        print(f"{'✅' if mcp_success else '⚠️'} MCP Server: {'PASS' if mcp_success else 'NOT RUNNING'}")
        
        if success:
            print("\n🚀 System ready for compliance analysis!")
            print("💡 Available capabilities:")
            print("   - Multi-model LLM analysis (OpenAI GPT-4o-mini, Gemini Flash, HuggingFace)")
            print("   - RAG-powered regulatory context retrieval")
            print("   - JSON-structured compliance decisions")
            print("   - Multi-jurisdiction support (EU, US, CA, FL)")
            
    else:
        print("\n❌ Production pipeline has issues")
        print("💡 Check API keys in .env file")

if __name__ == "__main__":
    main()
