"""Download MedlinePlus health topics (NIH, public domain) and build the search index.

Usage: python -m medassist.ingest
"""
import datetime as dt
import html
import json
import re
import xml.etree.ElementTree as ET

import numpy as np
import requests

from . import config

XML_URL = "https://medlineplus.gov/xml/mplus_topics_{date}.xml"


def download_xml() -> bytes:
    """MedlinePlus publishes a dated XML file; walk back from today until one exists."""
    today = dt.date.today()
    for back in range(0, 14):
        d = today - dt.timedelta(days=back)
        url = XML_URL.format(date=d.isoformat())
        r = requests.get(url, timeout=60)
        if r.status_code == 200:
            print(f"Downloaded {url} ({len(r.content) / 1e6:.1f} MB)")
            return r.content
    raise RuntimeError("Could not find a MedlinePlus topics XML. See https://medlineplus.gov/xml.html")


def strip_html(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_topics(xml_bytes: bytes) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    topics = []
    for t in root.iter("health-topic"):
        if t.get("language") != "English":
            continue
        summary = t.findtext("full-summary") or ""
        text = strip_html(summary)
        if len(text.split()) < 30:
            continue
        topics.append({"title": t.get("title"), "url": t.get("url"), "text": text})
    return topics


def chunk_text(text: str, size: int = config.CHUNK_WORDS) -> list[str]:
    """Sentence-aware chunking up to ~size words."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, cur, n = [], [], 0
    for s in sentences:
        w = len(s.split())
        if cur and n + w > size:
            chunks.append(" ".join(cur))
            cur, n = [], 0
        cur.append(s)
        n += w
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def build_chunks(topics: list[dict]) -> list[dict]:
    out = []
    for t in topics:
        for c in chunk_text(t["text"]):
            out.append({"id": len(out), "title": t["title"], "url": t["url"],
                        "source": "MedlinePlus (NIH)", "text": c})
    return out


def main():
    from sentence_transformers import SentenceTransformer

    config.INDEX_DIR.mkdir(parents=True, exist_ok=True)
    xml_bytes = download_xml()
    (config.DATA_DIR / "topics.xml").write_bytes(xml_bytes)
    topics = parse_topics(xml_bytes)
    chunks = build_chunks(topics)
    print(f"{len(topics)} topics -> {len(chunks)} chunks")

    model = SentenceTransformer(config.EMBED_MODEL)
    texts = [f"{c['title']}: {c['text']}" for c in chunks]
    emb = model.encode(texts, batch_size=64, normalize_embeddings=True, show_progress_bar=True)
    np.save(config.INDEX_DIR / "embeddings.npy", emb.astype(np.float32))
    (config.INDEX_DIR / "chunks.json").write_text(json.dumps(chunks), encoding="utf-8")
    print("Index saved to", config.INDEX_DIR)


if __name__ == "__main__":
    main()
