#!/usr/bin/env python3
"""
Quick Production LLM Handler Test
Tests the production LLM handler with available API providers.
"""

import os
import sys
import time
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_production_llm_only():
    """Test only the Production LLM Handler."""
    print("🤖 Testing Production LLM Handler Only...")
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
        
        # Test compliance analysis
        print("\n📝 Testing compliance analysis...")
        
        feature_artifact = """
        Smart Content Recommendation Engine:
        - Uses AI to analyze user behavior patterns and preferences
        - Collects viewing history, likes, shares, and time spent on content  
        - Creates personalized content feeds for each user
        - Shares anonymized usage data with content creators for analytics
        - Allows users to export their personal data
        - Includes parental controls for users under 18
        """
        
        regulatory_context = """
        EU Digital Services Act (DSA) Article 38: Very large online platforms that use recommender systems shall provide at least one option for each of their recommender systems that is not based on profiling.
        
        GDPR Article 6: Processing shall be lawful only if consent has been given by the data subject for processing for one or more specific purposes.
        
        DSA Article 28: Providers shall put in place appropriate and proportionate measures to ensure a high level of privacy, safety and security of minors.
        """
        
        print(f"Feature: {feature_artifact[:100]}...")
        
        # Analyze compliance
        result = llm_handler.analyze_compliance(feature_artifact, regulatory_context)
        
        print("\n✅ LLM Analysis completed!")
        print(f"🏛️ Model used: {result.get('model_used', 'unknown')}")
        print(f"🎯 Compliance: {result.get('require_compliance', 'unknown')}")
        print(f"📊 Confidence: {result.get('confidence', 0.0):.3f}")
        print(f"⚖️ Jurisdiction: {result.get('jurisdiction', 'unknown')}")
        print(f"📋 Law: {result.get('law', 'unknown')}")
        print(f"💡 Reasoning: {result.get('why_short', 'No reasoning provided')}")
        print(f"📚 Citations: {len(result.get('citations', []))} provided")
        
        if "error" in result:
            print(f"⚠️ Error encountered: {result['error']}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ LLM Handler test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 Quick Production LLM Handler Test")
    print("=" * 60)
    
    # Load environment variables
    print("🔧 Loading environment variables...")
    load_dotenv()
    
    # Check API keys
    api_keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"), 
        "HUGGINGFACEHUB_API_TOKEN": os.getenv("HUGGINGFACEHUB_API_TOKEN"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY")
    }
    
    for key, value in api_keys.items():
        if value:
            print(f"✅ {key} is configured")
        else:
            print(f"⚠️ {key} not set - corresponding model will be unavailable")
    
    print("\n" + "=" * 60)
    
    # Test Production LLM Handler
    llm_success = test_production_llm_only()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Production LLM: {'✅ PASS' if llm_success else '❌ FAIL'}")
    
    if llm_success:
        print("\n🚀 Production LLM Handler is ready for compliance analysis!")
    else:
        print("\n❌ LLM Handler failed. Check configuration and API keys.")

if __name__ == "__main__":
    main()
