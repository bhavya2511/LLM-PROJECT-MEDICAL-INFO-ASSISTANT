from medassist import ingest, pipeline, safety, verify


def test_safety_blocks_emergency_and_personal():
    assert safety.check("I have chest pain what do I do")["kind"] == "emergency"
    assert safety.check("How much ibuprofen should I take?")["kind"] == "personal"
    assert safety.check("What causes asthma?")["allowed"]


def test_chunking_respects_size():
    text = " ".join(f"This is sentence number {i} about health." for i in range(100))
    chunks = ingest.chunk_text(text, size=50)
    assert len(chunks) > 5 and all(len(c.split()) <= 60 for c in chunks)


def test_parse_topics():
    xml = (b'<health-topics><health-topic title="Asthma" url="http://x" language="English">'
           b'<full-summary>&lt;p&gt;' + b"Asthma is a disease of the airways. " * 10 +
           b'&lt;/p&gt;</full-summary></health-topic></health-topics>')
    t = ingest.parse_topics(xml)
    assert t[0]["title"] == "Asthma" and "<" not in t[0]["text"]


def test_split_claims_and_citation_cleaning():
    assert len(verify.split_claims("Asthma affects airways [1]. It is common in children [2].")) == 2
    assert "[9]" not in pipeline._clean_citations("Fact one [1]. Fact two [9].", 3)
