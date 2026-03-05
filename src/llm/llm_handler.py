"""
Production LLM Handler with Primary and Backup Models
"""

import json
import logging
import time
from typing import Dict, Any, Optional, Union
from huggingface_hub import login, InferenceClient
import asyncio

logger = logging.getLogger(__name__)


class LLMHandler:
    """Production LLM handler with primary/backup fallback strategy."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize LLM handler with configuration."""
        self.config = config
        self.hf_token = config.get("hf_token")
        
        # Model configurations
        self.primary_model = config.get("primary_model", "Qwen/Qwen2.5-72B-Instruct")
        self.backup_model = config.get("backup_model", "mistralai/Mixtral-8x22B-Instruct")
        
        # Thresholds and timeouts
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
        self.timeout_seconds = config.get("timeout_seconds", 30)
        self.max_retries = config.get("max_retries", 2)
        
        # Initialize HuggingFace client
        if self.hf_token:
            login(self.hf_token)
            logger.info("✅ HuggingFace authenticated")
        
        self.client = InferenceClient()
        
        # Track model health
        self.primary_failures = 0
        self.max_failures_before_fallback = 3
        
    def _create_compliance_prompt(self, feature_artifact: str, regulatory_context: str) -> str:
        """Create a structured prompt for compliance analysis."""
        
        prompt = f"""You are a legal compliance AI assistant analyzing whether a feature requires geo-regulation compliance.

REGULATORY CONTEXT:
{regulatory_context}

FEATURE ARTIFACT:
{feature_artifact}

TASK: Analyze if this feature requires compliance with the provided regulations using Natural Language Inference (NLI):
- ENTAILMENT: Feature clearly requires compliance (return YES)
- CONTRADICTION: Feature clearly does NOT require compliance (return NO)  
- NEUTRAL: Insufficient evidence or ambiguous (return ABSTAIN)

You must respond with VALID JSON only:

{{
  "feature_id": "extracted or generated ID",
  "jurisdiction": "applicable jurisdiction (EU/US/CA/FL/UT)",
  "law": "specific law/regulation name",
  "trigger": "what triggers compliance requirement",
  "require_compliance": "YES|NO|ABSTAIN",
  "confidence": 0.XX,
  "why_short": "brief explanation in 2-3 sentences",
  "citations": [{{"source": "regulation name", "snippet": "relevant text"}}]
}}

IMPORTANT: 
- Only return YES if entailment ≥ 0.7 AND you have supporting regulatory text
- Only return NO if contradiction ≥ 0.7 AND you have contradicting regulatory text
- Return ABSTAIN if confidence < 0.7 or evidence is unclear
- Always include at least one citation for YES/NO decisions
- Respond with JSON only, no other text"""

        return prompt
    
    async def _call_model_async(self, model_name: str, prompt: str) -> Dict[str, Any]:
        """Make async call to a specific model."""
        try:
            # For HuggingFace inference
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.text_generation,
                    prompt=prompt,
                    model=model_name,
                    max_new_tokens=512,
                    temperature=0.1,
                    return_full_text=False
                ),
                timeout=self.timeout_seconds
            )
            
            # Try to parse JSON response
            try:
                # Clean response and parse JSON
                clean_response = response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response.replace('```json', '').replace('```', '').strip()
                
                result = json.loads(clean_response)
                result['model_used'] = model_name
                result['timestamp'] = time.time()
                
                return result
                
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from {model_name}: {response[:200]}")
                return {
                    "error": "invalid_json",
                    "raw_response": response,
                    "model_used": model_name
                }
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout calling {model_name}")
            return {"error": "timeout", "model_used": model_name}
            
        except Exception as e:
            logger.error(f"Error calling {model_name}: {e}")
            return {"error": str(e), "model_used": model_name}
    
    def _call_model_sync(self, model_name: str, prompt: str) -> Dict[str, Any]:
        """Synchronous wrapper for model calls."""
        try:
            return asyncio.run(self._call_model_async(model_name, prompt))
        except Exception as e:
            logger.error(f"Sync call failed for {model_name}: {e}")
            return {"error": str(e), "model_used": model_name}
    
    def _is_valid_response(self, response: Dict[str, Any]) -> bool:
        """Check if response is valid and meets confidence threshold."""
        if "error" in response:
            return False
            
        required_fields = ["require_compliance", "confidence", "why_short"]
        if not all(field in response for field in required_fields):
            return False
            
        # Check confidence threshold for non-ABSTAIN responses
        compliance = response.get("require_compliance", "").upper()
        confidence = response.get("confidence", 0)
        
        if compliance in ["YES", "NO"] and confidence < self.confidence_threshold:
            return False
            
        return True
    
    def analyze_compliance(self, feature_artifact: str, regulatory_context: str) -> Dict[str, Any]:
        """Main method to analyze compliance with fallback strategy."""
        
        prompt = self._create_compliance_prompt(feature_artifact, regulatory_context)
        
        # Try primary model first
        logger.info(f"🚀 Attempting analysis with primary model: {self.primary_model}")
        
        for attempt in range(self.max_retries):
            try:
                response = self._call_model_sync(self.primary_model, prompt)
                
                if self._is_valid_response(response):
                    logger.info(f"✅ Primary model succeeded (attempt {attempt + 1})")
                    self.primary_failures = 0  # Reset failure counter
                    return response
                else:
                    logger.warning(f"⚠️ Primary model response invalid (attempt {attempt + 1})")
                    
            except Exception as e:
                logger.error(f"❌ Primary model error (attempt {attempt + 1}): {e}")
        
        # Track primary model failures
        self.primary_failures += 1
        logger.warning(f"Primary model failed {self.primary_failures} times")
        
        # Fall back to backup model
        logger.info(f"🔄 Falling back to backup model: {self.backup_model}")
        
        for attempt in range(self.max_retries):
            try:
                response = self._call_model_sync(self.backup_model, prompt)
                
                if self._is_valid_response(response):
                    logger.info(f"✅ Backup model succeeded (attempt {attempt + 1})")
                    return response
                else:
                    logger.warning(f"⚠️ Backup model response invalid (attempt {attempt + 1})")
                    
            except Exception as e:
                logger.error(f"❌ Backup model error (attempt {attempt + 1}): {e}")
        
        # Both models failed - return ABSTAIN with error info
        logger.error("❌ Both primary and backup models failed")
        
        return {
            "feature_id": "unknown",
            "jurisdiction": "unknown", 
            "law": "unknown",
            "trigger": "analysis_failed",
            "require_compliance": "ABSTAIN",
            "confidence": 0.0,
            "why_short": "Unable to analyze due to model failures. Manual review required.",
            "citations": [],
            "error": "both_models_failed",
            "primary_model": self.primary_model,
            "backup_model": self.backup_model,
            "timestamp": time.time()
        }


