# Medical Information Assistant (Educational Only)

RAG chatbot over NIH MedlinePlus that explains diseases with citations and labels every
claim as **Supported / Contradicted / Unsupported** using an NLI model. 100% free: local models, no API keys.

## Stack
- Corpus: MedlinePlus health topics XML (NIH, public domain)
- Retrieval: `bge-small-en-v1.5` embeddings + BM25, fused with RRF
- Generator: Ollama (`llama3.2:3b`) locally; optional free Groq key (`LLM_BACKEND=groq`, `GROQ_API_KEY=...`)
- Verifier: `cross-encoder/nli-deberta-v3-small` (entailment / contradiction / neutral)
- Safety: rule-based router (emergency and personal-advice refusal) + disclaimer
- UI: Streamlit

## Setup
```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python -m medassist.ingest        # downloads MedlinePlus XML, builds index (one-time)
ollama pull llama3.2:3b           # install Ollama from https://ollama.com first
streamlit run app.py
```

Tests: `python -m pytest -q`

## Pipeline
question -> safety gate -> hybrid retrieval -> LLM answer with [n] citations (invalid refs stripped)
-> split into claims -> retrieve evidence per claim -> NLI -> badge + evidence snippet.

"Unsupported" means not found in the indexed sources, not necessarily false.
