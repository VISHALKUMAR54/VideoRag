import os
from dotenv import load_dotenv

# load .env from the backend/ directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
OPENAI_API_KEY:  str = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY:    str = os.getenv("GROQ_API_KEY", "")

INSTAGRAM_USERNAME: str = os.getenv("INSTAGRAM_USERNAME", "")
INSTAGRAM_PASSWORD: str = os.getenv("INSTAGRAM_PASSWORD", "")

REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_URL:  str = os.getenv("QDRANT_URL",  f"http://{QDRANT_HOST}:{QDRANT_PORT}")

COLLECTION_NAME:    str = "videos"
EMBEDDING_DIM:      int = 384          # BAAI/bge-small-en-v1.5 output size
EMBEDDING_MODEL:    str = "BAAI/bge-small-en-v1.5"

CHUNK_SIZE:         int = 500          # characters per chunk
CHUNK_OVERLAP:      int = 100

LLM_MODEL:          str = "llama-3.3-70b-versatile"
LLM_TEMPERATURE:    float = 0.3
HISTORY_WINDOW:     int = 6            # conversation turns to keep
HISTORY_MAX_TOKENS: int = 1500

RETRIEVAL_TOP_K:    int = 4            # chunks per video per query
# warn at startup if required keys are missing
def warn_missing_keys() -> None:
    missing = []
    if not YOUTUBE_API_KEY: missing.append("YOUTUBE_API_KEY")
    if not GROQ_API_KEY:    missing.append("GROQ_API_KEY")
    if missing:
        print(
            f"[Config] WARNING: Missing environment variables: {missing}\n"
            "         Copy backend/.env.example to backend/.env and fill in values."
        )