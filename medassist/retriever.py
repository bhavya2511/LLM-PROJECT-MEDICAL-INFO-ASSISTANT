import json
import re

import numpy as np
from rank_bm25 import BM25Okapi

from . import config


def _tok(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", s.lower())


class Retriever:
    """Hybrid retrieval: dense (bge) + BM25, fused with reciprocal rank fusion."""

    def __init__(self):
        from sentence_transformers import SentenceTransformer

        self.chunks = json.loads((config.INDEX_DIR / "chunks.json").read_text(encoding="utf-8"))
        self.emb = np.load(config.INDEX_DIR / "embeddings.npy")
        self.model = SentenceTransformer(config.EMBED_MODEL)
        self.bm25 = BM25Okapi([_tok(f"{c['title']} {c['text']}") for c in self.chunks])

    def search(self, query: str, k: int = config.TOP_K) -> list[dict]:
        q = self.model.encode(config.QUERY_PREFIX + query, normalize_embeddings=True)
        dense_rank = np.argsort(-(self.emb @ q))[:50]
        bm_rank = np.argsort(-self.bm25.get_scores(_tok(query)))[:50]
        scores: dict[int, float] = {}
        for ranking in (dense_rank, bm_rank):
            for r, idx in enumerate(ranking):
                scores[int(idx)] = scores.get(int(idx), 0.0) + 1.0 / (60 + r)
        top = sorted(scores, key=scores.get, reverse=True)[:k]
        return [self.chunks[i] for i in top]
