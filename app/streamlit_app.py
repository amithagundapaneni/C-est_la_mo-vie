"""
C'est la mo-vie — Streamlit App
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

import streamlit as st

st.set_page_config(
    page_title="C'est la mo-vie",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from src.utils.poster import get_poster_url

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Mono:wght@300;400&family=Inter:wght@300;400&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: #0c0b09 !important;
    color: #d4c9b0;
}
[data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* ── TICKER ── */
.ticker {
    width: 100%;
    background: #c8a84b;
    overflow: hidden;
    white-space: nowrap;
    padding: 5px 0;
}
.ticker-inner {
    display: inline-block;
    animation: tick 35s linear infinite;
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    font-weight: 400;
    letter-spacing: 0.2em;
    color: #0c0b09;
    text-transform: uppercase;
}
@keyframes tick { from { transform: translateX(100vw); } to { transform: translateX(-100%); } }

/* ── HERO ── */
.hero {
    text-align: center;
    padding: 4rem 2rem 0;
    position: relative;
}
.hero-eyebrow {
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.4em;
    color: #c8a84b;
    text-transform: uppercase;
    margin-bottom: 1.2rem;
}
.hero-title {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: clamp(4rem, 10vw, 8rem);
    font-weight: 300;
    font-style: italic;
    color: #f0e8d6;
    line-height: 0.95;
    letter-spacing: -0.02em;
    margin-bottom: 1.4rem;
}
.hero-sub {
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    font-weight: 300;
    letter-spacing: 0.12em;
    color: #6b6050;
    text-transform: uppercase;
}

/* ── DIVIDER ── */
.rule {
    width: 100%;
    height: 1px;
    background: linear-gradient(90deg, transparent, #2a2318 30%, #2a2318 70%, transparent);
    margin: 2.5rem 0 0;
}

/* ── INPUT PANEL ── */
.input-panel {
    background: #100f0c;
    border-top: 2px solid #c8a84b;
    border-bottom: 1px solid #1e1c16;
    padding: 2.5rem 3rem 2rem;
    position: relative;
}
.panel-badge {
    position: absolute;
    top: -1px; right: 3rem;
    background: #c8a84b;
    color: #0c0b09;
    font-family: 'DM Mono', monospace;
    font-size: 0.55rem;
    letter-spacing: 0.25em;
    padding: 3px 12px;
    text-transform: uppercase;
}
.field-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.28em;
    color: #c8a84b;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.field-hint {
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    color: #3a3428;
    margin-top: 4px;
    font-weight: 300;
}

/* ── Streamlit widget overrides ── */
.stTextArea textarea, .stTextInput input {
    background: #0c0b09 !important;
    border: 1px solid #252018 !important;
    border-radius: 1px !important;
    color: #d4c9b0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 300 !important;
    line-height: 1.6 !important;
    caret-color: #c8a84b;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #c8a84b !important;
    box-shadow: none !important;
    outline: none !important;
}
label[data-testid="stWidgetLabel"] { display: none !important; }
.stSlider { padding-top: 0.2rem; }
.stSlider [data-baseweb="slider"] div[role="slider"] {
    background: #c8a84b !important;
    border-color: #c8a84b !important;
}
.stSlider [data-baseweb="slider"] div[data-testid="stThumbValue"] { color: #c8a84b !important; }
[data-baseweb="select"] > div {
    background: #0c0b09 !important;
    border: 1px solid #252018 !important;
    border-radius: 1px !important;
    color: #d4c9b0 !important;
}

/* ── CTA BUTTON ── */
.stButton > button {
    width: 100%;
    background: #c8a84b !important;
    border: none !important;
    color: #0c0b09 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.7rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.3em !important;
    text-transform: uppercase !important;
    padding: 1rem 2rem !important;
    border-radius: 1px !important;
    margin-top: 1.8rem;
    transition: opacity 0.2s;
}
.stButton > button:hover { opacity: 0.85; background: #c8a84b !important; }

/* ── RESULTS ── */
.results-header {
    font-family: 'Cormorant Garamond', serif;
    font-size: 0.75rem;
    font-weight: 400;
    font-style: italic;
    letter-spacing: 0.18em;
    color: #4a4030;
    text-transform: uppercase;
    text-align: center;
    padding: 2.5rem 0 2rem;
}

.card {
    background: #0f0e0b;
    border: 1px solid #1a1812;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s ease, transform 0.2s ease;
}
.card:hover {
    border-color: #c8a84b55;
    transform: translateY(-3px);
}
.card img {
    width: 100%;
    aspect-ratio: 2/3;
    object-fit: cover;
    display: block;
    filter: sepia(0.1) brightness(0.88) contrast(1.05);
    transition: filter 0.3s ease;
}
.card:hover img { filter: sepia(0) brightness(0.95) contrast(1.05); }

.card-corner {
    position: absolute;
    top: 10px; right: 10px;
    background: rgba(12,11,9,0.85);
    border: 1px solid #c8a84b55;
    padding: 3px 8px;
    font-family: 'DM Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 0.1em;
    color: #c8a84b;
}

.card-body { padding: 1rem 1rem 1.2rem; }
.card-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: #ede3cc;
    line-height: 1.25;
    margin-bottom: 0.3rem;
}
.card-meta {
    font-family: 'DM Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 0.1em;
    color: #3e3628;
    text-transform: uppercase;
    margin-bottom: 0.7rem;
}
.card-genre {
    font-family: 'DM Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 0.08em;
    color: #5a5040;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}
.match-track {
    height: 1px;
    background: #1e1c16;
    margin-bottom: 0.8rem;
    position: relative;
}
.match-fill {
    position: absolute;
    top: 0; left: 0;
    height: 1px;
    background: #c8a84b;
}
.card-overview {
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    font-weight: 300;
    color: #5a5040;
    line-height: 1.6;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.vibe-tag {
    display: inline-block;
    margin-top: 0.7rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.55rem;
    letter-spacing: 0.12em;
    color: #c8a84b;
    border-top: 1px solid #c8a84b44;
    padding-top: 0.5rem;
    width: 100%;
    text-transform: uppercase;
}

/* ── EXPANDER ── */
details { margin-top: 0.5rem; }
.stExpander {
    background: #0c0b09 !important;
    border: 1px solid #1a1812 !important;
    border-radius: 0 !important;
}
.stExpander summary {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.6rem !important;
    letter-spacing: 0.15em !important;
    color: #4a4030 !important;
    text-transform: uppercase !important;
}
.why-text {
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem;
    font-weight: 300;
    color: #8a7a60;
    line-height: 1.75;
    padding: 0.5rem 0;
}

/* ── EMPTY STATE ── */
.empty {
    text-align: center;
    padding: 5rem 2rem;
}
.empty-title {
    font-family: 'Cormorant Garamond', serif;
    font-style: italic;
    font-size: 2rem;
    font-weight: 300;
    color: #2a2318;
    margin-bottom: 0.8rem;
}
.empty-sub {
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.25em;
    color: #1e1c16;
    text-transform: uppercase;
}

/* ── FOOTER ── */
.footer {
    text-align: center;
    padding: 3rem 0 2rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.55rem;
    letter-spacing: 0.2em;
    color: #1e1c16;
    text-transform: uppercase;
}

/* ── SPINNER ── */
.stSpinner > div { border-top-color: #c8a84b !important; }

/* padding for inner columns */
.inner-pad { padding: 0 3rem; }
</style>
""", unsafe_allow_html=True)

