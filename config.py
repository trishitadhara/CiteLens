import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = "gpt-4o-mini"

    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "citelens")

    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "./data/mlruns")

    QDRANT_URL = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "citelens_papers")
    MEMORY_TTL_DAYS = 30

    PG_DSN = os.getenv("PG_DSN", "")
    MEM0_API_KEY = os.getenv("MEM0_API_KEY", "")

    # Edge mode: use Ollama for claim extraction if True
    EDGE_MODE = os.getenv("EDGE_MODE", "false").lower() == "true"

    # Verifier confidence threshold — below this triggers Reflexion retry
    VERIFIER_THRESHOLD = 0.6
    MAX_REFLEXION_RETRIES = 2

    TOP_K_PAPERS = 8


    HF_TOKEN = os.getenv("HF_TOKEN", "")
    if HF_TOKEN:
        os.environ["HF_TOKEN"] = HF_TOKEN
        os.environ["HUGGINGFACE_HUB_TOKEN"] = HF_TOKEN

cfg = Config()