class MockLLMHandler:
    """Mock LLM handler for testing when HuggingFace is unavailable."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logger.info("🧪 Using Mock LLM Handler for testing")
    
    def analyze_compliance(self, feature_artifact: str, regulatory_context: str) -> Dict[str, Any]:
        """Mock compliance analysis with realistic responses."""
        
        # Simple heuristics for mock responses
        artifact_lower = feature_artifact.lower()
        context_lower = regulatory_context.lower()
        
        # Determine compliance based on keywords
        if any(word in artifact_lower for word in ['data collection', 'user data', 'personal information', 'minors', 'children']):
            if 'gdpr' in context_lower or 'coppa' in context_lower:
                return {
                    "feature_id": "mock_feature_001",
                    "jurisdiction": "EU" if 'gdpr' in context_lower else "US",
                    "law": "GDPR" if 'gdpr' in context_lower else "COPPA",
                    "trigger": "Data collection from users detected",
                    "require_compliance": "YES",
                    "confidence": 0.85,
                    "why_short": "Feature involves data collection which triggers privacy regulations. Requires compliance implementation.",
                    "citations": [{"source": "Mock Regulation", "snippet": "Data collection requires user consent..."}],
                    "model_used": "mock_llm",
                    "timestamp": time.time()
                }
        
        elif any(word in artifact_lower for word in ['content moderation', 'reporting', 'harmful content']):
            return {
                "feature_id": "mock_feature_002", 
                "jurisdiction": "US",
                "law": "18 U.S.C. §2258A",
                "trigger": "Content moderation and reporting requirements",
                "require_compliance": "YES",
                "confidence": 0.78,
                "why_short": "Feature involves content moderation which requires compliance with reporting obligations.",
                "citations": [{"source": "18 U.S.C. §2258A", "snippet": "Providers must report suspected violations..."}],
                "model_used": "mock_llm",
                "timestamp": time.time()
            }
        
        else:
            return {
                "feature_id": "mock_feature_003",
                "jurisdiction": "unknown",
                "law": "unknown", 
                "trigger": "No clear regulatory triggers identified",
                "require_compliance": "ABSTAIN",
                "confidence": 0.45,
                "why_short": "Insufficient evidence to determine compliance requirements. Manual legal review recommended.",
                "citations": [],
                "model_used": "mock_llm", 
                "timestamp": time.time()
            }
