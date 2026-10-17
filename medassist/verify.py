"""Claim-level verification: is each claim supported, contradicted, or unsupported by trusted text?

Uses retrieval + a small NLI cross-encoder (runs on CPU, free).
"""
import re
from functools import lru_cache

import numpy as np

from . import config


@lru_cache(maxsize=1)
def _nli():
    from sentence_transformers import CrossEncoder
    return CrossEncoder(config.NLI_MODEL)


def split_claims(text: str) -> list[str]:
    text = re.sub(r"\[\d+\]", "", text)
    sents = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [s.strip(" -*•") for s in sents if len(s.split()) >= 4]


def _softmax(x):
    e = np.exp(x - x.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)


def verify_claim(claim: str, retriever, k: int = config.TOP_K) -> dict:
    evidence = retriever.search(claim, k=k)
    pairs = [(e["text"], claim) for e in evidence]
    probs = _softmax(np.array(_nli().predict(pairs)))  # columns: contradiction, entailment, neutral
    best_e, best_c = int(probs[:, 1].argmax()), int(probs[:, 0].argmax())
    entail, contra = float(probs[best_e, 1]), float(probs[best_c, 0])
    if entail >= config.ENTAIL_THRESHOLD and entail >= contra:
        label, ev, conf = "Supported", evidence[best_e], entail
    elif contra >= config.CONTRADICT_THRESHOLD:
        label, ev, conf = "Contradicted", evidence[best_c], contra
    else:
        label, ev, conf = "Unsupported", evidence[best_e], 1 - max(entail, contra)
    return {"claim": claim, "label": label, "confidence": round(conf, 3), "evidence": ev}


def verify_text(text: str, retriever) -> list[dict]:
    return [verify_claim(c, retriever) for c in split_claims(text)]