# ── TICKER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ticker">
  <span class="ticker-inner">
    C'est la mo-vie &nbsp;·&nbsp; Now Showing &nbsp;·&nbsp;
    Scene 1 Take 1 &nbsp;·&nbsp; Lights Camera Action &nbsp;·&nbsp;
    Fade In &nbsp;·&nbsp; Fade Out &nbsp;·&nbsp; Roll &nbsp;·&nbsp;
    Admit One &nbsp;·&nbsp; Dream On &nbsp;·&nbsp; The End &nbsp;·&nbsp;
    C'est la mo-vie &nbsp;·&nbsp; Now Showing &nbsp;·&nbsp;
  </span>
</div>
""", unsafe_allow_html=True)

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-eyebrow">✦ Now Showing ✦</div>
  <div class="hero-title">C'est la mo-vie</div>
  <div class="hero-sub">Some nights just need the perfect movies</div>
  <div class="rule"></div>
</div>
""", unsafe_allow_html=True)

# ── ENGINE ────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_engine():
    from src.etl.pipeline import run_pipeline
    from src.models.embedder import build_embeddings
    from src.models.recommender import AfterglowRecommender, build_clusters
    df = run_pipeline()
    embeddings = build_embeddings(df)
    build_clusters(embeddings)
    return AfterglowRecommender(df, embeddings)

# ── INPUT PANEL ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="input-panel">
  <div class="panel-badge">Your Cinema Brief</div>
