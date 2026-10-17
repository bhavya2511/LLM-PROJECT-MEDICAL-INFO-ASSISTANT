import requests

from . import config


def chat(system: str, user: str, temperature: float = 0.1) -> str:
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    if config.LLM_BACKEND == "groq":
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
            json={"model": config.GROQ_MODEL, "messages": msgs, "temperature": temperature},
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    try:
        r = requests.post(
            f"{config.OLLAMA_URL}/api/chat",
            json={"model": config.OLLAMA_MODEL, "messages": msgs, "stream": False,
                  "options": {"temperature": temperature}},
            timeout=300,
        )
        r.raise_for_status()
    except requests.ConnectionError as e:
        raise RuntimeError("Ollama is not running. Install from https://ollama.com and run "
                           f"`ollama pull {config.OLLAMA_MODEL}`.") from e
    return r.json()["message"]["content"]
