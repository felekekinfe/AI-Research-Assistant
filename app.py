import streamlit as st
from src.graph import get_graph

# Setup Page
st.set_page_config(page_title="Gemini Researcher (SQLite)", layout="wide")
st.title("🤖 Gemini Research Agent (Persistent)")
st.markdown("State is saved to `db/checkpoints.sqlite`.")

# Initialize Session State
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "session_1"
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.header("Settings")
    new_id = st.text_input("Thread ID", value=st.session_state.thread_id)
    if new_id != st.session_state.thread_id:
        st.session_state.thread_id = new_id
        st.session_state.messages = [] # Clear UI log on switch
        st.rerun()
    
    if st.button("Clear History"):
        st.session_state.messages = []
        st.rerun()

# Load Graph
graph = get_graph()
config = {"configurable": {"thread_id": st.session_state.thread_id}}

# --- Main Logic ---

# 1. Input Handling
user_input = st.chat_input("Enter research topic...")

# --- Updated Input Handling in app.py ---

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 1. Retrieve existing state from SQLite
    current_state = graph.get_state(config)
    
    if not current_state.values:
        # If this is a brand new thread, initialize the "Global Task"
        initial_payload = {
            "task": user_input, # This stays fixed as "ML Research"
            "revision_count": 0,
            "feedback": None,
            "messages": []
        }
        with st.spinner("Initializing Research..."):
            for event in graph.stream(initial_payload, config=config):
                pass
    else:
        # If thread exists, treat input as "Feedback" to existing task
        graph.update_state(config, {"feedback": user_input})
        with st.spinner("Updating Research..."):
            for event in graph.stream(None, config=config):
                pass
                
    st.rerun()

# 2. Check Current State from SQLite
current_state = graph.get_state(config)
state_values = current_state.values

# Render History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 3. Human-in-the-Loop Control
if current_state.next and current_state.next[0] == "human_review":
    draft = state_values.get("draft", "")
    
    st.divider()
    st.subheader("📝 Draft for Review")
    st.markdown(draft)
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("✅ Approve"):
            graph.update_state(config, {"feedback": "approve"})
            with st.spinner("Finalizing..."):
                for event in graph.stream(None, config=config):
                    pass
            st.session_state.messages.append({"role": "assistant", "content": draft})
            st.success("Workflow Complete!")
            st.rerun()

    with col2:
        feedback = st.text_input("Request Changes", key="feedback_input")
        if st.button("🔄 Request Revision") and feedback:
            graph.update_state(config, {"feedback": feedback})
            st.session_state.messages.append({"role": "assistant", "content": f"Revising based on: {feedback}"})
            with st.spinner("Revising..."):
                for event in graph.stream(None, config=config):
                    pass
            st.rerun()

elif not current_state.next and state_values:
    st.success("Task completed.")