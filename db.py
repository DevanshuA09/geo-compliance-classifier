#!/usr/bin/env python3
"""
Database module for compliance checker app
Uses SQLAlchemy ORM with SQLite for demo simplicity
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Float, DateTime, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func

# Import canonical FeatureRecord schema
try:
    from artifact_preprocessor.schema import FeatureRecord
    FEATURE_RECORD_AVAILABLE = True
except ImportError:
    FEATURE_RECORD_AVAILABLE = False
    print("Warning: FeatureRecord schema not available, using simplified version")

# Database setup
DATABASE_URL = "sqlite:///compliance_decisions.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Decision(Base):
    """
    Decision table model aligned with canonical FeatureRecord schema
    """
    __tablename__ = "decisions"
    
    # Database-specific fields
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # FeatureRecord core identifiers (canonical)
    feature_id = Column(String(255), index=True)
    doc_id = Column(String(255), index=True)
    source_path = Column(Text)
    
    # FeatureRecord document metadata (canonical)
    date = Column(String(50))  # Optional date from document
    
    # FeatureRecord feature content (canonical)
    feature_title = Column(Text)
    feature_description = Column(Text)
    
    # FeatureRecord extracted sections (canonical)
    objectives = Column(Text)
    user_segments = Column(Text)
    
    # FeatureRecord geographic information (canonical)
    geo_country = Column(String(10), index=True)
    geo_state = Column(String(50))
    
    # FeatureRecord compliance analysis (canonical)
    domain = Column(String(255), index=True)  # recommendations, advertising, safety, etc.
    label = Column(String(50))  # non-compliant, partially-compliant, compliant
    implicated_regulations = Column(Text)  # JSON array of exact legal regulations
    data_practices = Column(Text)  # JSON array of intervention_logs, content_analysis, etc.
    rationale = Column(Text)  # Why regulations apply to this feature
    risk_tags = Column(Text)  # JSON array of addiction_risk, minor_targeting, etc.
    confidence_score = Column(Float)  # Canonical confidence score
    
    # Codename expansion (canonical)
    codename_hits_json = Column(Text)  # JSON array of codename hits
    
    # Analysis metadata (additional fields for decision tracking)
    jurisdiction = Column(String(10), index=True)  # Analysis jurisdiction
    law = Column(String(255), index=True)  # Specific law analyzed
    trigger = Column(String(255))  # What triggered the analysis
    require_compliance = Column(String(10))  # YES | NO | ABSTAIN (derived from label)
    analysis_confidence = Column(Float)  # Analysis-specific confidence (may differ from canonical)
    citations = Column(Text)  # JSON string of legal citations
    llm_output = Column(Text)  # JSON string of LLM analysis
    
    # Human review fields
    human_override = Column(String(10), nullable=True)  # YES | NO | ABSTAIN
    reviewer_notes = Column(Text, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert decision to dictionary with canonical FeatureRecord format"""
        return {
            # Database fields
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            
            # Canonical FeatureRecord fields
            'feature_id': self.feature_id,
            'doc_id': self.doc_id,
            'source_path': self.source_path,
            'date': self.date,
            'feature_title': self.feature_title,
            'feature_description': self.feature_description,
            'objectives': self.objectives,
            'user_segments': self.user_segments,
            'geo_country': self.geo_country,
            'geo_state': self.geo_state,
            'domain': self.domain,
            'label': self.label,
            'implicated_regulations': json.loads(self.implicated_regulations) if self.implicated_regulations else [],
            'data_practices': json.loads(self.data_practices) if self.data_practices else [],
            'rationale': self.rationale,
            'risk_tags': json.loads(self.risk_tags) if self.risk_tags else [],
            'confidence_score': self.confidence_score,
            'codename_hits_json': json.loads(self.codename_hits_json) if self.codename_hits_json else [],
            
            # Analysis-specific fields
            'jurisdiction': self.jurisdiction,
            'law': self.law,
            'trigger': self.trigger,
            'require_compliance': self.require_compliance,
            'analysis_confidence': self.analysis_confidence,
            'citations': json.loads(self.citations) if self.citations else [],
            'llm_output': json.loads(self.llm_output) if self.llm_output else {},
            
            # Human review fields
            'human_override': self.human_override,
            'reviewer_notes': self.reviewer_notes,
            
            # Backward compatibility fields for existing Streamlit app
            'feature_text': self.feature_description or self.feature_title or 'No description',
            'confidence': self.analysis_confidence or self.confidence_score or 0.0,
            'human_reviewer': getattr(self, 'human_reviewer', None),
            'last_updated': getattr(self, 'last_updated', self.updated_at)
        }
    
    def to_feature_record(self) -> 'FeatureRecord':
        """Convert to canonical FeatureRecord object"""
        if not FEATURE_RECORD_AVAILABLE:
            raise ImportError("FeatureRecord schema not available")
        
        # Parse codename hits
        codename_hits = []
        if self.codename_hits_json:
            try:
                hits_data = json.loads(self.codename_hits_json)
                for hit_data in hits_data:
                    from artifact_preprocessor.schema import CodenameHit
                    codename_hits.append(CodenameHit(
                        term=hit_data['term'],
                        expansion=hit_data['expansion'],
                        count=hit_data['count'],
                        spans=hit_data['spans']
                    ))
            except Exception:
                pass  # Ignore parsing errors
        
        return FeatureRecord(
            feature_id=self.feature_id,
            doc_id=self.doc_id,
            source_path=self.source_path,
            date=self.date,
            feature_title=self.feature_title,
            feature_description=self.feature_description,
            objectives=self.objectives,
            user_segments=self.user_segments,
            geo_country=self.geo_country,
            geo_state=self.geo_state,
            codename_hits=codename_hits,
            domain=self.domain,
            label=self.label,
            implicated_regulations=json.loads(self.implicated_regulations) if self.implicated_regulations else [],
            data_practices=json.loads(self.data_practices) if self.data_practices else [],
            rationale=self.rationale,
            risk_tags=json.loads(self.risk_tags) if self.risk_tags else [],
            confidence_score=self.confidence_score
        )

