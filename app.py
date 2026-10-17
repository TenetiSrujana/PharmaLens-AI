from __future__ import annotations

import io
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
DATA_PATH = APP_DIR / "data" / "adverse_events.csv"
DB_PATH = APP_DIR / "data" / "pharmalens_investigations.db"

st.set_page_config(
    page_title="PharmaLens AI | Health & Drug Safety Intelligence",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Theme ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root { --ink:#f1f5fb; --muted:#b8c5d8; --teal:#19d3bd; --blue:#72d5ff; --panel:#121d2d; --line:#2a3b52; }
html, body, [class*="css"], [data-testid="stAppViewContainer"] { font-family:'Inter',Arial,sans-serif !important; }
.stApp { background:#0b111b; color:var(--ink); font-size:16px; }
[data-testid="stHeader"] { background:rgba(11,17,27,.97); }
[data-testid="stSidebar"] { background:#101a29; border-right:1px solid var(--line); }
[data-testid="stSidebar"] * { color:#e5edf8; }
.block-container { padding-top:1.65rem; padding-bottom:3.2rem; max-width:1600px; }
h1,h2,h3,h4,h5,h6 { font-family:'Inter',Arial,sans-serif !important; font-style:normal !important; color:#f1f5fb !important; font-weight:750 !important; letter-spacing:-.35px; }
h1 { font-size:2.35rem !important; line-height:1.18 !important; }
h2 { font-size:1.75rem !important; }
h3 { font-size:1.4rem !important; }
h4 { font-size:1.2rem !important; }
p, li, label, .stMarkdown, .stCaption, [data-testid="stCaptionContainer"] { color:#d2dceb; }
p { font-size:1rem; line-height:1.7; }
[data-testid="stMetric"] { background:linear-gradient(145deg,#152236,#111a28); border:1px solid #2a3b52; border-radius:15px; padding:18px 20px; }
[data-testid="stMetricLabel"] { color:#c0cde0 !important; font-size:1rem !important; }
[data-testid="stMetricValue"] { color:#78d9ff !important; font-size:2rem !important; font-weight:750 !important; }
[data-testid="stMetricDelta"] { font-size:.9rem !important; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-color:#2a3b52 !important; border-radius:16px; }
.stButton>button, .stDownloadButton>button, [data-testid="stFormSubmitButton"]>button { min-height:44px; border-radius:10px; font-family:'Inter',Arial,sans-serif !important; font-size:1rem !important; line-height:1.35 !important; font-weight:700 !important; color:#f8fbff !important; background:#1a2b40 !important; border:1px solid #3a526d !important; padding:.65rem 1rem !important; white-space:normal !important; }
.stButton>button:hover, .stDownloadButton>button:hover, [data-testid="stFormSubmitButton"]>button:hover { background:#263e59 !important; border-color:#6d91b8 !important; color:#ffffff !important; }
.stButton>button[kind="primary"], .stDownloadButton>button[kind="primary"], [data-testid="stFormSubmitButton"]>button[kind="primary"] { background:linear-gradient(100deg,#1479dc,#00a990) !important; color:#ffffff !important; border:1px solid #20cdb8 !important; }
.stButton>button p, .stDownloadButton>button p, [data-testid="stFormSubmitButton"]>button p { color:#ffffff !important; font-size:1rem !important; font-weight:750 !important; }
/* Make form labels, placeholders and navigation readable against the dark theme. */
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label, .stSelectbox label, .stMultiSelect label, .stTextInput label, .stTextArea label, .stNumberInput label, .stCheckbox label, .stRadio label { color:#dce6f4 !important; font-size:.98rem !important; font-weight:600 !important; }
input, textarea, [data-baseweb="select"] > div { font-size:1rem !important; }
[data-baseweb="select"] *, [data-baseweb="input"] *, [data-baseweb="textarea"] * { color:#172335; }
[data-baseweb="tab-list"] { gap:8px; }
[data-baseweb="tab"] { background:#172438; border-radius:8px 8px 0 0; color:#e7eef9 !important; font-size:1rem !important; }
[data-baseweb="tab"] p { color:#e7eef9 !important; }
.small-muted { color:#bdcadd !important; font-size:1.03rem; line-height:1.65; }
.eyebrow { color:#27dfc5; font-size:.82rem; font-weight:800; letter-spacing:1.7px; text-transform:uppercase; margin-bottom:.35rem; }
.hero-title { font-family:'Inter',Arial,sans-serif !important; font-style:normal !important; font-weight:800 !important; color:#f2f6fc !important; font-size:clamp(2.1rem,3vw,3rem); line-height:1.18; letter-spacing:-1.1px; margin:.25rem 0 .75rem; }
.gradient { background:linear-gradient(100deg,#7bdcff,#7ce7ce); -webkit-background-clip:text; background-clip:text; color:transparent; }
.notice { background:#142338; border:1px solid #344c69; border-radius:12px; padding:14px 17px; color:#dce6f4; font-size:1rem; line-height:1.65; }
[data-testid="stDataFrame"] { font-size:.95rem; }
[data-testid="stDataFrame"] * { font-size:.92rem; }
[data-testid="stExpander"] summary p { color:#eaf1fa !important; font-size:1rem !important; font-weight:650 !important; }
footer {visibility:hidden}
@media(max-width:700px){.block-container{padding-left:1rem;padding-right:1rem}h1{font-size:1.9rem !important}}
</style>
""", unsafe_allow_html=True)

# ---------- Data helpers ----------
ALIASES = {
    "drug": ["generic_name", "drug_name", "drug", "medication", "product_name", "medicinal_product", "active_ingredient"],
    "reaction": ["reaction", "reaction_name", "event", "adverse_event", "pt", "preferred_term", "event_name", "side_effect"],
    "date": ["report_date", "date", "received_date", "event_date", "start_date", "case_date", "submission_date"],
    "country": ["country", "reporter_country", "country_name", "sender_country"],
    "serious": ["serious", "seriousness", "serious_flag", "is_serious", "serious_case"],
    "death": ["death", "patient_died", "fatal", "death_flag", "outcome_death"],
    "hospital": ["hospitalization", "hospitalised", "hospitalized", "hospitalization_flag", "hospital"],
    "life_threatening": ["life_threatening", "life-threatening", "lifethreatening", "life_threatening_flag"],
    "age": ["patient_age", "age", "age_years", "patientage"],
    "sex": ["sex", "gender", "patient_sex"],
    "report_id": ["report_id", "case_id", "case_number", "primaryid", "id", "safetyreportid"],
}
SERIOUS_TERMS = ("serious", "hospital", "death", "fatal", "life-threatening", "lifethreatening", "disabling", "congenital", "intervention")

def clean_col(x):
    return re.sub(r"[^a-z0-9]+", "_", str(x).strip().lower()).strip("_")

def truthy(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    s = series.astype(str).str.strip().str.lower()
    return s.isin(["1", "true", "yes", "y", "t", "serious", "death", "fatal", "hospitalized", "hospitalisation", "hospitalization"])

def find_column(df, key):
    cols = {clean_col(c): c for c in df.columns}
    for alias in ALIASES[key]:
        if clean_col(alias) in cols:
            return cols[clean_col(alias)]
    # Loose matching for messy exports
    for c in df.columns:
        n = clean_col(c)
        for alias in ALIASES[key]:
            a = clean_col(alias)
            if len(a) > 3 and (n == a or n.endswith("_" + a) or a in n):
                return c
    return None

@st.cache_data(show_spinner="Loading and preparing adverse-event reports…")
def load_data(path_string, mtime):
    path = Path(path_string)
    if not path.exists():
        return pd.DataFrame(), {}, "Dataset not found"
    try:
        raw = pd.read_csv(path, low_memory=False)
    except UnicodeDecodeError:
        raw = pd.read_csv(path, encoding="latin-1", low_memory=False)
    except Exception as exc:
        return pd.DataFrame(), {}, f"Could not read CSV: {exc}"
    raw.columns = [str(c).strip() for c in raw.columns]
    mapping = {k: find_column(raw, k) for k in ALIASES}
    df = raw.copy()
    df["_row_id"] = np.arange(1, len(df) + 1)

    def add_text(key, default="Unknown"):
        col = mapping.get(key)
        if col and col in df:
            s = df[col].astype("string").fillna(default).str.strip()
            s = s.replace({"": default, "nan": default, "None": default, "NULL": default})
            return s
        return pd.Series([default] * len(df), index=df.index, dtype="string")

    df["_drug"] = add_text("drug")
    df["_reaction"] = add_text("reaction")
    df["_country"] = add_text("country")
    df["_report_id"] = add_text("report_id", default="")
    date_col = mapping.get("date")
    df["_date"] = pd.to_datetime(df[date_col], errors="coerce", format="mixed") if date_col else pd.NaT

    serious_col = mapping.get("serious")
    if serious_col:
        df["_serious"] = truthy(df[serious_col])
    else:
        df["_serious"] = False
        for k in ("death", "hospital", "life_threatening"):
            c = mapping.get(k)
            if c:
                df["_serious"] |= truthy(df[c])
        # Only infer seriousness from a text outcome when no structured flags exist.
        if not any(mapping.get(k) for k in ("death", "hospital", "life_threatening")):
            outcome_cols = [c for c in raw.columns if any(t in clean_col(c) for t in ("outcome", "seriousness", "death", "hospital", "life_threat"))]
            for c in outcome_cols:
                vals = raw[c].astype(str).str.lower()
                df["_serious"] |= vals.apply(lambda v: any(term in v for term in SERIOUS_TERMS))

    death_col = mapping.get("death")
    if death_col:
        df["_death"] = truthy(df[death_col])
    else:
        df["_death"] = False
        for c in raw.columns:
            if "outcome" in clean_col(c) and "death" in clean_col(c):
                df["_death"] |= truthy(raw[c])
                df["_death"] |= raw[c].astype(str).str.lower().str.contains("death|fatal", regex=True, na=False)

    age_col = mapping.get("age")
    df["_age"] = pd.to_numeric(df[age_col], errors="coerce") if age_col else np.nan
    sex_col = mapping.get("sex")
    df["_sex"] = add_text("sex")
    df["_drug"] = df["_drug"].replace("Unknown", pd.NA)
    df["_reaction"] = df["_reaction"].replace("Unknown", pd.NA)
    # Rows remain in the dataset, but analysis views exclude rows without an identifiable drug/event.
    return df, mapping, None

def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""CREATE TABLE IF NOT EXISTS investigations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        drug TEXT NOT NULL,
        reaction TEXT NOT NULL,
        priority TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Open',
        notes TEXT DEFAULT '',
        created_at TEXT NOT NULL
    )""")
    conn.commit()
    return conn

def fmt_num(n):
    return f"{int(n):,}"

def pct(n, d):
    return f"{(100*n/d):.1f}%" if d else "—"

def theme_chart(fig, height=350):
    fig.update_layout(
        template="plotly_dark", height=height, margin=dict(l=8, r=8, t=45, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Arial, sans-serif", color="#e5edf8", size=14),
        title_font=dict(size=18, color="#f1f5fb"), legend_title_text="",
    )
    fig.update_xaxes(gridcolor="rgba(145,170,205,.10)", zerolinecolor="rgba(145,170,205,.12)")
    fig.update_yaxes(gridcolor="rgba(145,170,205,.10)", zerolinecolor="rgba(145,170,205,.12)")
    return fig

def evidence_table(df):
    return df.rename(columns={
        "_drug": "Drug", "_reaction": "Reported reaction", "_country": "Country",
        "_date": "Report date", "_serious": "Serious flag", "_death": "Death flag",
        "_age": "Age", "_sex": "Sex", "_report_id": "Report ID",
    })

def make_signals(data):
    valid = data.dropna(subset=["_drug", "_reaction"]).copy()
    if valid.empty:
        return pd.DataFrame()
    # Reporting odds ratio computed from report-level counts within the loaded file.
    total = len(valid)
    drug_counts = valid.groupby("_drug").size()
    reaction_counts = valid.groupby("_reaction").size()
    pair = valid.groupby(["_drug", "_reaction"]).size().rename("pair_reports").reset_index()
    pair["drug_reports"] = pair["_drug"].map(drug_counts)
    pair["reaction_reports"] = pair["_reaction"].map(reaction_counts)
    pair["other_drug_event"] = pair["reaction_reports"] - pair["pair_reports"]
    pair["drug_other_events"] = pair["drug_reports"] - pair["pair_reports"]
    pair["other_other"] = total - pair["pair_reports"] - pair["other_drug_event"] - pair["drug_other_events"]
    # Haldane-Anscombe correction protects against zero cells.
    a = pair["pair_reports"].astype(float) + .5
    b = pair["drug_other_events"].astype(float) + .5
    c = pair["other_drug_event"].astype(float) + .5
    d = pair["other_other"].astype(float) + .5
    pair["ror"] = (a*d)/(b*c)
    pair["log_ror_se"] = np.sqrt(1/a + 1/b + 1/c + 1/d)
    pair["ror_ci_low"] = np.exp(np.log(pair["ror"]) - 1.96*pair["log_ror_se"])
    pair["ror_ci_high"] = np.exp(np.log(pair["ror"]) + 1.96*pair["log_ror_se"])
    pair["serious_reports"] = valid.groupby(["_drug", "_reaction"])["_serious"].sum().values if False else 0
    serious = valid.groupby(["_drug", "_reaction"])["_serious"].sum().rename("serious_reports").reset_index()
    pair = pair.drop(columns=["serious_reports"], errors="ignore").merge(serious, on=["_drug", "_reaction"], how="left")
    pair["screening_flag"] = np.where((pair["pair_reports"] >= 3) & (pair["ror"] > 1) & (pair["ror_ci_low"] > 1), "Elevated reporting", "Review")
    pair["priority_score"] = (np.log1p(pair["pair_reports"]) * np.log1p(pair["ror"].clip(lower=0)) * (1 + pair["serious_reports"] / pair["pair_reports"].clip(lower=1))).round(3)
    return pair.sort_values(["priority_score", "pair_reports"], ascending=False)

def safe_csv(df):
    return df.to_csv(index=False).encode("utf-8")

def header(kicker, title, subtitle):
    st.markdown(f'<div class="eyebrow">{kicker}</div><div class="hero-title">{title}</div><p class="small-muted">{subtitle}</p>', unsafe_allow_html=True)

# ---------- Sidebar ----------
def navigate_to(target):
    """Update navigation from a Streamlit callback before widgets are rebuilt."""
    st.session_state["nav_page"] = target
    st.query_params["page"] = target

with st.sidebar:
    st.markdown('<div class="eyebrow">PHARMACOVIGILANCE WORKSPACE</div>', unsafe_allow_html=True)
    st.markdown("## 💊 PharmaLens AI")
    st.caption("Drug Safety Intelligence & Signal Exploration")
    page_options = [
        "Home", "Overview", "Signal Lab", "Drug Explorer", "Reaction Explorer",
        "Time & Geography", "Investigation Queue", "Safety Copilot",
        "Data Quality"
    ]
    requested_page = st.query_params.get("page", "Home")
    if isinstance(requested_page, list):
        requested_page = requested_page[0] if requested_page else "Home"
    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = requested_page if requested_page in page_options else "Home"
    page = st.radio("NAVIGATION", page_options, key="nav_page", label_visibility="visible")
    st.divider()
    if DATA_PATH.exists():
        st.success(f"Dataset found · {DATA_PATH.stat().st_size / (1024*1024):.1f} MB")
    else:
        st.error("Dataset missing")
        st.caption("Place adverse_events.csv inside the project's data/ folder.")
    st.caption("Prototype · Not for clinical decisions")

if DATA_PATH.exists():
    data, column_map, data_error = load_data(str(DATA_PATH), DATA_PATH.stat().st_mtime)
else:
    data, column_map, data_error = pd.DataFrame(), {}, "Dataset not found"

if data_error or data.empty:
    header("GETTING STARTED", "Your safety workspace starts here.", "Connect the existing adverse-event CSV to load the analytics.")
    st.error(data_error or "The dataset is empty.")
    st.code("mkdir -p data\ncp ~/Desktop/Projects/PharmaLens-AI/data/adverse_events.csv data/adverse_events.csv")
    st.info("Save the CSV as `data/adverse_events.csv` relative to app.py, then refresh the app.")
    st.stop()

valid = data.dropna(subset=["_drug", "_reaction"]).copy()
if valid.empty:
    st.error("The CSV loaded, but the app could not identify drug and reaction columns.")
    st.write("Detected columns:", list(data.columns))
    st.write("Column mapping:", column_map)
    st.info("Use Data Quality to inspect the file, or update ALIASES near the top of app.py to match your CSV's column names.")
    st.stop()

signals = make_signals(valid)
n_reports = len(data)
n_valid = len(valid)
n_drugs = valid["_drug"].nunique()
n_reactions = valid["_reaction"].nunique()
serious_n = int(valid["_serious"].sum())
death_n = int(valid["_death"].sum())
date_min = data["_date"].min()
date_max = data["_date"].max()

# No global quick filters: each analysis module owns its relevant controls.
filtered = valid.copy()

# ---------- Overview ----------
# ---------- Home ----------
if page == "Home":
    # The home page intentionally has no analytics sidebar: it should feel like a landing page.
    st.markdown("""
    <style>
    /* Landing page uses the full browser width and predictable vertical rhythm. */
    [data-testid="stAppViewContainer"] [data-testid="stMainBlockContainer"],
    [data-testid="stAppViewContainer"] .main .block-container {
        padding-top: 0 !important; padding-bottom: 0 !important;
        max-width: none !important; width: 100% !important;
        padding-left: 0 !important; padding-right: 0 !important; margin: 0 !important;
    }
    [data-testid="stHeader"] {background:rgba(12,16,25,.96);}
    [data-testid="stMainBlockContainer"] .stVerticalBlock {gap:0.65rem;}
    .home-nav {
        height:52px; box-sizing:border-box; display:flex; align-items:center;
        justify-content:space-between; padding:0 4.7vw;
        border-bottom:1px solid rgba(112,145,185,.12); background:#0d1119;
        margin:0;
    }
    .home-brand {font-family:'Inter',Arial,sans-serif;font-weight:800;font-size:20px;color:#f1f5fb;}
    .home-brand span {color:#00d2b2;}
    .home-dot {color:#00d2b2;margin-right:9px;text-shadow:0 0 12px #00d2b2;}

    /* SECTION 1: a complete landing screen, with the copy and metrics grouped centrally. */
    .home-hero {
        width:100%; min-height:calc(100svh - 52px); box-sizing:border-box;
        padding:clamp(46px,7vh,84px) 24px clamp(48px,8vh,90px);
        text-align:center; display:flex; flex-direction:column; align-items:center;
        justify-content:center; background-color:#111725;
        background-image:linear-gradient(rgba(94,143,190,.075) 1px,transparent 1px),
        linear-gradient(90deg,rgba(94,143,190,.075) 1px,transparent 1px),
        radial-gradient(ellipse at 50% 10%,rgba(68,68,150,.20),transparent 58%);
        background-size:46px 46px,46px 46px,auto;
    }
    .home-eyebrow {display:inline-block;border:1px solid rgba(25,211,189,.32);border-radius:28px;padding:10px 18px;background:rgba(25,211,189,.09);color:#a5f7e9;font-size:13px;font-weight:750;}
    .home-title {font-family:Georgia,"Times New Roman",serif;font-size:clamp(42px,4vw,62px);line-height:1.13;letter-spacing:-1.1px;font-weight:700;font-style:italic;margin:34px auto 22px;color:#f1f5fb;width:100%;max-width:1120px;text-align:center;}
    .home-gradient {background:linear-gradient(100deg,#6fd5ff 7%,#8caeff 52%,#70efb5 96%);-webkit-background-clip:text;background-clip:text;color:transparent;white-space:normal;}
    .home-intro {font-size:16px;line-height:1.9;color:#c5d1e2;max-width:700px;margin:0 auto;}
    .home-intro strong {color:#e2e7f2;}
    .home-stat-wrap {display:flex;justify-content:center;gap:clamp(24px,4.5vw,76px);margin-top:42px;flex-wrap:wrap;}
    .home-stat {display:flex;flex-direction:column;gap:5px;min-width:90px;}
    .home-stat strong {font-family:'Inter',Arial,sans-serif;font-size:32px;font-weight:800;color:#78d9ff;}
    .home-stat span {font-size:13px;color:#bdcadd;}

    /* SECTION 2: title + form together fill the next viewport. The workspace starts below it. */
    .home-section {box-sizing:border-box;background:#0c121d;border-top:1px solid rgba(130,164,210,.12);}
    .home-wellness-heading {
        min-height:30svh; padding:28px clamp(20px,6vw,90px) 18px;
        display:flex; flex-direction:column; align-items:center; justify-content:center;
    }
    .home-section-title {font-family:'Inter',Arial,sans-serif;font-style:normal;text-align:center;font-size:clamp(30px,3.5vw,42px);font-weight:800;margin:12px 0 14px;color:#f1f5fb;letter-spacing:-.8px;}
    .home-section-copy {text-align:center;color:#aebdd1;font-size:16px;line-height:1.85;max-width:760px;margin:0 auto;}
    [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stForm"]) {
        box-sizing:border-box; min-height:calc(70svh - 22px);
        margin:0 clamp(18px,6vw,90px) 0 !important;
        padding:24px 26px 24px; display:flex; flex-direction:column; justify-content:center;
        background:#0c121d; border:1px solid #26364a; border-radius:18px;
    }
    [data-testid="stForm"] {background:#101a29;border:1px solid #26364a;border-radius:18px;padding:24px 24px 20px;}
    [data-testid="stForm"] [data-testid="stWidgetLabel"] p {font-size:14px!important;}
    [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stForm"]) h3 {margin-top:0;}
    [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stForm"]) + div {margin-top:0;}

    /* SECTION 3: a clear workspace landing section, with purposeful cards and real navigation actions. */
    .home-workspace-heading {
        min-height:32svh; padding:clamp(36px,5vh,58px) clamp(20px,6vw,90px) 18px;
        display:flex; flex-direction:column; align-items:center; justify-content:center;
        background:radial-gradient(ellipse at 50% 20%,rgba(42,91,150,.13),transparent 65%);
    }
    .home-feature-spacer {height:clamp(18px,3vh,34px);min-height:18px;}
    .home-card {
        min-height:245px; box-sizing:border-box; display:flex; flex-direction:column;
        justify-content:flex-start; align-items:flex-start; gap:12px;
        background:linear-gradient(145deg,rgba(25,42,64,.96),rgba(14,24,39,.98));
        border:1px solid #2a3b52; border-radius:18px; padding:26px 25px 24px;
        box-shadow:0 12px 32px rgba(0,0,0,.10); transition:border-color .2s ease,transform .2s ease;
    }
    .home-card:hover {border-color:rgba(42,211,192,.55);transform:translateY(-3px);}
    .home-feature-icon {width:44px;height:44px;display:flex;align-items:center;justify-content:center;
        border-radius:13px;background:rgba(25,211,189,.10);border:1px solid rgba(25,211,189,.20);font-size:22px;}
    .home-feature-kicker {font-size:10px;letter-spacing:1.6px;font-weight:850;color:#35dfc9;text-transform:uppercase;margin-top:2px;}
    .home-card .home-feature-copy {max-width:36ch;}
    .home-feature-title {font-size:19px;font-weight:800;color:#f1f5fb;margin:0 0 3px;letter-spacing:-.25px;}
    .home-feature-copy {font-size:14px;line-height:1.75;color:#bdcadd;margin:0;}
    .home-feature-action {margin-top:14px;}
    .home-feature-action [data-testid="stButton"] button {width:100%;min-height:42px;border:1px solid #2b4964;background:#1a2d43;color:#eaf5ff;border-radius:10px;font-weight:750;transition:all .2s ease;}
    .home-feature-action [data-testid="stButton"] button:hover {border-color:#23cdb8;background:#173b45;color:#fff;}
    .home-divider {height:1px;background:#26364a;margin:28px 0 0;}
    .home-footer {border-top:1px solid #202a3b;background:#0c1018;padding:22px 5vw;color:#8291aa;font-size:12px;display:flex;justify-content:space-between;}
    @media(max-width:700px) {
        [data-testid="stAppViewContainer"] [data-testid="stMainBlockContainer"],
        [data-testid="stAppViewContainer"] .main .block-container {padding-top:0!important;}
        .home-nav {height:52px;padding:0 18px;}
        .home-nav>div:last-child {font-size:9px!important;text-align:right;}
        .home-hero {min-height:calc(100svh - 52px);padding:42px 18px 48px;}
        .home-title {font-size:clamp(35px,8.5vw,52px);margin:28px auto 18px;letter-spacing:-.7px;}
        .home-gradient {white-space:normal;}
        .home-intro {font-size:14px;line-height:1.75;}
        .home-stat-wrap {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px 12px;max-width:360px;margin:30px auto 0;}
        .home-stat strong {font-size:28px;}
        .home-stat span {font-size:11px;}
        .home-wellness-heading {min-height:28svh;padding:22px 18px 12px;}
        .home-section-title {font-size:28px;}
        .home-section-copy {font-size:14px;line-height:1.7;}
        [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stForm"]) {min-height:calc(72svh - 10px);margin:0 12px!important;padding:16px 12px;}
        [data-testid="stForm"] {padding:16px 12px;}
        .home-workspace-heading {min-height:30svh;padding:34px 18px 16px;}
        .home-feature-spacer {height:18px;min-height:0;}
        .home-card {min-height:220px;padding:20px;}
        .home-feature-title {font-size:17px;}
        .home-feature-copy {font-size:13px;}
        .home-footer {gap:12px;flex-wrap:wrap;}
    }
    </style>
    """, unsafe_allow_html=True)

    home_report_count = f"{n_reports/1000:.0f}K+" if n_reports >= 1000 else str(n_reports)
    home_drug_count = fmt_num(n_drugs)
    home_reaction_count = f"{n_reactions/1000:.1f}K+" if n_reactions >= 1000 else str(n_reactions)
    st.markdown(f"""
    <div class="home-nav">
      <div class="home-brand"><span class="home-dot">●</span>Pharma<span>Lens AI</span></div>
      <div style="font-size:13px;font-weight:800;color:#27dfc5;">HEALTH INTELLIGENCE · DRUG SAFETY</div>
    </div>
    <section class="home-hero">
      <div class="home-eyebrow">🌍 AI Health Intelligence — For Every Human on Earth</div>
      <div class="home-title">Health intelligence.<br><span class="home-gradient">Safer, better-informed decisions.</span></div>
      <p class="home-intro"><strong>PharmaLens AI</strong> combines practical wellness education with explainable drug-safety analytics. Review everyday health habits, explore real adverse-event reports, and investigate reporting patterns with clear evidence and transparent limitations.</p>
      <div class="home-stat-wrap">
        <div class="home-stat"><strong>{home_report_count}</strong><span>Reports in your dataset</span></div>
        <div class="home-stat"><strong>{home_drug_count}</strong><span>Identified medicines</span></div>
        <div class="home-stat"><strong>{home_reaction_count}</strong><span>Reported reactions</span></div>
        <div class="home-stat"><strong>9</strong><span>Research modules</span></div>
      </div>
    </section>
    """, unsafe_allow_html=True)

    st.markdown('<section class="home-section home-wellness-heading"><div class="eyebrow" style="text-align:center;">YOUR PERSONAL WELLNESS CHECK-IN</div><h2 class="home-section-title">Small habits. Better-informed choices.</h2><p class="home-section-copy">Answer a few optional lifestyle questions to receive practical, general wellness suggestions. This is a habit reflection tool, not a biological-age test or medical diagnosis.</p></section>', unsafe_allow_html=True)

    # Form submits once and only then shows recommendations.
    with st.container(border=True):
        st.markdown("### 🌿 Your healthy-habits check-in")
        st.caption("Your answers are used in this session to create suggestions. They are not saved to the drug-safety database.")
        with st.form("home_wellness_assessment"):
            a1,a2,a3 = st.columns(3)
            sleep = a1.selectbox("Typical sleep per night", ["Less than 5 hours","5–6 hours","7–9 hours","More than 9 hours","Varies a lot"])
            activity = a2.selectbox("Physical activity", ["Rarely","1–2 days per week","3–4 days per week","5+ days per week"])
            nutrition = a3.selectbox("Usual eating pattern", ["Often irregular","Mixed / varies","Usually balanced","Prefer not to say"])
            a4,a5,a6 = st.columns(3)
            stress = a4.selectbox("Stress lately", ["Low","Manageable","Often high","Overwhelming"])
            hydration = a5.selectbox("Hydration through the day", ["Often forget","Somewhat consistent","Usually consistent"])
            screen = a6.selectbox("Screen-free wind-down before sleep", ["Rarely","Sometimes","Usually"])
            a7,a8 = st.columns(2)
            smoking = a7.selectbox("Tobacco / nicotine", ["No","Yes","Prefer not to say"])
            checkups = a8.selectbox("Preventive health check-ups", ["Up to date","Due / unsure","Prefer not to say"])
            submitted = st.form_submit_button("✨ Build my habit recommendations", type="primary", use_container_width=True)

    if submitted:
        recs=[]
        if sleep in ["Less than 5 hours","5–6 hours","Varies a lot"]:
            recs.append(("Sleep routine","Try a consistent sleep and wake time. If sleep problems persist or affect daily life, discuss them with a healthcare professional.","High"))
        elif sleep == "More than 9 hours":
            recs.append(("Sleep pattern","Sleep needs vary. If you regularly need unusually long sleep or still feel exhausted, consider discussing it with a clinician.","Medium"))
        else:
            recs.append(("Protect your sleep","Keep a regular sleep schedule and a calming wind-down routine where practical.","Positive"))
        if activity in ["Rarely","1–2 days per week"]:
            recs.append(("Build movement gradually","Start with a manageable walk or movement break and increase gradually according to your ability. Any movement is a useful start.","High"))
        else:
            recs.append(("Keep movement sustainable","Maintain a routine you enjoy and include strength, balance, or mobility work appropriate to your ability.","Positive"))
        if nutrition in ["Often irregular","Mixed / varies"]:
            recs.append(("Make meals more consistent","When possible, aim for regular meals and a varied pattern with vegetables, fruit, whole grains, protein sources, and fibre.","Medium"))
        if stress in ["Often high","Overwhelming"]:
            recs.append(("Give stress a practical outlet","Try a short breathing break, a walk, journaling, or talking with someone you trust. If distress feels unmanageable, seek professional support.","High"))
        elif stress == "Manageable":
            recs.append(("Maintain recovery time","Protect small breaks and social connection, even on busy days.","Positive"))
        if hydration == "Often forget":
            recs.append(("Make hydration easier","Keep water visible or link a drink of water to an existing routine. Follow any fluid limits recommended by your clinician.","Medium"))
        if screen == "Rarely":
            recs.append(("Create a gentler bedtime transition","Try lowering brightness and setting aside a few minutes away from screens before bed if that works for you.","Medium"))
        if smoking == "Yes":
            recs.append(("Nicotine support","If you want to reduce or stop tobacco/nicotine use, a healthcare professional can help you explore evidence-based support options without judgement.","High"))
        if checkups == "Due / unsure":
            recs.append(("Preventive care reminder","Consider checking which routine screenings or vaccinations are recommended for your age and circumstances with a qualified healthcare professional.","Medium"))
        if not recs:
            recs.append(("Keep your foundations steady","Continue the habits that work for you and make changes gradually rather than chasing perfection.","Positive"))
        st.session_state["wellness_recommendations"] = recs

    if st.session_state.get("wellness_recommendations"):
        st.markdown("### Your practical next steps")
        st.caption("Suggestions are based on your answers, not a medical risk prediction.")
        recs=st.session_state["wellness_recommendations"]
        cols=st.columns(2)
        for i,(title,body,priority) in enumerate(recs):
            with cols[i%2]:
                with st.container(border=True):
                    st.markdown(f"**{title}**")
                    st.write(body)
                    if priority=="High":
                        st.caption("Suggested first step")
                    elif priority=="Positive":
                        st.caption("Keep building on this")
                    else:
                        st.caption("Optional next step")
        st.info("This check-in does not calculate biological age, diagnose a condition, or replace individual medical advice. If you have symptoms or a health concern, contact a qualified healthcare professional.")

    st.markdown('<section class="home-section home-workspace-heading"><div class="eyebrow" style="text-align:center;">DRUG-SAFETY WORKSPACE</div><h2 class="home-section-title">From reports to reviewable evidence.</h2><p class="home-section-copy">Three focused tools to explore report patterns, screen potential signals, and document investigations with evidence.</p></section>', unsafe_allow_html=True)
    st.markdown('<div class="home-feature-spacer"></div>', unsafe_allow_html=True)
    feature_cols = st.columns(3, gap="large")
    features = [
        ("📊", "REPORT ANALYTICS", "Explore reports", "Review report volume by medicine, reaction, reporting time, and country.", "Open overview", "Overview"),
        ("🧬", "SIGNAL SCREENING", "Screen drug-safety signals", "Inspect drug–reaction pairs, report counts, ROR estimates, and confidence intervals.", "Open Signal Lab", "Signal Lab"),
        ("🗂️", "INVESTIGATION WORKFLOW", "Document an investigation", "Save review notes, track investigation status, and export evidence for follow-up.", "Open investigation queue", "Investigation Queue"),
    ]
    for idx, (col, feature) in enumerate(zip(feature_cols, features)):
        icon, kicker, title, description, action, target = feature
        with col:
            st.markdown(f'<div class="home-card"><div class="home-feature-icon">{icon}</div><div class="home-feature-kicker">{kicker}</div><div class="home-feature-title">{title}</div><p class="home-feature-copy">{description}</p></div>', unsafe_allow_html=True)
            st.markdown('<div class="home-feature-action">', unsafe_allow_html=True)
            st.button(
                f"{action}  →",
                key=f"home_workspace_{idx}",
                use_container_width=True,
                on_click=navigate_to,
                args=(target,),
            )
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="home-divider"></div><div class="home-footer"><span>● PharmaLens AI</span><span>Evidence-aware health intelligence · Student research prototype</span></div>', unsafe_allow_html=True)

# ---------- Overview ----------
elif page == "Overview":
    header("DRUG SAFETY INTELLIGENCE", "See the signal. <span class='gradient'>Investigate the evidence.</span>", "An explainable pharmacovigilance workspace built around your adverse-event reports.",)
    st.markdown('<div class="notice">Important: spontaneous reports describe suspected events, not confirmed causes. Counts are not incidence rates, and a reporting signal is a screening lead that requires expert review.</div>', unsafe_allow_html=True)
    st.write("")
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Reports loaded", fmt_num(n_reports))
    c2.metric("Drugs identified", fmt_num(n_drugs))
    c3.metric("Reported reactions", fmt_num(n_reactions))
    c4.metric("Serious-flag reports", fmt_num(serious_n), pct(serious_n, n_valid))
    c5.metric("Death-flag reports", fmt_num(death_n), pct(death_n, n_valid))
    st.write("")
    left, right = st.columns([1.15, .85])
    with left:
        st.subheader("Most reported drugs")
        drug_counts = filtered["_drug"].value_counts().head(12).sort_values()
        fig = px.bar(x=drug_counts.values, y=drug_counts.index, orientation="h", labels={"x":"Reports","y":"Drug"}, title="Report volume by drug")
        st.plotly_chart(theme_chart(fig, 390), use_container_width=True)
    with right:
        st.subheader("Report seriousness")
        seriousness = pd.DataFrame({"Category":["Serious flag","No serious flag"],"Reports":[int(filtered["_serious"].sum()), int((~filtered["_serious"]).sum())]})
        fig = px.pie(seriousness, names="Category", values="Reports", hole=.66, title="Across loaded reports")
        fig.update_traces(textposition="inside", textinfo="percent")
        st.plotly_chart(theme_chart(fig, 390), use_container_width=True)
    left, right = st.columns(2)
    with left:
        st.subheader("Most common reported reactions")
        rc = filtered["_reaction"].value_counts().head(10).sort_values()
        fig = px.bar(x=rc.values, y=rc.index, orientation="h", labels={"x":"Reports","y":"Reaction"})
        st.plotly_chart(theme_chart(fig, 340), use_container_width=True)
    with right:
        st.subheader("Signal-screening leads")
        show = signals.head(10).copy()
        show = show.rename(columns={"_drug":"Drug","_reaction":"Reaction","pair_reports":"Reports","ror":"ROR","ror_ci_low":"95% CI lower","ror_ci_high":"95% CI upper","screening_flag":"Screen"})
        st.dataframe(show[["Drug","Reaction","Reports","ROR","95% CI lower","95% CI upper","Screen"]].round(2), use_container_width=True, hide_index=True)
        st.caption("ROR values are calculated only within the loaded dataset; interpretation depends on data coverage and report structure.")
    if data["_date"].notna().any():
        st.subheader("Report timeline")
        monthly = data.dropna(subset=["_date"]).assign(Month=lambda d:d["_date"].dt.to_period("M").astype(str)).groupby("Month").size().reset_index(name="Reports")
        fig = px.area(monthly, x="Month", y="Reports", markers=True, title="Reports by report date")
        st.plotly_chart(theme_chart(fig, 300), use_container_width=True)
    with st.expander("Dataset snapshot"):
        st.write(f"Date range parsed: **{date_min.date() if pd.notna(date_min) else 'not available'}** to **{date_max.date() if pd.notna(date_max) else 'not available'}**")
        st.write(f"Rows with both drug and reaction identified: **{n_valid:,} / {n_reports:,}**")
        st.write("Column mapping:", {k: str(v) if v else "not found" for k,v in column_map.items()})

# ---------- Signal Lab ----------
elif page == "Signal Lab":
    header("EXPLORATORY SIGNAL SCREENING", "Signal Lab", "Rank drug–reaction pairs using report counts and reporting odds ratios (ROR).")
    st.markdown('<div class="notice">This is exploratory disproportionality screening, not a validated regulatory signal-detection system. It cannot establish causality or patient-level risk. If your CSV contains a preselected subset of drugs, comparison estimates may be biased.</div>', unsafe_allow_html=True)
    a,b,c = st.columns(3)
    min_reports = a.number_input("Minimum reports for a pair", min_value=1, max_value=10000, value=3, step=1)
    min_ror = b.number_input("Minimum ROR to display", min_value=0.0, max_value=1000.0, value=1.0, step=.5)
    elevated_only = c.checkbox("Show only elevated screening leads", value=False)
    s = signals.copy()
    s = s[s["pair_reports"] >= min_reports]
    s = s[s["ror"] >= min_ror]
    if elevated_only:
        s = s[(s["ror_ci_low"] > 1) & (s["pair_reports"] >= 3)]
    st.metric("Pairs matching screen", fmt_num(len(s)))
    show = s.rename(columns={"_drug":"Drug","_reaction":"Reaction","pair_reports":"Pair reports","drug_reports":"Reports for drug","reaction_reports":"Reports for reaction","serious_reports":"Serious reports","ror":"ROR","ror_ci_low":"95% CI lower","ror_ci_high":"95% CI upper","screening_flag":"Screening status","priority_score":"Exploration score"})
    st.dataframe(show[["Drug","Reaction","Pair reports","Reports for drug","Reports for reaction","Serious reports","ROR","95% CI lower","95% CI upper","Screening status","Exploration score"]].round(3), use_container_width=True, hide_index=True, height=460)
    st.download_button("⬇ Download signal-screen results (CSV)", safe_csv(show), "pharmalens_signal_screen.csv", "text/csv", type="primary")
    if not s.empty:
        st.subheader("Signal landscape")
        fig = px.scatter(s, x="pair_reports", y="ror", size="serious_reports", color="_drug", hover_name="_reaction", log_y=True,
                         labels={"pair_reports":"Reports for drug–reaction pair","ror":"Reporting odds ratio (log scale)","_drug":"Drug"},
                         title="Pair volume vs. reporting odds ratio")
        st.plotly_chart(theme_chart(fig, 440), use_container_width=True)
        selected = st.selectbox("Inspect a pair", [f"{r['_drug']}  ·  {r['_reaction']}" for _,r in s.head(200).iterrows()])
        drug, reaction = selected.split("  ·  ",1)
        row = s[(s["_drug"]==drug)&(s["_reaction"]==reaction)].iloc[0]
        k1,k2,k3,k4 = st.columns(4)
        k1.metric("Pair reports", fmt_num(row["pair_reports"]))
        k2.metric("ROR", f'{row["ror"]:.2f}')
        k3.metric("95% CI", f'{row["ror_ci_low"]:.2f}–{row["ror_ci_high"]:.2f}')
        k4.metric("Serious-flag reports", fmt_num(row["serious_reports"]))
        evidence = valid[(valid["_drug"]==drug)&(valid["_reaction"]==reaction)]
        with st.expander("View supporting reports"):
            st.dataframe(evidence_table(evidence.head(500)), use_container_width=True, hide_index=True)
            st.caption(f"Showing at most 500 of {len(evidence):,} matching rows.")
        with st.form("create_signal_investigation"):
            title = st.text_input("Investigation title", value=f"Review: {drug} / {reaction}")
            priority = st.selectbox("Priority", ["High","Medium","Low"], index=0 if row["ror_ci_low"]>1 and row["pair_reports"]>=3 else 1)
            notes = st.text_area("Analyst notes", placeholder="Why should this pair be reviewed? What confounders or evidence should be checked?")
            if st.form_submit_button("＋ Add pair to investigation queue", type="primary"):
                conn = get_db()
                conn.execute("INSERT INTO investigations(title,drug,reaction,priority,status,notes,created_at) VALUES(?,?,?,?,?,?,?)",
                             (title.strip() or f"Review: {drug} / {reaction}", drug, reaction, priority, "Open", notes, datetime.now().isoformat(timespec="seconds")))
                conn.commit(); conn.close()
                st.success("Investigation saved to the local queue.")

# ---------- Drug Explorer ----------
elif page == "Drug Explorer":
    header("DRUG-LEVEL EXPLORATION", "Drug Explorer", "Compare report patterns and inspect the evidence behind a selected drug.")
    chosen = st.selectbox("Choose a drug", sorted(valid["_drug"].unique()), key="drug_explorer_choice")
    dd = valid[valid["_drug"]==chosen].copy()
    x1,x2,x3,x4 = st.columns(4)
    x1.metric("Reports", fmt_num(len(dd)))
    x2.metric("Unique reactions", fmt_num(dd["_reaction"].nunique()))
    x3.metric("Serious-flag reports", fmt_num(int(dd["_serious"].sum())), pct(int(dd["_serious"].sum()),len(dd)))
    x4.metric("Death-flag reports", fmt_num(int(dd["_death"].sum())), pct(int(dd["_death"].sum()),len(dd)))
    left,right = st.columns(2)
    with left:
        counts=dd["_reaction"].value_counts().head(15).sort_values()
        fig=px.bar(x=counts.values,y=counts.index,orientation="h",labels={"x":"Reports","y":"Reaction"},title=f"Top reactions · {chosen}")
        st.plotly_chart(theme_chart(fig,420),use_container_width=True)
    with right:
        by_country=dd["_country"].value_counts().head(12).sort_values()
        fig=px.bar(x=by_country.values,y=by_country.index,orientation="h",labels={"x":"Reports","y":"Country"},title="Reports by country")
        st.plotly_chart(theme_chart(fig,420),use_container_width=True)
    if dd["_date"].notna().any():
        monthly=dd.dropna(subset=["_date"]).assign(Month=lambda d:d["_date"].dt.to_period("M").astype(str)).groupby("Month").size().reset_index(name="Reports")
        fig=px.line(monthly,x="Month",y="Reports",markers=True,title="Timeline for selected drug")
        st.plotly_chart(theme_chart(fig,310),use_container_width=True)
    pair_signals=signals[signals["_drug"]==chosen].sort_values("pair_reports",ascending=False).head(100)
    st.subheader("Drug–reaction pairs")
    st.dataframe(pair_signals.rename(columns={"_reaction":"Reaction","pair_reports":"Reports","ror":"ROR","ror_ci_low":"95% CI lower","ror_ci_high":"95% CI upper","screening_flag":"Screen"})[["Reaction","Reports","ROR","95% CI lower","95% CI upper","screen"]].round(2) if "screen" in pair_signals.columns else pair_signals.rename(columns={"_reaction":"Reaction","pair_reports":"Reports","ror":"ROR","ror_ci_low":"95% CI lower","ror_ci_high":"95% CI upper","screening_flag":"Screening status"})[["Reaction","Reports","ROR","95% CI lower","95% CI upper","Screening status"]].round(2),use_container_width=True,hide_index=True)
    st.download_button("⬇ Export selected drug reports",safe_csv(evidence_table(dd)),"drug_report_evidence.csv","text/csv")
    with st.expander("Raw report evidence"):
        st.dataframe(evidence_table(dd.head(1000)),use_container_width=True,hide_index=True)
        st.caption(f"Showing up to 1,000 of {len(dd):,} rows.")

# ---------- Reaction Explorer ----------
elif page == "Reaction Explorer":
    header("EVENT-LEVEL EXPLORATION", "Reaction Explorer", "Trace a reported reaction across drugs, seriousness flags, and report records.")
    chosen_reaction = st.selectbox("Choose a reported reaction", sorted(valid["_reaction"].unique()), key="reaction_choice")
    rd = valid[valid["_reaction"]==chosen_reaction].copy()
    c1,c2,c3 = st.columns(3)
    c1.metric("Reports",fmt_num(len(rd)))
    c2.metric("Drugs associated",fmt_num(rd["_drug"].nunique()))
    c3.metric("Serious-flag reports",fmt_num(int(rd["_serious"].sum())),pct(int(rd["_serious"].sum()),len(rd)))
    bydrug=rd["_drug"].value_counts().head(15).sort_values()
    fig=px.bar(x=bydrug.values,y=bydrug.index,orientation="h",labels={"x":"Reports","y":"Drug"},title="Drugs with this reported reaction")
    st.plotly_chart(theme_chart(fig,400),use_container_width=True)
    pair=signals[signals["_reaction"]==chosen_reaction].sort_values("pair_reports",ascending=False)
    st.subheader("Pair-level screening context")
    if not pair.empty:
        pair_display = pair.rename(columns={"_drug":"Drug","pair_reports":"Pair reports","ror":"ROR","ror_ci_low":"95% CI lower","ror_ci_high":"95% CI upper","screening_flag":"Screening status"})
        display_cols = [c for c in ["Drug","Pair reports","ROR","95% CI lower","95% CI upper","Screening status"] if c in pair_display.columns]
        st.dataframe(pair_display[display_cols].round(2),use_container_width=True,hide_index=True)
    with st.expander("Matching report records"):
        st.dataframe(evidence_table(rd.head(1000)),use_container_width=True,hide_index=True)
    st.download_button("⬇ Export reaction evidence",safe_csv(evidence_table(rd)),"reaction_evidence.csv","text/csv")

# ---------- Time & Geography ----------
elif page == "Time & Geography":
    header("TEMPORAL & GEOGRAPHIC INTELLIGENCE", "When and where are reports submitted?", "Explore submission patterns without interpreting them as disease prevalence or geographic risk.")
    dated=filtered.dropna(subset=["_date"]).copy()
    left,right=st.columns(2)
    with left:
        st.subheader("Report volume over time")
        if dated.empty:
            st.info("No parseable date column was found. Check Data Quality.")
        else:
            freq=st.selectbox("Time aggregation",["Month","Quarter","Year"],index=0)
            if freq=="Month": dated["Period"]=dated["_date"].dt.to_period("M").astype(str)
            elif freq=="Quarter": dated["Period"]=dated["_date"].dt.to_period("Q").astype(str)
            else: dated["Period"]=dated["_date"].dt.year.astype("Int64").astype(str)
            ts=dated.groupby("Period").size().reset_index(name="Reports")
            fig=px.line(ts,x="Period",y="Reports",markers=True,title=f"Reports by {freq.lower()}")
            st.plotly_chart(theme_chart(fig,360),use_container_width=True)
    with right:
        st.subheader("Top reporting countries")
        cc=filtered["_country"].value_counts().head(15).sort_values()
        fig=px.bar(x=cc.values,y=cc.index,orientation="h",labels={"x":"Reports","y":"Country"})
        st.plotly_chart(theme_chart(fig,360),use_container_width=True)
    st.subheader("Country × drug matrix")
    top_c=filtered["_country"].value_counts().head(12).index
    top_d=filtered["_drug"].value_counts().head(12).index
    matrix=filtered[filtered["_country"].isin(top_c)&filtered["_drug"].isin(top_d)].pivot_table(index="_country",columns="_drug",values="_row_id",aggfunc="count",fill_value=0)
    if not matrix.empty:
        fig=px.imshow(matrix,aspect="auto",labels=dict(x="Drug",y="Country",color="Reports"),title="Report counts (top countries and drugs)")
        st.plotly_chart(theme_chart(fig,420),use_container_width=True)
    st.caption("Reporting volume is influenced by market size, reporting rules, access to healthcare, publicity, and data completeness. It is not a map of risk.")

# ---------- Investigation Queue ----------
elif page == "Investigation Queue":
    header("CASE MANAGEMENT", "Investigation Queue", "Save review tasks, assign priority, update status, and export an audit-friendly list.")
    conn=get_db()
    inv=pd.read_sql_query("SELECT * FROM investigations ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END, created_at DESC",conn)
    conn.close()
    if inv.empty:
        st.info("Your queue is empty. Add a drug–reaction pair from Signal Lab or create a manual investigation below.")
    else:
        a,b,c,d=st.columns(4)
        a.metric("Total cases",len(inv))
        b.metric("Open",int((inv["status"]=="Open").sum()))
        c.metric("In review",int((inv["status"]=="In review").sum()))
        d.metric("Closed",int((inv["status"]=="Closed").sum()))
        st.dataframe(inv,use_container_width=True,hide_index=True)
        case_id=st.selectbox("Select case to update",inv["id"].tolist(),format_func=lambda x:f"#{x} · {inv.loc[inv.id==x,'title'].iloc[0]}")
        selected=inv[inv.id==case_id].iloc[0]
        with st.form("update_investigation"):
            new_status=st.selectbox("Status",["Open","In review","Closed"],index=["Open","In review","Closed"].index(selected["status"]) if selected["status"] in ["Open","In review","Closed"] else 0)
            new_priority=st.selectbox("Priority",["High","Medium","Low"],index=["High","Medium","Low"].index(selected["priority"]) if selected["priority"] in ["High","Medium","Low"] else 1)
            new_notes=st.text_area("Analyst notes",value=selected["notes"] or "")
            u1,u2=st.columns(2)
            save=u1.form_submit_button("Save changes",type="primary")
            delete=u2.form_submit_button("Delete case")
            if save or delete:
                conn=get_db()
                if save:
                    conn.execute("UPDATE investigations SET status=?,priority=?,notes=? WHERE id=?",(new_status,new_priority,new_notes,int(case_id)))
                    st.success("Investigation updated.")
                if delete:
                    conn.execute("DELETE FROM investigations WHERE id=?",(int(case_id),))
                    st.warning("Investigation deleted.")
                conn.commit();conn.close();st.rerun()
        st.download_button("⬇ Export queue CSV",safe_csv(inv),"pharmalens_investigation_queue.csv","text/csv")
    st.divider()
    st.subheader("＋ Create manual investigation")
    with st.form("manual_investigation"):
        title=st.text_input("Title",placeholder="e.g. Review a cluster of reports")
        col1,col2=st.columns(2)
        drug=col1.selectbox("Drug",sorted(valid["_drug"].unique()),key="manual_drug")
        reaction=col2.selectbox("Reaction",sorted(valid["_reaction"].unique()),key="manual_reaction")
        col3,col4=st.columns(2)
        priority=col3.selectbox("Priority",["High","Medium","Low"])
        status=col4.selectbox("Initial status",["Open","In review","Closed"])
        notes=st.text_area("Notes / next steps")
        if st.form_submit_button("Create investigation",type="primary"):
            if not title.strip():
                st.error("Add a short title first.")
            else:
                conn=get_db()
                conn.execute("INSERT INTO investigations(title,drug,reaction,priority,status,notes,created_at) VALUES(?,?,?,?,?,?,?)",
                             (title.strip(),drug,reaction,priority,status,notes,datetime.now().isoformat(timespec="seconds")))
                conn.commit();conn.close();st.success("Investigation created.");st.rerun()

# ---------- Safety Copilot ----------
elif page == "Safety Copilot":
    header("EVIDENCE-GROUNDED ASSISTANT", "Safety Copilot", "Choose a question for a clear, dataset-backed answer, or enter a custom question the supported analysis can interpret.")
    st.markdown('<div class="notice">Answers are computed from the loaded CSV using transparent rules. This is not a general-purpose medical AI, does not browse medical literature, and cannot establish that a drug caused an event.</div>', unsafe_allow_html=True)
    question_options = [
        "Which medicines have the most reports?",
        "What are the most common reported reactions?",
        "How many reports have serious or death flags?",
        "Which drug–reaction pairs are the strongest screening leads?",
        "Which countries have the most reports?",
        "How do report counts change over time?",
        "What reactions are most reported for a selected medicine?",
        "Which medicines are reported with a selected reaction?",
        "Explain ROR and its confidence interval.",
        "What are the main limitations of this dataset?",
    ]
    chosen_question = st.selectbox("Choose a question", question_options, key="copilot_question_choice")
    drug_for_question = None
    reaction_for_question = None
    if chosen_question == "What reactions are most reported for a selected medicine?":
        drug_for_question = st.selectbox("Medicine", sorted(valid["_drug"].dropna().unique()), key="copilot_drug_choice")
    if chosen_question == "Which medicines are reported with a selected reaction?":
        reaction_for_question = st.selectbox("Reported reaction", sorted(valid["_reaction"].dropna().unique()), key="copilot_reaction_choice")
    custom_question = st.text_input("Or ask your own dataset question (optional)", placeholder="e.g. show serious reports for semaglutide")
    run_copilot = st.button("Generate answer", type="primary", use_container_width=True)
    if run_copilot:
        q = (custom_question.strip() or chosen_question).lower()
        using_preset = not custom_question.strip()
        if using_preset and chosen_question == "What reactions are most reported for a selected medicine?" and drug_for_question:
            st.markdown(f"### Reported reactions for {drug_for_question}")
            subset = valid[valid["_drug"] == drug_for_question]
            table = subset["_reaction"].value_counts().head(12).rename_axis("Reported reaction").reset_index(name="Reports")
            st.dataframe(table, use_container_width=True, hide_index=True)
            st.caption("Counts describe co-reported terms in the selected medicine's reports, not confirmed causation.")
        elif using_preset and chosen_question == "Which medicines are reported with a selected reaction?" and reaction_for_question:
            st.markdown(f"### Medicines reported with {reaction_for_question}")
            subset = valid[valid["_reaction"] == reaction_for_question]
            table = subset["_drug"].value_counts().head(12).rename_axis("Medicine").reset_index(name="Reports")
            st.dataframe(table, use_container_width=True, hide_index=True)
            st.caption("This is a report-count comparison, not a comparative safety or risk estimate.")
        elif any(t in q for t in ["limitation", "cannot claim", "causality", "cause", "incidence", "risk estimate"]):
            st.markdown("### What the dataset can and cannot tell you")
            st.write("The app can summarize submitted reports and screen drug–reaction reporting patterns. Spontaneous reports do not establish causality, incidence, or absolute risk because the number of exposed people is unknown. Reporting is affected by under-reporting, stimulated reporting, duplicates, missing fields, indication, co-medications, and the dataset's coverage.")
            st.caption("Interpret findings as review leads, not confirmed adverse reactions or a ranking of the safest/most dangerous medicines.")
        elif any(t in q for t in ["ror", "confidence interval", "disproportionality", "screening statistic"]):
            st.markdown("### Reporting odds ratio (ROR)")
            st.latex(r"ROR = \frac{a/b}{c/d} = \frac{ad}{bc}")
            st.write("Here, a is reports containing both the selected drug and reaction; b is reports for that drug with other reactions; c is reports for other drugs with the selected reaction; and d is reports for other drugs with other reactions.")
            st.latex(r"95\%\ CI = \exp\left(\ln(ROR) \pm 1.96\sqrt{\frac{1}{a}+\frac{1}{b}+\frac{1}{c}+\frac{1}{d}}\right)")
            st.caption("The app applies a 0.5 continuity correction when a cell is zero. ROR is exploratory and depends on dataset composition; it is not a causal or absolute-risk estimate.")
        elif any(t in q for t in ["most reports", "top drug", "which medicines", "highest report", "medicine has the most"]):
            st.markdown("### Medicines with the highest report volume")
            top = valid["_drug"].value_counts().head(10).rename_axis("Medicine").reset_index(name="Reports")
            st.dataframe(top, use_container_width=True, hide_index=True)
            st.caption("This ranks report counts in the loaded CSV, not drug danger or the likelihood of an adverse event.")
        elif any(t in q for t in ["common reported reactions", "most common reactions", "most reported reactions", "reported reactions"]):
            st.markdown("### Most common reported reactions")
            rc = valid["_reaction"].value_counts().head(10).rename_axis("Reported reaction").reset_index(name="Reports")
            st.dataframe(rc, use_container_width=True, hide_index=True)
            st.caption("These are reported terms. A report does not confirm that a medicine caused the reaction.")
        elif any(t in q for t in ["serious", "death", "fatal", "hospital"]):
            st.markdown("### Seriousness-related counts")
            x1, x2, x3 = st.columns(3)
            x1.metric("Serious-flag reports", fmt_num(int(valid["_serious"].sum())))
            x2.metric("Death-flag reports", fmt_num(int(valid["_death"].sum())))
            x3.metric("Reports loaded", fmt_num(len(valid)))
            st.caption("Flags depend on the columns and values available in the CSV. A missing flag does not prove an event was non-serious.")
        elif any(t in q for t in ["screening lead", "signal", "drug–reaction", "drug-reaction", "strongest"]):
            st.markdown("### Highest exploratory signal-screening leads")
            show = signals.head(15).rename(columns={"_drug":"Medicine", "_reaction":"Reported reaction", "pair_reports":"Pair reports", "ror":"ROR", "ror_ci_low":"95% CI lower", "ror_ci_high":"95% CI upper", "screening_flag":"Screening status"})
            st.dataframe(show[["Medicine", "Reported reaction", "Pair reports", "ROR", "95% CI lower", "95% CI upper", "Screening status"]].round(2), use_container_width=True, hide_index=True)
            st.caption("These are exploratory statistical leads. Review case details and alternative explanations before drawing conclusions.")
            with st.expander("Reviewer checklist"):
                st.write("1. Confirm the event definition and data coverage. 2. Check duplicates and missingness. 3. Review timing, indication, co-medications, and alternative explanations where available. 4. Validate against independent evidence. 5. Document uncertainty and escalate for expert review when appropriate.")
        elif any(t in q for t in ["countries", "country", "geograph", "global"]):
            st.markdown("### Most represented reporting countries")
            country_counts = valid["_country"].value_counts().head(10).rename_axis("Country").reset_index(name="Reports")
            st.dataframe(country_counts, use_container_width=True, hide_index=True)
            st.caption("Reporting volume is not geographic disease prevalence or risk. Reporting systems and dataset coverage differ by country.")
        elif any(t in q for t in ["time", "trend", "month", "year", "date", "change over time"]):
            dated = valid.dropna(subset=["_date"]).copy()
            if dated.empty:
                st.info("No parseable report-date column was detected in this CSV. Open Data Quality to inspect the detected columns.")
            else:
                dated["Month"] = dated["_date"].dt.to_period("M").astype(str)
                monthly = dated.groupby("Month").size().reset_index(name="Reports").tail(36)
                st.markdown("### Monthly report counts")
                st.dataframe(monthly, use_container_width=True, hide_index=True)
                fig = px.line(monthly, x="Month", y="Reports", markers=True, title="Reports by parsed report month")
                st.plotly_chart(theme_chart(fig, 330), use_container_width=True)
                st.caption("Changes may reflect reporting practices, exposure, or data coverage. They do not directly measure changes in risk.")
        else:
            st.warning("I couldn't map that custom wording to a supported analysis. Choose one of the question options above for a reliable answer, or try keywords such as medicine, reaction, serious, death, signal, ROR, country, date, or limitations.")
            st.markdown("**Supported question areas**")
            st.write("• Highest-report medicines  • Common reactions  • Serious/death flags  • Drug–reaction screening leads  • Countries  • Monthly trends  • Drug-specific reactions  • Reaction-associated medicines  • ROR explanation  • Dataset limitations")

# ---------- Data Quality ----------
elif page == "Data Quality":
    header("DATA TRANSPARENCY", "Data Quality & Coverage", "Understand what the CSV contains, what the app could parse, and where missingness limits interpretation.")
    st.metric("CSV rows",fmt_num(len(data)))
    quality=[]
    for key,label in [("_drug","Drug"),("_reaction","Reaction"),("_date","Date"),("_country","Country"),("_serious","Serious flag"),("_death","Death flag"),("_age","Age"),("_sex","Sex"),("_report_id","Report ID")]:
        s=data[key]
        missing=int(s.isna().sum()) if hasattr(s,"isna") else 0
        if key=="_report_id": missing=int((s.astype(str).str.len()==0).sum())
        quality.append({"Field":label,"Available":len(data)-missing,"Missing/blank":missing,"Completeness %":round(100*(len(data)-missing)/len(data),1) if len(data) else 0})
    qdf=pd.DataFrame(quality)
    st.dataframe(qdf,use_container_width=True,hide_index=True)
    fig=px.bar(qdf,x="Field",y="Completeness %",range_y=[0,100],title="Field completeness")
    st.plotly_chart(theme_chart(fig,330),use_container_width=True)
    st.subheader("Detected source columns")
    mapping_rows=[{"Concept":k.replace("_"," ").title(),"Detected column":str(v) if v else "Not detected"} for k,v in column_map.items()]
    st.dataframe(pd.DataFrame(mapping_rows),use_container_width=True,hide_index=True)
    st.subheader("Duplicate checks")
    report_id_col=column_map.get("report_id")
    if report_id_col:
        ids=data[report_id_col].dropna().astype(str)
        st.metric("Duplicate report IDs",fmt_num(int(ids.duplicated().sum())))
    else:
        st.info("No recognized report identifier column. Duplicate-case detection cannot be performed reliably.")
    st.subheader("Preview")
    st.dataframe(data.head(100),use_container_width=True,hide_index=True)
    st.download_button("⬇ Export cleaned analysis fields",safe_csv(evidence_table(valid)),"pharmalens_cleaned_analysis_rows.csv","text/csv")

st.divider()
st.caption("PharmaLens AI · Drug Safety Intelligence & Signal Exploration · Research prototype · Not for diagnosis, treatment, or regulatory decision-making.")

