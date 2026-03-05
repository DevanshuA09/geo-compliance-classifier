"""
Enhanced LLM Handler with OpenAI GPT-4o-mini, Gemini, and HuggingFace support
"""

import json
import logging
import time
import os
from typing import Dict, Any, Optional, List
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class ProductionLLMHandler:
    """Production LLM handler with OpenAI, Gemini, and HuggingFace models."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize with multiple LLM providers."""
        if config is None:
            config = {}
            
        self.config = config
        
        # Model configurations
        self.primary_model = config.get("primary_model", "openai-gpt4o-mini")
        self.backup_models = config.get("backup_models", ["gemini-flash", "huggingface"])
        
        # API configurations
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        
        # Thresholds
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
        self.timeout_seconds = config.get("timeout_seconds", 30)
        self.max_retries = config.get("max_retries", 2)
        
        # Initialize clients
        self.clients = {}
        self._initialize_clients()
        
        # Track model health
        self.model_failures = {}
        self.max_failures_before_fallback = 3
        
        # Model configurations - use environment variables as defaults
        self.primary_model = config.get(
            "primary_model", 
            os.getenv("PRIMARY_MODEL", "openai-gpt4o-mini")
        )
        self.backup_models = config.get(
            "backup_models", 
            os.getenv("BACKUP_MODELS", "gemini-flash,huggingface").split(",")
        )
        
        # API configurations
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        
        # Thresholds - use environment variables with defaults
        self.confidence_threshold = config.get(
            "confidence_threshold", 
            float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
        )
        self.timeout_seconds = config.get(
            "timeout_seconds", 
            int(os.getenv("TIMEOUT_SECONDS", "30"))
        )
        self.max_retries = config.get("max_retries", 2)
        
        # Initialize clients
        self.clients = {}
        self._initialize_clients()
        
        # Track model health
        self.model_failures = {}
        self.max_failures_before_fallback = 3
        
    def _initialize_clients(self):
        """Initialize API clients for different providers."""
        try:
            # OpenAI client
            if self.openai_api_key:
                try:
                    import openai
                    self.clients['openai'] = openai.OpenAI(api_key=self.openai_api_key)
                    logger.info("✅ OpenAI client initialized")
                except ImportError:
                    logger.warning("⚠️ OpenAI library not found. Install with: pip install openai")
                    
            # Google client
            if self.google_api_key:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=self.google_api_key)
                    self.clients['google'] = genai.GenerativeModel('gemini-1.5-flash')
                    logger.info("✅ Google Gemini client initialized")
                except ImportError:
                    logger.warning("⚠️ Google AI library not found. Install with: pip install google-generativeai")
                    
            # HuggingFace client
            if self.hf_token:
                try:
                    from huggingface_hub import login, InferenceClient
                    login(self.hf_token)
                    self.clients['huggingface'] = InferenceClient()
                    logger.info("✅ HuggingFace client initialized")
                except ImportError:
                    logger.warning("⚠️ HuggingFace Hub library not found. Install with: pip install huggingface_hub")
                    
        except Exception as e:
            logger.error(f"❌ Error initializing clients: {e}")
            
    def _create_compliance_prompt(self, feature_artifact: str, regulatory_context: str) -> str:
        """Create a structured prompt for compliance analysis with JSON schema."""
        
        prompt = f"""You are a legal compliance AI assistant. Analyze whether a feature requires geo-regulation compliance.

REGULATORY CONTEXT:
{regulatory_context}

FEATURE ARTIFACT:
{feature_artifact}

ANALYSIS TASK:
Use Natural Language Inference (NLI) to determine compliance requirements:
- ENTAILMENT: Feature clearly requires compliance → return "YES"
- CONTRADICTION: Feature clearly does NOT require compliance → return "NO"  
- NEUTRAL: Insufficient evidence or ambiguous → return "ABSTAIN"

RESPONSE FORMAT:
You MUST respond with valid JSON matching this exact schema:

{{
  "feature_id": "string - extracted or generated ID",
  "jurisdiction": "string - EU/US/US-CA/US-FL/US-UT etc.",
  "law": "string - specific regulation name",
  "trigger": "string - what triggers compliance requirement", 
  "require_compliance": "YES|NO|ABSTAIN",
  "confidence": 0.XX,
  "why_short": "string - brief 2-3 sentence explanation",
  "citations": [
    {{
      "source": "string - regulation name",
      "snippet": "string - relevant regulatory text"
    }}
  ]
}}

DECISION RULES:
- Return "YES" only if: entailment confidence ≥ 0.7 AND supporting regulatory text exists
- Return "NO" only if: contradiction confidence ≥ 0.7 AND contradicting regulatory text exists  
- Return "ABSTAIN" if: confidence < 0.7 OR evidence is unclear
- Always include at least one citation for YES/NO decisions
- Keep why_short under 3 sentences

Respond with JSON only, no other text."""

        return prompt
    
    async def _call_openai_gpt4o_mini(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI GPT-4o-mini."""
        try:
            if 'openai' not in self.clients:
                return {"error": "openai_client_not_available"}
                
            response = await asyncio.to_thread(
                self.clients['openai'].chat.completions.create,
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a legal compliance expert. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            result['model_used'] = 'openai-gpt4o-mini'
            result['timestamp'] = time.time()
            
            return result
            
        except Exception as e:
            logger.error(f"OpenAI GPT-4o-mini error: {e}")
            return {"error": str(e), "model_used": "openai-gpt4o-mini"}
    
    async def _call_huggingface(self, prompt: str) -> Dict[str, Any]:
        """Call HuggingFace models."""
        try:
            if 'huggingface' not in self.clients:
                return {"error": "huggingface_client_not_available"}
                
            # Use a good instruction-following model
            response = await asyncio.to_thread(
                self.clients['huggingface'].text_generation,
                prompt=prompt,
                model="microsoft/DialoGPT-medium",  # or another good model
                max_new_tokens=1000,
                temperature=0.1,
                return_full_text=False
            )
            
            content = response.strip()
            
            # Clean and parse JSON
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
                
            try:
                result = json.loads(content)
                result['model_used'] = 'huggingface'
                result['timestamp'] = time.time()
                return result
            except json.JSONDecodeError:
                # If not valid JSON, create a mock response
                return {
                    "feature_id": "hf_analysis",
                    "jurisdiction": "unknown",
                    "law": "multiple_regulations",
                    "trigger": "feature_analysis_required",
                    "require_compliance": "ABSTAIN",
                    "confidence": 0.5,
                    "why_short": "HuggingFace model analysis suggests manual review needed for compliance determination.",
                    "citations": [],
                    "model_used": "huggingface",
                    "timestamp": time.time()
                }
            
        except Exception as e:
            logger.error(f"HuggingFace error: {e}")
            return {"error": str(e), "model_used": "huggingface"}
    
    async def _call_gemini_flash(self, prompt: str) -> Dict[str, Any]:
        """Call Gemini 1.5 Flash."""
        try:
            if 'google' not in self.clients:
                return {"error": "google_client_not_available"}
                
            response = await asyncio.to_thread(
                self.clients['google'].generate_content,
                prompt,
                generation_config={
                    'temperature': 0.1,
                    'max_output_tokens': 1000,
                }
            )
            
            content = response.text
            
            # Clean and parse JSON
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
                
            result = json.loads(content)
            result['model_used'] = 'gemini-flash'
            result['timestamp'] = time.time()
            
            return result
            
        except Exception as e:
            logger.error(f"Gemini Flash error: {e}")
            return {"error": str(e), "model_used": "gemini-flash"}
    
    def _get_model_function(self, model_name: str):
        """Get the appropriate model function."""
        model_functions = {
            'openai-gpt4o-mini': self._call_openai_gpt4o_mini,
            'gemini-flash': self._call_gemini_flash,
            'huggingface': self._call_huggingface
        }
        return model_functions.get(model_name)
    
    def _is_valid_response(self, response: Dict[str, Any]) -> bool:
        """Check if response is valid and meets confidence threshold."""
        if "error" in response:
            return False
            
        required_fields = ["require_compliance", "confidence", "why_short"]
        if not all(field in response for field in required_fields):
            logger.warning(f"Missing required fields: {[f for f in required_fields if f not in response]}")
            return False
            
        # Check confidence threshold for non-ABSTAIN responses
        compliance = response.get("require_compliance", "").upper()
        confidence = response.get("confidence", 0)
        
        if compliance in ["YES", "NO"] and confidence < self.confidence_threshold:
            logger.warning(f"Confidence {confidence} below threshold {self.confidence_threshold}")
            return False
            
        return True
    
    async def _try_model_async(self, model_name: str, prompt: str) -> Dict[str, Any]:
        """Try a specific model with timeout."""
        model_func = self._get_model_function(model_name)
        if not model_func:
            return {"error": f"unsupported_model: {model_name}"}
            
        try:
            result = await asyncio.wait_for(
                model_func(prompt),
                timeout=self.timeout_seconds
            )
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout for {model_name}")
            return {"error": "timeout", "model_used": model_name}
        except Exception as e:
            logger.error(f"Error with {model_name}: {e}")
            return {"error": str(e), "model_used": model_name}
    
    def analyze_compliance(self, feature_artifact: str, regulatory_context: str) -> Dict[str, Any]:
        """Main method to analyze compliance with cascading fallback."""
        
        prompt = self._create_compliance_prompt(feature_artifact, regulatory_context)
        
        # Create model priority list
        models_to_try = [self.primary_model] + self.backup_models
        
        async def try_all_models():
            for model_name in models_to_try:
                logger.info(f"🚀 Attempting analysis with {model_name}")
                
                for attempt in range(self.max_retries):
                    try:
                        response = await self._try_model_async(model_name, prompt)
                        
                        if self._is_valid_response(response):
                            logger.info(f"✅ {model_name} succeeded (attempt {attempt + 1})")
                            # Reset failure counter for this model
                            self.model_failures[model_name] = 0
                            return response
                        else:
                            logger.warning(f"⚠️ {model_name} response invalid (attempt {attempt + 1})")
                            
                    except Exception as e:
                        logger.error(f"❌ {model_name} error (attempt {attempt + 1}): {e}")
                
                # Track model failures
                self.model_failures[model_name] = self.model_failures.get(model_name, 0) + 1
                logger.warning(f"{model_name} failed {self.model_failures[model_name]} times")
            
            # All models failed
            return self._create_fallback_response()
        
        # Run async analysis
        try:
            return asyncio.run(try_all_models())
        except Exception as e:
            logger.error(f"❌ Analysis pipeline failed: {e}")
            return self._create_fallback_response()
    
    def _create_fallback_response(self) -> Dict[str, Any]:
        """Create fallback response when all models fail."""
        return {
            "feature_id": "unknown",
            "jurisdiction": "unknown",
            "law": "unknown", 
            "trigger": "analysis_failed",
            "require_compliance": "ABSTAIN",
            "confidence": 0.0,
            "why_short": "Unable to analyze due to model failures. Manual legal review required.",
            "citations": [],
            "error": "all_models_failed",
            "attempted_models": [self.primary_model] + self.backup_models,
            "timestamp": time.time()
        }
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all available models."""
        status = {
            "available_models": [],
            "model_failures": self.model_failures,
            "primary_model": self.primary_model,
            "backup_models": self.backup_models
        }
        
        # Check which clients are available
        if 'openai' in self.clients:
            status["available_models"].append("openai-gpt4o-mini")
        if 'google' in self.clients:
            status["available_models"].append("gemini-flash")
        if 'huggingface' in self.clients:
            status["available_models"].append("huggingface")
            
        return status
