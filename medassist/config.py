import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Tiny .env loader (KEY=value lines); real environment variables win."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv(ROOT / ".env")
DATA_DIR = ROOT / "data"
INDEX_DIR = DATA_DIR / "index"

EMBED_MODEL = "BAAI/bge-small-en-v1.5"  # ~130MB, runs fine on CPU
NLI_MODEL = "cross-encoder/nli-deberta-v3-small"  # labels: contradiction, entailment, neutral
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "  # bge query instruction

CHUNK_WORDS = 110
TOP_K = 4

# LLM backend: "ollama" (local, free, default) or "groq" (free-tier key, no card)
LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

ENTAIL_THRESHOLD = 0.5
CONTRADICT_THRESHOLD = 0.5
