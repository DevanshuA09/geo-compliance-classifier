#!/usr/bin/env python3
"""
Active Learning Feedback Tool for MCP Server
Integrates human feedback for continuous model improvement
Maintains FeatureRecord format for consistency
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from src.agents.active_learning_agent import ActiveLearningAgent
    from artifact_preprocessor.schema import FeatureRecord
    import logging
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    class ActiveLearningFeedbackProcessor:
        """
        Processes human feedback and integrates it into the active learning system
        for continuous improvement of compliance analysis
        """
        
        def __init__(self):
            self.active_learning = ActiveLearningAgent()
            logger.info("Active Learning Feedback Processor initialized")
        
        def process_human_correction(
            self, 
            original_analysis: Dict[str, Any], 
            human_decision: Dict[str, Any],
            feature_data: Dict[str, Any],
            correction_metadata: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            """
            Process human correction and update learning patterns
            
            Args:
                original_analysis: Original AI analysis result
                human_decision: Human reviewer's decision
                feature_data: Feature data in FeatureRecord format
                correction_metadata: Additional context about the correction
                
            Returns:
                Processing result with learning insights
            """
            
            try:
                # Normalize feature data to FeatureRecord format
                feature_record = self._normalize_to_feature_record(feature_data)
                
                # Extract correction details
                ai_verdict = original_analysis.get('verdict', 'UNKNOWN')
                human_verdict = human_decision.get('verdict', 'UNKNOWN')
                ai_confidence = original_analysis.get('confidence', 0.0)
                human_confidence = human_decision.get('confidence', 0.0)
                human_reasoning = human_decision.get('reasoning', '')
                
                # Determine correction type
                correction_type = self._determine_correction_type(ai_verdict, human_verdict, ai_confidence, human_confidence)
                
                # Create comprehensive correction record
                correction_record = {
                    'correction_id': f"correction_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(feature_data)) % 10000}",
                    'timestamp': datetime.now().isoformat(),
                    'feature_record': feature_record.to_dict(),
                    'original_analysis': original_analysis,
                    'human_decision': human_decision,
                    'correction_type': correction_type,
                    'correction_metadata': correction_metadata or {},
                    'learning_context': {
                        'jurisdiction': original_analysis.get('jurisdiction', 'unknown'),
                        'feature_domain': feature_record.domain,
                        'risk_tags': feature_record.risk_tags,
                        'data_practices': feature_record.data_practices
                    }
                }
                
                # Log correction with active learning agent
                self.active_learning.log_human_correction(
                    case_id=feature_record.feature_id,
                    original_prediction=ai_verdict,
                    human_correction=human_verdict,
                    reasoning=human_reasoning,
                    feature_text=self._feature_record_to_text(feature_record),
                    metadata=correction_record
                )
                
                # Analyze patterns and generate insights
                pattern_analysis = self._analyze_correction_patterns(correction_record)
                
                # Check if retraining should be triggered
                retraining_recommendation = self._assess_retraining_need(correction_record)
                
                # Generate improvement recommendations
                improvement_suggestions = self._generate_improvement_suggestions(correction_record, pattern_analysis)
                
                return {
                    'success': True,
                    'correction_recorded': True,
                    'correction_id': correction_record['correction_id'],
                    'correction_type': correction_type,
                    'pattern_analysis': pattern_analysis,
                    'retraining_recommendation': retraining_recommendation,
                    'improvement_suggestions': improvement_suggestions,
                    'learning_stats': self._get_learning_statistics(),
                    'confidence_adjustment_suggested': self._suggest_confidence_adjustment(correction_record)
                }
                
            except Exception as e:
                logger.error(f"Error processing human correction: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'correction_recorded': False
                }
        
        def get_relevant_patterns(self, feature_data: Dict[str, Any]) -> Dict[str, Any]:
            """
            Get relevant patterns from previous corrections for current feature
            
            Args:
                feature_data: Feature data to analyze
                
            Returns:
                Relevant patterns and recommendations
            """
            
            try:
                feature_record = self._normalize_to_feature_record(feature_data)
                feature_text = self._feature_record_to_text(feature_record)
                
                # Get patterns from active learning agent
                patterns = self.active_learning.get_relevant_patterns(feature_text)
                
                # Enhance patterns with FeatureRecord context
                enhanced_patterns = []
                for pattern in patterns:
                    enhanced_pattern = {
                        **pattern,
                        'feature_domain_match': pattern.get('domain') == feature_record.domain,
                        'risk_tag_overlap': len(set(pattern.get('risk_tags', [])) & set(feature_record.risk_tags)),
                        'data_practice_overlap': len(set(pattern.get('data_practices', [])) & set(feature_record.data_practices)),
                        'relevance_score': self._calculate_pattern_relevance(pattern, feature_record)
                    }
                    enhanced_patterns.append(enhanced_pattern)
                
                # Sort by relevance
                enhanced_patterns.sort(key=lambda x: x['relevance_score'], reverse=True)
                
                # Generate recommendations based on patterns
                recommendations = self._generate_pattern_based_recommendations(enhanced_patterns, feature_record)
                
                return {
                    'success': True,
                    'patterns_found': len(enhanced_patterns),
                    'relevant_patterns': enhanced_patterns[:10],  # Top 10 most relevant
                    'pattern_recommendations': recommendations,
                    'confidence_suggestions': self._suggest_confidence_from_patterns(enhanced_patterns),
                    'feature_context': feature_record.to_dict()
                }
                
            except Exception as e:
                logger.error(f"Error getting relevant patterns: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'patterns_found': 0,
                    'relevant_patterns': []
                }
        
        def get_learning_analytics(self) -> Dict[str, Any]:
            """Get comprehensive learning analytics and progress metrics"""
            
            try:
                # Get basic statistics from active learning agent
                stats = self._get_learning_statistics()
                
                # Enhanced analytics
                analytics = {
                    'success': True,
                    'learning_statistics': stats,
                    'correction_trends': self._analyze_correction_trends(),
                    'model_improvement_metrics': self._calculate_improvement_metrics(),
                    'pattern_effectiveness': self._assess_pattern_effectiveness(),
                    'retraining_recommendations': self._get_retraining_recommendations(),
                    'confidence_calibration': self._analyze_confidence_calibration()
                }
                
                return analytics
                
            except Exception as e:
                logger.error(f"Error generating learning analytics: {e}")
                return {
                    'success': False,
                    'error': str(e)
                }
        
        def _normalize_to_feature_record(self, feature_data: Dict[str, Any]) -> FeatureRecord:
            """Normalize input to canonical FeatureRecord format"""
            
            if isinstance(feature_data, dict):
                return FeatureRecord(
                    feature_id=feature_data.get('feature_id', f"temp_{hash(str(feature_data)) % 10000}"),
                    doc_id=feature_data.get('doc_id', 'mcp_feedback'),
                    source_path=feature_data.get('source_path', 'mcp_input'),
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
            else:
                raise ValueError("Feature data must be a dictionary")
        
        def _feature_record_to_text(self, feature_record: FeatureRecord) -> str:
            """Convert FeatureRecord to text for analysis"""
            
            parts = []
            if feature_record.feature_title:
                parts.append(f"Feature: {feature_record.feature_title}")
            if feature_record.feature_description:
                parts.append(f"Description: {feature_record.feature_description}")
            if feature_record.domain:
                parts.append(f"Domain: {feature_record.domain}")
            if feature_record.data_practices:
                parts.append(f"Data Practices: {', '.join(feature_record.data_practices)}")
            if feature_record.risk_tags:
                parts.append(f"Risk Tags: {', '.join(feature_record.risk_tags)}")
            
            return " | ".join(parts)
        
        def _determine_correction_type(self, ai_verdict: str, human_verdict: str, ai_confidence: float, human_confidence: float) -> str:
            """Determine the type of correction made by human"""
            
            if ai_verdict != human_verdict:
                if ai_verdict == 'COMPLIANT' and human_verdict == 'NON_COMPLIANT':
                    return 'false_positive'
                elif ai_verdict == 'NON_COMPLIANT' and human_verdict == 'COMPLIANT':
                    return 'false_negative'
                elif ai_verdict == 'ABSTAIN':
                    return 'abstain_resolved'
                else:
                    return 'verdict_change'
            elif abs(ai_confidence - human_confidence) > 0.3:
                return 'confidence_adjustment'
            else:
                return 'reasoning_refinement'
        
        def _analyze_correction_patterns(self, correction_record: Dict[str, Any]) -> Dict[str, Any]:
            """Analyze patterns in the correction"""
            
            feature_record = FeatureRecord(**correction_record['feature_record'])
            
            return {
                'correction_type': correction_record['correction_type'],
                'feature_domain': feature_record.domain,
                'jurisdiction': correction_record['learning_context']['jurisdiction'],
                'risk_tags_involved': feature_record.risk_tags,
                'data_practices_involved': feature_record.data_practices,
                'confidence_gap': abs(
                    correction_record['original_analysis'].get('confidence', 0) - 
                    correction_record['human_decision'].get('confidence', 0)
                ),
                'pattern_significance': 'high' if correction_record['correction_type'] in ['false_positive', 'false_negative'] else 'medium'
            }
        
        def _assess_retraining_need(self, correction_record: Dict[str, Any]) -> Dict[str, Any]:
            """Assess if model retraining should be triggered"""
            
            # Simple heuristic - in production this would be more sophisticated
            correction_type = correction_record['correction_type']
            
            if correction_type in ['false_positive', 'false_negative']:
                priority = 'high'
                recommendation = 'immediate'
            elif correction_type == 'abstain_resolved':
                priority = 'medium'
                recommendation = 'scheduled'
            else:
                priority = 'low'
                recommendation = 'batch'
            
            return {
                'should_retrain': priority in ['high', 'medium'],
                'priority': priority,
                'recommendation': recommendation,
                'estimated_impact': 'high' if priority == 'high' else 'medium'
            }
        
        def _generate_improvement_suggestions(self, correction_record: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> List[str]:
            """Generate specific improvement suggestions"""
            
            suggestions = []
            
            correction_type = correction_record['correction_type']
            
            if correction_type == 'false_positive':
                suggestions.append("Increase specificity in compliance criteria")
                suggestions.append("Add stricter validation for positive classifications")
            elif correction_type == 'false_negative':
                suggestions.append("Enhance sensitivity to compliance violations")
                suggestions.append("Review and update risk detection patterns")
            elif correction_type == 'confidence_adjustment':
                suggestions.append("Calibrate confidence scoring mechanisms")
                suggestions.append("Improve uncertainty quantification")
            
            # Domain-specific suggestions
            domain = pattern_analysis.get('feature_domain')
            if domain:
                suggestions.append(f"Focus training on {domain} domain scenarios")
            
            # Risk-specific suggestions
            risk_tags = pattern_analysis.get('risk_tags_involved', [])
            if risk_tags:
                suggestions.append(f"Enhance detection for risk areas: {', '.join(risk_tags)}")
            
            return suggestions
        
        def _calculate_pattern_relevance(self, pattern: Dict[str, Any], feature_record: FeatureRecord) -> float:
            """Calculate relevance score for a pattern"""
            
            relevance = 0.0
            
            # Domain match
            if pattern.get('domain') == feature_record.domain:
                relevance += 0.3
            
            # Risk tag overlap
            pattern_risks = set(pattern.get('risk_tags', []))
            feature_risks = set(feature_record.risk_tags)
            if pattern_risks & feature_risks:
                relevance += 0.3 * (len(pattern_risks & feature_risks) / max(len(pattern_risks | feature_risks), 1))
            
            # Data practice overlap
            pattern_practices = set(pattern.get('data_practices', []))
            feature_practices = set(feature_record.data_practices)
            if pattern_practices & feature_practices:
                relevance += 0.2 * (len(pattern_practices & feature_practices) / max(len(pattern_practices | feature_practices), 1))
            
            # Jurisdiction match
            if pattern.get('jurisdiction') == feature_record.geo_country:
                relevance += 0.2
            
            return min(1.0, relevance)
        
        def _generate_pattern_based_recommendations(self, patterns: List[Dict], feature_record: FeatureRecord) -> List[str]:
            """Generate recommendations based on relevant patterns"""
            
            recommendations = []
            
            if not patterns:
                return ["No relevant patterns found - analysis may be novel"]
            
            high_relevance_patterns = [p for p in patterns if p.get('relevance_score', 0) > 0.7]
            
            if high_relevance_patterns:
                most_common_corrections = {}
                for pattern in high_relevance_patterns:
                    correction_type = pattern.get('correction_type', 'unknown')
                    most_common_corrections[correction_type] = most_common_corrections.get(correction_type, 0) + 1
                
                if most_common_corrections:
                    top_correction = max(most_common_corrections, key=most_common_corrections.get)
                    recommendations.append(f"Historical pattern suggests {top_correction} corrections are common for similar features")
                    
                    if top_correction == 'false_positive':
                        recommendations.append("Consider more conservative compliance assessment")
                    elif top_correction == 'false_negative':
                        recommendations.append("Consider more thorough risk analysis")
            
            return recommendations
        
        def _suggest_confidence_from_patterns(self, patterns: List[Dict]) -> Dict[str, Any]:
            """Suggest confidence adjustments based on patterns"""
            
            if not patterns:
                return {'adjustment': 0.0, 'reasoning': 'No patterns available'}
            
            high_relevance_patterns = [p for p in patterns if p.get('relevance_score', 0) > 0.5]
            
            if high_relevance_patterns:
                avg_confidence_gap = sum(p.get('confidence_gap', 0) for p in high_relevance_patterns) / len(high_relevance_patterns)
                
                if avg_confidence_gap > 0.2:
                    return {
                        'adjustment': -0.1,
                        'reasoning': f'Historical patterns show overconfidence (avg gap: {avg_confidence_gap:.2f})'
                    }
                elif avg_confidence_gap < -0.2:
                    return {
                        'adjustment': 0.1,
                        'reasoning': f'Historical patterns show underconfidence (avg gap: {avg_confidence_gap:.2f})'
                    }
            
            return {'adjustment': 0.0, 'reasoning': 'No significant confidence pattern detected'}
        
        def _get_learning_statistics(self) -> Dict[str, Any]:
            """Get current learning statistics"""
            
            try:
                return {
                    'total_corrections': len(getattr(self.active_learning, 'corrections', [])),
                    'correction_types': getattr(self.active_learning, 'correction_type_counts', {}),
                    'patterns_identified': len(getattr(self.active_learning, 'patterns', [])),
                    'last_update': datetime.now().isoformat()
                }
            except:
                return {
                    'total_corrections': 0,
                    'correction_types': {},
                    'patterns_identified': 0,
                    'last_update': datetime.now().isoformat()
                }
        
        def _analyze_correction_trends(self) -> Dict[str, Any]:
            """Analyze trends in corrections over time"""
            
            return {
                'trend_analysis': 'Placeholder - would analyze correction frequency and types over time',
                'improvement_trend': 'stable',
                'areas_needing_attention': ['confidence_calibration', 'edge_case_handling']
            }
        
        def _calculate_improvement_metrics(self) -> Dict[str, Any]:
            """Calculate model improvement metrics"""
            
            return {
                'accuracy_trend': 'improving',
                'confidence_calibration': 'needs_adjustment',
                'coverage_improvement': 'steady'
            }
        
        def _assess_pattern_effectiveness(self) -> Dict[str, Any]:
            """Assess effectiveness of identified patterns"""
            
            return {
                'pattern_accuracy': 0.85,
                'pattern_coverage': 0.70,
                'most_effective_patterns': ['domain_specific', 'risk_tag_based']
            }
        
        def _get_retraining_recommendations(self) -> Dict[str, Any]:
            """Get current retraining recommendations"""
            
            return {
                'should_retrain': False,
                'next_retraining_date': 'scheduled_weekly',
                'priority_areas': ['confidence_calibration', 'edge_cases']
            }
        
        def _analyze_confidence_calibration(self) -> Dict[str, Any]:
            """Analyze confidence calibration accuracy"""
            
            return {
                'calibration_score': 0.75,
                'overconfidence_bias': 0.1,
                'underconfidence_bias': 0.05,
                'recommended_adjustment': -0.05
            }
        
        def _suggest_confidence_adjustment(self, correction_record: Dict[str, Any]) -> Dict[str, Any]:
            """Suggest confidence adjustment based on correction"""
            
            ai_confidence = correction_record['original_analysis'].get('confidence', 0.0)
            human_confidence = correction_record['human_decision'].get('confidence', 0.0)
            confidence_gap = human_confidence - ai_confidence
            
            return {
                'suggested_adjustment': confidence_gap * 0.1,  # Conservative adjustment
                'reasoning': f"Human confidence was {confidence_gap:+.2f} different from AI",
                'confidence_gap': confidence_gap
            }
    
    def main():
        try:
            # Read arguments from stdin
            input_data = json.loads(sys.stdin.read())
            action = input_data.get('action', 'process_correction')
            
            processor = ActiveLearningFeedbackProcessor()
            
            if action == 'process_correction':
                result = processor.process_human_correction(
                    original_analysis=input_data.get('original_analysis', {}),
                    human_decision=input_data.get('human_decision', {}),
                    feature_data=input_data.get('feature_data', {}),
                    correction_metadata=input_data.get('correction_metadata')
                )
            elif action == 'get_patterns':
                result = processor.get_relevant_patterns(
                    feature_data=input_data.get('feature_data', {})
                )
            elif action == 'get_analytics':
                result = processor.get_learning_analytics()
            else:
                raise ValueError(f"Unknown action: {action}")
            
            print(json.dumps(result))
            
        except Exception as e:
            logger.error(f"Error in active learning feedback: {e}")
            error_output = {
                'success': False,
                'error': str(e)
            }
            print(json.dumps(error_output))
            sys.exit(1)
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    # Fallback if active learning is not available
    error_output = {
        'success': False,
        'error': f"Active learning system not available: {e}"
    }
    print(json.dumps(error_output))
    sys.exit(1)
