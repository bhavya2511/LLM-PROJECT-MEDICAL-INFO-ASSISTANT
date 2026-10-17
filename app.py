import streamlit as st

from medassist import pipeline, safety, verify

st.set_page_config(page_title="Medical Information Assistant", page_icon="🩺")
st.title("🩺 Medical Information Assistant")
st.caption(safety.DISCLAIMER)

BADGE = {"Supported": "🟢", "Contradicted": "🔴", "Unsupported": "🟡"}


@st.cache_resource
def get_retriever():
    from medassist.retriever import Retriever
    return Retriever()


try:
    retriever = get_retriever()
except FileNotFoundError:
    st.error("Index not found. Run `python -m medassist.ingest` first.")
    st.stop()

tab_ask, tab_check = st.tabs(["Ask about a condition", "Check a health claim"])


def show_claims(claims):
    for c in claims:
        st.markdown(f"{BADGE[c['label']]} **{c['label']}** ({c['confidence']:.0%}): {c['claim']}")
        with st.expander("Evidence"):
            e = c["evidence"]
            st.write(e["text"])
            st.caption(f"{e['source']} - [{e['title']}]({e['url']})")


with tab_ask:
    q = st.text_input("Question", placeholder="What causes type 2 diabetes?")
    if q:
        with st.spinner("Searching trusted sources..."):
            try:
                res = pipeline.ask(q, retriever)
            except RuntimeError as e:
                st.error(str(e))
                st.stop()
        if res["blocked"]:
            st.warning(res["answer"])
        else:
            st.markdown(res["answer"])
            if res["claims"]:
                st.subheader("Claim check")
                show_claims(res["claims"])
            st.subheader("Sources")
            for i, s in enumerate(res["sources"], 1):
                st.markdown(f"[{i}] [{s['title']}]({s['url']}) - {s['source']}")

with tab_check:
    claim = st.text_area("Paste a health claim", placeholder="Vitamin C cures the common cold.")
    if claim:
        with st.spinner("Verifying..."):
            show_claims(verify.verify_text(claim, retriever))
        st.caption("'Unsupported' means not found in the indexed sources, not necessarily false.")
