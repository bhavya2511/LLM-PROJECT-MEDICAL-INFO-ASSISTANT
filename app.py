import html
import re

import streamlit as st

from medassist import pipeline, safety, verify

st.set_page_config(page_title="Medical Information Assistant", page_icon="🩺", layout="centered")

# Label -> (icon, css class, plain-language meaning). Icon + text + colour, never colour alone.
LABELS = {
    "Supported": ("✓", "ok", "A trusted source says this."),
    "Contradicted": ("✕", "bad", "A trusted source says the opposite."),
    "Unsupported": ("?", "unk", "Not found in the indexed sources. This does not mean it is false."),
}
ASK_EXAMPLES = ["What causes type 2 diabetes?", "What are the symptoms of asthma?",
                "What is high blood pressure?"]
CLAIM_EXAMPLES = ["Vitamin C cures the common cold.",
                  "Antibiotics are effective against the flu.",
                  "Regular exercise lowers blood pressure."]

st.markdown(
    """
<style>
  .block-container {padding-top: 2rem; max-width: 760px;}
  h1 {font-size: 1.9rem !important; margin-bottom: .1rem;}
  .subtitle {color:#4A5B6C; margin-bottom: 1rem; font-size: 1.02rem;}
  .banner {background:#FFF8E6; border:1px solid #F0D58C; color:#5C4300; border-radius:10px;
           padding:.6rem .9rem; font-size:.9rem; margin-bottom:1.2rem;}
  .card {background:#fff; border:1px solid #D9E2EA; border-radius:12px; padding:1rem 1.15rem;
         margin:.5rem 0 1rem; line-height:1.65; font-size:1.02rem;}
  .card.alert {border-color:#E3A6A6; background:#FFF4F4;}
  .card.notice {border-color:#F0D58C; background:#FFFBEF;}
  .cite {display:inline-block; background:#D6EFEA; color:#0B5A53; border-radius:6px; font-size:.72rem;
         font-weight:600; padding:0 .35rem; margin:0 .1rem; vertical-align:super; line-height:1.25;}
  .claim {background:#fff; border:1px solid #D9E2EA; border-left-width:6px; border-radius:10px;
          padding:.65rem .9rem; margin:.5rem 0 .2rem;}
  .claim.ok {border-left-color:#1B7F4B;} .claim.bad {border-left-color:#C0392B;}
  .claim.unk {border-left-color:#B7791F;}
  .tag {font-weight:700; font-size:.82rem; border-radius:999px; padding:.05rem .6rem; margin-right:.5rem;}
  .ok .tag {background:#DDF3E6; color:#14633B;} .bad .tag {background:#FBE3E0; color:#9B2C20;}
  .unk .tag {background:#FCEFD4; color:#8A5A0B;}
  .conf {color:#5B6B7B; font-size:.82rem;}
  .summary span {display:inline-block; border-radius:999px; padding:.15rem .75rem; margin:0 .4rem .4rem 0;
                 font-size:.85rem; font-weight:600;}
  .s-ok {background:#DDF3E6; color:#14633B;} .s-bad {background:#FBE3E0; color:#9B2C20;}
  .s-unk {background:#FCEFD4; color:#8A5A0B;}
  .src {border:1px solid #D9E2EA; background:#fff; border-radius:10px; padding:.5rem .8rem; margin:.35rem 0;
        font-size:.93rem;}
  .src b {color:#0B5A53;}
  .footer {color:#6A7A8A; font-size:.8rem; margin-top:2.2rem; border-top:1px solid #D9E2EA; padding-top:.8rem;}
  div[data-testid="stForm"] {border:none; padding:0; background:transparent;}
</style>
""",
    unsafe_allow_html=True,
)

st.title("🩺 Medical Information Assistant")
st.markdown('<div class="subtitle">Plain-language answers about health conditions, checked against '
            "NIH MedlinePlus. Every statement is labelled so you can see what is backed by evidence."
            "</div>", unsafe_allow_html=True)
