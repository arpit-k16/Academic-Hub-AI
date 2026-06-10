"""
Streamlit Review Dashboard.
"""

import streamlit as st
import requests
from datetime import datetime
import pandas as pd

# Configuration
API_URL = "http://localhost:8000/api"

st.set_page_config(
    page_title="Academic Resource Review",
    page_icon="📚",
    layout="wide",
)


def get_pending_resources(filters=None):
    """Fetch pending resources from API."""
    try:
        params = {"status": "pending", "limit": 50}
        if filters:
            params.update(filters)
        response = requests.get(f"{API_URL}/resources/pending", params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching resources: {e}")
        return []


def get_stats():
    """Fetch statistics from API."""
    try:
        response = requests.get(f"{API_URL}/resources/stats")
        response.raise_for_status()
        return response.json()
    except:
        return {"total": 0, "pending": 0, "approved": 0, "rejected": 0}


def review_resource(resource_id: int, status: str, reviewer: str = "admin", reason: str = None):
    """Submit review for a resource."""
    try:
        data = {
            "status": status,
            "reviewed_by": reviewer,
        }
        if reason:
            data["rejection_reason"] = reason
        
        response = requests.put(
            f"{API_URL}/resources/{resource_id}/review",
            json=data
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Error reviewing resource: {e}")
        return False


def get_courses():
    """Fetch courses for filter."""
    try:
        response = requests.get(f"{API_URL}/courses/", params={"limit": 500})
        response.raise_for_status()
        return response.json()
    except:
        return []


def get_colleges():
    """Fetch colleges for filter."""
    try:
        response = requests.get(f"{API_URL}/colleges/")
        response.raise_for_status()
        return response.json()
    except:
        return []


# Main app
st.title("📚 Academic Resource Review Dashboard")

# Sidebar - Statistics and Filters
with st.sidebar:
    st.header("📊 Statistics")
    stats = get_stats()
    
    col1, col2 = st.columns(2)
    col1.metric("Total", stats.get("total", 0))
    col2.metric("Pending", stats.get("pending", 0))
    
    col3, col4 = st.columns(2)
    col3.metric("Approved", stats.get("approved", 0))
    col4.metric("Rejected", stats.get("rejected", 0))
    
    st.divider()
    st.header("🔍 Filters")
    
    # Course filter
    courses = get_courses()
    course_options = ["All"] + [c.get("course_code", "") for c in courses]
    selected_course = st.selectbox("Course", course_options)
    
    # College filter
    colleges = get_colleges()
    college_options = ["All"] + [c.get("name", "") for c in colleges]
    selected_college = st.selectbox("College", college_options)
    
    # Type filter
    type_options = ["All", "notes", "question_paper", "syllabus", "practical", "tutorial", "reference", "other"]
    selected_type = st.selectbox("Resource Type", type_options)
    
    # Refresh button
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()


# Build filters
filters = {}
if selected_course != "All":
    filters["course_code"] = selected_course
if selected_college != "All":
    college = next((c for c in colleges if c.get("name") == selected_college), None)
    if college:
        filters["college_id"] = college.get("id")
if selected_type != "All":
    filters["resource_type"] = selected_type


# Main content - Pending Resources
st.header("📋 Pending Resources")

resources = get_pending_resources(filters)

if not resources:
    st.info("No pending resources to review. Great job! 🎉")
else:
    st.write(f"Showing {len(resources)} pending resources")
    
    for i, resource in enumerate(resources):
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader(f"📄 {resource.get('title', 'Untitled')[:80]}")
                
                # Metadata row
                meta_cols = st.columns(4)
                meta_cols[0].write(f"**Course:** {resource.get('course_code', 'N/A')}")
                meta_cols[1].write(f"**Type:** {resource.get('resource_type', 'N/A')}")
                meta_cols[2].write(f"**College:** {resource.get('college_name', 'Unknown')}")
                meta_cols[3].write(f"**Score:** {resource.get('final_score', 0):.1f}")
                
                # Content preview
                with st.expander("View Content Snippet"):
                    st.write(resource.get("content_snippet", "No content available"))
                
                # Link
                st.markdown(f"🔗 [Open Resource]({resource.get('file_url', '#')})")
            
            with col2:
                st.write("**AI Confidence:**")
                confidence = resource.get("ai_confidence", 0)
                st.progress(confidence / 100)
                st.write(f"{confidence}%")
                
                # Review buttons
                resource_id = resource.get("id")
                
                col_approve, col_reject = st.columns(2)
                
                with col_approve:
                    if st.button("✅ Approve", key=f"approve_{resource_id}", use_container_width=True):
                        if review_resource(resource_id, "approved"):
                            st.success("Approved!")
                            st.rerun()
                
                with col_reject:
                    if st.button("❌ Reject", key=f"reject_{resource_id}", use_container_width=True):
                        if review_resource(resource_id, "rejected"):
                            st.warning("Rejected!")
                            st.rerun()
            
            st.divider()


# Footer
st.markdown("---")
st.markdown("*Academic Resource Discovery System - Review Dashboard*")
