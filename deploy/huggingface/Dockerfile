FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces runs containers as user 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    LLM_BACKEND=groq \
    PYTHONUNBUFFERED=1

WORKDIR /home/user
RUN git clone --depth 1 https://github.com/bhavya2511/LLM-PROJECT-MEDICAL-INFO-ASSISTANT.git app
WORKDIR /home/user/app

# CPU-only torch keeps the image small; then the rest of the requirements
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Build the knowledge base and cache the NLI model at build time (takes several minutes, once)
RUN python -m medassist.ingest \
    && python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/nli-deberta-v3-small')"

EXPOSE 7860
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
