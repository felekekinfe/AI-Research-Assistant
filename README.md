# Gemini Research Agent (LangGraph & Streamlit)

A stateful, autonomous research agent built with **LangGraph**, **LangChain**, and **Streamlit**. This application employs a graph-based workflow to perform research on user-defined topics, collect information from web and academic sources, synthesize drafts, validate content, and incorporate human oversight via a Human-in-the-Loop (HITL) mechanism.

## 🚀 Features

- **Graph-Based Workflow**: Supports non-linear execution with conditional routing and iterative refinement cycles.
- **State Persistence**: Utilizes SQLite checkpointing to maintain state and memory across interactions.
- **Human-in-the-Loop**: Interrupts execution to allow human review and approval prior to finalization.
- **Multi-Step Research Process**:
  - Web search using DuckDuckGo.
  - Academic search using Semantic Scholar.
  - Draft synthesis and iterative writing.
  - Automated validation and self-correction.
- **Refinement Loop**: Detects validation failures and automatically generates new search queries (limited to 3 revisions to prevent infinite loops).
- **Interactive Streamlit UI**: Displays real-time progress, execution logs, gathered research data, current draft, and a visual workflow diagram.
- **LangSmith Tracing**: Optional integration for monitoring and debugging workflows.

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/felekekinfe/AI-RESEARCH-ASSISTANT.git
   cd AI-RESEARCH-ASSISTANT
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file in the project root:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ```
   For LangSmith tracing (optional):
   ```
   LANGCHAIN_TRACING=true
   LANGCHAIN_API_KEY=your_langsmith_api_key
   LANGCHAIN_PROJECT=gemini-research-agent
   ```

## ▶️ Usage

Start the application:
```bash
streamlit run app.py
```

- Provide your Google API key in the sidebar if not configured via environment.
- Enter a research topic in the chat input field to begin.
- Monitor progress in real-time status updates.
- Review gathered research data and the current draft in expandable sections.
- During the human review phase:
  - Click **Approve & Finish** to finalize.
  - Or provide feedback via the chat input to trigger refinement.

The agent follows this sequence:
1. Web research
2. Academic research
3. Draft writing
4. Validation
5. Refinement (if needed)
6. Human review

## 🏗️ Architecture

The workflow is implemented as a `StateGraph` in `src/graph.py`.

### Nodes
- `web_researcher`: Performs general web searches via DuckDuckGo.
- `academic_researcher`: Queries Semantic Scholar for peer-reviewed sources.
- `writer`: Synthesizes research into a structured Markdown report using Gemini.
- `validator`: Evaluates draft quality against defined criteria.
- `refiner`: Generates improved search queries based on validation failure or feedback.
- `human_review`: Interrupt node for user interaction.

### State Management
Defined in `src/state.py` with annotated fields for accumulation (e.g., research data and messages). Persistence is handled via `langgraph-checkpoint-sqlite` in `db/checkpoints.sqlite`.

### LLM Configuration
Uses `gemini-1.5-flash` (via `langchain-google-genai`) with temperature=0 for consistent outputs.

## 🔧 Customization & Extension

- Modify prompts in `src/nodes.py` to adjust behavior.
- Add new nodes or tools to the graph in `src/graph.py`.
- Upgrade the checkpointer (e.g., to PostgreSQL) for production use.

## ⚠️ Notes & Limitations

- Academic searches via Semantic Scholar may occasionally return limited results or encounter errors; robust fallbacks are implemented.
- The refinement loop is capped at 3 iterations.
- Ensure compliance with API terms of service for Google Gemini, DuckDuckGo, and Semantic Scholar.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome. Please follow standard GitHub workflow practices.

## 📄 License

This project is released under the MIT License.