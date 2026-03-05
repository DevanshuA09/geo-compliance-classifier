#!/usr/bin/env python3
"""
Environment Setup Validator for Production Pipeline
"""

import os
from dotenv import load_dotenv

def validate_environment():
    """Validate all environment variables are properly set."""
    
    print("🔧 Loading environment variables from .env file...")
    load_dotenv()
    
    # Required API keys
    api_keys = {
        'OPENAI_API_KEY': {
            'env_var': 'OPENAI_API_KEY',
            'description': 'OpenAI API key for GPT-4o-mini',
            'required': False,
            'test_value': 'sk-'
        },
        'ANTHROPIC_API_KEY': {
            'env_var': 'ANTHROPIC_API_KEY', 
            'description': 'Anthropic API key for Claude Haiku',
            'required': False,
            'test_value': 'sk-ant-'
        },
        'GOOGLE_API_KEY': {
            'env_var': 'GOOGLE_API_KEY',
            'description': 'Google API key for Gemini 1.5 Flash',
            'required': False,
            'test_value': 'AIza'
        },
        'HUGGINGFACEHUB_API_TOKEN': {
            'env_var': 'HUGGINGFACEHUB_API_TOKEN',
            'description': 'HuggingFace API token (optional)',
            'required': False,
            'test_value': 'hf_'
        }
    }
    
    # System configuration
    system_config = {
        'DEBUG': {
            'env_var': 'DEBUG',
            'description': 'Debug mode flag',
            'default': 'false',
            'required': False
        },
        'LOG_LEVEL': {
            'env_var': 'LOG_LEVEL',
            'description': 'Logging level',
            'default': 'INFO',
            'required': False
        },
        'MCP_PORT': {
            'env_var': 'MCP_PORT',
            'description': 'MCP server port',
            'default': '8000',
            'required': False
        },
        'PRIMARY_MODEL': {
            'env_var': 'PRIMARY_MODEL',
            'description': 'Primary LLM model',
            'default': 'openai-gpt4o-mini',
            'required': False
        }
    }
    
    print("\n📋 API Key Status:")
    print("=" * 50)
    
    available_models = []
    
    for key, config in api_keys.items():
        value = os.getenv(config['env_var'])
        
        if value and value != f"your_{key.lower()}_here":
            # Check if it looks like a real API key
            if config['test_value'] and value.startswith(config['test_value']):
                print(f"✅ {key}: Configured and valid format")
                
                # Map to model availability
                if key == 'OPENAI_API_KEY':
                    available_models.append('openai-gpt4o-mini')
                elif key == 'ANTHROPIC_API_KEY':
                    available_models.append('claude-haiku')
                elif key == 'GOOGLE_API_KEY':
                    available_models.append('gemini-flash')
                elif key == 'HUGGINGFACEHUB_API_TOKEN':
                    available_models.append('huggingface-models')
                    
            else:
                print(f"⚠️  {key}: Configured but format may be invalid")
        else:
            print(f"❌ {key}: Not configured")
            print(f"   💡 {config['description']}")
    
    print("\n🤖 Available LLM Models:")
    print("=" * 50)
    
    if available_models:
        for model in available_models:
            print(f"✅ {model}")
    else:
        print("❌ No LLM models available - please configure API keys")
        
    print("\n⚙️  System Configuration:")
    print("=" * 50)
    
    for key, config in system_config.items():
        value = os.getenv(config['env_var'], config.get('default', 'not set'))
        print(f"📋 {key}: {value}")
    
    print("\n🚀 Model Recommendations:")
    print("=" * 50)
    
    if 'openai-gpt4o-mini' in available_models:
        print("🎯 PRIMARY: OpenAI GPT-4o-mini - 128k context, structured JSON, very reliable")
    
    backup_models = []
    if 'claude-haiku' in available_models:
        backup_models.append("Claude Haiku - excellent reasoning")
    if 'gemini-flash' in available_models:
        backup_models.append("Gemini 1.5 Flash - fast and capable")
        
    if backup_models:
        print("🔄 BACKUP MODELS:")
        for model in backup_models:
            print(f"   • {model}")
    
    # Configuration suggestions
    print("\n💡 Configuration Suggestions:")
    print("=" * 50)
    
    if len(available_models) >= 2:
        print("✅ Multiple models available - good fallback strategy")
    elif len(available_models) == 1:
        print("⚠️  Only one model available - consider adding backup models")
    else:
        print("❌ No models available - add at least one API key")
        
    if 'openai-gpt4o-mini' in available_models:
        print("✅ OpenAI GPT-4o-mini available - excellent for structured JSON output")
    else:
        print("💡 Consider adding OpenAI GPT-4o-mini for best JSON compliance")
    
    print("\n🔑 To configure API keys:")
    print("=" * 50)
    print("1. Edit the .env file in the project root")
    print("2. Replace 'your_api_key_here' with actual API keys")
    print("3. Get free API keys from:")
    print("   • OpenAI: https://platform.openai.com/api-keys")
    print("   • Anthropic: https://console.anthropic.com/")
    print("   • Google: https://makersuite.google.com/app/apikey")
    
    return len(available_models) > 0

def test_api_connections():
    """Test actual connections to configured APIs."""
    
    print("\n🔗 Testing API Connections:")
    print("=" * 50)
    
    # Test OpenAI
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key and openai_key.startswith('sk-'):
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)
            
            # Test with a simple request
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hello, respond with just 'OK'"}],
                max_tokens=5
            )
            print("✅ OpenAI GPT-4o-mini: Connection successful")
            
        except ImportError:
            print("⚠️  OpenAI: Library not installed (pip install openai)")
        except Exception as e:
            print(f"❌ OpenAI: Connection failed - {e}")
    
    # Test Anthropic
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    if anthropic_key and anthropic_key.startswith('sk-ant-'):
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=5,
                messages=[{"role": "user", "content": "Hello, respond with just 'OK'"}]
            )
            print("✅ Claude Haiku: Connection successful")
            
        except ImportError:
            print("⚠️  Anthropic: Library not installed (pip install anthropic)")
        except Exception as e:
            print(f"❌ Anthropic: Connection failed - {e}")
    
    # Test Google
    google_key = os.getenv('GOOGLE_API_KEY')
    if google_key and google_key.startswith('AIza'):
        try:
            import google.generativeai as genai
            genai.configure(api_key=google_key)
            
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content("Hello, respond with just 'OK'")
            print("✅ Gemini 1.5 Flash: Connection successful")
            
        except ImportError:
            print("⚠️  Google AI: Library not installed (pip install google-generativeai)")
        except Exception as e:
            print(f"❌ Google AI: Connection failed - {e}")

if __name__ == "__main__":
    print("🔍 Production Pipeline Environment Validator")
    print("=" * 60)
    
    # Load and validate environment
    has_models = validate_environment()
    
    if has_models:
        print("\n" + "=" * 60)
        test_api_connections()
        
        print("\n✅ Environment validation complete!")
        print("🚀 Run: python test_production_integration.py")
    else:
        print("\n❌ Environment validation failed!")
        print("🔧 Please configure API keys in .env file first")
