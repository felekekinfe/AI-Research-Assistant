import streamlit as st
import os
from src.graph import get_graph
from src.config import get_llm
from langsmith import Client
# --- Page Config ---
st.set_page_config(page_title="Gemini Research Agent", layout="wide", page_icon="🤖")

st.title("🤖 Gemini Research Agent")
st.markdown("##### Advanced Autonomous Researcher with LangGraph & LangSmith")


# --- Sidebar & Configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key Handling
    if not get_llm():
        user_key = st.text_input("Enter Google API Key", type="password")
        if user_key:
            os.environ["GOOGLE_API_KEY"] = user_key
            st.rerun()
        else:
            st.warning("⚠️ API Key required to proceed.")
            st.stop()
            
    st.divider()
    
    # Session Management
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = "session_1"
        
    new_id = st.text_input("Thread ID", value=st.session_state.thread_id)
    if new_id != st.session_state.thread_id:
        st.session_state.thread_id = new_id
        st.rerun()
        
    if st.button("🗑️ Clear History"):
        # We generate a new thread ID to effectively 'clear' the graph state
        import uuid
        st.session_state.thread_id = str(uuid.uuid4())[:8]
        st.rerun()

    st.info(f"Active Thread: `{st.session_state.thread_id}`")
    
    if os.getenv("LANGCHAIN_TRACING") == "true":
        st.success("✅ LangSmith Tracing Active")

# --- State Management ---
graph = get_graph()
config = {"configurable": {"thread_id": st.session_state.thread_id}}

try:
    current_state = graph.get_state(config)
except Exception as e:
    st.error("Error accessing database. Please clear history.")
    st.stop()
#graph ui
from IPython.display import Image

with st.sidebar:
    st.subheader("Graph Visualization")
    # Generate the Mermaid PNG and display it
    try:
        graph_img = graph.get_graph().draw_mermaid_png()
        st.image(graph_img, caption="Agent Workflow Diagram")
    except Exception as e:
        st.error(f"Could not render graph: {e}")
# --- UI Layout ---

# Initialize LangSmith Client for flushing traces
ls_client = Client()

user_input = st.chat_input("Enter research topic or feedback...")

if user_input:
    # Determine if this is a new task or feedback
    if not current_state.values:
        # Initial Launch
        initial_payload = {
            "task": user_input,
            "revision_count": 0,
            "messages": [f"🚀 Starting task: {user_input}"]
        }
        with st.status("🤖 AI Researcher working...", expanded=True) as status:
            for event in graph.stream(initial_payload, config=config):
                # Visualize steps dynamically
                for node, values in event.items():
                    if "messages" in values and values["messages"]:
                        status.write(values["messages"][-1])
    else:
        # Feedback Loop
        graph.update_state(config, {"feedback": user_input})
        with st.status("🤖 Refining based on feedback...", expanded=True) as status:
            for event in graph.stream(None, config=config):
                 for node, values in event.items():
                    if "messages" in values and values["messages"]:
                        status.write(values["messages"][-1])
        ls_client.flush()
    
    st.rerun()

# --- Main Display Area ---

# 1. Message History (Logs)
if current_state.values:
    messages = current_state.values.get("messages", [])
    if messages:
        with st.expander("📜 Execution Log", expanded=False):
            for msg in messages:
                st.write(msg)

    # 2. Research Data
    research_content = current_state.values.get("research_data", "")
    if research_content:
        with st.expander("🔍 Gathered Research Data", expanded=False):
            st.code(research_content, language="markdown")

    # 3. Current Draft (The "Product")
    draft = current_state.values.get("draft", "")
    
    if draft:
        st.subheader("📝 Current Draft")
        st.markdown(draft)

    # 4. Human Review Controls
    if current_state.next and current_state.next[0] == "human_review":
        st.divider()
        st.warning("⚠️ Human Review Required")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("✅ Approve & Finish", type="primary"):
                graph.update_state(config, {"feedback": "approve"})
                with st.spinner("Finalizing..."):
                    for event in graph.stream(None, config=config):
                        pass
                st.balloons()
                st.rerun()
        
        with col2:
            st.caption("To request changes, type feedback in the chat bar below.")

elif not current_state.values:
    st.markdown("""
    ### Ready to Research
    Type a topic below to start. The agent will:
    1. 🌍 Search the Web
    2. 🎓 Check Academic Sources
    3. ✍️ Write a Draft
    4. ⚖️ Self-Validate
    5. 🗣️ Ask for your review
    """)