</div>
""", unsafe_allow_html=True)

_, mid, _ = st.columns([1, 10, 1])
with mid:
    col_l, col_r = st.columns(2, gap="large")

    with col_l:
        st.markdown('<div class="field-label">Favourite Movies</div>', unsafe_allow_html=True)
        fav_raw = st.text_area(
            "fav", label_visibility="collapsed",
            placeholder="La La Land, Past Lives, Zootopia…",
            height=100, key="fav"
        )
        st.markdown('<div class="field-hint">Separate titles with commas</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="field-label">What are you in the mood for?</div>', unsafe_allow_html=True)
        intent = st.text_area(
            "intent", label_visibility="collapsed",
            placeholder='"Something hopeful but not devastating"\n"Cozy rainy-day film"\n"Like Interstellar but lighter"',
            height=100, key="intent"
        )

    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        st.markdown('<div class="field-label">Recommendations</div>', unsafe_allow_html=True)
        top_k = st.slider("k", 3, 20, 9, label_visibility="collapsed")
    with c2:
        st.markdown('<div class="field-label">Max Runtime (min)</div>', unsafe_allow_html=True)
        runtime_choice = st.selectbox("rt", ["Any","90","100","120","150","180"], label_visibility="collapsed")
        max_runtime = None if runtime_choice == "Any" else int(runtime_choice)
    with c3:
        st.markdown('<div class="field-label">Min Rating</div>', unsafe_allow_html=True)
        min_rating = st.slider("mr", 0.0, 9.0, 5.0, 0.5, label_visibility="collapsed")

    recommend_btn = st.button("✦  Find my film  ✦")

# ── RESULTS ───────────────────────────────────────────────────────────────────
if recommend_btn:
    if not intent.strip():
        st.warning("Tell us what you feel like watching tonight.")
    else:
        with st.spinner("Searching the archive…"):
            engine = load_engine()
            favourites = [t.strip() for t in fav_raw.split(",") if t.strip()] if fav_raw else []
            results = engine.recommend(
                intent_text=intent,
                favourite_titles=favourites,
                top_k=top_k,
                max_runtime=max_runtime,
                min_rating=min_rating,
            )

        st.markdown(
            f'<div class="results-header">— {len(results)} films selected for you —</div>',
            unsafe_allow_html=True
        )

        _, mid2, _ = st.columns([1, 10, 1])
        with mid2:
            cols = st.columns(3, gap="large")
            for i, (_, movie) in enumerate(results.iterrows()):
                with cols[i % 3]:
                    poster_url = get_poster_url(movie.get("poster_path", ""))
                    score_pct  = int(min(movie["score"] * 100 + 40, 99))
                    year       = str(movie.get("release_date", ""))[:4]
                    runtime    = f"{int(movie['runtime'])} min" if movie.get("runtime", 0) > 0 else ""
                    rating     = f"★ {movie['vote_average']:.1f}" if movie.get("vote_average", 0) > 0 else ""
                    meta_parts = [p for p in [year, runtime, rating] if p]
                    genres     = " · ".join(str(movie.get("genres_text","")).split()[:3])
                    vibe       = movie.get("vibe", "")

                    st.markdown(f"""
<div class="card">
  <img src="{poster_url}" alt="{movie['title']}"
       onerror="this.src='https://via.placeholder.com/400x600/0c0b09/2a2318?text=No+Poster'" />
  <div class="card-corner">{score_pct}% match</div>
  <div class="card-body">
    <div class="card-title">{movie['title']}</div>
    <div class="card-meta">{" · ".join(meta_parts)}</div>
    <div class="card-genre">{genres}</div>
    <div class="match-track"><div class="match-fill" style="width:{score_pct}%"></div></div>
    <div class="card-overview">{movie.get('overview','')}</div>
    {"<div class='vibe-tag'>✦ " + vibe + "</div>" if vibe else ""}
  </div>
</div>
""", unsafe_allow_html=True)

                    with st.expander("Why this film?"):
                        st.markdown(
                            f'<div class="why-text">{movie["explanation"]}</div>',
                            unsafe_allow_html=True
                        )

else:
    st.markdown("""
<div class="empty">
  <div class="empty-title">What are you in the mood for?</div>
  <div class="empty-sub">Every mood has a movie</div>
</div>
""", unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
  C'est la mo-vie &nbsp;·&nbsp; A mood-aware cinema companion &nbsp;·&nbsp; 
</div>
""", unsafe_allow_html=True)