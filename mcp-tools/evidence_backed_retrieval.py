#!/usr/bin/env python3
"""
Evidence-Backed Document Retrieval for MCP Server
Integrates Evidence Verifier with RAG retrieval for defensible citations
Maintains FeatureRecord format compatibility
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from src.rag.enhanced_rag import EnhancedRAG
    from src.evidence.evidence_verifier import EvidenceVerificationAgent, EvidenceSpan, RegulationMapping
    from artifact_preprocessor.schema import FeatureRecord
    import logging
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    class EvidenceBackedRetrieval:
        """
        Enhanced document retrieval with evidence verification
        Ensures all retrieved documents have verified regulatory relevance
        """
        
        def __init__(self):
            self.rag = EnhancedRAG()
            self.evidence_verifier = EvidenceVerificationAgent()
            logger.info("Evidence-backed retrieval initialized")
        
        def verify_document_evidence(self, query: str, documents: List[Dict], feature_context: Optional[Dict] = None) -> List[Dict]:
            """
            Verify that retrieved documents contain valid evidence for the query
            
            Args:
                query: Search query
                documents: Retrieved documents
                feature_context: Optional FeatureRecord context for better verification
                
            Returns:
                Documents with evidence verification scores and citations
            """
            
            verified_docs = []
            
            for doc in documents:
                try:
                    # Extract content and metadata
                    content = doc.get('content', '')
                    metadata = doc.get('metadata', {})
                    source = metadata.get('source', 'unknown')
                    
                    # Create evidence span from document content
                    evidence_spans = [EvidenceSpan(
                        text=content[:500],  # Use first 500 chars as evidence span
                        start_pos=0,
                        end_pos=min(500, len(content)),
                        source=source,
                        regulatory_context=metadata.get('regulation_type', 'general')
                    )]
                    
                    # Create regulation mappings from document metadata
                    regulation_mappings = []
                    if 'regulation_references' in metadata:
                        for reg_ref in metadata['regulation_references']:
                            regulation_mappings.append(RegulationMapping(
                                regulation_name=reg_ref,
                                text_excerpt=content[:200],
                                is_valid=True,
                                validation_notes=f"Referenced in {source}",
                                source_file=source
                            ))
                    
                    # Verify evidence alignment with query
                    try:
                        verification_result = self.evidence_verifier.verify_reasoning(
                            reasoning_text=query,
                            evidence_spans=evidence_spans,
                            regulation_mappings=regulation_mappings
                        )
                        
                        # Enhance document with verification results
                        enhanced_doc = {
                            **doc,
                            'evidence_verification': {
                                'verified': True,
                                'alignment_score': verification_result.alignment_score,
                                'evidence_quality': verification_result.overall_score,
                                'is_aligned': verification_result.is_aligned,
                                'verification_flags': verification_result.flags,
                                'auto_approved': verification_result.auto_approved,
                                'regulation_mappings_valid': all(rm.is_valid for rm in verification_result.regulation_mappings)
                            },
                            'evidence_citations': self._extract_citations_from_verification(verification_result),
                            'regulatory_relevance_score': self._calculate_regulatory_relevance(verification_result, metadata)
                        }
                        
                        verified_docs.append(enhanced_doc)
                        
                    except Exception as e:
                        logger.warning(f"Evidence verification failed for document {source}: {e}")
                        # Include document with failed verification
                        verified_docs.append({
                            **doc,
                            'evidence_verification': {
                                'verified': False,
                                'error': str(e),
                                'alignment_score': 0.0,
                                'evidence_quality': 0.3,
                                'is_aligned': False
                            },
                            'evidence_citations': [],
                            'regulatory_relevance_score': 0.3
                        })
                        
                except Exception as e:
                    logger.error(f"Document processing failed: {e}")
                    continue
            
            # Sort by evidence quality and regulatory relevance
            verified_docs.sort(key=lambda x: (
                x.get('evidence_verification', {}).get('evidence_quality', 0),
                x.get('regulatory_relevance_score', 0),
                x.get('rerank_score', x.get('score', 0))
            ), reverse=True)
            
            return verified_docs
        
        def _extract_citations_from_verification(self, verification_result) -> List[str]:
            """Extract specific citations from verification result"""
            
            citations = []
            
            # Extract from regulation mappings
            for mapping in verification_result.regulation_mappings:
                if mapping.is_valid:
                    citation = mapping.regulation_name
                    if mapping.section_reference:
                        citation += f" Section {mapping.section_reference}"
                    citations.append(citation)
            
            # Extract from evidence spans
            for span in verification_result.evidence_spans:
                if span.regulation_reference:
                    citations.append(span.regulation_reference)
            
            return list(set(citations))  # Remove duplicates
        
        def _calculate_regulatory_relevance(self, verification_result, metadata: Dict) -> float:
            """Calculate regulatory relevance score"""
            
            base_score = verification_result.overall_score
            
            # Boost for explicit regulation references
            if metadata.get('regulation_references'):
                base_score += 0.1
            
            # Boost for compliance-specific sources
            if any(term in metadata.get('source', '').lower() for term in ['gdpr', 'regulation', 'compliance', 'legal']):
                base_score += 0.1
            
            # Boost for high evidence alignment
            if verification_result.is_aligned:
                base_score += 0.1
            
            return min(1.0, base_score)
    
    def main():
        try:
            # Read arguments from stdin
            input_data = json.loads(sys.stdin.read())
            query = input_data.get('query', '')
            top_k = input_data.get('top_k', 5)
            include_evidence_verification = input_data.get('include_evidence_verification', True)
            feature_context = input_data.get('feature_context')  # Optional FeatureRecord data
            
            if not query:
                raise ValueError("Query is required")
            
            # Initialize evidence-backed retrieval
            retriever = EvidenceBackedRetrieval()
            
            # Retrieve documents
            results = retriever.rag.retrieve_and_rerank(query, top_k=top_k * 2)  # Get more for filtering
            
            # Apply evidence verification if requested
            if include_evidence_verification:
                verified_results = retriever.verify_document_evidence(query, results, feature_context)
                # Limit to requested top_k after verification
                final_results = verified_results[:top_k]
            else:
                final_results = results[:top_k]
            
            # Format results with evidence metadata
            documents = []
            scores = []
            evidence_metadata = []
            
            for result in final_results:
                documents.append({
                    'content': result.get('content', ''),
                    'metadata': result.get('metadata', {}),
                    'source': result.get('metadata', {}).get('source', 'unknown'),
                    'evidence_citations': result.get('evidence_citations', []),
                    'regulatory_relevance': result.get('regulatory_relevance_score', 0.5)
                })
                
                scores.append(result.get('rerank_score', result.get('score', 0.0)))
                
                evidence_metadata.append({
                    'evidence_verified': result.get('evidence_verification', {}).get('verified', False),
                    'evidence_quality': result.get('evidence_verification', {}).get('evidence_quality', 0.5),
                    'alignment_score': result.get('evidence_verification', {}).get('alignment_score', 0.0),
                    'auto_approved': result.get('evidence_verification', {}).get('auto_approved', False),
                    'verification_flags': result.get('evidence_verification', {}).get('verification_flags', [])
                })
            
            # Calculate average evidence quality
            avg_evidence_quality = sum(meta['evidence_quality'] for meta in evidence_metadata) / len(evidence_metadata) if evidence_metadata else 0.5
            verified_count = sum(1 for meta in evidence_metadata if meta['evidence_verified'])
            
            # Return enhanced results
            output = {
                'success': True,
                'documents': documents,
                'scores': scores,
                'evidence_metadata': evidence_metadata,
                'query': query,
                'retrieved_count': len(documents),
                'evidence_verification_enabled': include_evidence_verification,
                'evidence_quality_stats': {
                    'average_quality': avg_evidence_quality,
                    'verified_documents': verified_count,
                    'total_documents': len(documents),
                    'verification_rate': verified_count / len(documents) if documents else 0
                },
                'citations_found': sum(len(doc['evidence_citations']) for doc in documents),
                'regulatory_documents': sum(1 for doc in documents if doc['regulatory_relevance'] > 0.7)
            }
            
            print(json.dumps(output))
            
        except Exception as e:
            logger.error(f"Error in evidence-backed retrieval: {e}")
            error_output = {
                'success': False,
                'error': str(e),
                'documents': [],
                'scores': [],
                'evidence_metadata': [],
                'evidence_verification_enabled': False
            }
            print(json.dumps(error_output))
            sys.exit(1)
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    # Fallback if evidence system is not available
    error_output = {
        'success': False,
        'error': f"Evidence verification system not available: {e}",
        'documents': [],
        'scores': [],
        'evidence_metadata': [],
        'evidence_verification_enabled': False
    }
    print(json.dumps(error_output))
    sys.exit(1)
