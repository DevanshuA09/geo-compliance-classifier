#!/usr/bin/env python3
"""
Human Review Dashboard
Simple Streamlit dashboard for reviewing compliance analysis results
"""

import streamlit as st
import json
import os
from pathlib import Path
import datetime
from typing import Dict, List

# Configure page
st.set_page_config(
    page_title="Compliance Review Dashboard",
    page_icon="🔍",
    layout="wide"
)

def load_review_requests() -> List[Dict]:
    """Load pending human review requests"""
    reviews_dir = Path("../human-reviews")
    reviews = []
    
    if reviews_dir.exists():
        for review_file in reviews_dir.glob("*.json"):
            try:
                with open(review_file, 'r') as f:
                    review_data = json.load(f)
                    review_data['file_path'] = review_file
                    reviews.append(review_data)
            except Exception as e:
                st.error(f"Error loading {review_file}: {e}")
    
    return sorted(reviews, key=lambda x: x.get('timestamp', ''), reverse=True)

def save_review_decision(review_id: str, decision: Dict):
    """Save human review decision"""
    reviews_dir = Path("../human-reviews")
    review_file = reviews_dir / f"{review_id}.json"
    
    if review_file.exists():
        with open(review_file, 'r') as f:
            review_data = json.load(f)
        
        review_data['human_decision'] = decision
        review_data['status'] = 'completed'
        review_data['reviewed_at'] = datetime.datetime.now().isoformat()
        
        with open(review_file, 'w') as f:
            json.dump(review_data, f, indent=2)
        
        return True
    return False

def main():
    st.title("🔍 Compliance Review Dashboard")
    st.markdown("Human-in-the-loop review for compliance analysis results")
    
    # Load pending reviews
    reviews = load_review_requests()
    pending_reviews = [r for r in reviews if r.get('status') == 'pending']
    completed_reviews = [r for r in reviews if r.get('status') == 'completed']
    
    # Sidebar stats
    st.sidebar.header("📊 Review Statistics")
    st.sidebar.metric("Pending Reviews", len(pending_reviews))
    st.sidebar.metric("Completed Reviews", len(completed_reviews))
    st.sidebar.metric("Total Reviews", len(reviews))
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["🚨 Pending Reviews", "✅ Completed Reviews", "📈 Analytics"])
    
    with tab1:
        st.header("Pending Human Reviews")
        
        if not pending_reviews:
            st.info("🎉 No pending reviews! All compliance analyses are confident.")
        else:
            for review in pending_reviews:
                with st.expander(f"Review #{review['id'][-8:]} - {review['reason'].title()} - Priority: {review['priority'].title()}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.subheader("Analysis Context")
                        context = review.get('context', {})
                        
                        # Show original analysis if available
                        if 'analysis_result' in context:
                            result = context['analysis_result']
                            st.write("**Original AI Analysis:**")
                            st.write(f"- Verdict: {result.get('verdict', 'Unknown')}")
                            st.write(f"- Confidence: {result.get('confidence', 0):.2f}")
                            st.write(f"- Reasoning: {result.get('reasoning', 'Not provided')}")
                        
                        # Show feature data
                        if 'feature_data' in context:
                            st.write("**Feature Being Analyzed:**")
                            st.json(context['feature_data'])
                        
                        # Show jurisdiction
                        jurisdiction = context.get('jurisdiction', 'Unknown')
                        st.write(f"**Jurisdiction:** {jurisdiction}")
                    
                    with col2:
                        st.subheader("Human Decision")
                        
                        # Human review form
                        human_verdict = st.selectbox(
                            "Your Verdict:",
                            ["COMPLIANT", "NON_COMPLIANT", "NEEDS_MODIFICATION"],
                            key=f"verdict_{review['id']}"
                        )
                        
                        human_confidence = st.slider(
                            "Your Confidence:",
                            0.0, 1.0, 0.8,
                            key=f"confidence_{review['id']}"
                        )
                        
                        human_reasoning = st.text_area(
                            "Your Reasoning:",
                            placeholder="Explain your decision...",
                            key=f"reasoning_{review['id']}"
                        )
                        
                        if st.button(f"Submit Decision", key=f"submit_{review['id']}"):
                            decision = {
                                'verdict': human_verdict,
                                'confidence': human_confidence,
                                'reasoning': human_reasoning,
                                'reviewer': 'human_reviewer',  # Could be made dynamic
                                'timestamp': datetime.datetime.now().isoformat()
                            }
                            
                            if save_review_decision(review['id'], decision):
                                st.success("✅ Decision saved successfully!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to save decision")
    
    with tab2:
        st.header("Completed Reviews")
        
        if not completed_reviews:
            st.info("No completed reviews yet.")
        else:
            for review in completed_reviews:
                with st.expander(f"Review #{review['id'][-8:]} - Completed"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Original AI Analysis:**")
                        context = review.get('context', {})
                        if 'analysis_result' in context:
                            result = context['analysis_result']
                            st.write(f"- Verdict: {result.get('verdict', 'Unknown')}")
                            st.write(f"- Confidence: {result.get('confidence', 0):.2f}")
                    
                    with col2:
                        st.write("**Human Decision:**")
                        decision = review.get('human_decision', {})
                        st.write(f"- Verdict: {decision.get('verdict', 'Unknown')}")
                        st.write(f"- Confidence: {decision.get('confidence', 0):.2f}")
                        st.write(f"- Reviewed: {decision.get('timestamp', 'Unknown')}")
                    
                    if decision.get('reasoning'):
                        st.write("**Human Reasoning:**")
                        st.write(decision['reasoning'])
    
    with tab3:
        st.header("Review Analytics")
        
        if reviews:
            # Calculate agreement metrics
            agreements = 0
            disagreements = 0
            
            for review in completed_reviews:
                context = review.get('context', {})
                ai_result = context.get('analysis_result', {})
                human_decision = review.get('human_decision', {})
                
                ai_verdict = ai_result.get('verdict', '')
                human_verdict = human_decision.get('verdict', '')
                
                if ai_verdict and human_verdict:
                    if ai_verdict == human_verdict:
                        agreements += 1
                    else:
                        disagreements += 1
            
            if agreements + disagreements > 0:
                agreement_rate = agreements / (agreements + disagreements)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Agreement Rate", f"{agreement_rate:.1%}")
                with col2:
                    st.metric("Agreements", agreements)
                with col3:
                    st.metric("Disagreements", disagreements)
            
            # Reason distribution
            reasons = [r.get('reason', 'unknown') for r in reviews]
            reason_counts = {reason: reasons.count(reason) for reason in set(reasons)}
            
            st.subheader("Review Reasons")
            for reason, count in reason_counts.items():
                st.write(f"- {reason.replace('_', ' ').title()}: {count}")
        
        else:
            st.info("No review data available yet.")

if __name__ == "__main__":
    main()
