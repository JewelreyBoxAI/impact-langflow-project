"""
Streamlit Chat UI for Impact Realty AI Platform
ChatGPT-style interface with thread sidebar for LangFlow agents
"""

import streamlit as st
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional
import asyncio
import logging

from lf_client import LangFlowClient
from db import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Impact Realty AI Platform",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize clients
@st.cache_resource
def initialize_clients():
    """Initialize LangFlow client and database manager"""
    lf_client = LangFlowClient()
    db_manager = DatabaseManager()
    return lf_client, db_manager

lf_client, db_manager = initialize_clients()

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "current_thread_id" not in st.session_state:
    st.session_state.current_thread_id = None
    
if "threads" not in st.session_state:
    st.session_state.threads = []

# Available flows
AVAILABLE_FLOWS = {
    "Karen's Executive Assistant": {
        "flow_id": "karen_exec",
        "description": "Admin & Compliance tasks",
        "icon": "📋"
    },
    "Katelyn's Recruiting": {
        "flow_id": "recruiting", 
        "description": "Agent recruitment and onboarding",
        "icon": "👥"
    },
    "Eileen's Office Operations": {
        "flow_id": "office_ops",
        "description": "Back-office operations and automation",
        "icon": "🏢"
    },
    "Kevin's SOB Supervisor": {
        "flow_id": "sob_supervisor",
        "description": "Executive oversight and reporting",
        "icon": "👨‍💼"
    }
}

def create_new_thread(flow_name: str) -> str:
    """Create a new chat thread"""
    thread_id = str(uuid.uuid4())
    thread_data = {
        "id": thread_id,
        "name": f"{flow_name} - {datetime.now().strftime('%m/%d %H:%M')}",
        "flow_name": flow_name,
        "flow_id": AVAILABLE_FLOWS[flow_name]["flow_id"],
        "created_at": datetime.now(),
        "messages": []
    }
    
    # Save to database
    db_manager.create_thread(thread_data)
    
    return thread_id

def load_thread_messages(thread_id: str) -> List[Dict]:
    """Load messages for a specific thread"""
    return db_manager.get_thread_messages(thread_id)

def save_message(thread_id: str, role: str, content: str, metadata: Optional[Dict] = None):
    """Save message to database"""
    message_data = {
        "thread_id": thread_id,
        "role": role,
        "content": content,
        "metadata": metadata or {},
        "timestamp": datetime.now()
    }
    db_manager.save_message(message_data)

# Sidebar - Thread Management
with st.sidebar:
    st.title("🏠 Impact Realty AI")
    
    # Flow selector
    selected_flow = st.selectbox(
        "Choose Assistant",
        options=list(AVAILABLE_FLOWS.keys()),
        format_func=lambda x: f"{AVAILABLE_FLOWS[x]['icon']} {x}",
        key="flow_selector"
    )
    
    # New thread button
    if st.button("➕ New Chat", use_container_width=True):
        new_thread_id = create_new_thread(selected_flow)
        st.session_state.current_thread_id = new_thread_id
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    # Load and display threads
    threads = db_manager.get_user_threads()
    st.session_state.threads = threads
    
    if threads:
        st.subheader("Chat History")
        for thread in threads:
            # Create a container for each thread
            thread_container = st.container()
            with thread_container:
                # Thread selection button
                button_label = f"{thread['name']}"
                if st.button(
                    button_label,
                    key=f"thread_{thread['id']}",
                    use_container_width=True
                ):
                    st.session_state.current_thread_id = thread["id"]
                    st.session_state.messages = load_thread_messages(thread["id"])
                    st.rerun()
                
                # Show current thread indicator
                if st.session_state.current_thread_id == thread["id"]:
                    st.markdown("🔹 *Current chat*")
    
    st.divider()
    
    # Settings
    with st.expander("⚙️ Settings"):
        st.markdown("**Environment**: Development")
        st.markdown(f"**Session ID**: `{st.session_state.session_id[:8]}...`")
        
        if st.button("Clear All Chats"):
            db_manager.clear_all_threads()
            st.session_state.threads = []
            st.session_state.current_thread_id = None
            st.session_state.messages = []
            st.success("All chats cleared!")
            st.rerun()

# Main chat interface
if st.session_state.current_thread_id is None:
    # Welcome screen
    st.markdown("""
    # Welcome to Impact Realty AI Platform
    
    Select an assistant from the sidebar to get started:
    """)
    
    # Display available assistants
    cols = st.columns(2)
    for i, (name, info) in enumerate(AVAILABLE_FLOWS.items()):
        with cols[i % 2]:
            with st.container():
                st.markdown(f"""
                ### {info['icon']} {name}
                {info['description']}
                """)
    
    st.markdown("""
    ---
    **Phase 1 Focus**: Admin & Compliance (Karen) and Recruiting (Katelyn) modules are fully implemented.
    
    **Phase 2**: Office Operations (Eileen) - In development
    
    **Phase 3**: Supreme Oversight Board (Kevin) - Planned
    """)

else:
    # Get current thread info
    current_thread = next((t for t in st.session_state.threads if t["id"] == st.session_state.current_thread_id), None)
    
    if current_thread:
        flow_info = AVAILABLE_FLOWS[current_thread["flow_name"]]
        st.markdown(f"# {flow_info['icon']} {current_thread['flow_name']}")
        st.markdown(f"*{flow_info['description']}*")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show metadata if available (record IDs, links, etc.)
            if message.get("metadata") and message["role"] == "assistant":
                metadata = message["metadata"]
                if metadata.get("record_ids"):
                    st.caption(f"🔗 Record IDs: {', '.join(metadata['record_ids'])}")
                if metadata.get("links"):
                    st.caption(f"📎 Links: {', '.join(metadata['links'])}")

    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        save_message(st.session_state.current_thread_id, "user", prompt)
        
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = asyncio.run(lf_client.run_flow(
                        flow_id=current_thread["flow_id"],
                        input_data={"input": prompt},
                        session_id=st.session_state.session_id
                    ))
                    
                    # Extract response content and metadata
                    response_content = response.get("outputs", {}).get("message", "I apologize, but I encountered an issue processing your request.")
                    metadata = {
                        "record_ids": response.get("metadata", {}).get("record_ids", []),
                        "links": response.get("metadata", {}).get("links", []),
                        "execution_id": response.get("execution_id")
                    }
                    
                    st.markdown(response_content)
                    
                    # Show metadata
                    if metadata.get("record_ids"):
                        st.caption(f"🔗 Record IDs: {', '.join(metadata['record_ids'])}")
                    if metadata.get("links"):
                        st.caption(f"📎 Links: {', '.join(metadata['links'])}")
                    
                    # Save assistant response
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_content,
                        "metadata": metadata
                    })
                    save_message(st.session_state.current_thread_id, "assistant", response_content, metadata)
                    
                except Exception as e:
                    error_message = f"I apologize, but I encountered an error: {str(e)}"
                    st.error(error_message)
                    
                    # Save error message
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": error_message
                    })
                    save_message(st.session_state.current_thread_id, "assistant", error_message)
        
        # Rerun to update the interface
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
Impact Realty AI Platform - Phase 1 Development<br>
LangFlow + Streamlit + Azure Infrastructure
</div>
""", unsafe_allow_html=True)