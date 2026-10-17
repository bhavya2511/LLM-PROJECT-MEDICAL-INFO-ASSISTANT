import re

from . import config, llm, safety, verify

SYSTEM = (
    "You are a medical education assistant. Answer ONLY using the numbered context passages. "
    "Write 3-6 short plain-language sentences. After each sentence cite the passage number like [1]. "
    "If the context does not contain the answer, reply exactly: INSUFFICIENT EVIDENCE. "
    "Never give personal diagnosis, treatment or dosage advice."
)


def _clean_citations(answer: str, n: int) -> str:
    """Drop citations pointing to passages that don't exist (hallucinated refs)."""
    return re.sub(r"\[(\d+)\]", lambda m: m.group(0) if 1 <= int(m.group(1)) <= n else "", answer)


def ask(question: str, retriever, verify_answer: bool = True) -> dict:
    gate = safety.check(question)
    if not gate["allowed"]:
        return {"blocked": True, "answer": gate["message"], "kind": gate["kind"],
                "sources": [], "claims": [], "disclaimer": safety.DISCLAIMER}

    sources = retriever.search(question, k=config.TOP_K)
    context = "\n\n".join(f"[{i}] ({s['title']}) {s['text']}" for i, s in enumerate(sources, 1))
    answer = llm.chat(SYSTEM, f"Context:\n{context}\n\nQuestion: {question}")
    answer = _clean_citations(answer, len(sources))

    claims = []
    if verify_answer and "INSUFFICIENT EVIDENCE" not in answer.upper():
        claims = verify.verify_text(answer, retriever)
    return {"blocked": False, "answer": answer, "sources": sources, "claims": claims,
            "disclaimer": safety.DISCLAIMER}
