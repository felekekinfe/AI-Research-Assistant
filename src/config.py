import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load env variables
load_dotenv()

# Initialize LLM globally for reuse
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0,
    api_key=os.getenv("GOOGLE_API_KEY")
)

DB_PATH = "db/checkpoints.sqlite"