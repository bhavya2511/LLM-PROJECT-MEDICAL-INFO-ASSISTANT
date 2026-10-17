# System flowchart

Rendered automatically by GitHub (Mermaid).

## 1. Offline: building the knowledge base (`python -m medassist.ingest`)

```mermaid
flowchart LR
    A[MedlinePlus health topics XML<br/>NIH, public domain] --> B[Parse topics<br/>keep English, strip HTML,<br/>drop very short entries]
    B --> C[Chunk text<br/>sentence-aware, ~110 words]
    C --> D[Embed chunks<br/>bge-small-en-v1.5]
    D --> E[(data/index<br/>chunks.json + embeddings.npy)]
```

## 2. Online: answering a question (tab "Ask about a condition")

```mermaid
flowchart TD
    U([User question]) --> S{Safety gate<br/>safety.check}
    S -- emergency words --> E1[/Emergency message<br/>call local emergency number/]
    S -- personal diagnosis<br/>or dosage request --> E2[/Polite refusal<br/>ask a clinician/]
    S -- allowed --> R

    subgraph RET [Hybrid retrieval]
        R[Embed query] --> R1[Dense search<br/>cosine similarity, top 50]
        R --> R2[BM25 keyword search, top 50]
        R1 --> RRF[Reciprocal rank fusion]
        R2 --> RRF
        RRF --> TOP[Top 4 chunks]
    end

    TOP --> P[Build prompt<br/>numbered context passages<br/>+ strict system rules]
    P --> L[LLM<br/>Groq gpt-oss-20b or local Ollama]
    L --> CC[Remove citations that point to<br/>non-existent passages]
    CC --> I{Answer says<br/>INSUFFICIENT EVIDENCE?}
    I -- yes --> NE[/Show: not enough evidence/]
    I -- no --> SP[Split answer into claims<br/>one per sentence]

    subgraph VER [Claim verification, per claim]
        SP --> V1[Retrieve top 4 chunks<br/>for the claim]
        V1 --> V2[NLI model<br/>deberta-v3-small<br/>claim vs each chunk]
        V2 --> V3{Best score}
        V3 -- entailment >= 0.5 --> LS[Supported]
        V3 -- contradiction >= 0.5 --> LC[Contradicted]
        V3 -- otherwise --> LU[Unsupported]
    end

    LS --> OUT
    LC --> OUT
    LU --> OUT
    OUT[/Streamlit UI<br/>answer with citation badges,<br/>claim cards + evidence,<br/>source list, disclaimer/]
```

## 3. Online: checking a claim (tab "Check a health claim")

```mermaid
flowchart LR
    C([Pasted claim]) --> SP[Split into sentences<br/>min 4 words]
    SP --> RT[Retrieve evidence<br/>hybrid search]
    RT --> N[NLI entailment check]
    N --> L[Supported / Contradicted / Unsupported<br/>+ evidence snippet and source link]
```

## Module map

| Step | File |
|---|---|
| Download, parse, chunk, embed | `medassist/ingest.py` |
| Hybrid retrieval (dense + BM25 + RRF) | `medassist/retriever.py` |
| Safety gate and disclaimer | `medassist/safety.py` |
| LLM call (Groq or Ollama) | `medassist/llm.py` |
| Orchestration, citation cleanup | `medassist/pipeline.py` |
| Claim splitting and NLI verdicts | `medassist/verify.py` |
| User interface | `app.py` |