def init_database():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("Database initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        print(f"Error getting database session: {e}")
        db.close()
        raise

def save_decision(decision_dict: Dict[str, Any]) -> Optional[int]:
    """
    Save a new decision record to the database using canonical FeatureRecord format
    
    Args:
        decision_dict: Dictionary containing decision data (can be FeatureRecord format or analysis format)
        
    Returns:
        ID of the saved decision or None if failed
    """
    try:
        db = get_db()
        
        # Handle FeatureRecord input vs analysis input
        if 'feature_record' in decision_dict:
            # This is from enhanced analysis with FeatureRecord
            feature_record_data = decision_dict['feature_record']
            analysis_data = decision_dict
        elif all(key in decision_dict for key in ['feature_id', 'doc_id', 'source_path']):
            # This looks like a FeatureRecord format
            feature_record_data = decision_dict
            analysis_data = decision_dict
        else:
            # Legacy format - create FeatureRecord structure
            feature_record_data = {
                'feature_id': decision_dict.get('feature_id', f"feature_{int(datetime.now().timestamp())}"),
                'doc_id': decision_dict.get('doc_id', 'analysis_input'),
                'source_path': decision_dict.get('source_path', 'mcp_analysis'),
                'feature_title': decision_dict.get('feature_text', decision_dict.get('feature_description', decision_dict.get('name', ''))),
                'feature_description': decision_dict.get('feature_text', decision_dict.get('feature_description', decision_dict.get('description', ''))),
                'geo_country': decision_dict.get('jurisdiction', decision_dict.get('geo_country')),
                'domain': decision_dict.get('domain'),
                'data_practices': decision_dict.get('data_practices', []),
                'risk_tags': decision_dict.get('risk_tags', []),
                'implicated_regulations': decision_dict.get('implicated_regulations', [])
            }
            analysis_data = decision_dict
        
        # Extract canonical FeatureRecord fields
        feature_id = feature_record_data.get('feature_id', f"feature_{int(datetime.now().timestamp())}")
        doc_id = feature_record_data.get('doc_id', 'mcp_analysis')
        source_path = feature_record_data.get('source_path', 'mcp_input')
        date = feature_record_data.get('date')
        feature_title = feature_record_data.get('feature_title', feature_record_data.get('name'))
        feature_description = feature_record_data.get('feature_description', feature_record_data.get('description'))
        objectives = feature_record_data.get('objectives')
        user_segments = feature_record_data.get('user_segments')
        geo_country = feature_record_data.get('geo_country')
        geo_state = feature_record_data.get('geo_state')
        domain = feature_record_data.get('domain')
        
        # Handle compliance label mapping
        verdict = analysis_data.get('verdict', analysis_data.get('require_compliance', 'ABSTAIN'))
        if verdict == 'COMPLIANT':
            label = 'compliant'
            require_compliance = 'NO'
        elif verdict == 'NON_COMPLIANT':
            label = 'non-compliant'
            require_compliance = 'YES'
        else:
            label = 'partially-compliant'  # For ABSTAIN cases
            require_compliance = 'ABSTAIN'
        
        # Extract or default canonical arrays
        implicated_regulations = feature_record_data.get('implicated_regulations', analysis_data.get('citations', []))
        data_practices = feature_record_data.get('data_practices', [])
        risk_tags = feature_record_data.get('risk_tags', [])
        codename_hits = feature_record_data.get('codename_hits_json', [])
        
        # Rationale and confidence
        rationale = feature_record_data.get('rationale', analysis_data.get('reasoning'))
        confidence_score = feature_record_data.get('confidence_score', analysis_data.get('confidence', 0.0))
        
        # Analysis-specific fields
        jurisdiction = analysis_data.get('jurisdiction', geo_country or 'UNKNOWN')
        law = analysis_data.get('law', analysis_data.get('applicable_law', 'GENERAL'))
        trigger = analysis_data.get('trigger', analysis_data.get('risk_trigger', 'analysis'))
        analysis_confidence = analysis_data.get('confidence', confidence_score or 0.0)
        
        # Handle citations and LLM output
        citations = analysis_data.get('citations', implicated_regulations)
        if isinstance(citations, list):
            citations_json = json.dumps(citations)
        else:
            citations_json = json.dumps([str(citations)] if citations else [])
        
        llm_output = analysis_data.get('llm_output', analysis_data.get('reasoning', {}))
        if isinstance(llm_output, str):
            llm_output = {'reasoning': llm_output}
        llm_output_json = json.dumps(llm_output)
        
        # Create decision record with canonical FeatureRecord schema
        decision = Decision(
            # Canonical FeatureRecord fields
            feature_id=feature_id,
            doc_id=doc_id,
            source_path=source_path,
            date=date,
            feature_title=feature_title,
            feature_description=feature_description,
            objectives=objectives,
            user_segments=user_segments,
            geo_country=geo_country,
            geo_state=geo_state,
            domain=domain,
            label=label,
            implicated_regulations=json.dumps(implicated_regulations),
            data_practices=json.dumps(data_practices),
            rationale=rationale,
            risk_tags=json.dumps(risk_tags),
            confidence_score=confidence_score,
            codename_hits_json=json.dumps(codename_hits),
            
            # Analysis-specific fields
            jurisdiction=jurisdiction,
            law=law,
            trigger=trigger,
            require_compliance=require_compliance,
            analysis_confidence=float(analysis_confidence),
            citations=citations_json,
            llm_output=llm_output_json
        )
        
        db.add(decision)
        db.commit()
        db.refresh(decision)
        
        decision_id = decision.id
        db.close()
        
        print(f"Decision saved with ID: {decision_id} (FeatureRecord format)")
        return decision_id
        
    except Exception as e:
        print(f"Error saving decision: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return None

def update_decision(decision_id: int, updates: Dict[str, Any], reviewer_name: str = "Human", reviewer_notes: str = "") -> bool:
    """
    Update an existing decision record with human override using canonical FeatureRecord format
    
    Args:
        decision_id: ID of the decision to update
        updates: Dictionary containing fields to update (can include canonical FeatureRecord fields)
        reviewer_name: Name of the reviewer making the override
        reviewer_notes: Optional notes from the reviewer
        
    Returns:
        True if successful, False otherwise
    """
    try:
        db = get_db()
        decision = db.query(Decision).filter(Decision.id == decision_id).first()
        
        if not decision:
            db.close()
            return False
        
        # Update canonical FeatureRecord fields if provided
        canonical_fields = [
            'feature_id', 'doc_id', 'source_path', 'date', 'feature_title', 
            'feature_description', 'objectives', 'user_segments', 'geo_country', 
            'geo_state', 'domain', 'label', 'rationale', 'confidence_score'
        ]
        
        for field in canonical_fields:
            if field in updates:
                setattr(decision, field, updates[field])
        
        # Handle canonical array fields (convert to JSON)
        array_fields = ['implicated_regulations', 'data_practices', 'risk_tags', 'codename_hits_json']
        for field in array_fields:
            if field in updates:
                value = updates[field]
                if isinstance(value, list):
                    setattr(decision, field, json.dumps(value))
                else:
                    setattr(decision, field, json.dumps([value] if value else []))
        
        # Handle analysis-specific fields
        if 'jurisdiction' in updates:
            decision.jurisdiction = updates['jurisdiction']
        
        if 'law' in updates:
            decision.law = updates['law']
            
        if 'trigger' in updates:
            decision.trigger = updates['trigger']
        
        # Handle compliance updates
        if 'verdict' in updates or 'require_compliance' in updates:
            verdict = updates.get('verdict', updates.get('require_compliance'))
            if verdict == 'COMPLIANT':
                decision.require_compliance = 'NO'
                if 'label' not in updates:
                    decision.label = 'compliant'
            elif verdict == 'NON_COMPLIANT':
                decision.require_compliance = 'YES'
                if 'label' not in updates:
                    decision.label = 'non-compliant'
            else:
                decision.require_compliance = 'ABSTAIN'
                if 'label' not in updates:
                    decision.label = 'partially-compliant'
        
        # Handle confidence updates
        if 'confidence' in updates:
            decision.analysis_confidence = float(updates['confidence'])
            if 'confidence_score' not in updates:
                decision.confidence_score = float(updates['confidence'])
        
        # Handle citations
        if 'citations' in updates:
            citations = updates['citations']
            if isinstance(citations, list):
                decision.citations = json.dumps(citations)
                # Also update canonical implicated_regulations if not explicitly set
                if 'implicated_regulations' not in updates:
                    decision.implicated_regulations = json.dumps(citations)
            else:
                citations_json = json.dumps([str(citations)] if citations else [])
                decision.citations = citations_json
                if 'implicated_regulations' not in updates:
                    decision.implicated_regulations = citations_json
        
        # Handle LLM output
        if 'llm_output' in updates or 'reasoning' in updates:
            llm_output = updates.get('llm_output', updates.get('reasoning', {}))
            if isinstance(llm_output, str):
                llm_output = {'reasoning': llm_output}
            decision.llm_output = json.dumps(llm_output)
            
            # Also update canonical rationale if not explicitly set
            if 'rationale' not in updates:
                if isinstance(llm_output, dict) and 'reasoning' in llm_output:
                    decision.rationale = llm_output['reasoning']
                elif isinstance(llm_output, str):
                    decision.rationale = llm_output
        
        # Set human override tracking
        decision.human_override = True
        decision.human_reviewer = reviewer_name
        decision.reviewer_notes = reviewer_notes
        decision.last_updated = datetime.now()
        
        db.commit()
        db.close()
        
        print(f"Decision {decision_id} updated with human override (FeatureRecord format)")
        return True
        
    except Exception as e:
        print(f"Error updating decision: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False

def update_with_human_override(
    decision_id: int, 
    override: str, 
    notes: str, 
    reviewer_id: str = "human_reviewer"
) -> bool:
    """
    Update decision with human override and reviewer notes
    
    Args:
        decision_id: ID of the decision to update
        override: Human override decision (YES | NO | ABSTAIN)
        notes: Reviewer notes
        reviewer_id: ID of the reviewer
        
    Returns:
        True if successful, False otherwise
    """
    try:
        db = get_db()
        
        decision = db.query(Decision).filter(Decision.id == decision_id).first()
        
        if not decision:
            print(f"Decision with ID {decision_id} not found")
            db.close()
            return False
        
        # Update fields
        decision.human_override = override
        decision.reviewer_notes = f"[{reviewer_id}] {notes}" if notes else f"[{reviewer_id}] Override: {override}"
        decision.updated_at = datetime.now()
        
        db.commit()
        db.close()
        
        print(f"Decision {decision_id} updated with human override: {override}")
        return True
        
    except Exception as e:
        print(f"Error updating decision: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False

def list_recent_decisions(limit: int = 50, jurisdiction: str = None, law: str = None) -> List[Dict[str, Any]]:
    """
    Get recent decisions with optional filtering
    
    Args:
        limit: Maximum number of decisions to return
        jurisdiction: Filter by jurisdiction (optional)
        law: Filter by law (optional)
        
    Returns:
        List of decision dictionaries
    """
    try:
        db = get_db()
        
        query = db.query(Decision).order_by(Decision.created_at.desc())
        
        # Apply filters
        if jurisdiction and jurisdiction != 'ALL':
            query = query.filter(Decision.jurisdiction == jurisdiction)
        
        if law and law != 'ALL':
            query = query.filter(Decision.law == law)
        
        decisions = query.limit(limit).all()
        
        result = [decision.to_dict() for decision in decisions]
        db.close()
        
        return result
        
    except Exception as e:
        print(f"Error fetching decisions: {e}")
        if 'db' in locals():
            db.close()
        return []

def get_decision_by_id(decision_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a specific decision by ID
    
    Args:
        decision_id: ID of the decision
        
    Returns:
        Decision dictionary or None if not found
    """
    try:
        db = get_db()
        
        decision = db.query(Decision).filter(Decision.id == decision_id).first()
        
        if decision:
            result = decision.to_dict()
            db.close()
            return result
        else:
            db.close()
            return None
            
    except Exception as e:
        print(f"Error fetching decision: {e}")
        if 'db' in locals():
            db.close()
        return None

def get_decision_stats() -> Dict[str, Any]:
    """
    Get summary statistics about decisions
    
    Returns:
        Dictionary with statistics
    """
    try:
        db = get_db()
        
        total_decisions = db.query(Decision).count()
        
        # Count by compliance requirement
        compliant_count = db.query(Decision).filter(Decision.require_compliance == 'NO').count()
        non_compliant_count = db.query(Decision).filter(Decision.require_compliance == 'YES').count()
        abstain_count = db.query(Decision).filter(Decision.require_compliance == 'ABSTAIN').count()
        
        # Count human overrides
        override_count = db.query(Decision).filter(Decision.human_override.isnot(None)).count()
        
        # Count by jurisdiction
        jurisdiction_stats = db.query(
            Decision.jurisdiction, 
            func.count(Decision.id).label('count')
        ).group_by(Decision.jurisdiction).all()
        
        # Recent activity (last 7 days)
        from datetime import timedelta
        week_ago = datetime.now() - timedelta(days=7)
        recent_count = db.query(Decision).filter(Decision.created_at >= week_ago).count()
        
        db.close()
        
        return {
            'total_decisions': total_decisions,
            'compliant': compliant_count,
            'non_compliant': non_compliant_count,
            'abstain': abstain_count,
            'human_overrides': override_count,
            'recent_activity': recent_count,
            'jurisdiction_breakdown': {jur: count for jur, count in jurisdiction_stats}
        }
        
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return {
            'total_decisions': 0,
            'compliant': 0,
            'non_compliant': 0,
            'abstain': 0,
            'human_overrides': 0,
            'recent_activity': 0,
            'jurisdiction_breakdown': {}
        }

def search_decisions(
    query: str, 
    limit: int = 20, 
    jurisdiction: str = None,
    law: str = None
) -> List[Dict[str, Any]]:
    """
    Search decisions by text in canonical FeatureRecord fields and analysis fields
    
    Args:
        query: Search query
        limit: Maximum results
        jurisdiction: Filter by jurisdiction
        law: Filter by law
        
    Returns:
        List of matching decisions
    """
    try:
        db = get_db()
        
        # Build comprehensive search query across canonical FeatureRecord fields
        search_query = db.query(Decision).filter(
            (Decision.feature_title.contains(query)) |
            (Decision.feature_description.contains(query)) |
            (Decision.rationale.contains(query)) |
            (Decision.objectives.contains(query)) |
            (Decision.user_segments.contains(query)) |
            (Decision.domain.contains(query)) |
            (Decision.reviewer_notes.contains(query)) |
            (Decision.trigger.contains(query)) |
            (Decision.implicated_regulations.contains(query)) |
            (Decision.data_practices.contains(query)) |
            (Decision.risk_tags.contains(query))
        ).order_by(Decision.created_at.desc())
        
        # Apply filters
        if jurisdiction and jurisdiction != 'ALL':
            search_query = search_query.filter(Decision.jurisdiction == jurisdiction)
        
        if law and law != 'ALL':
            search_query = search_query.filter(Decision.law == law)
        
        decisions = search_query.limit(limit).all()
        
        result = [decision.to_dict() for decision in decisions]
        db.close()
        
        return result
        
    except Exception as e:
        print(f"Error searching decisions: {e}")
        if 'db' in locals():
            db.close()
        return []

def export_decisions_to_json(filename: str = None) -> str:
    """
    Export all decisions to JSON file
    
    Args:
        filename: Optional filename, defaults to timestamped file
        
    Returns:
        Path to exported file
    """
    try:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"compliance_decisions_export_{timestamp}.json"
        
        decisions = list_recent_decisions(limit=10000)  # Get all decisions
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_decisions': len(decisions),
            'decisions': decisions
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"Exported {len(decisions)} decisions to {filename}")
        return filename
        
    except Exception as e:
        print(f"Error exporting decisions: {e}")
        return ""

# Initialize database on import
if __name__ == "__main__":
    init_database()
    print("Database module initialized")
else:
    # Auto-initialize when imported
    init_database()