st.markdown(f'<div class="banner" role="note"><b>Educational use only.</b> {html.escape(safety.DISCLAIMER)}'
            "</div>", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading the knowledge base (first start takes a moment)...")
def get_retriever():
    from medassist.retriever import Retriever
    return Retriever()


try:
    retriever = get_retriever()
except FileNotFoundError:
    st.error("The knowledge base has not been built yet. Run `python -m medassist.ingest` once, "
             "then reload this page.")
    st.stop()


def with_citations(text: str) -> str:
    """Escape model output, then turn [n] into small citation badges."""
    safe = html.escape(text).replace("\n", "<br>")
    return re.sub(r"\[(\d+)\]", r'<span class="cite" title="Source \1">\1</span>', safe)


def render_claims(claims: list[dict]):
    counts = {k: sum(c["label"] == k for c in claims) for k in LABELS}
    st.markdown(
        '<div class="summary">'
        f'<span class="s-ok">✓ {counts["Supported"]} supported</span>'
        f'<span class="s-bad">✕ {counts["Contradicted"]} contradicted</span>'
        f'<span class="s-unk">? {counts["Unsupported"]} unsupported</span></div>',
        unsafe_allow_html=True)
    for c in claims:
        icon, cls, meaning = LABELS[c["label"]]
        conf = "" if c["label"] == "Unsupported" else f'<span class="conf">{c["confidence"]:.0%} confidence</span>'
        st.markdown(
            f'<div class="claim {cls}"><span class="tag">{icon} {c["label"]}</span>{conf}<br>'
            f'{html.escape(c["claim"])}</div>', unsafe_allow_html=True)
        with st.expander("See the evidence"):
            e = c["evidence"]
            st.caption(meaning)
            st.write(e["text"])
            st.markdown(f"Source: [{e['title']}]({e['url']}) · {e['source']}")


def render_sources(sources: list[dict]):
    for i, s in enumerate(sources, 1):
        st.markdown(f'<div class="src"><span class="cite">{i}</span> <b>{html.escape(s["title"])}</b> · '
                    f'{html.escape(s["source"])} · <a href="{html.escape(s["url"])}" target="_blank" '
                    'rel="noopener">Read on MedlinePlus ↗</a></div>', unsafe_allow_html=True)


def _pick_example(target: str, run_flag: str, text: str):
    st.session_state[target] = text
    st.session_state[run_flag] = True


def example_buttons(examples: list[str], key: str, target: str):
    st.caption("Try an example:")
    cols = st.columns(len(examples))
    for col, ex in zip(cols, examples):
        col.button(ex, key=f"{key}-{ex}", use_container_width=True, on_click=_pick_example,
                   args=(target, f"run_{key}", ex))


def legend():
    with st.expander("What do the labels mean?"):
        for name, (icon, _, meaning) in LABELS.items():
            st.markdown(f"**{icon} {name}**: {meaning}")


tab_ask, tab_check = st.tabs(["💬 Ask about a condition", "🔍 Check a health claim"])

# ---------------------------------------------------------------- Ask
with tab_ask:
    with st.form("ask_form", clear_on_submit=False):
        question = st.text_input("Your question", key="q_input",
                                 placeholder="e.g. What causes type 2 diabetes?",
                                 help="Ask about a disease or condition: causes, symptoms, "
                                      "treatments, prevention.")
        submitted = st.form_submit_button("Ask", type="primary", use_container_width=True)
    example_buttons(ASK_EXAMPLES, "ask", "q_input")

    if submitted or st.session_state.pop("run_ask", False):
        q = st.session_state.get("q_input", "").strip()
        if not q:
            st.info("Type a question above, or pick an example.")
        else:
            with st.spinner("Finding trusted sources and checking each statement..."):
                try:
                    st.session_state["ask_result"] = (q, pipeline.ask(q, retriever))
                except Exception as e:  # network/key/model problems should not crash the page
                    st.session_state["ask_result"] = (q, {"error": str(e)})

    if "ask_result" in st.session_state:
        q, res = st.session_state["ask_result"]
        st.markdown(f"##### {html.escape(q)}")
        if "error" in res:
            st.error("Could not generate an answer. Check your Groq key in `.env` and your internet "
                     "connection, then try again.")
            with st.expander("Technical details"):
                st.code(res["error"])
        elif res["blocked"]:
            cls = "alert" if res["kind"] == "emergency" else "notice"
            title = "Please get help now" if res["kind"] == "emergency" else "I can't help with that"
            st.markdown(f'<div class="card {cls}" role="alert"><b>{title}</b><br>'
                        f'{html.escape(res["answer"])}</div>', unsafe_allow_html=True)
        elif "INSUFFICIENT EVIDENCE" in res["answer"].upper():
            st.markdown('<div class="card notice"><b>Not enough evidence</b><br>The trusted sources I '
                        "have do not answer this clearly. Try rephrasing, or ask a clinician."
                        "</div>", unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="card">{with_citations(res["answer"])}</div>',
                        unsafe_allow_html=True)
            st.markdown("##### How well is each statement supported?")
            legend()
            render_claims(res["claims"])
            st.markdown("##### Sources")
            render_sources(res["sources"])

# -------------------------------------------------------------- Check
with tab_check:
    st.write("Paste something you read or heard. I'll look for evidence for or against it.")
    with st.form("check_form"):
        claim = st.text_area("Health claim", key="c_input", height=90,
                             placeholder="e.g. Vitamin C cures the common cold.")
        check_submitted = st.form_submit_button("Check claim", type="primary", use_container_width=True)
    example_buttons(CLAIM_EXAMPLES, "check", "c_input")

    if check_submitted or st.session_state.pop("run_check", False):
        c = st.session_state.get("c_input", "").strip()
        if not c:
            st.info("Type or paste a claim above, or pick an example.")
        else:
            with st.spinner("Comparing against trusted sources..."):
                st.session_state["check_result"] = (c, verify.verify_text(c, retriever))

    if "check_result" in st.session_state:
        c, claims = st.session_state["check_result"]
        if not claims:
            st.info("Please enter a full sentence (at least four words) so it can be checked.")
        else:
            legend()
            render_claims(claims)
            st.caption("Evidence comes from MedlinePlus only. A result of Unsupported means the claim "
                       "was not found there, which is not proof that it is false.")

st.markdown('<div class="footer">Sources: NIH MedlinePlus (public domain). Answers are generated by an AI '
            "model from retrieved text and may contain mistakes. Always confirm with a qualified "
            "healthcare professional.</div>", unsafe_allow_html=True)
