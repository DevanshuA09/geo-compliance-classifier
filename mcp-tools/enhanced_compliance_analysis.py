#!/usr/bin/env python3
"""
Enhanced Compliance Analysis Tool for MCP Server
Integrates all agentic tools: Confidence Validator, Evidence Verifier, Active Learning
Maintains FeatureRecord format as the canonical structure
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    # Core production components
    from src.llm.production_llm_handler import ProductionLLMHandler
    from src.rag.enhanced_rag import EnhancedRAG
    
    # Agentic tools - the power multipliers
    from src.agents.confidence_validator import ConfidenceValidatorAgent
    from src.evidence.evidence_verifier import EvidenceVerificationAgent
    from src.agents.active_learning_agent import ActiveLearningAgent
    
    # Artifact preprocessor schema - the holy grail format
    from artifact_preprocessor.schema import FeatureRecord, OUTPUT_SCHEMA
    
    # Evidence system
    from src.evidence.evidence_logger import log_compliance_decision
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    class EnhancedComplianceAnalyzer:
        """
        Enhanced compliance analyzer that orchestrates all agentic tools
        for superior decision-making with evidence-backed reasoning
        """
        
        def __init__(self):
            # Core components
            self.llm_handler = ProductionLLMHandler()
            self.rag = EnhancedRAG()
            
            # Agentic tools
            self.confidence_validator = ConfidenceValidatorAgent()
            self.evidence_verifier = EvidenceVerificationAgent()
            self.active_learning = ActiveLearningAgent()
            
            logger.info("Enhanced Compliance Analyzer initialized with all agentic tools")
        
        async def analyze_feature_comprehensive(
            self, 
            feature_data: Dict[str, Any], 
            jurisdiction: str = 'EU'
        ) -> Dict[str, Any]:
            """
            Comprehensive analysis using all agentic tools
            
            Args:
                feature_data: Feature data in FeatureRecord-compatible format
                jurisdiction: Target jurisdiction for analysis
                
            Returns:
                Enhanced analysis with evidence verification, confidence validation, and learning
            """
            
            # Step 1: Validate and normalize feature data to FeatureRecord format
            feature_record = self._normalize_to_feature_record(feature_data)
            
            # Step 2: RAG-enhanced context retrieval
            context_docs = await self._retrieve_enhanced_context(feature_record, jurisdiction)
            
            # Step 3: Multi-model confidence validation
            confidence_result = await self._validate_with_confidence_agent(feature_record, jurisdiction, context_docs)
            
            # Step 4: Evidence verification for defensible decisions
            evidence_result = await self._verify_evidence_alignment(confidence_result, feature_record)
            
            # Step 5: Apply active learning insights
            learning_insights = await self._apply_active_learning(feature_record, confidence_result)
            
            # Step 6: Synthesize final decision with comprehensive reasoning
            final_decision = self._synthesize_final_decision(
                confidence_result, evidence_result, learning_insights, feature_record, jurisdiction
            )
            
            # Step 7: Log for continuous improvement
            await self._log_decision_for_learning(final_decision, feature_record)
            
            return final_decision
        
        def _normalize_to_feature_record(self, feature_data: Dict[str, Any]) -> FeatureRecord:
            """Normalize input to canonical FeatureRecord format"""
            
            # Handle various input formats and normalize to FeatureRecord
            if isinstance(feature_data, dict):
                return FeatureRecord(
                    feature_id=feature_data.get('feature_id', f"temp_{hash(str(feature_data)) % 10000}"),
                    doc_id=feature_data.get('doc_id', 'mcp_analysis'),
                    source_path=feature_data.get('source_path', 'mcp_input'),
                    feature_title=feature_data.get('name', feature_data.get('feature_title')),
                    feature_description=feature_data.get('description', feature_data.get('feature_description')),
                    objectives=feature_data.get('objectives'),
                    user_segments=feature_data.get('user_segments'),
                    geo_country=feature_data.get('geo_country'),
                    geo_state=feature_data.get('geo_state'),
                    domain=feature_data.get('domain'),
                    data_practices=feature_data.get('data_practices', []),
                    risk_tags=feature_data.get('risk_tags', [])
                )
            else:
                raise ValueError("Feature data must be a dictionary")
        
        async def _retrieve_enhanced_context(self, feature_record: FeatureRecord, jurisdiction: str) -> List[Dict]:
            """Enhanced RAG retrieval with feature context"""
            
            # Build comprehensive query from FeatureRecord
            query_parts = []
            if feature_record.feature_title:
                query_parts.append(feature_record.feature_title)
            if feature_record.feature_description:
                query_parts.append(feature_record.feature_description)
            if feature_record.data_practices:
                query_parts.extend(feature_record.data_practices)
            
            query = f"{jurisdiction} jurisdiction compliance: " + " ".join(query_parts)
            
            # Retrieve with enhanced context
            docs = self.rag.retrieve_and_rerank(query, top_k=7)
            
            return docs
        
        async def _validate_with_confidence_agent(
            self, 
            feature_record: FeatureRecord, 
            jurisdiction: str, 
            context_docs: List[Dict]
        ) -> Dict[str, Any]:
            """Use Confidence Validator for multi-model ensemble analysis"""
            
            # Convert FeatureRecord to text for analysis
            feature_text = self._feature_record_to_text(feature_record)
            
            # Build context from retrieved documents
            context = "\n\n".join([
                f"Document: {doc.get('metadata', {}).get('source', 'Unknown')}\n{doc.get('content', '')}"
                for doc in context_docs[:5]
            ])
            
            # Multi-model validation
            try:
                validation_result = self.confidence_validator.validate_case(
                    text=feature_text,
                    context=context,
                    jurisdiction=jurisdiction
                )
                
                return {
                    'ensemble_decision': validation_result.ensemble_decision,
                    'ensemble_confidence': validation_result.ensemble_confidence,
                    'model_predictions': {name: pred.__dict__ for name, pred in validation_result.predictions.items()},
                    'agreement_level': validation_result.agreement_level,
                    'auto_approved': validation_result.auto_approved,
                    'flags': validation_result.flags,
                    'majority_vote': validation_result.majority_vote,
                    'validation_notes': validation_result.notes
                }
            except Exception as e:
                logger.warning(f"Confidence validation failed, using fallback: {e}")
                return await self._fallback_single_model_analysis(feature_record, jurisdiction, context)
        
        async def _verify_evidence_alignment(
            self, 
            confidence_result: Dict[str, Any], 
            feature_record: FeatureRecord
        ) -> Dict[str, Any]:
            """Use Evidence Verifier to ensure defensible decisions"""
            
            try:
                # Extract reasoning from confidence result
                reasoning_text = ""
                if 'model_predictions' in confidence_result:
                    for model_name, pred in confidence_result['model_predictions'].items():
                        if pred.get('reasoning'):
                            reasoning_text += f"{model_name}: {pred['reasoning']}\n"
                
                if not reasoning_text:
                    reasoning_text = f"Analysis for {feature_record.feature_title}: {confidence_result.get('ensemble_decision', 'Unknown')}"
                
                # Create evidence spans from feature data
                evidence_spans = self._create_evidence_spans_from_feature(feature_record)
                
                # Create regulation mappings
                regulation_mappings = self._create_regulation_mappings(feature_record)
                
                # Verify evidence alignment
                verification_result = self.evidence_verifier.verify_reasoning(
                    reasoning_text=reasoning_text,
                    evidence_spans=evidence_spans,
                    regulation_mappings=regulation_mappings
                )
                
                return {
                    'evidence_verified': True,
                    'verification_result': verification_result.__dict__,
                    'evidence_quality_score': verification_result.overall_score,
                    'evidence_flags': verification_result.flags,
                    'auto_approved_evidence': verification_result.auto_approved
                }
                
            except Exception as e:
                logger.warning(f"Evidence verification failed: {e}")
                return {
                    'evidence_verified': False,
                    'error': str(e),
                    'evidence_quality_score': 0.5,
                    'evidence_flags': ['verification_error'],
                    'auto_approved_evidence': False
                }
        
        async def _apply_active_learning(
            self, 
            feature_record: FeatureRecord, 
            confidence_result: Dict[str, Any]
        ) -> Dict[str, Any]:
            """Apply active learning insights for continuous improvement"""
            
            try:
                # Check for relevant patterns from previous corrections
                feature_text = self._feature_record_to_text(feature_record)
                
                # Get pattern insights
                patterns = self.active_learning.get_relevant_patterns(feature_text)
                
                # Get confidence adjustment recommendations
                confidence_adjustment = self.active_learning.suggest_confidence_adjustment(
                    feature_text, confidence_result.get('ensemble_confidence', 0.5)
                )
                
                return {
                    'learning_patterns_found': len(patterns) > 0,
                    'relevant_patterns': patterns,
                    'confidence_adjustment': confidence_adjustment,
                    'learning_insights': f"Found {len(patterns)} relevant patterns from previous corrections"
                }
                
            except Exception as e:
                logger.warning(f"Active learning application failed: {e}")
                return {
                    'learning_patterns_found': False,
                    'relevant_patterns': [],
                    'confidence_adjustment': 0.0,
                    'learning_insights': f"Learning unavailable: {e}"
                }
        
        def _synthesize_final_decision(
            self,
            confidence_result: Dict[str, Any],
            evidence_result: Dict[str, Any],
            learning_insights: Dict[str, Any],
            feature_record: FeatureRecord,
            jurisdiction: str
        ) -> Dict[str, Any]:
            """Synthesize all analysis components into final decision"""
            
            # Base decision from confidence validator
            base_decision = confidence_result.get('ensemble_decision', 'ABSTAIN')
            base_confidence = confidence_result.get('ensemble_confidence', 0.0)
            
            # Adjust confidence based on evidence quality
            evidence_quality = evidence_result.get('evidence_quality_score', 0.5)
            evidence_adjustment = (evidence_quality - 0.5) * 0.2  # ±0.1 max adjustment
            
            # Apply active learning adjustment
            learning_adjustment = learning_insights.get('confidence_adjustment', 0.0)
            
            # Final confidence calculation
            final_confidence = max(0.0, min(1.0, base_confidence + evidence_adjustment + learning_adjustment))
            
            # Determine if human review is needed
            human_review_triggers = []
            
            if final_confidence < 0.8:
                human_review_triggers.append('low_confidence')
            if base_decision == 'ABSTAIN':
                human_review_triggers.append('abstain')
            if confidence_result.get('agreement_level') == 'Low':
                human_review_triggers.append('model_disagreement')
            if evidence_result.get('evidence_quality_score', 1.0) < 0.7:
                human_review_triggers.append('weak_evidence')
            if not evidence_result.get('auto_approved_evidence', True):
                human_review_triggers.append('evidence_verification_failed')
            
            needs_human_review = len(human_review_triggers) > 0
            
            # Build comprehensive reasoning
            reasoning_parts = []
            reasoning_parts.append(f"Multi-model ensemble analysis: {base_decision} (confidence: {base_confidence:.2f})")
            
            if evidence_result.get('evidence_verified'):
                reasoning_parts.append(f"Evidence verification: Quality score {evidence_quality:.2f}")
            
            if learning_insights.get('learning_patterns_found'):
                reasoning_parts.append(f"Active learning: Found {len(learning_insights.get('relevant_patterns', []))} relevant patterns")
            
            reasoning_parts.append(f"Final confidence: {final_confidence:.2f}")
            
            # Extract citations from evidence and context
            citations = []
            if 'model_predictions' in confidence_result:
                for pred in confidence_result['model_predictions'].values():
                    if pred.get('regulatory_context'):
                        citations.extend(pred['regulatory_context'])
            
            # Remove duplicates and ensure we have some citations
            citations = list(set(citations)) if citations else [f"{jurisdiction} regulations"]
            
            # Build final response in the expected format
            return {
                'success': True,
                'verdict': base_decision,
                'confidence': final_confidence,
                'reasoning': " | ".join(reasoning_parts),
                'citations': citations,
                'recommendations': self._generate_recommendations(base_decision, evidence_result, feature_record),
                'risk_level': self._assess_risk_level(base_decision, final_confidence, evidence_result),
                'jurisdiction': jurisdiction,
                
                # Enhanced metadata from agentic analysis
                'agentic_analysis': {
                    'confidence_validation': confidence_result,
                    'evidence_verification': evidence_result,
                    'active_learning': learning_insights,
                    'human_review_triggers': human_review_triggers,
                    'feature_record_format': feature_record.to_dict()
                },
                
                'human_review_needed': needs_human_review,
                'documents_used': len(confidence_result.get('model_predictions', {})),
                'analysis_timestamp': str(datetime.now().isoformat()) if 'datetime' in globals() else 'unknown'
            }
        
        def _feature_record_to_text(self, feature_record: FeatureRecord) -> str:
            """Convert FeatureRecord to text for analysis"""
            
            parts = []
            if feature_record.feature_title:
                parts.append(f"Feature: {feature_record.feature_title}")
            if feature_record.feature_description:
                parts.append(f"Description: {feature_record.feature_description}")
            if feature_record.objectives:
                parts.append(f"Objectives: {feature_record.objectives}")
            if feature_record.user_segments:
                parts.append(f"User Segments: {feature_record.user_segments}")
            if feature_record.data_practices:
                parts.append(f"Data Practices: {', '.join(feature_record.data_practices)}")
            if feature_record.risk_tags:
                parts.append(f"Risk Tags: {', '.join(feature_record.risk_tags)}")
                
            return " | ".join(parts)
        
        def _create_evidence_spans_from_feature(self, feature_record: FeatureRecord):
            """Create evidence spans from feature record for verification"""
            from src.evidence.evidence_verifier import EvidenceSpan
            
            spans = []
            text = self._feature_record_to_text(feature_record)
            
            # Create spans for key elements
            if feature_record.feature_description:
                spans.append(EvidenceSpan(
                    text=feature_record.feature_description,
                    start_pos=0,
                    end_pos=len(feature_record.feature_description),
                    source="feature_description"
                ))
            
            return spans
        
        def _create_regulation_mappings(self, feature_record: FeatureRecord):
            """Create regulation mappings from feature record"""
            from src.evidence.evidence_verifier import RegulationMapping
            
            mappings = []
            if feature_record.implicated_regulations:
                for reg in feature_record.implicated_regulations:
                    mappings.append(RegulationMapping(
                        regulation_name=reg,
                        text_excerpt=reg,
                        is_valid=True,
                        validation_notes="From feature record"
                    ))
            
            return mappings
        
        async def _fallback_single_model_analysis(self, feature_record: FeatureRecord, jurisdiction: str, context: str):
            """Fallback to single model if ensemble fails"""
            
            feature_text = self._feature_record_to_text(feature_record)
            
            prompt = f"""
