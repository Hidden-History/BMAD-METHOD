"""
BMAD Memory Intelligence Dashboard
===================================
Streamlit dashboard for monitoring memory quality, health, and performance.

2025 Best Practices:
- Caching for performance
- Session state management
- Proper error handling
- Responsive layout
- Security (read-only operations)
"""

import os
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

# Use internal container name for Docker network communication
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
KNOWLEDGE_COLLECTION = os.getenv("QDRANT_KNOWLEDGE_COLLECTION", "bmad-knowledge")
BEST_PRACTICES_COLLECTION = os.getenv("QDRANT_BEST_PRACTICES_COLLECTION", "bmad-best-practices")
AGENT_MEMORY_COLLECTION = os.getenv("QDRANT_AGENT_MEMORY_COLLECTION", "agent-memory")

# NOTE: When accessing from host machine, use http://localhost:16350
# Inside Docker network, containers use http://qdrant:6333

# Page configuration (2025 best practice: set first)
st.set_page_config(
    page_title="BMAD Memory Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CONNECTION & CACHING
# =============================================================================

@st.cache_resource
def get_qdrant_client():
    """Get cached Qdrant client connection."""
    try:
        if QDRANT_API_KEY:
            client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        else:
            client = QdrantClient(url=QDRANT_URL)
        return client
    except Exception as e:
        st.error(f"Failed to connect to Qdrant: {e}")
        return None

@st.cache_data(ttl=30)  # Cache for 30 seconds
def get_collection_info(collection_name: str) -> Dict[str, Any]:
    """Get collection metadata with caching."""
    client = get_qdrant_client()
    if not client:
        return {}

    try:
        info = client.get_collection(collection_name)
        return {
            "name": collection_name,
            "points_count": info.points_count,
            "vectors_count": info.vectors_count,
            "indexed_vectors_count": info.indexed_vectors_count,
            "status": info.status.value
        }
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=60)  # Cache for 60 seconds
def get_recent_memories(collection_name: str, limit: int = 10) -> List[Dict]:
    """Get recent memories from collection."""
    client = get_qdrant_client()
    if not client:
        return []

    try:
        result = client.scroll(
            collection_name=collection_name,
            limit=limit,
            with_payload=True,
            with_vectors=False
        )
        points = result[0]  # First element is list of points
        return [{"id": p.id, "payload": p.payload} for p in points]
    except Exception as e:
        st.error(f"Error fetching memories: {e}")
        return []

# =============================================================================
# HEADER
# =============================================================================

st.title("🧠 BMAD Memory Intelligence Dashboard")
st.markdown("**Real-time monitoring of memory quality, health, and performance**")
st.divider()

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.header("⚙️ Controls")

    # Connection status
    st.subheader("Connection")
    client = get_qdrant_client()
    if client:
        st.success(f"✅ Connected to {QDRANT_URL}")
    else:
        st.error("❌ Not connected")
        st.stop()

    # Collection selector
    st.subheader("Collection")
    collection = st.selectbox(
        "Select Collection",
        [KNOWLEDGE_COLLECTION, BEST_PRACTICES_COLLECTION, AGENT_MEMORY_COLLECTION],
        index=0
    )

    # Refresh button
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    # Refresh interval
    auto_refresh = st.checkbox("Auto-refresh", value=False)
    if auto_refresh:
        refresh_interval = st.slider("Interval (seconds)", 10, 300, 30)
        import time
        time.sleep(refresh_interval)
        st.rerun()

# =============================================================================
# MAIN DASHBOARD
# =============================================================================

# Collection Overview
col1, col2, col3, col4 = st.columns(4)

info = get_collection_info(collection)

with col1:
    st.metric(
        "Total Points",
        info.get("points_count", "N/A"),
        help="Total number of vectors in collection"
    )

with col2:
    st.metric(
        "Vectors Count",
        info.get("vectors_count", "N/A"),
        help="Number of vector embeddings"
    )

with col3:
    st.metric(
        "Indexed Vectors",
        info.get("indexed_vectors_count", "N/A"),
        help="Vectors indexed for search"
    )

with col4:
    status = info.get("status", "unknown")
    status_color = "🟢" if status == "green" else "🟡" if status == "yellow" else "🔴"
    st.metric(
        "Status",
        f"{status_color} {status.upper()}",
        help="Collection health status"
    )

st.divider()

# =============================================================================
# TABS
# =============================================================================

tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔍 Search", "📝 Recent Memories", "📈 Analytics"])

# ---------------------------------------------------------------------------
# TAB 1: OVERVIEW
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Collection Health")

    # Placeholder metrics (will be implemented with real data)
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Average Quality Score", "0.78", "↑ 0.05")
        st.metric("Duplicate Detection Rate", "0%", "0")
        st.metric("Storage Efficiency", "92%", "↑ 3%")

    with col2:
        st.metric("Search Latency (avg)", "245ms", "↓ 12ms")
        st.metric("Token Efficiency", "87%", "↑ 2%")
        st.metric("Cache Hit Rate", "94%", "↑ 1%")

    # Placeholder chart
    st.subheader("Memory Growth Over Time")
    dates = pd.date_range(start='2026-01-01', end='2026-01-03', freq='6H')
    data = pd.DataFrame({
        'Date': dates,
        'Memories': range(0, len(dates) * 10, 10)
    })
    fig = px.line(data, x='Date', y='Memories', title='Memory Collection Growth')
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 2: SEARCH
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("Search Memories")

    search_query = st.text_input("Enter search query", placeholder="e.g., JWT authentication")
    search_limit = st.slider("Number of results", 1, 20, 5)

    if st.button("🔍 Search", type="primary"):
        if search_query:
            with st.spinner("Searching..."):
                # Placeholder - implement actual search
                st.info("Search functionality will be implemented with embedding-based search")
        else:
            st.warning("Please enter a search query")

# ---------------------------------------------------------------------------
# TAB 3: RECENT MEMORIES
# ---------------------------------------------------------------------------
with tab3:
    st.subheader(f"Recent Memories from {collection}")

    limit = st.slider("Number of memories", 5, 50, 10)
    memories = get_recent_memories(collection, limit)

    if memories:
        for i, memory in enumerate(memories, 1):
            with st.expander(f"Memory {i} - ID: {memory['id']}"):
                payload = memory.get('payload', {})

                # Display metadata
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Type:**", payload.get('type', 'N/A'))
                    st.write("**Agent:**", payload.get('agent', 'N/A'))
                    st.write("**Created:**", payload.get('created_at', 'N/A'))

                with col2:
                    st.write("**Component:**", payload.get('component', 'N/A'))
                    st.write("**Importance:**", payload.get('importance', 'N/A'))
                    st.write("**Story ID:**", payload.get('story_id', 'N/A'))

                # Display content
                st.write("**Content:**")
                st.code(payload.get('content', 'No content'), language="markdown")
    else:
        st.info("No memories found")

# ---------------------------------------------------------------------------
# TAB 4: ANALYTICS
# ---------------------------------------------------------------------------
with tab4:
    st.subheader("Memory Analytics")

    # Placeholder analytics
    st.info("Advanced analytics features coming soon:")
    st.markdown("""
    - Memory quality distribution
    - Agent usage patterns
    - Token budget compliance
    - Duplicate detection stats
    - Search performance metrics
    - Storage optimization recommendations
    """)

# =============================================================================
# FOOTER
# =============================================================================

st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | BMAD Memory Intelligence v1.0.0")
