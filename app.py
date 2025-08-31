#!/usr/bin/env python3
"""
Comprehensive Compliance Verification System - Streamlit UI
Integrates dashboard, human-in-loop controls, tool explorer, and agent-specific requests
"""

import streamlit as st
import json
import requests
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import time
import os

# Import database functions
from db import (
    init_database, save_decision, update_with_human_override, 
    list_recent_decisions, get_decision_stats, search_decisions,
    export_decisions_to_json, get_decision_by_id
)

# Page configuration
st.set_page_config(
    page_title="Compliance Verification System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
try:
    init_database()
except Exception as e:
    st.error(f"Database initialization failed: {e}")

# Project root
PROJECT_ROOT = Path(__file__).parent.absolute()

# Initialize session state
if 'review_history' not in st.session_state:
    st.session_state.review_history = []
if 'current_analysis' not in st.session_state:
    st.session_state.current_analysis = None
if 'tool_responses' not in st.session_state:
    st.session_state.tool_responses = {}
if 'agent_responses' not in st.session_state:
    st.session_state.agent_responses = {}

# ================================
# HELPER FUNCTIONS
# ================================

def call_mcp_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper function to call MCP tools and automatically save decisions to database
    In production, this would send REST requests to the MCP server
    For now, we'll call the tools directly
    """
    try:
        tool_path = PROJECT_ROOT / f"mcp-tools/{tool_name}.py"
        
        if not tool_path.exists():
            return {
                'success': False,
                'error': f"Tool {tool_name} not found",
                'mock_data': True
            }
        
        # Call the tool directly
        result = subprocess.run(
            [sys.executable, str(tool_path)],
            input=json.dumps(params),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            try:
                response = json.loads(result.stdout)
                
                # Auto-save compliance decisions to database
                if tool_name in ['check_compliance', 'enhanced_compliance_analysis'] and response.get('success'):
                    save_compliance_decision_to_db(tool_name, params, response)
                
                return response
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'raw_output': result.stdout,
                    'note': 'Tool output was not JSON formatted'
                }
        else:
            # Return mock data for demo resilience
            mock_response = get_mock_response(tool_name, params)
            
            # Auto-save mock decisions too for demo purposes
            if tool_name in ['check_compliance', 'enhanced_compliance_analysis'] and mock_response.get('success'):
                save_compliance_decision_to_db(tool_name, params, mock_response)
            
            return mock_response
            
    except Exception as e:
        mock_response = get_mock_response(tool_name, params, error=str(e))
        
        # Auto-save mock decisions for demo purposes
        if tool_name in ['check_compliance', 'enhanced_compliance_analysis'] and mock_response.get('success'):
            save_compliance_decision_to_db(tool_name, params, mock_response)
        
        return mock_response

def save_compliance_decision_to_db(tool_name: str, params: Dict[str, Any], response: Dict[str, Any]):
    """Save compliance decision to database using canonical FeatureRecord format"""
    try:
        # Extract feature information
        feature_data = params.get('feature_data', {})
        feature_text = params.get('feature_text', feature_data.get('description', feature_data.get('name', '')))
        jurisdiction = params.get('jurisdiction', 'UNKNOWN')
        
        # Extract decision information from response
        if tool_name == 'enhanced_compliance_analysis':
            # Enhanced analysis has nested structure
            compliance_analysis = response.get('compliance_analysis', response)
            verdict = compliance_analysis.get('verdict', 'ABSTAIN')
            confidence = compliance_analysis.get('confidence', 0.0)
            reasoning = compliance_analysis.get('reasoning', '')
            citations = compliance_analysis.get('citations', [])
            
            # Try to get law from evidence verification
            evidence_verification = response.get('evidence_verification', {})
            regulatory_refs = evidence_verification.get('regulatory_references', [])
            law = regulatory_refs[0].get('regulation', 'GENERAL') if regulatory_refs else 'GENERAL'
            
        else:
            # Basic compliance check
            verdict = response.get('verdict', 'ABSTAIN')
            confidence = response.get('confidence', 0.0)
            reasoning = response.get('reasoning', '')
            citations = response.get('citations', [])
            law = response.get('applicable_law', 'GENERAL')
        
        # Create canonical FeatureRecord format decision
        canonical_decision = {
            # Canonical FeatureRecord fields
            'feature_id': feature_data.get('feature_id', f"feature_{int(datetime.now().timestamp())}"),
            'doc_id': feature_data.get('doc_id', f"mcp_{tool_name}"),
            'source_path': feature_data.get('source_path', f"mcp_tools/{tool_name}"),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'feature_title': feature_data.get('name', f"Feature from {tool_name}"),
            'feature_description': feature_text,
            'objectives': feature_data.get('objectives'),
            'user_segments': feature_data.get('user_segments'),
            'geo_country': jurisdiction.split('_')[0] if '_' in jurisdiction else jurisdiction,
            'geo_state': jurisdiction.split('_')[1] if '_' in jurisdiction else None,
            'domain': feature_data.get('domain', 'compliance_analysis'),
            'label': 'compliant' if verdict == 'COMPLIANT' else 'non-compliant' if verdict == 'NON_COMPLIANT' else 'partially-compliant',
            'implicated_regulations': citations,
            'data_practices': feature_data.get('data_practices', []),
            'rationale': reasoning,
            'risk_tags': feature_data.get('risk_tags', []),
            'confidence_score': float(confidence),
            'codename_hits_json': feature_data.get('codename_hits', []),
            
            # Analysis-specific fields for compatibility
            'jurisdiction': jurisdiction,
            'law': law,
            'trigger': f"{tool_name}_analysis",
            'verdict': verdict,
            'confidence': confidence,
            'citations': citations,
            'reasoning': reasoning,
            'llm_output': {
                'tool_used': tool_name,
                'reasoning': reasoning,
                'full_response': response,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Save to database
        decision_id = save_decision(canonical_decision)
        if decision_id:
            # Store decision ID in session state for potential human override
            if 'recent_decision_ids' not in st.session_state:
                st.session_state.recent_decision_ids = []
            st.session_state.recent_decision_ids.append(decision_id)
            
            # Keep only last 10 decision IDs
            st.session_state.recent_decision_ids = st.session_state.recent_decision_ids[-10:]
            
    except Exception as e:
        st.warning(f"Could not save decision to database: {e}")

def get_mock_response(tool_name: str, params: Dict[str, Any], error: str = None) -> Dict[str, Any]:
    """
    Provide mock responses for demo resilience
    """
    mock_responses = {
        'enhanced_compliance_analysis': {
            'success': True,
            'mock_data': True,
            'error': error,
            'analysis_type': 'comprehensive_agentic',
            'compliance_analysis': {
                'verdict': 'NON_COMPLIANT',
                'confidence': 0.75,
                'reasoning': 'Mock analysis: Feature requires explicit consent under GDPR'
            },
            'confidence_validation': {
                'final_confidence': 0.75,
                'ensemble_agreement': 0.8
            },
            'evidence_verification': {
                'evidence_quality_score': 0.85,
                'citations': ['GDPR Article 6', 'GDPR Article 7']
            },
            'final_recommendation': {
                'final_verdict': 'NON_COMPLIANT',
                'final_confidence': 0.75
            }
        },
        'evidence_backed_retrieval': {
            'success': True,
            'mock_data': True,
            'error': error,
            'documents_found': 3,
            'regulatory_references': [
                {'regulation': 'GDPR Article 6', 'relevance': 0.95},
                {'regulation': 'GDPR Article 7', 'relevance': 0.88}
            ],
            'evidence_quality_score': 0.85
        },
        'check_compliance': {
            'success': True,
            'mock_data': True,
            'error': error,
            'verdict': 'NON_COMPLIANT',
            'confidence': 0.72,
            'reasoning': 'Mock compliance check: Data processing requires explicit consent'
        },
        'retrieve_docs': {
            'success': True,
            'mock_data': True,
            'error': error,
            'documents': [
                {'content': 'GDPR requires explicit consent...', 'score': 0.95},
                {'content': 'Data protection regulations...', 'score': 0.88}
            ],
            'total_found': 2
        }
    }
    
    return mock_responses.get(tool_name, {
        'success': False,
        'mock_data': True,
        'error': error or f'No mock data available for {tool_name}'
    })

def load_review_history() -> List[Dict]:
    """Load review history from human-reviews directory"""
    reviews = []
    reviews_dir = PROJECT_ROOT / "human-reviews"
    
    if reviews_dir.exists():
        for review_file in reviews_dir.glob("*.json"):
            try:
                with open(review_file, 'r') as f:
                    review_data = json.load(f)
                    reviews.append(review_data)
            except Exception as e:
                st.warning(f"Could not load review {review_file.name}: {e}")
    
    return sorted(reviews, key=lambda x: x.get('timestamp', ''), reverse=True)

def save_human_decision(review_id: str, decision: Dict[str, Any]):
    """Save human decision to review file"""
    reviews_dir = PROJECT_ROOT / "human-reviews"
    review_file = reviews_dir / f"{review_id}.json"
    
    if review_file.exists():
        try:
            with open(review_file, 'r') as f:
                review_data = json.load(f)
            
            review_data['human_decision'] = decision
            review_data['reviewed_at'] = datetime.now().isoformat()
            review_data['status'] = 'completed'
            
            with open(review_file, 'w') as f:
                json.dump(review_data, f, indent=2)
                
            st.success(f"Decision saved for review {review_id}")
            
        except Exception as e:
            st.error(f"Failed to save decision: {e}")

def get_verdict_color(verdict: str) -> str:
    """Get color for verdict display"""
    colors = {
        'COMPLIANT': 'green',
        'NON_COMPLIANT': 'red', 
        'ABSTAIN': 'orange',
        'YES': 'red',
        'NO': 'green',
        'UNKNOWN': 'gray'
    }
    return colors.get(verdict, 'gray')

def render_verdict_badge(verdict: str, confidence: float = None):
    """Render a colored verdict badge"""
    color = get_verdict_color(verdict)
    confidence_text = f" ({confidence:.2f})" if confidence is not None else ""
    
    st.markdown(
        f"""
        <span style="
            background-color: {color}; 
            color: white; 
            padding: 4px 8px; 
            border-radius: 4px; 
            font-weight: bold;
            font-size: 12px;
        ">
            {verdict}{confidence_text}
        </span>
        """,
        unsafe_allow_html=True
    )

def get_available_tools() -> List[Dict[str, Any]]:
    """Get list of available MCP tools with mock manifest"""
    tools_dir = PROJECT_ROOT / "mcp-tools"
    tools = []
    
    # Mock tool schemas for the tool explorer
    tool_schemas = {
        'enhanced_compliance_analysis': {
            'name': 'Enhanced Compliance Analysis',
            'description': 'Comprehensive compliance analysis with agentic integration',
            'parameters': {
                'feature_data': {'type': 'object', 'description': 'Feature data in FeatureRecord format'},
                'jurisdiction': {'type': 'string', 'description': 'Jurisdiction code (e.g., US, EU)', 'default': 'US'}
            }
        },
        'evidence_backed_retrieval': {
            'name': 'Evidence-Backed Retrieval',
            'description': 'Retrieve documents with evidence verification',
            'parameters': {
                'feature_data': {'type': 'object', 'description': 'Feature data to analyze'},
                'jurisdiction': {'type': 'string', 'description': 'Jurisdiction code', 'default': 'US'},
                'max_results': {'type': 'integer', 'description': 'Maximum results', 'default': 10}
            }
        },
        'check_compliance': {
            'name': 'Check Compliance',
            'description': 'Basic compliance check',
            'parameters': {
                'feature_text': {'type': 'string', 'description': 'Feature description text'},
                'jurisdiction': {'type': 'string', 'description': 'Jurisdiction code', 'default': 'US'}
            }
        },
        'retrieve_docs': {
            'name': 'Retrieve Documents',
            'description': 'Retrieve relevant documents',
            'parameters': {
                'query': {'type': 'string', 'description': 'Search query'},
                'top_k': {'type': 'integer', 'description': 'Number of results', 'default': 5}
            }
        },
        'call_llm': {
            'name': 'Call LLM',
            'description': 'Call language model directly',
            'parameters': {
                'prompt': {'type': 'string', 'description': 'Prompt for the LLM'},
                'model': {'type': 'string', 'description': 'Model name', 'default': 'gpt-4o-mini'}
            }
        },
        'system_status': {
            'name': 'System Status',
            'description': 'Get system status and health',
            'parameters': {}
        },
        'active_learning_feedback': {
            'name': 'Active Learning Feedback',
            'description': 'Process human feedback for learning',
            'parameters': {
                'action': {'type': 'string', 'description': 'Action to perform', 'default': 'process_correction'},
                'original_analysis': {'type': 'object', 'description': 'Original AI analysis'},
                'human_decision': {'type': 'object', 'description': 'Human reviewer decision'},
                'feature_data': {'type': 'object', 'description': 'Feature data'}
            }
        }
    }
    
    for tool_file in tools_dir.glob("*.py"):
        tool_name = tool_file.stem
        if tool_name in tool_schemas:
            tools.append({
                'name': tool_name,
                'display_name': tool_schemas[tool_name]['name'],
                'description': tool_schemas[tool_name]['description'],
                'parameters': tool_schemas[tool_name]['parameters']
            })
    
    return tools

# ================================
# UI SECTIONS
# ================================

def dashboard_section():
    """Dashboard section showing pipeline outputs and database history"""
    st.header("🛡️ Compliance Dashboard")
    
    # Database Statistics
    st.subheader("📊 System Statistics")
    
    try:
        stats = get_decision_stats()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Decisions", stats['total_decisions'])
        with col2:
            st.metric("Compliant (NO)", stats['compliant'])
        with col3:
            st.metric("Non-Compliant (YES)", stats['non_compliant'])
        with col4:
            st.metric("Abstain", stats['abstain'])
        with col5:
            st.metric("Human Overrides", stats['human_overrides'])
        
        # Jurisdiction breakdown
        if stats['jurisdiction_breakdown']:
            st.write("**Decisions by Jurisdiction:**")
            jur_df = pd.DataFrame([
                {'Jurisdiction': jur, 'Count': count} 
                for jur, count in stats['jurisdiction_breakdown'].items()
            ])
            st.bar_chart(jur_df.set_index('Jurisdiction'))
    
    except Exception as e:
        st.error(f"Could not load statistics: {e}")
    
    # Current Analysis Section
    st.subheader("Current Analysis")
    
    if st.session_state.current_analysis:
        analysis = st.session_state.current_analysis
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Verdict", analysis.get('verdict', 'UNKNOWN'))
            render_verdict_badge(analysis.get('verdict', 'UNKNOWN'))
        
        with col2:
            confidence = analysis.get('confidence', 0.0)
            st.metric("Confidence", f"{confidence:.2f}")
            
        with col3:
            risk_level = analysis.get('risk_level', 'UNKNOWN')
            st.metric("Risk Level", risk_level)
        
        # Detailed Analysis
        with st.expander("📋 Detailed Analysis", expanded=True):
            st.text_area(
                "Reasoning",
                analysis.get('reasoning', 'No reasoning provided'),
                height=100,
                disabled=True
            )
            
            citations = analysis.get('citations', [])
            if citations:
                st.write("**Citations:**")
                for citation in citations:
                    st.write(f"• {citation}")
            
            recommendations = analysis.get('recommendations', [])
            if recommendations:
                st.write("**Recommendations:**")
                for rec in recommendations:
                    st.write(f"• {rec}")
    
    else:
        st.info("No current analysis. Use the Tool Explorer or Agent sections to run analysis.")
    
    # Recent Decisions from Database
    st.subheader("� Recent Decisions")
    
    try:
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            jurisdiction_filter = st.selectbox(
                "Filter by Jurisdiction:",
                ["ALL", "US", "EU", "CA", "UK", "AU"]
            )
        
        with col2:
            law_filter = st.selectbox(
                "Filter by Law:",
                ["ALL", "GDPR", "CCPA", "PIPEDA", "GENERAL"]
            )
        
        with col3:
            limit = st.number_input("Number of Records:", 10, 100, 25)
        
        # Get decisions from database
        decisions = list_recent_decisions(
            limit=limit,
            jurisdiction=jurisdiction_filter if jurisdiction_filter != "ALL" else None,
            law=law_filter if law_filter != "ALL" else None
        )
        
        if decisions:
            # Convert to DataFrame for better display
            display_data = []
            for decision in decisions:
                # Use canonical field names with fallback for backward compatibility
                feature_display = decision.get('feature_title', decision.get('feature_description', decision.get('feature_text', 'Unknown Feature')))
                if len(feature_display) > 50:
                    feature_display = feature_display[:50] + "..."
                
                confidence_score = decision.get('confidence_score', decision.get('analysis_confidence', decision.get('confidence', 0.0)))
                
                display_data.append({
                    'ID': decision['id'],
                    'Feature': feature_display,
                    'Jurisdiction': decision['jurisdiction'],
                    'Law': decision['law'],
                    'AI Decision': decision['require_compliance'],
                    'Confidence': f"{float(confidence_score):.2f}",
                    'Human Override': decision['human_override'] or 'None',
                    'Created': decision['created_at'][:16] if decision['created_at'] else 'Unknown'
                })
            
            df = pd.DataFrame(display_data)
            
            # Style the dataframe
            def style_compliance(val):
                if val == 'YES':
                    return 'background-color: #ffcccc'  # Light red
                elif val == 'NO':
                    return 'background-color: #ccffcc'  # Light green
                elif val == 'ABSTAIN':
                    return 'background-color: #fff2cc'  # Light yellow
                return ''
            
            styled_df = df.style.applymap(style_compliance, subset=['AI Decision', 'Human Override'])
            st.dataframe(styled_df, use_container_width=True)
            
            # Decision details expander
            with st.expander("View Decision Details"):
                selected_id = st.selectbox(
                    "Select Decision ID to view details:",
                    [decision['id'] for decision in decisions]
                )
                
                if selected_id:
                    selected_decision = next(d for d in decisions if d['id'] == selected_id)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Decision Information:**")
                        st.json({
                            'id': selected_decision['id'],
                            'feature_id': selected_decision['feature_id'],
                            'jurisdiction': selected_decision['jurisdiction'],
                            'law': selected_decision['law'],
                            'require_compliance': selected_decision['require_compliance'],
                            'confidence': selected_decision['confidence'],
                            'created_at': selected_decision['created_at']
                        })
                    
                    with col2:
                        st.write("**Feature Details:**")
                        feature_text = selected_decision.get('feature_description', selected_decision.get('feature_text', 'No description available'))
                        st.text_area(
                            "Feature Description:",
                            feature_text,
                            height=100,
                            disabled=True
                        )
                        
                        if selected_decision['reviewer_notes']:
                            st.write("**Reviewer Notes:**")
                            st.text_area(
                                "Notes:",
                                selected_decision['reviewer_notes'],
                                height=80,
                                disabled=True
                            )
                    
                    st.write("**Citations:**")
                    st.json(selected_decision['citations'])
                    
                    st.write("**LLM Output:**")
                    st.json(selected_decision['llm_output'])
        
        else:
            st.info("No decisions found in database. Run some analyses to populate the database.")
    
    except Exception as e:
        st.error(f"Could not load decisions from database: {e}")
    
    # Export functionality
    st.subheader("📤 Export Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export to JSON"):
            try:
                filename = export_decisions_to_json()
                if filename:
                    st.success(f"Data exported to {filename}")
                    
                    # Provide download link
                    with open(filename, 'r') as f:
                        st.download_button(
                            label="⬇️ Download JSON Export",
                            data=f.read(),
                            file_name=filename,
                            mime="application/json"
                        )
                else:
                    st.error("Export failed")
            except Exception as e:
                st.error(f"Export error: {e}")
    
    with col2:
        if st.button("📊 Export to CSV"):
            try:
                # Import the CSV export function
                import subprocess
                result = subprocess.run([
                    sys.executable, "export_csv.py"
                ], capture_output=True, text=True, cwd=PROJECT_ROOT)
                
                if result.returncode == 0:
                    # Find the generated CSV files
                    import glob
                    csv_files = glob.glob("compliance_decisions_export_*.csv")
                    summary_files = glob.glob("compliance_summary_*.csv")
                    
                    if csv_files:
                        latest_csv = max(csv_files, key=os.path.getctime)
                        st.success(f"CSV exported: {latest_csv}")
                        
                        # Provide download link for full export
                        with open(latest_csv, 'r', encoding='utf-8') as f:
                            st.download_button(
                                label="⬇️ Download Full CSV Export",
                                data=f.read(),
                                file_name=latest_csv,
                                mime="text/csv"
                            )
                    
                    if summary_files:
                        latest_summary = max(summary_files, key=os.path.getctime)
                        st.success(f"Summary CSV: {latest_summary}")
                        
                        # Provide download link for summary
                        with open(latest_summary, 'r', encoding='utf-8') as f:
                            st.download_button(
                                label="⬇️ Download Summary CSV",
                                data=f.read(),
                                file_name=latest_summary,
                                mime="text/csv"
                            )
                else:
                    st.error(f"CSV export failed: {result.stderr}")
            except Exception as e:
                st.error(f"CSV export error: {e}")
    
    with col3:
        # Search functionality
        st.write("**Search Decisions:**")
        search_query = st.text_input("Search in feature text or notes:")
        
        if search_query and st.button("🔍 Search"):
            try:
                search_results = search_decisions(search_query, limit=20)
                
                if search_results:
                    st.write(f"Found {len(search_results)} results:")
                    
                    search_df = pd.DataFrame([
                        {
                            'ID': r['id'],
                            'Feature': (r.get('feature_title', r.get('feature_description', r.get('feature_text', 'Unknown')))[:50] + "..."),
                            'Decision': r['require_compliance'],
                            'Created': r['created_at'][:16]
                        }
                        for r in search_results
                    ])
                    
                    st.dataframe(search_df, use_container_width=True)
                else:
                    st.info("No results found")
                    
            except Exception as e:
                st.error(f"Search error: {e}")

def human_in_loop_section():
    """Human-in-loop controls for decision making with database integration"""
    st.header("👤 Human Review Controls")
    
    # Recent Decisions Requiring Review
    st.subheader("Recent AI Decisions")
    
    try:
        # Get recent decisions that don't have human overrides
        recent_decisions = list_recent_decisions(limit=20)
        pending_decisions = [d for d in recent_decisions if not d['human_override']]
        
        if pending_decisions:
            # Decision Selection
            decision_options = {}
            for d in pending_decisions[:10]:  # Show top 10
                feature_display = d.get('feature_title', d.get('feature_description', d.get('feature_text', 'Unknown Feature')))
                if len(feature_display) > 50:
                    feature_display = feature_display[:50] + "..."
                decision_options[f"ID {d['id']} - {feature_display}"] = d
            
            selected_decision_key = st.selectbox(
                "Select Decision to Review:",
                list(decision_options.keys())
            )
            
            if selected_decision_key:
                selected_decision = decision_options[selected_decision_key]
                
                # Display Decision Details
                st.subheader("Decision Details")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**AI Analysis:**")
                    
                    # Display key metrics
                    col1a, col1b, col1c = st.columns(3)
                    with col1a:
                        render_verdict_badge(selected_decision['require_compliance'])
                    with col1b:
                        confidence_score = selected_decision.get('confidence_score', selected_decision.get('analysis_confidence', selected_decision.get('confidence', 0.0)))
                        st.metric("Confidence", f"{float(confidence_score):.2f}")
                    with col1c:
                        st.metric("Jurisdiction", selected_decision['jurisdiction'])
                    
                    feature_text = selected_decision.get('feature_description', selected_decision.get('feature_text', 'No description available'))
                    st.text_area(
                        "Feature Description:",
                        feature_text,
                        height=100,
                        disabled=True
                    )
                    
                    st.write(f"**Law:** {selected_decision['law']}")
                    st.write(f"**Trigger:** {selected_decision['trigger']}")
                    
                with col2:
                    st.write("**Citations & Evidence:**")
                    citations = selected_decision['citations']
                    if citations:
                        for citation in citations:
                            st.write(f"• {citation}")
                    else:
                        st.write("No citations available")
                    
                    st.write("**LLM Reasoning:**")
                    llm_output = selected_decision['llm_output']
                    reasoning = llm_output.get('reasoning', 'No reasoning provided') if isinstance(llm_output, dict) else str(llm_output)
                    st.text_area(
                        "AI Reasoning:",
                        reasoning,
                        height=150,
                        disabled=True
                    )
                
                # Human Decision Interface
                st.subheader("Human Review")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    human_override = st.selectbox(
                        "Your Decision:",
                        ["YES", "NO", "ABSTAIN"],
                        help="YES = Compliance Required, NO = Compliant, ABSTAIN = Uncertain"
                    )
                
                with col2:
                    reviewer_confidence = st.slider(
                        "Your Confidence:",
                        0.0, 1.0, 0.8, 0.05
                    )
                
                with col3:
                    reviewer_name = st.text_input(
                        "Reviewer ID:",
                        value="human_reviewer"
                    )
                
                # Comments
                reviewer_notes = st.text_area(
                    "Reviewer Notes:",
                    placeholder="Explain your decision, cite specific regulations, or note concerns..."
                )
                
                # Action Buttons
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("✅ Agree with AI", type="primary"):
                        notes = f"Confirmed AI decision. {reviewer_notes}" if reviewer_notes else "Confirmed AI decision."
                        
                        success = update_with_human_override(
                            selected_decision['id'],
                            selected_decision['require_compliance'],  # Keep AI decision
                            notes,
                            reviewer_name
                        )
                        
                        if success:
                            st.success("Decision confirmed!")
                            st.rerun()
                        else:
                            st.error("Failed to update decision")
                
                with col2:
                    if st.button("🔄 Override AI Decision"):
                        notes = f"Override: {human_override} (confidence: {reviewer_confidence:.2f}). {reviewer_notes}"
                        
                        success = update_with_human_override(
                            selected_decision['id'],
                            human_override,
                            notes,
                            reviewer_name
                        )
                        
                        if success:
                            st.success("Decision overridden!")
                            
                            # Process feedback for learning (if active learning is available)
                            try:
                                feedback_params = {
                                    'action': 'process_correction',
                                    'original_analysis': {
                                        'verdict': selected_decision['require_compliance'],
                                        'confidence': selected_decision['confidence']
                                    },
                                    'human_decision': {
                                        'verdict': human_override,
                                        'confidence': reviewer_confidence,
                                        'reasoning': reviewer_notes
                                    },
                                    'feature_data': {
                                        'description': selected_decision.get('feature_description', selected_decision.get('feature_text', 'No description')),
                                        'jurisdiction': selected_decision['jurisdiction']
                                    }
                                }
                                
                                feedback_result = call_mcp_tool('active_learning_feedback', feedback_params)
                                
                                if feedback_result.get('success'):
                                    st.info("Feedback processed for continuous learning!")
                                
                            except Exception as e:
                                st.warning(f"Could not process feedback for learning: {e}")
                            
                            st.rerun()
                        else:
                            st.error("Failed to update decision")
                
                with col3:
                    if st.button("⚠️ Escalate"):
                        escalation_notes = f"Escalated by {reviewer_name}. Reason: {reviewer_notes}"
                        
                        success = update_with_human_override(
                            selected_decision['id'],
                            "ESCALATED",
                            escalation_notes,
                            reviewer_name
                        )
                        
                        if success:
                            st.success("Decision escalated!")
                            st.rerun()
                        else:
                            st.error("Failed to escalate decision")
                
                with col4:
                    if st.button("� Re-analyze"):
                        # Re-run analysis with current feature data
                        with st.spinner("Re-running analysis..."):
                            analysis_params = {
                                'feature_text': selected_decision.get('feature_description', selected_decision.get('feature_text', 'No description')),
                                'jurisdiction': selected_decision['jurisdiction']
                            }
                            
                            new_analysis = call_mcp_tool('check_compliance', analysis_params)
                        
                        st.write("**Updated Analysis:**")
                        st.json(new_analysis)
        
        else:
            st.info("No pending decisions available for review.")
    
    except Exception as e:
        st.error(f"Could not load decisions for review: {e}")
    
    # Quick Analysis Section
    st.subheader("Quick Feature Analysis")
    
    with st.expander("Analyze New Feature", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            feature_name = st.text_input("Feature Name:")
            feature_description = st.text_area("Feature Description:")
            jurisdiction = st.selectbox("Jurisdiction:", ["US", "EU", "CA", "UK"])
        
        with col2:
            data_types = st.multiselect(
                "Data Types:",
                ["personal_data", "behavioral_data", "location_data", "biometric_data", "financial_data"]
            )
            
            third_party_sharing = st.checkbox("Third Party Sharing")
            user_consent = st.selectbox("User Consent:", ["explicit", "implied", "none"])
        
        if st.button("🔍 Analyze Feature", type="primary"):
            if feature_name and feature_description:
                feature_data = {
                    'name': feature_name,
                    'description': feature_description,
                    'data_types': data_types,
                    'third_party_sharing': third_party_sharing,
                    'user_consent': user_consent,
                    'feature_id': f"manual_{int(datetime.now().timestamp())}"
                }
                
                with st.spinner("Running compliance analysis..."):
                    # Use enhanced analysis for better results
                    analysis_result = call_mcp_tool('enhanced_compliance_analysis', {
                        'feature_data': feature_data,
                        'jurisdiction': jurisdiction
                    })
                
                if analysis_result.get('success'):
                    st.session_state.current_analysis = analysis_result.get('compliance_analysis', analysis_result)
                    st.success("Analysis completed! Check the Dashboard for results and this section for review options.")
                    
                    # Show quick results
                    if 'compliance_analysis' in analysis_result:
                        ca = analysis_result['compliance_analysis']
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            render_verdict_badge(ca.get('verdict', 'UNKNOWN'))
                        with col2:
                            st.metric("Confidence", f"{ca.get('confidence', 0):.2f}")
                        with col3:
                            risk = ca.get('risk_level', 'UNKNOWN')
                            st.metric("Risk Level", risk)
                    
                    # Note about database save
                    st.info("📄 Decision automatically saved to database for future review.")
                    
                else:
                    st.error("Analysis failed. Please check the inputs and try again.")
                    st.json(analysis_result)
            else:
                st.error("Please provide feature name and description.")
    
    # Human Override History
    st.subheader("👥 Human Override History")
    
    try:
        # Get decisions with human overrides
        all_decisions = list_recent_decisions(limit=100)
        override_decisions = [d for d in all_decisions if d['human_override']]
        
        if override_decisions:
            # Summary stats
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Overrides", len(override_decisions))
            
            with col2:
                # Calculate agreement rate
                agreements = len([d for d in override_decisions if d['human_override'] == d['require_compliance']])
                agreement_rate = agreements / len(override_decisions) if override_decisions else 0
                st.metric("Agreement Rate", f"{agreement_rate:.1%}")
            
            with col3:
                escalations = len([d for d in override_decisions if d['human_override'] == 'ESCALATED'])
                st.metric("Escalations", escalations)
            
            # Recent overrides table
            override_df = pd.DataFrame([
                {
                    'ID': d['id'],
                    'Feature': (d.get('feature_title', d.get('feature_description', d.get('feature_text', 'Unknown')))[:40] + "..."),
                    'AI Decision': d['require_compliance'],
                    'Human Override': d['human_override'],
                    'Jurisdiction': d['jurisdiction'],
                    'Updated': d['updated_at'][:16] if d['updated_at'] else 'Unknown'
                }
                for d in override_decisions[:20]
            ])
            
            st.dataframe(override_df, use_container_width=True)
        
        else:
            st.info("No human overrides recorded yet.")
    
    except Exception as e:
        st.error(f"Could not load override history: {e}")

def tool_explorer_section():
    """Tool explorer for all available MCP tools"""
    st.header("🔧 Tool Explorer")
    st.write("Explore and test all available MCP tools and repository tools.")
    
    # Get available tools
    tools = get_available_tools()
    
    if tools:
        # Tool Selection
        tool_names = [tool['display_name'] for tool in tools]
        selected_tool_name = st.selectbox("Select Tool:", tool_names)
        
        # Find selected tool
        selected_tool = next(tool for tool in tools if tool['display_name'] == selected_tool_name)
        
        st.write(f"**Description:** {selected_tool['description']}")
        
        # Dynamic Parameter Input
        params = {}
        
        with st.expander(f"Parameters for {selected_tool_name}", expanded=True):
            for param_name, param_info in selected_tool['parameters'].items():
                param_type = param_info.get('type', 'string')
                param_desc = param_info.get('description', '')
                param_default = param_info.get('default')
                
                st.write(f"**{param_name}** ({param_type}): {param_desc}")
                
                if param_type == 'string':
                    if param_name in ['feature_data', 'original_analysis', 'human_decision']:
                        # JSON input for complex objects
                        default_json = json.dumps(param_default or {}, indent=2)
                        params[param_name] = st.text_area(
                            f"{param_name}:",
                            value=default_json,
                            height=100,
                            key=f"param_{param_name}"
                        )
                        try:
                            params[param_name] = json.loads(params[param_name])
                        except:
                            pass
                    else:
                        params[param_name] = st.text_input(
                            f"{param_name}:",
                            value=str(param_default or ''),
                            key=f"param_{param_name}"
                        )
                
                elif param_type == 'integer':
                    params[param_name] = st.number_input(
                        f"{param_name}:",
                        value=param_default or 0,
                        key=f"param_{param_name}"
                    )
                
                elif param_type == 'object':
                    if param_name == 'feature_data':
                        # Provide a sample feature data structure
                        sample_feature = {
                            "name": "Sample Feature",
                            "description": "A sample feature for testing",
                            "data_types": ["personal_data"],
                            "user_consent": "explicit",
                            "third_party_sharing": False
                        }
                        params[param_name] = st.text_area(
                            f"{param_name} (JSON):",
                            value=json.dumps(sample_feature, indent=2),
                            height=150,
                            key=f"param_{param_name}"
                        )
                        try:
                            params[param_name] = json.loads(params[param_name])
                        except:
                            params[param_name] = sample_feature
                    else:
                        params[param_name] = st.text_area(
                            f"{param_name} (JSON):",
                            value='{}',
                            height=100,
                            key=f"param_{param_name}"
                        )
                        try:
                            params[param_name] = json.loads(params[param_name])
                        except:
                            params[param_name] = {}
        
        # Execute Tool
        col1, col2 = st.columns([1, 4])
        
        with col1:
            if st.button(f"🚀 Execute {selected_tool_name}", type="primary"):
                with st.spinner(f"Executing {selected_tool_name}..."):
                    result = call_mcp_tool(selected_tool['name'], params)
                
                st.session_state.tool_responses[selected_tool['name']] = {
                    'timestamp': datetime.now().isoformat(),
                    'params': params,
                    'result': result
                }
                
                st.success(f"{selected_tool_name} executed successfully!")
        
        with col2:
            if st.button("📋 Copy as Code"):
                code = f"""
# Execute {selected_tool_name}
params = {json.dumps(params, indent=2)}
result = call_mcp_tool('{selected_tool['name']}', params)
print(json.dumps(result, indent=2))
                """
                st.code(code, language='python')
        
        # Show Results
        if selected_tool['name'] in st.session_state.tool_responses:
            response_data = st.session_state.tool_responses[selected_tool['name']]
            
            st.subheader("📊 Response")
            
            # Success indicator
            result = response_data['result']
            if result.get('success', False):
                st.success("✅ Tool executed successfully")
            else:
                st.error("❌ Tool execution failed")
            
            if result.get('mock_data'):
                st.warning("⚠️ This is mock data (tool not fully available)")
            
            # Raw JSON Response
            with st.expander("Raw JSON Response", expanded=True):
                st.json(result)
            
            # Formatted Display
            if selected_tool['name'] == 'enhanced_compliance_analysis':
                if 'compliance_analysis' in result:
                    ca = result['compliance_analysis']
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        render_verdict_badge(ca.get('verdict', 'UNKNOWN'))
                    with col2:
                        st.metric("Confidence", f"{ca.get('confidence', 0):.2f}")
                    with col3:
                        st.metric("Risk Level", ca.get('risk_level', 'UNKNOWN'))
            
            elif selected_tool['name'] == 'retrieve_docs':
                if 'documents' in result:
                    st.write("**Retrieved Documents:**")
                    for i, doc in enumerate(result['documents'][:5]):
                        with st.expander(f"Document {i+1} (Score: {doc.get('score', 0):.2f})"):
                            st.write(doc.get('content', 'No content'))
    
    else:
        st.warning("No tools available. Check MCP server configuration.")

def agents_section():
    """Agent-specific request interfaces"""
    st.header("🤖 Agent Interface")
    st.write("Interact with specific agents in the compliance system.")
    
    # Agent Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Primary LLM", "Backup LLM", "Compliance Checker", "Retriever"])
    
    with tab1:
        st.subheader("🧠 Primary LLM (GPT-4o-mini)")
        
        prompt = st.text_area(
            "Enter your prompt:",
            placeholder="Analyze this privacy policy section...",
            height=100
        )
        
        col1, col2 = st.columns(2)
        with col1:
            temperature = st.slider("Temperature:", 0.0, 1.0, 0.7, 0.1)
        with col2:
            max_tokens = st.number_input("Max Tokens:", 100, 4000, 1000)
        
        if st.button("🚀 Call Primary LLM", type="primary"):
            if prompt:
                with st.spinner("Calling GPT-4o-mini..."):
                    result = call_mcp_tool('call_llm', {
                        'prompt': prompt,
                        'model': 'gpt-4o-mini',
                        'temperature': temperature,
                        'max_tokens': max_tokens
                    })
                
                st.session_state.agent_responses['primary_llm'] = result
                
                st.subheader("Response:")
                if result.get('success'):
                    response_text = result.get('response', result.get('content', 'No response'))
                    st.write(response_text)
                else:
                    st.error("LLM call failed")
                
                with st.expander("Raw Response"):
                    st.json(result)
            else:
                st.error("Please enter a prompt.")
    
    with tab2:
        st.subheader("🔄 Backup LLM (Gemini Flash)")
        
        backup_prompt = st.text_area(
            "Fallback prompt:",
            placeholder="Provide a second opinion on compliance...",
            height=100
        )
        
        if st.button("🚀 Call Backup LLM", type="primary"):
            if backup_prompt:
                with st.spinner("Calling Gemini Flash..."):
                    result = call_mcp_tool('call_llm', {
                        'prompt': backup_prompt,
                        'model': 'gemini-flash',
                        'fallback': True
                    })
                
                st.session_state.agent_responses['backup_llm'] = result
                
                st.subheader("Response:")
                if result.get('success'):
                    response_text = result.get('response', result.get('content', 'No response'))
                    st.write(response_text)
                else:
                    st.error("Backup LLM call failed")
                
                with st.expander("Raw Response"):
                    st.json(result)
            else:
                st.error("Please enter a prompt.")
    
    with tab3:
        st.subheader("⚖️ Compliance Checker (RAG+LLM)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            feature_text = st.text_area(
                "Feature Description:",
                placeholder="Describe the feature to check for compliance...",
                height=120
            )
        
        with col2:
            jurisdiction = st.selectbox("Jurisdiction:", ["US", "EU", "CA", "UK", "Global"])
            check_types = st.multiselect(
                "Check Types:",
                ["GDPR", "CCPA", "PIPEDA", "Privacy", "Data Protection", "Consent"]
            )
        
        if st.button("🔍 Check Compliance", type="primary"):
            if feature_text:
                with st.spinner("Running compliance check..."):
                    result = call_mcp_tool('check_compliance', {
                        'feature_text': feature_text,
                        'jurisdiction': jurisdiction,
                        'check_types': check_types
                    })
                
                st.session_state.agent_responses['compliance_checker'] = result
                st.session_state.current_analysis = result  # Update dashboard
                
                st.subheader("Compliance Analysis:")
                
                if result.get('success'):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        verdict = result.get('verdict', 'UNKNOWN')
                        render_verdict_badge(verdict)
                    
                    with col2:
                        confidence = result.get('confidence', 0.0)
                        st.metric("Confidence", f"{confidence:.2f}")
                    
                    with col3:
                        risk = result.get('risk_level', 'UNKNOWN')
                        st.metric("Risk Level", risk)
                    
                    reasoning = result.get('reasoning', 'No reasoning provided')
                    st.text_area("Reasoning:", reasoning, height=100, disabled=True)
                    
                    citations = result.get('citations', [])
                    if citations:
                        st.write("**Legal Citations:**")
                        for citation in citations:
                            st.write(f"• {citation}")
                
                with st.expander("Detailed Response"):
                    st.json(result)
            else:
                st.error("Please enter feature description.")
    
    with tab4:
        st.subheader("📚 Retriever")
        
        col1, col2 = st.columns(2)
        
        with col1:
            query = st.text_input(
                "Search Query:",
                placeholder="data protection requirements"
            )
            
        with col2:
            top_k = st.number_input("Number of Results:", 1, 20, 5)
            
        retrieval_type = st.selectbox(
            "Retrieval Type:",
            ["semantic", "keyword", "hybrid", "evidence_backed"]
        )
        
        if st.button("🔍 Retrieve Documents", type="primary"):
            if query:
                with st.spinner("Retrieving documents..."):
                    if retrieval_type == "evidence_backed":
                        # Use evidence-backed retrieval
                        result = call_mcp_tool('evidence_backed_retrieval', {
                            'query': query,
                            'top_k': top_k,
                            'feature_data': {'description': query}
                        })
                    else:
                        # Use basic retrieval
                        result = call_mcp_tool('retrieve_docs', {
                            'query': query,
                            'top_k': top_k,
                            'retrieval_type': retrieval_type
                        })
                
                st.session_state.agent_responses['retriever'] = result
                
                st.subheader("Retrieved Documents:")
                
                if result.get('success'):
                    documents = result.get('documents', [])
                    
                    if documents:
                        for i, doc in enumerate(documents):
                            score = doc.get('score', 0)
                            content = doc.get('content', 'No content available')
                            
                            with st.expander(f"Document {i+1} - Relevance: {score:.3f}"):
                                st.write(content[:500] + "..." if len(content) > 500 else content)
                                
                                if 'metadata' in doc:
                                    st.write("**Metadata:**")
                                    st.json(doc['metadata'])
                    else:
                        st.info("No documents found for the query.")
                
                with st.expander("Raw Response"):
                    st.json(result)
            else:
                st.error("Please enter a search query.")

def history_section():
    """Dedicated history section with advanced filtering and analytics"""
    st.header("📋 Compliance Decision History")
    
    try:
        # Statistics Overview
        stats = get_decision_stats()
        
        st.subheader("📊 Overview Statistics")
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.metric("Total Decisions", stats['total_decisions'])
        with col2:
            st.metric("Compliant", stats['compliant'])
        with col3:
            st.metric("Non-Compliant", stats['non_compliant'])
        with col4:
            st.metric("Abstain", stats['abstain'])
        with col5:
            st.metric("Human Overrides", stats['human_overrides'])
        with col6:
            override_rate = (stats['human_overrides'] / stats['total_decisions'] * 100) if stats['total_decisions'] > 0 else 0
            st.metric("Override Rate", f"{override_rate:.1f}%")
        
        # Jurisdiction breakdown chart
        if stats['jurisdiction_breakdown']:
            st.subheader("📍 Decisions by Jurisdiction")
            
            jur_data = pd.DataFrame([
                {'Jurisdiction': jur, 'Count': count}
                for jur, count in stats['jurisdiction_breakdown'].items()
            ])
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.bar_chart(jur_data.set_index('Jurisdiction'))
            
            with col2:
                st.dataframe(jur_data, use_container_width=True)
        
        # Advanced Filtering
        st.subheader("🔍 Filter & Search Decisions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            jurisdiction_filter = st.selectbox(
                "Jurisdiction:",
                ["ALL"] + list(stats['jurisdiction_breakdown'].keys()) if stats['jurisdiction_breakdown'] else ["ALL", "US", "EU", "CA", "UK"]
            )
        
        with col2:
            law_filter = st.selectbox(
                "Law/Regulation:",
                ["ALL", "GDPR", "CCPA", "PIPEDA", "GENERAL", "COPPA", "HIPAA"]
            )
        
        with col3:
            compliance_filter = st.selectbox(
                "Compliance Decision:",
                ["ALL", "YES", "NO", "ABSTAIN"]
            )
        
        with col4:
            limit = st.number_input("Max Records:", 10, 500, 50)
        
        # Search bar
        search_query = st.text_input("🔍 Search in feature text or notes:", placeholder="Enter keywords...")
        
        # Date range filter
        col1, col2 = st.columns(2)
        with col1:
            date_from = st.date_input("From Date:", value=None)
        with col2:
            date_to = st.date_input("To Date:", value=None)
        
        # Apply filters and search
        if st.button("🔄 Apply Filters") or search_query:
            with st.spinner("Filtering decisions..."):
                
                if search_query:
                    # Use search function
                    decisions = search_decisions(
                        search_query,
                        limit=limit,
                        jurisdiction=jurisdiction_filter if jurisdiction_filter != "ALL" else None,
                        law=law_filter if law_filter != "ALL" else None
                    )
                else:
                    # Use regular filter
                    decisions = list_recent_decisions(
                        limit=limit,
                        jurisdiction=jurisdiction_filter if jurisdiction_filter != "ALL" else None,
                        law=law_filter if law_filter != "ALL" else None
                    )
                
                # Additional filtering
                if compliance_filter != "ALL":
                    decisions = [d for d in decisions if d['require_compliance'] == compliance_filter]
                
                # Date filtering (simplified - would need proper date parsing in production)
                # This is a basic implementation
                
                st.subheader(f"📋 Results ({len(decisions)} decisions)")
                
                if decisions:
                    # Create detailed dataframe
                    display_data = []
                    for decision in decisions:
                        # Calculate agreement
                        agreement = "✅" if decision['human_override'] == decision['require_compliance'] else "❌" if decision['human_override'] else "⏳"
                        
                        # Use canonical field names with fallback
                        feature_display = decision.get('feature_title', decision.get('feature_description', decision.get('feature_text', 'Unknown Feature')))
                        if len(feature_display) > 60:
                            feature_display = feature_display[:60] + "..."
                        
                        confidence_score = decision.get('confidence_score', decision.get('analysis_confidence', decision.get('confidence', 0.0)))
                        
                        display_data.append({
                            'ID': decision['id'],
                            'Feature': feature_display,
                            'Jurisdiction': decision['jurisdiction'],
                            'Law': decision['law'],
                            'AI Decision': decision['require_compliance'],
                            'Confidence': f"{float(confidence_score):.2f}",
                            'Human Override': decision['human_override'] or '—',
                            'Agreement': agreement,
                            'Created': decision['created_at'][:16] if decision['created_at'] else 'Unknown',
                            'Updated': decision['updated_at'][:16] if decision['updated_at'] else 'Unknown'
                        })
                    
                    df = pd.DataFrame(display_data)
                    
                    # Style the dataframe
                    def style_decision(val):
                        if val == 'YES':
                            return 'background-color: #ffcccc; color: darkred; font-weight: bold'
                        elif val == 'NO':
                            return 'background-color: #ccffcc; color: darkgreen; font-weight: bold'
                        elif val == 'ABSTAIN':
                            return 'background-color: #fff2cc; color: orange; font-weight: bold'
                        return ''
                    
                    def style_agreement(val):
                        if val == '✅':
                            return 'color: green; font-size: 16px'
                        elif val == '❌':
                            return 'color: red; font-size: 16px'
                        return ''
                    
                    styled_df = df.style.applymap(style_decision, subset=['AI Decision', 'Human Override']).applymap(style_agreement, subset=['Agreement'])
                    
                    st.dataframe(styled_df, use_container_width=True)
                    
                    # Export filtered results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Convert to CSV for download
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📄 Download as CSV",
                            data=csv,
                            file_name=f"compliance_decisions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    with col2:
                        # JSON export
                        json_data = json.dumps([d for d in decisions], indent=2, default=str)
                        st.download_button(
                            label="📋 Download as JSON",
                            data=json_data,
                            file_name=f"compliance_decisions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                    
                    # Detailed view
                    st.subheader("🔍 Decision Details")
                    
                    selected_id = st.selectbox(
                        "Select Decision ID for detailed view:",
                        [d['id'] for d in decisions],
                        key="history_detail_select"
                    )
                    
                    if selected_id:
                        selected_decision = next(d for d in decisions if d['id'] == selected_id)
                        
                        with st.expander(f"Decision {selected_id} - Full Details", expanded=True):
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**Decision Summary:**")
                                summary_data = {
                                    'Decision ID': selected_decision['id'],
                                    'Feature ID': selected_decision['feature_id'],
                                    'Jurisdiction': selected_decision['jurisdiction'],
                                    'Applicable Law': selected_decision['law'],
                                    'Trigger': selected_decision['trigger'],
                                    'AI Decision': selected_decision['require_compliance'],
                                    'AI Confidence': selected_decision['confidence'],
                                    'Human Override': selected_decision['human_override'] or 'None',
                                    'Created': selected_decision['created_at'],
                                    'Last Updated': selected_decision['updated_at']
                                }
                                
                                for key, value in summary_data.items():
                                    st.write(f"**{key}:** {value}")
                            
                            with col2:
                                st.write("**Feature Description:**")
                                st.text_area(
                                    "Full Feature Text:",
                                    selected_decision['feature_text'],
                                    height=200,
                                    disabled=True,
                                    key=f"feature_text_{selected_id}"
                                )
                            
                            st.write("**Legal Citations:**")
                            if selected_decision['citations']:
                                for i, citation in enumerate(selected_decision['citations']):
                                    st.write(f"{i+1}. {citation}")
                            else:
                                st.write("No citations available")
                            
                            st.write("**LLM Analysis Output:**")
                            st.json(selected_decision['llm_output'])
                            
                            if selected_decision['reviewer_notes']:
                                st.write("**Reviewer Notes:**")
                                st.text_area(
                                    "Human Reviewer Comments:",
                                    selected_decision['reviewer_notes'],
                                    height=100,
                                    disabled=True,
                                    key=f"reviewer_notes_{selected_id}"
                                )
                
                else:
                    st.info("No decisions found matching the current filters.")
        
        else:
            # Show recent decisions by default
            st.subheader("📋 Recent Decisions (Default View)")
            
            recent_decisions = list_recent_decisions(limit=25)
            
            if recent_decisions:
                summary_df = pd.DataFrame([
                    {
                        'ID': d['id'],
                        'Feature': d['feature_text'][:50] + "...",
                        'Jurisdiction': d['jurisdiction'],
                        'AI Decision': d['require_compliance'],
                        'Human Override': d['human_override'] or '—',
                        'Created': d['created_at'][:16] if d['created_at'] else 'Unknown'
                    }
                    for d in recent_decisions
                ])
                
                st.dataframe(summary_df, use_container_width=True)
                st.info("💡 Use the filters above to search and analyze specific decisions")
            else:
                st.info("No decisions in database yet. Run some compliance analyses to populate the history.")
    
    except Exception as e:
        st.error(f"Error loading decision history: {e}")
        st.exception(e)

# ================================
# MAIN APP
# ================================

def main():
    """Main Streamlit application"""
    
    # Sidebar Navigation
    st.sidebar.title("🛡️ Compliance System")
    st.sidebar.markdown("---")
    
    # Navigation
    page = st.sidebar.selectbox(
        "Navigate:",
        ["Dashboard", "Human Review", "History", "Tool Explorer", "Agent Interface"]
    )
    
    # System Status in Sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("System Status")
    
    with st.sidebar:
        if st.button("🔄 Refresh Status"):
            with st.spinner("Checking system status..."):
                status_result = call_mcp_tool('system_status', {})
            
            if status_result.get('success'):
                st.success("✅ System Online")
                if status_result.get('mock_data'):
                    st.warning("⚠️ Mock Mode")
            else:
                st.error("❌ System Issues")
    
    # Quick Actions in Sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("Quick Actions")
    
    with st.sidebar:
        if st.button("🆕 New Analysis"):
            st.switch_page # Would switch to tool explorer or human review
        
        if st.button("📊 View History"):
            st.switch_page # Would switch to dashboard
        
        if st.button("🔧 System Health"):
            with st.spinner("Getting system health..."):
                health_result = call_mcp_tool('enhanced_mcp_orchestrator', {'action': 'system_status'})
            
            with st.expander("System Health Details"):
                st.json(health_result)
    
    # Main Content Area
    if page == "Dashboard":
        dashboard_section()
    elif page == "Human Review":
        human_in_loop_section()
    elif page == "History":
        history_section()
    elif page == "Tool Explorer":
        tool_explorer_section()
    elif page == "Agent Interface":
        agents_section()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
        Compliance Verification System v1.0 | 
        Enhanced with Agentic Integration | 
        FeatureRecord Canonical Format
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