Analyze this feature for {jurisdiction} compliance:

Feature: {feature_text}

Context: {context}

Provide analysis in JSON format:
{{
    "decision": "COMPLIANT|NON_COMPLIANT|ABSTAIN",
    "confidence": 0.0-1.0,
    "reasoning": "detailed analysis"
}}
"""
            
            response = await self.llm_handler.call_llm(prompt)
            
            try:
                import re
                json_match = re.search(r'\{.*\}', str(response), re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return {
                        'ensemble_decision': result.get('decision', 'ABSTAIN'),
                        'ensemble_confidence': result.get('confidence', 0.5),
                        'model_predictions': {'fallback': {'reasoning': result.get('reasoning', '')}},
                        'agreement_level': 'Single Model',
                        'auto_approved': False,
                        'flags': ['fallback_mode'],
                        'majority_vote': result.get('decision', 'ABSTAIN'),
                        'validation_notes': 'Fallback single model analysis'
                    }
            except:
                pass
            
            return {
                'ensemble_decision': 'ABSTAIN',
                'ensemble_confidence': 0.3,
                'model_predictions': {'fallback': {'reasoning': 'Analysis failed'}},
                'agreement_level': 'Error',
                'auto_approved': False,
                'flags': ['analysis_error'],
                'majority_vote': 'ABSTAIN',
                'validation_notes': 'Fallback analysis failed'
            }
        
        def _generate_recommendations(self, decision: str, evidence_result: Dict, feature_record: FeatureRecord) -> List[str]:
            """Generate actionable recommendations"""
            
            recommendations = []
            
            if decision == 'NON_COMPLIANT':
                recommendations.append("Review feature design for compliance requirements")
                recommendations.append("Implement additional safeguards and controls")
            elif decision == 'ABSTAIN':
                recommendations.append("Conduct detailed legal review")
                recommendations.append("Gather additional regulatory guidance")
            
            if evidence_result.get('evidence_quality_score', 1.0) < 0.7:
                recommendations.append("Strengthen evidence documentation")
                recommendations.append("Add specific regulatory citations")
            
            if feature_record.risk_tags:
                recommendations.append(f"Address identified risk areas: {', '.join(feature_record.risk_tags)}")
            
            return recommendations or ["Continue monitoring for regulatory changes"]
        
        def _assess_risk_level(self, decision: str, confidence: float, evidence_result: Dict) -> str:
            """Assess overall risk level"""
            
            if decision == 'NON_COMPLIANT':
                return 'HIGH'
            elif decision == 'ABSTAIN' or confidence < 0.5:
                return 'MEDIUM'
            elif evidence_result.get('evidence_quality_score', 1.0) < 0.7:
                return 'MEDIUM'
            else:
                return 'LOW'
        
        async def _log_decision_for_learning(self, decision: Dict, feature_record: FeatureRecord):
            """Log decision for active learning"""
            
            try:
                if log_compliance_decision:
                    log_compliance_decision(
                        case_id=feature_record.feature_id,
                        decision=decision['verdict'],
                        confidence=decision['confidence'],
                        reasoning=decision['reasoning'],
                        evidence_spans=[],
                        metadata={'agentic_analysis': True, 'feature_record': feature_record.to_dict()}
                    )
            except Exception as e:
                logger.warning(f"Failed to log decision: {e}")
    
    async def main():
        try:
            # Read arguments from stdin
            input_data = json.loads(sys.stdin.read())
            feature_data = input_data.get('feature_data', {})
            jurisdiction = input_data.get('jurisdiction', 'EU')
            
            if not feature_data:
                raise ValueError("Feature data is required")
            
            # Initialize enhanced analyzer
            analyzer = EnhancedComplianceAnalyzer()
            
            # Perform comprehensive analysis
            result = await analyzer.analyze_feature_comprehensive(feature_data, jurisdiction)
            
            print(json.dumps(result))
            
        except Exception as e:
            logger.error(f"Error in enhanced compliance analysis: {e}")
            error_output = {
                'success': False,
                'error': str(e),
                'verdict': 'ABSTAIN',
                'confidence': 0.0,
                'reasoning': f'Enhanced analysis failed: {e}',
                'citations': [],
                'recommendations': ['System error - manual review required'],
                'risk_level': 'HIGH',
                'agentic_analysis': {'error': str(e)}
            }
            print(json.dumps(error_output))
            sys.exit(1)
    
    if __name__ == "__main__":
        import asyncio
        from datetime import datetime
        asyncio.run(main())
        
except ImportError as e:
    # Fallback if agentic components are not available
    logger.error(f"Agentic components not available: {e}")
    error_output = {
        'success': False,
        'error': f"Enhanced analysis system not available: {e}",
        'verdict': 'ABSTAIN',
        'confidence': 0.0,
        'reasoning': f'Agentic tools unavailable: {e}',
        'citations': [],
        'recommendations': ['System setup required for enhanced analysis'],
        'risk_level': 'HIGH',
        'agentic_analysis': {'error': 'Components not available'}
    }
    print(json.dumps(error_output))
    sys.exit(1)
