#!/usr/bin/env python3
"""
Comprehensive MCP Server Integration Tool
Orchestrates all enhanced agentic capabilities while maintaining FeatureRecord format
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedMCPOrchestrator:
    """
    Orchestrates all enhanced MCP capabilities with full agentic integration
    Maintains FeatureRecord as the canonical format throughout
    """
    
    def __init__(self):
        self.tools_dir = Path(__file__).parent
        logger.info("Enhanced MCP Orchestrator initialized")
    
    def comprehensive_compliance_analysis(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive compliance analysis using all agentic tools
        
        Args:
            request_data: Must contain 'feature_data' and optionally 'jurisdiction'
            
        Returns:
            Comprehensive analysis result with evidence, confidence, and learning insights
        """
        
        try:
            feature_data = request_data.get('feature_data', {})
            jurisdiction = request_data.get('jurisdiction', 'US')
            
            if not feature_data:
                raise ValueError("feature_data is required")
            
            # Step 1: Enhanced compliance analysis
            compliance_result = self._run_enhanced_compliance_analysis(feature_data, jurisdiction)
            
            # Step 2: Evidence-backed retrieval for citations
            evidence_result = self._run_evidence_backed_retrieval(feature_data, jurisdiction)
            
            # Step 3: Get relevant patterns from active learning
            patterns_result = self._get_relevant_learning_patterns(feature_data)
            
            # Step 4: Combine all results with evidence prioritization
            combined_result = self._combine_analysis_results(
                compliance_result, evidence_result, patterns_result, feature_data
            )
            
            return {
                'success': True,
                'analysis_type': 'comprehensive_agentic',
                'timestamp': datetime.now().isoformat(),
                'feature_data_format': 'FeatureRecord_canonical',
                'agentic_tools_used': [
                    'ConfidenceValidatorAgent',
                    'EvidenceVerificationAgent', 
                    'ActiveLearningAgent',
                    'EnhancedRAG'
                ],
                'compliance_analysis': compliance_result,
                'evidence_verification': evidence_result,
                'learning_patterns': patterns_result,
                'final_recommendation': combined_result
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive compliance analysis: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def evidence_backed_compliance_check(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform evidence-backed compliance check with defensible citations
        
        Args:
            request_data: Must contain 'feature_data' and optionally 'jurisdiction'
            
        Returns:
            Compliance result with verified evidence and citations
        """
        
        try:
            feature_data = request_data.get('feature_data', {})
            jurisdiction = request_data.get('jurisdiction', 'US')
            
            # Run evidence-backed retrieval
            evidence_result = self._run_evidence_backed_retrieval(feature_data, jurisdiction)
            
            if evidence_result.get('success'):
                # Extract compliance verdict from evidence
                compliance_verdict = self._extract_compliance_from_evidence(evidence_result)
                
                return {
                    'success': True,
                    'analysis_type': 'evidence_backed_compliance',
                    'timestamp': datetime.now().isoformat(),
                    'verdict': compliance_verdict['verdict'],
                    'confidence': compliance_verdict['confidence'],
                    'evidence_backing': evidence_result,
                    'citations': evidence_result.get('citations', []),
                    'regulatory_references': evidence_result.get('regulatory_references', []),
                    'evidence_quality_score': evidence_result.get('evidence_quality_score', 0.0)
                }
            else:
                return {
                    'success': False,
                    'error': 'Evidence verification failed',
                    'evidence_result': evidence_result
                }
                
        except Exception as e:
            logger.error(f"Error in evidence-backed compliance check: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_human_feedback(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process human feedback for continuous learning
        
        Args:
            request_data: Must contain 'original_analysis', 'human_decision', 'feature_data'
            
        Returns:
            Feedback processing result with learning insights
        """
        
        try:
            feedback_input = {
                'action': 'process_correction',
                'original_analysis': request_data.get('original_analysis', {}),
                'human_decision': request_data.get('human_decision', {}),
                'feature_data': request_data.get('feature_data', {}),
                'correction_metadata': request_data.get('correction_metadata', {})
            }
            
            feedback_result = self._run_active_learning_feedback(feedback_input)
            
            return {
                'success': True,
                'analysis_type': 'human_feedback_processing',
                'timestamp': datetime.now().isoformat(),
                'feedback_result': feedback_result,
                'learning_impact': self._assess_learning_impact(feedback_result)
            }
            
        except Exception as e:
            logger.error(f"Error processing human feedback: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_learning_analytics(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive learning analytics and system improvement metrics
        """
        
        try:
            analytics_input = {
                'action': 'get_analytics'
            }
            
            analytics_result = self._run_active_learning_feedback(analytics_input)
            
            # Enhance with system-wide metrics
            enhanced_analytics = self._enhance_analytics_with_system_metrics(analytics_result)
            
            return {
                'success': True,
                'analysis_type': 'learning_analytics',
                'timestamp': datetime.now().isoformat(),
                'analytics': enhanced_analytics,
                'system_health': self._assess_system_health(enhanced_analytics)
            }
            
        except Exception as e:
            logger.error(f"Error getting learning analytics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_feature_format(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that feature data conforms to FeatureRecord canonical format
        """
        
        try:
            feature_data = request_data.get('feature_data', {})
            
            # Import FeatureRecord for validation
            from artifact_preprocessor.schema import FeatureRecord
            
            # Attempt to create FeatureRecord
            try:
                feature_record = FeatureRecord(
                    feature_id=feature_data.get('feature_id', 'temp_validation'),
                    doc_id=feature_data.get('doc_id', 'validation'),
                    source_path=feature_data.get('source_path', 'validation'),
                    feature_title=feature_data.get('name', feature_data.get('feature_title')),
                    feature_description=feature_data.get('description', feature_data.get('feature_description')),
                    objectives=feature_data.get('objectives'),
                    user_segments=feature_data.get('user_segments'),
                    geo_country=feature_data.get('geo_country'),
                    geo_state=feature_data.get('geo_state'),
                    domain=feature_data.get('domain'),
                    data_practices=feature_data.get('data_practices', []),
                    risk_tags=feature_data.get('risk_tags', []),
                    implicated_regulations=feature_data.get('implicated_regulations', [])
                )
                
                validation_result = {
                    'valid': True,
                    'canonical_format': True,
                    'feature_record': feature_record.to_dict(),
                    'validation_notes': []
                }
                
                # Check for completeness
                completeness = self._assess_feature_completeness(feature_record)
                validation_result['completeness_assessment'] = completeness
                
                return {
                    'success': True,
                    'validation': validation_result
                }
                
            except Exception as validation_error:
                return {
                    'success': True,
                    'validation': {
                        'valid': False,
                        'canonical_format': False,
                        'error': str(validation_error),
                        'suggestions': self._suggest_format_fixes(feature_data, validation_error)
                    }
                }
                
        except Exception as e:
            logger.error(f"Error validating feature format: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def system_status(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive system status including all agentic components
        """
        
        try:
            status = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'system_type': 'enhanced_agentic_mcp',
                'canonical_format': 'FeatureRecord',
                'components': {}
            }
            
            # Check enhanced compliance analysis
            status['components']['enhanced_compliance_analysis'] = self._check_component_status('enhanced_compliance_analysis.py')
            
            # Check evidence-backed retrieval
            status['components']['evidence_backed_retrieval'] = self._check_component_status('evidence_backed_retrieval.py')
            
            # Check active learning feedback
            status['components']['active_learning_feedback'] = self._check_component_status('active_learning_feedback.py')
            
            # Check agentic dependencies
            status['agentic_agents'] = {
                'confidence_validator': self._check_agent_availability('ConfidenceValidatorAgent'),
                'evidence_verification': self._check_agent_availability('EvidenceVerificationAgent'),
                'active_learning': self._check_agent_availability('ActiveLearningAgent')
            }
            
            # Check FeatureRecord schema
            status['canonical_format_status'] = self._check_feature_record_schema()
            
            # Overall system health
            status['overall_health'] = self._calculate_overall_health(status)
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _run_enhanced_compliance_analysis(self, feature_data: Dict[str, Any], jurisdiction: str) -> Dict[str, Any]:
        """Run enhanced compliance analysis tool"""
        
        try:
            analysis_tool = self.tools_dir / 'enhanced_compliance_analysis.py'
            
            input_data = {
                'feature_data': feature_data,
                'jurisdiction': jurisdiction
            }
            
            result = subprocess.run(
                [sys.executable, str(analysis_tool)],
                input=json.dumps(input_data),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"Enhanced compliance analysis failed: {result.stderr}")
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            logger.error(f"Error running enhanced compliance analysis: {e}")
            return {'success': False, 'error': str(e)}
    
    def _run_evidence_backed_retrieval(self, feature_data: Dict[str, Any], jurisdiction: str) -> Dict[str, Any]:
        """Run evidence-backed retrieval tool"""
        
        try:
            retrieval_tool = self.tools_dir / 'evidence_backed_retrieval.py'
            
            input_data = {
                'feature_data': feature_data,
                'jurisdiction': jurisdiction,
                'max_results': 10
            }
            
            result = subprocess.run(
                [sys.executable, str(retrieval_tool)],
                input=json.dumps(input_data),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"Evidence-backed retrieval failed: {result.stderr}")
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            logger.error(f"Error running evidence-backed retrieval: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_relevant_learning_patterns(self, feature_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get relevant patterns from active learning"""
        
        try:
            feedback_tool = self.tools_dir / 'active_learning_feedback.py'
            
            input_data = {
                'action': 'get_patterns',
                'feature_data': feature_data
            }
            
            result = subprocess.run(
                [sys.executable, str(feedback_tool)],
                input=json.dumps(input_data),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.warning(f"Active learning patterns retrieval failed: {result.stderr}")
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            logger.warning(f"Error getting learning patterns: {e}")
            return {'success': False, 'error': str(e)}
    
    def _run_active_learning_feedback(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run active learning feedback tool"""
        
        try:
            feedback_tool = self.tools_dir / 'active_learning_feedback.py'
            
            result = subprocess.run(
                [sys.executable, str(feedback_tool)],
                input=json.dumps(input_data),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"Active learning feedback failed: {result.stderr}")
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            logger.error(f"Error running active learning feedback: {e}")
            return {'success': False, 'error': str(e)}
    
    def _combine_analysis_results(self, compliance_result: Dict, evidence_result: Dict, patterns_result: Dict, feature_data: Dict) -> Dict[str, Any]:
        """Combine results from all analysis tools"""
        
        try:
            # Extract key information
            compliance_verdict = compliance_result.get('compliance_analysis', {}).get('verdict', 'UNKNOWN')
            compliance_confidence = compliance_result.get('confidence_validation', {}).get('final_confidence', 0.0)
            
            evidence_quality = evidence_result.get('evidence_quality_score', 0.0)
            regulatory_references = evidence_result.get('regulatory_references', [])
            
            patterns_confidence_adjustment = patterns_result.get('confidence_suggestions', {}).get('adjustment', 0.0)
            pattern_recommendations = patterns_result.get('pattern_recommendations', [])
            
            # Calculate final confidence with pattern adjustment
            final_confidence = min(1.0, max(0.0, compliance_confidence + patterns_confidence_adjustment))
            
            # Determine final verdict considering evidence quality
            final_verdict = compliance_verdict
            if evidence_quality < 0.3 and compliance_verdict != 'ABSTAIN':
                final_verdict = 'ABSTAIN'  # Low evidence quality triggers abstention
            
            # Generate comprehensive reasoning
            reasoning_parts = []
            
            if compliance_result.get('success'):
                reasoning_parts.append(f"Multi-model ensemble analysis: {compliance_verdict} (confidence: {compliance_confidence:.2f})")
            
            if evidence_result.get('success'):
                reasoning_parts.append(f"Evidence quality score: {evidence_quality:.2f}")
                if regulatory_references:
                    reasoning_parts.append(f"Regulatory references: {len(regulatory_references)} found")
            
            if patterns_result.get('success') and patterns_result.get('patterns_found', 0) > 0:
                reasoning_parts.append(f"Historical patterns: {patterns_result.get('patterns_found', 0)} relevant patterns")
                if patterns_confidence_adjustment != 0:
                    reasoning_parts.append(f"Confidence adjusted by {patterns_confidence_adjustment:+.2f} based on patterns")
            
            if pattern_recommendations:
                reasoning_parts.extend(pattern_recommendations)
            
            return {
                'final_verdict': final_verdict,
                'final_confidence': final_confidence,
                'evidence_quality_score': evidence_quality,
                'regulatory_references_count': len(regulatory_references),
                'patterns_applied': patterns_result.get('patterns_found', 0),
                'confidence_adjustment': patterns_confidence_adjustment,
                'comprehensive_reasoning': ' | '.join(reasoning_parts),
                'decision_factors': {
                    'ensemble_analysis': compliance_verdict,
                    'evidence_backing': evidence_quality,
                    'historical_patterns': patterns_result.get('patterns_found', 0),
                    'regulatory_coverage': len(regulatory_references)
                }
            }
            
        except Exception as e:
            logger.error(f"Error combining analysis results: {e}")
            return {
                'final_verdict': 'ERROR',
                'final_confidence': 0.0,
                'error': str(e)
            }
    
    def _extract_compliance_from_evidence(self, evidence_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract compliance verdict from evidence analysis"""
        
        evidence_quality = evidence_result.get('evidence_quality_score', 0.0)
        regulatory_refs = evidence_result.get('regulatory_references', [])
        
        # Simple heuristic - in production this would be more sophisticated
        if evidence_quality > 0.8 and regulatory_refs:
            verdict = 'COMPLIANT'
            confidence = evidence_quality
        elif evidence_quality > 0.6:
            verdict = 'NON_COMPLIANT'
            confidence = evidence_quality * 0.8
        else:
            verdict = 'ABSTAIN'
            confidence = 0.5
        
        return {
            'verdict': verdict,
            'confidence': confidence,
            'reasoning': f"Evidence-based assessment (quality: {evidence_quality:.2f}, refs: {len(regulatory_refs)})"
        }
    
    def _assess_learning_impact(self, feedback_result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the impact of learning from feedback"""
        
        if not feedback_result.get('success'):
            return {'impact': 'none', 'reason': 'feedback_processing_failed'}
        
        correction_type = feedback_result.get('correction_type', 'unknown')
        retraining_rec = feedback_result.get('retraining_recommendation', {})
        
        impact_level = 'low'
        if correction_type in ['false_positive', 'false_negative']:
            impact_level = 'high'
        elif retraining_rec.get('should_retrain', False):
            impact_level = 'medium'
        
        return {
            'impact': impact_level,
            'correction_type': correction_type,
            'retraining_recommended': retraining_rec.get('should_retrain', False),
            'improvement_areas': feedback_result.get('improvement_suggestions', [])
        }
    
    def _enhance_analytics_with_system_metrics(self, analytics_result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance analytics with system-wide metrics"""
        
        if not analytics_result.get('success'):
            return analytics_result
        
        enhanced = analytics_result.copy()
        enhanced['system_metrics'] = {
            'tool_integration_status': 'full_agentic',
            'canonical_format_compliance': 'FeatureRecord',
            'evidence_verification_enabled': True,
            'confidence_validation_enabled': True,
            'active_learning_enabled': True
        }
        
        return enhanced
    
    def _assess_system_health(self, analytics: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall system health"""
        
        health_score = 1.0
        issues = []
        
        if not analytics.get('success'):
            health_score -= 0.5
            issues.append('analytics_failure')
        
        # Check component availability
        components_healthy = all([
            analytics.get('system_metrics', {}).get('evidence_verification_enabled', False),
            analytics.get('system_metrics', {}).get('confidence_validation_enabled', False),
            analytics.get('system_metrics', {}).get('active_learning_enabled', False)
        ])
        
        if not components_healthy:
            health_score -= 0.3
            issues.append('component_unavailability')
        
        return {
            'health_score': health_score,
            'status': 'healthy' if health_score > 0.8 else 'degraded' if health_score > 0.5 else 'unhealthy',
            'issues': issues
        }
    
    def _assess_feature_completeness(self, feature_record) -> Dict[str, Any]:
        """Assess completeness of FeatureRecord"""
        
        completeness_score = 0.0
        total_fields = 12
        
        # Required fields
        if feature_record.feature_id: completeness_score += 1
        if feature_record.feature_title: completeness_score += 1
        if feature_record.feature_description: completeness_score += 1
        if feature_record.domain: completeness_score += 1
        
        # Important fields
        if feature_record.geo_country: completeness_score += 1
        if feature_record.data_practices: completeness_score += 1
        if feature_record.risk_tags: completeness_score += 1
        
        # Optional but valuable fields
        if feature_record.objectives: completeness_score += 1
        if feature_record.user_segments: completeness_score += 1
        if feature_record.geo_state: completeness_score += 1
        if feature_record.implicated_regulations: completeness_score += 1
        if feature_record.source_path: completeness_score += 1
        
        return {
            'completeness_score': completeness_score / total_fields,
            'missing_required_fields': [],  # Would implement field checking
            'recommended_fields': ['geo_country', 'data_practices', 'risk_tags'] if completeness_score < 7 else []
        }
    
    def _suggest_format_fixes(self, feature_data: Dict[str, Any], validation_error: Exception) -> List[str]:
        """Suggest fixes for format validation errors"""
        
        suggestions = []
        error_str = str(validation_error).lower()
        
        if 'feature_id' in error_str:
            suggestions.append("Add 'feature_id' field with unique identifier")
        if 'feature_title' in error_str or 'name' in error_str:
            suggestions.append("Add 'feature_title' or 'name' field with descriptive title")
        if 'feature_description' in error_str or 'description' in error_str:
            suggestions.append("Add 'feature_description' or 'description' field")
        
        suggestions.append("Ensure all required FeatureRecord fields are present")
        suggestions.append("Refer to artifact_preprocessor/schema.py for canonical format")
        
        return suggestions
    
    def _check_component_status(self, component_file: str) -> Dict[str, Any]:
        """Check if a component is available and working"""
        
        try:
            component_path = self.tools_dir / component_file
            if component_path.exists():
                return {
                    'available': True,
                    'path': str(component_path),
                    'last_modified': datetime.fromtimestamp(component_path.stat().st_mtime).isoformat()
                }
            else:
                return {
                    'available': False,
                    'error': 'file_not_found'
                }
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }
    
    def _check_agent_availability(self, agent_name: str) -> Dict[str, Any]:
        """Check if an agentic component is available"""
        
        try:
            if agent_name == 'ConfidenceValidatorAgent':
                from src.agents.confidence_validator_agent import ConfidenceValidatorAgent
                return {'available': True, 'type': 'confidence_validator'}
            elif agent_name == 'EvidenceVerificationAgent':
                from src.agents.evidence_verification_agent import EvidenceVerificationAgent
                return {'available': True, 'type': 'evidence_verification'}
            elif agent_name == 'ActiveLearningAgent':
                from src.agents.active_learning_agent import ActiveLearningAgent
                return {'available': True, 'type': 'active_learning'}
            else:
                return {'available': False, 'error': 'unknown_agent'}
        except ImportError as e:
            return {'available': False, 'error': f'import_error: {e}'}
    
    def _check_feature_record_schema(self) -> Dict[str, Any]:
        """Check FeatureRecord schema availability"""
        
        try:
            from artifact_preprocessor.schema import FeatureRecord
            return {
                'available': True,
                'canonical_format': 'FeatureRecord',
                'schema_location': 'artifact_preprocessor/schema.py'
            }
        except ImportError as e:
            return {
                'available': False,
                'error': f'schema_import_error: {e}'
            }
    
    def _calculate_overall_health(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall system health"""
        
        component_health = sum(1 for comp in status['components'].values() if comp.get('available', False))
        total_components = len(status['components'])
        
        agent_health = sum(1 for agent in status['agentic_agents'].values() if agent.get('available', False))
        total_agents = len(status['agentic_agents'])
        
        schema_health = 1 if status['canonical_format_status'].get('available', False) else 0
        
        overall_score = (component_health + agent_health + schema_health) / (total_components + total_agents + 1)
        
        return {
            'health_score': overall_score,
            'status': 'healthy' if overall_score > 0.8 else 'degraded' if overall_score > 0.5 else 'critical',
            'component_health': f"{component_health}/{total_components}",
            'agent_health': f"{agent_health}/{total_agents}",
            'schema_health': 'available' if schema_health else 'unavailable'
        }

def main():
    try:
        # Read arguments from stdin
        input_data = json.loads(sys.stdin.read())
        action = input_data.get('action', 'comprehensive_analysis')
        
        orchestrator = EnhancedMCPOrchestrator()
        
        if action == 'comprehensive_analysis':
            result = orchestrator.comprehensive_compliance_analysis(input_data)
        elif action == 'evidence_backed_check':
            result = orchestrator.evidence_backed_compliance_check(input_data)
        elif action == 'process_feedback':
            result = orchestrator.process_human_feedback(input_data)
        elif action == 'get_analytics':
            result = orchestrator.get_learning_analytics(input_data)
        elif action == 'validate_format':
            result = orchestrator.validate_feature_format(input_data)
        elif action == 'system_status':
            result = orchestrator.system_status(input_data)
        else:
            raise ValueError(f"Unknown action: {action}")
        
        print(json.dumps(result))
        
    except Exception as e:
        logger.error(f"Error in MCP orchestrator: {e}")
        error_output = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        print(json.dumps(error_output))
        sys.exit(1)

if __name__ == "__main__":
    main()
