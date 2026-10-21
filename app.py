from pathlib import Path
import base64
import sqlite3
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st


ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
ASSET_DIR = ROOT / "assets"
DB_PATH = DATA_DIR / "wind_story.db"
YEARS = tuple(range(2021, 2026))

# Official source index used by the source boxes throughout the app.
SOURCE_LINKS_HTML = (
    '<div class="source-links"><b>数据来源：</b>'
    '<a href="http://www.shandong.gov.cn/" target="_blank" rel="noopener">山东省人民政府</a>'
    '<span> · </span>'
    '<a href="http://fgw.shandong.gov.cn/" target="_blank" rel="noopener">山东省发展和改革委员会</a>'
    '<span> · </span>'
    '<a href="http://nyj.shandong.gov.cn/" target="_blank" rel="noopener">山东省能源局</a>'
    '</div>'
)

st.set_page_config(page_title="风从海上来 | 山东海上风电交互平台", page_icon="🌊", layout="wide", initial_sidebar_state="expanded")


def sync_local_database():
    """将已核验的 CSV 快照写入本地 SQLite，供页面查询。"""
    energy_csv = pd.read_csv(DATA_DIR / "energy.csv")
    sites_csv = pd.read_csv(DATA_DIR / "wind_sites.csv")
    with sqlite3.connect(DB_PATH) as conn:
        energy_csv.to_sql("energy", conn, if_exists="replace", index=False)
        sites_csv.to_sql("wind_sites", conn, if_exists="replace", index=False)
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@st.cache_data
def load_data():
    # CSV is the portable source of truth; refresh the local SQLite snapshot on each app start.
    sync_local_database()
    with sqlite3.connect(DB_PATH) as conn:
        energy_db = pd.read_sql_query("SELECT * FROM energy ORDER BY year", conn)
        sites_db = pd.read_sql_query("SELECT * FROM wind_sites", conn)
    return energy_db, sites_db


energy, sites = load_data()
st.session_state.setdefault("year", 2024)


def page_background_style(asset):
    if not asset or asset.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        return "background:linear-gradient(135deg,#061824 0%,#0b3540 55%,#07171f 100%);"
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}[asset.suffix.lower()]
    encoded = base64.b64encode(asset.read_bytes()).decode("ascii")
    return (
        "background-image:linear-gradient(rgba(2,14,26,.48),rgba(2,14,26,.48)),"
        f"url(data:{mime};base64,{encoded});"
        "background-size:cover;background-position:center;background-attachment:fixed;"
        "background-repeat:no-repeat;"
    )


background_asset = ASSET_DIR / "hero.png"
page_background = page_background_style(background_asset)
sidebar_background = page_background


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;600;700;800&family=Noto+Serif+SC:wght@500;600;700&display=swap');
    :root { --ink:#eef4fa; --muted:#a9bfd4; --paper:#0a1f38; --panel:#0d2a4a; --sea:#0a2e4d; --deep:#041c33; --line:#cfb86a; --cyan:#c9a227; --orange:#c98a3e; --yellow:#d9b061; }
    .stApp { __PAGE_BACKGROUND__ color:#eef4fa; }
    .block-container { padding:1.35rem 2.8rem 3rem; max-width:1480px; }
    header[data-testid="stHeader"] { background:transparent !important; height:0 !important; }
    [data-testid="stToolbar"], [data-testid="stStatusWidget"], [data-testid="stDecoration"], #MainMenu, footer { display:none !important; visibility:hidden !important; }
    .stAppViewContainer { padding-top:0 !important; }
    [data-testid="stAppViewBlockContainer"] { padding-top:1rem !important; }
    [data-testid="stSidebar"] { __SIDEBAR_BACKGROUND__ background-color:rgba(3,16,38,.78) !important; background-blend-mode:multiply; border-right:1px solid rgba(190,176,100,.28); box-shadow:8px 0 28px rgba(0,18,27,.18); backdrop-filter:blur(8px); }
    [data-testid="stSidebar"] > div,
    [data-testid="stSidebar"] [data-testid="stSidebarContent"],
    [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { background:transparent !important; background-color:transparent !important; }
    [data-testid="stSidebar"] hr { border-color:rgba(190,168,96,.22); margin:1.1rem 0; }
    [data-testid="stSidebar"] input[type="radio"] { accent-color:#dfb568; }
    [data-testid="stSidebar"] * { font-family:'Manrope', sans-serif; }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label { color:#eef4fa !important; }
    [data-testid="collapsedControl"] { display:none !important; visibility:hidden !important; }
    [data-testid="collapsedControl"] * { display:none !important; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 { color:#f4f1e8 !important; font-family:'Noto Serif SC',serif; font-size:1.18rem; letter-spacing:.02em; margin:.55rem 0 .15rem; }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color:#a9bfd4 !important; font-size:.72rem; line-height:1.6; }
    [data-testid="stSidebar"] [data-testid="stRadio"] > label { color:#a9c4dc !important; font:600 .85rem 'Noto Serif SC',serif; letter-spacing:.06em; margin:.8rem 0 .45rem; }
    [data-testid="stSidebar"] .stRadio > div { gap:.42rem; }
    [data-testid="stSidebar"] .stRadio label { min-height:44px; box-sizing:border-box; padding:.66rem .78rem; border:1px solid transparent; border-left:3px solid transparent; border-radius:4px; background:rgba(3,16,38,.22); }
    [data-testid="stSidebar"] .stRadio label:hover { background:transparent; border-color:transparent; border-left-color:transparent; }
    [data-testid="stSidebar"] .stRadio label p { color:#e4eef6 !important; font-size:1.04rem; font-weight:600; }
    [data-testid="stSidebar"] .stRadio label:has(input:checked) { background:rgba(201,162,39,.20); border-color:rgba(217,176,97,.35); border-left-color:#e3c079; }
    [data-testid="stSidebar"] .stRadio label:has(input:checked) p { color:#ffffff !important; font-weight:800; }
    [data-testid="stSidebar"] [data-testid="stExpander"] { background:rgba(4,20,42,.58); border:1px solid rgba(196,168,92,.28); }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color:#a9c9c8 !important; }
    h1,h2,h3,h4,p,span,div { font-family:'Manrope', sans-serif; }
    h1,h2,h3,h4 { color:#eef4fa; }
    .mono { font:500 .68rem 'DM Mono',monospace; letter-spacing:.12em; text-transform:uppercase; }
    .eyebrow { color:var(--cyan); margin-bottom:.8rem; }
    .topbar { display:flex; justify-content:space-between; align-items:center; background:#0a1e38; color:#eef4fa; padding:.75rem 1rem; margin:-.3rem 0 1.4rem; min-height:58px; }
    .topbrand { display:flex; align-items:center; gap:.7rem; }
    .brand-mark { width:38px; height:38px; display:grid; place-items:center; }
    .topbrand strong { display:block; font-size:.92rem; letter-spacing:.02em; }
    .topbrand span { display:block; color:#8ba6bf; font-size:.68rem; margin-top:.12rem; }
    .top-actions { display:flex; align-items:center; gap:1rem; color:#9ab0c8; font-size:.72rem; }
    .top-status { display:inline-flex; align-items:center; gap:.35rem; padding:.3rem .55rem; border:1px solid #3a4a72; color:#e3cd8f; }
    .top-status i { width:6px; height:6px; border-radius:50%; background:#e0b768; display:inline-block; }
    .section-kicker { color:var(--orange); margin:2.2rem 0 .5rem; }
    .section-title { font-family:'Noto Serif SC',serif; color:#eef4fa; font-size:1.8rem; font-weight:700; margin:0 0 .85rem; }
    .section-copy { color:#c2d3df; line-height:1.8; max-width:800px; font-size:.95rem; }
    .metric-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:1.3rem 0 2rem; }
    .metric { background:var(--panel); border:1px solid var(--line); border-top:3px solid var(--cyan); padding:1rem 1.15rem 1.1rem; min-height:105px; }
    .metric:nth-child(3) { border-top-color:var(--orange); }
    .metric:nth-child(4) { border-top-color:var(--yellow); }
    .metric-label { color:var(--muted); font:.67rem 'DM Mono',monospace; letter-spacing:.06em; }
    .metric-value { color:var(--ink); font-size:1.72rem; font-weight:800; margin:.36rem 0 .12rem; }
    .metric-note { color:#8ea3b8; font-size:.72rem; }
    .story-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin:1rem 0 2rem; }
    .story-card { min-height:145px; padding:1.15rem; background:var(--panel); border:1px solid var(--line); }
    .story-card .num { color:var(--orange); font:.7rem 'DM Mono',monospace; }
    .story-card h4 { margin:.8rem 0 .35rem; font-family:'Noto Serif SC',serif; font-size:1.08rem; }
    .story-card p { color:var(--muted); font-size:.8rem; line-height:1.65; margin:0; }
    .chain { display:grid; grid-template-columns:repeat(4,1fr); gap:0; margin:1rem 0 2.2rem; }
    .chain-step { background:#0d2a4a; border-right:1px solid #33466b; padding:1.05rem 1.1rem; min-height:100px; }
    .chain-step:last-child { border-right:0; background:#123354; }
    .chain-step .num { color:var(--orange); font:.7rem 'DM Mono',monospace; }
    .chain-step strong { display:block; color:var(--ink); margin:.65rem 0 .28rem; }
    .chain-step span { color:var(--muted); font-size:.75rem; line-height:1.45; }
    .panel { background:rgba(10,28,52,.82); border:1px solid var(--line); padding:1.1rem 1.2rem; }
    .panel-title { color:var(--ink); font-family:'Noto Serif SC',serif; font-size:1.15rem; font-weight:700; margin-bottom:.2rem; }
    .panel-note { color:var(--muted); font-size:.76rem; line-height:1.55; margin-bottom:.7rem; }
    .storyline { background:#0d2a4a; border-left:3px solid var(--cyan); padding:.8rem 1rem; color:#8fb0c0; line-height:1.7; font-size:.82rem; }
    .source-box { background:#0d2a4a; border:1px dashed #4a5c80; padding:.9rem 1rem; color:#6b8499; font-size:.76rem; line-height:1.7; }
    .source-links { margin-top:.55rem; padding-top:.45rem; border-top:1px solid rgba(160,150,100,.24); color:#6b8499; }
    .source-links a { color:#3d7db0 !important; text-decoration:underline; text-underline-offset:2px; font-weight:700; }
    .source-links a:hover { color:#123d63 !important; }
    .metric-label,.metric-value,.metric-note,.panel-title,.panel-note,.story-card h4,.story-card p,.chain-step strong,.chain-step span { color:var(--ink); }
    .panel-note,.story-card p,.chain-step span { color:var(--muted); }
    .stButton > button { background:#123d63; color:#f2fbf9; border:1px solid #e0b768; border-radius:2px; font-weight:700; }
    .stButton > button:hover { background:#1a4a7a; color:#ffffff; border-color:#ecd69e; }
    .year-card { background:rgba(10,34,64,.25); border:1px solid rgba(196,162,88,.4); border-radius:14px; padding:1.2rem 1.4rem; }
    .year-card .big { font-size:2.4rem; font-weight:800; color:#e0b768; line-height:1.1; }
    .year-card .unit { font-size:.9rem; color:#9ab4c6; }
    .year-card .lbl { font:600 .68rem 'DM Mono',monospace; letter-spacing:.08em; color:#7fa8a2; margin-bottom:.3rem; }
    .year-card .row { display:flex; justify-content:space-between; border-top:1px dashed rgba(196,162,88,.3); padding:.5rem 0; color:#cfe0ea; font-size:.86rem; }
    .year-card .row b { color:#e0b768; }
    .status-tag { display:inline-block; font-size:.72rem; color:#bfd4e3; background:rgba(201,162,39,.18); border:1px solid rgba(201,162,39,.4); padding:.2rem .6rem; border-radius:12px; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color:#e3eef4 !important; }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color:#a9bfd4 !important; }
    [data-testid="stSidebar"] input + div, [data-testid="stSidebar"] [role="radiogroup"] label p { color:#e3eef4 !important; }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary { color:#e3eef4 !important; }
    .footer { border-top:1px solid var(--line); margin-top:3rem; padding-top:1rem; color:#7e97ad; font:.68rem 'DM Mono',monospace; }
    .ov-panel { background:rgba(6,22,44,.72); border:1px solid rgba(196,168,92,.38); padding:.5rem 1.1rem .95rem; margin:.9rem 0 1.5rem; }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.time-panel):not(:has(.ov-panel)){ background:rgba(6,22,44,.72); border:1px solid rgba(196,168,92,.38); border-radius:6px; padding:.4rem 1rem 1rem; margin:.9rem 0 1.5rem; }
    .ov-panel .ov-tag, [data-testid="stVerticalBlockBorderWrapper"]:has(.time-panel) .ov-tag { color:#e0bd6f; font:.66rem 'DM Mono',monospace; letter-spacing:.12em; text-transform:uppercase; }
    .ov-panel .ov-title, [data-testid="stVerticalBlockBorderWrapper"]:has(.time-panel) .ov-title { color:#ffffff; font-family:'Noto Serif SC',serif; font-size:1.3rem; font-weight:700; margin:.22rem 0 .55rem; }
    .ov-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }
    .ov-item .lbl { color:#a9c2d8; font-size:.74rem; letter-spacing:.03em; }
    .ov-item .val { color:#ffffff; font-size:1.62rem; font-weight:800; margin:.25rem 0 .15rem; }
    .ov-item .val em { color:#e0b768; font-style:normal; }
    .ov-item .note { color:#9fb6cd; font-size:.68rem; line-height:1.5; }
    .overview-time { background:rgba(6,22,44,.72); border:1px solid rgba(196,168,92,.38); padding:1.15rem 1.25rem 1.25rem; margin:1rem 0 1.4rem; }
    .overview-time-head { display:flex; justify-content:space-between; align-items:flex-end; gap:1rem; margin-bottom:.6rem; }
    .overview-time-title { color:#fff; font-family:'Noto Serif SC',serif; font-size:1.28rem; font-weight:700; }
    .overview-time-note { color:#9fb6cd; font-size:.74rem; line-height:1.55; max-width:520px; }
    .overview-insight { background:rgba(8,30,58,.52); border:1px solid rgba(196,162,88,.34); padding:1.15rem 1.2rem; min-height:100%; }
    .overview-insight .eyebrow { margin:0 0 .45rem; color:#e0bd6f; }
    .overview-insight h3 { color:#fff; font-family:'Noto Serif SC',serif; font-size:1.35rem; margin:.1rem 0 .85rem; }
    .overview-insight .big { color:#e0b768; font-size:2.45rem; font-weight:800; line-height:1.05; }
    .overview-insight .unit { color:#b8ccdc; font-size:.86rem; }
    .overview-insight .line { display:flex; justify-content:space-between; gap:1rem; border-top:1px dashed rgba(196,168,90,.28); padding:.55rem 0; color:#cce0ea; font-size:.8rem; }
    .overview-insight .line b { color:#fff; }
    .overview-alert { color:#dfc083; background:rgba(94,72,20,.28); border-left:3px solid #d9b061; padding:.7rem .85rem; margin-top:.8rem; font-size:.75rem; line-height:1.55; }
    .overview-summary-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:14px; margin:0 0 1.4rem; }
    .overview-summary { background:rgba(6,22,44,.66); border:1px solid rgba(196,168,92,.32); padding:1rem 1.15rem; }
    .overview-summary .tag { color:#e0bd6f; font:500 .65rem 'DM Mono',monospace; letter-spacing:.1em; text-transform:uppercase; }
    .overview-summary h3 { color:#fff; font-family:'Noto Serif SC',serif; font-size:1.05rem; margin:.35rem 0 .8rem; }
    .overview-summary .stats { display:grid; grid-template-columns:repeat(3,1fr); gap:.7rem; }
    .overview-summary .stats b { display:block; color:#e0b768; font-size:1.22rem; }
    .overview-summary .stats span { color:#a9c2d8; font-size:.69rem; line-height:1.4; }
    @media (max-width:900px) { .overview-summary-grid { grid-template-columns:1fr; } .overview-time-head { display:block; } }
    @media (max-width:900px) { .ov-grid { grid-template-columns:1fr; } }
    @media (max-width: 900px) { .block-container { padding:1.2rem 1rem 2rem; } .metric-grid,.story-grid,.chain { grid-template-columns:repeat(2,1fr); } .top-actions { display:none; } }
    @media (max-width: 560px) { .metric-grid,.story-grid,.chain { grid-template-columns:1fr; } .chain-step { border-right:0; border-bottom:1px solid #33466b; } }

    /* ===== 图二·时序页样式（合并自「时序发展分析」原型）===== */
    .st-key-panel_controls2 { background:rgba(11,39,57,.98); border:1px solid rgba(176,218,241,.22); border-radius:14px; padding:9px 15px; margin:12px 0 4px; }
    .st-key-panel_controls2 [role="radiogroup"] { display:flex; gap:8px; flex-wrap:nowrap; }
    .st-key-panel_controls2 label[data-baseweb="radio"] { flex:1; min-width:65px; margin:0; justify-content:center; padding:6px 11px; border:1px solid rgba(176,218,241,.3); border-radius:8px; background:rgba(10,43,62,.8); cursor:pointer; transition:background .2s,border-color .2s; }
    .st-key-panel_controls2 label[data-baseweb="radio"] p { font-size:14px; color:#d6e4ef; }
    .st-key-panel_controls2 label[data-baseweb="radio"] > div:first-child { display:none; }
    .st-key-panel_controls2 label[data-baseweb="radio"]:has(input:checked) { background:rgba(89,227,197,.15); border-color:#59e3c5; box-shadow:inset 0 0 0 1px rgba(89,227,197,.15); }
    .st-key-panel_controls2 label[data-baseweb="radio"]:has(input:checked) p { color:#93f6df; font-weight:600; }
    .st-key-panel_controls2 label[data-baseweb="radio"]:hover { border-color:#8bcfc9; }
    .st-key-panel_tline2 { background:rgba(7,30,47,.95); border:1px solid rgba(176,218,241,.22); border-radius:14px; padding:15px 18px; box-shadow:0 10px 30px rgba(0,10,26,.12); }
    .t2-year-label { color:#d2e5ef; font-size:13px; white-space:nowrap; line-height:1.5; }
    .t2-year-label strong { color:#59e3c5; font-size:20px; margin-left:7px; font-variant-numeric:tabular-nums; }
    .t2-year-caption { color:#bed3e2; font-size:11px; line-height:1.5; margin-top:2px; }
    .t2-overview { display:grid; grid-template-columns:minmax(220px,1fr) 3fr; background:rgba(8,32,48,.95); border:1px solid rgba(176,218,241,.22); border-radius:14px; padding:16px 22px; gap:22px; margin:12px 0 18px; }
    .t2-metric { border-right:1px solid rgba(176,218,241,.22); padding-right:18px; }
    .t2-metric-label { color:#c9deea; font-size:13px; }
    .t2-metric-value { color:#f3fbff; font-size:32px; line-height:1.2; font-weight:650; font-variant-numeric:tabular-nums; }
    .t2-metric-value small { color:#c1d8e6; font-size:13px; font-weight:400; margin-left:8px; }
    .t2-metric-date { color:#b6cfdc; font-size:12px; line-height:1.6; }
    .t2-metric-date strong { color:#59e3c5; font-weight:500; }
    .t2-reading { align-self:center; }
    .t2-reading-label { color:#59e3c5; font-size:12px; font-weight:600; letter-spacing:1px; }
    .t2-reading p { color:#edf6fc; font-size:14px; line-height:1.75; margin:4px 0; }
    .t2-reading-note { color:#bed3e2; font-size:12px; line-height:1.7; }
    .t2-heading { display:flex; align-items:baseline; gap:12px; padding:6px 0; margin-top:6px; }
    .t2-heading h3 { color:#f0f9ff; font-size:20px; margin:0; padding:0; font-weight:600; letter-spacing:.5px; font-family:'Noto Serif SC',serif; }
    .t2-heading span { color:#59e3c5; font-size:11px; letter-spacing:1.5px; }
    .t2-panel-title { display:flex; align-items:center; gap:10px; margin-bottom:4px; color:#eff9ff; font-size:16px; font-weight:650; }
    .t2-panel-title em { color:#59e3c5; font-style:normal; font-weight:500; font-size:11px; letter-spacing:1px; }
    .t2-panel-desc { color:#bed3e2; font-size:13px; line-height:1.7; margin:0 0 3px; }
    .t2-scope { color:#d2e4ef; font-size:12px; line-height:1.8; margin-top:6px; }
    .t2-scope strong { color:#a5efde; font-weight:500; }
    @media (max-width:640px) { .t2-overview { grid-template-columns:1fr; padding:13px; gap:10px; } .t2-metric { border-right:0; border-bottom:1px solid rgba(176,218,241,.22); padding:0 0 10px; } .st-key-panel_controls2 [data-testid="stHorizontalBlock"] { flex-direction:column; gap:5px; } .st-key-panel_controls2 [data-testid="stColumn"] { width:100%!important; flex:1 1 100%!important; min-width:0; } .t2-year-caption { display:none; } }


    /* ===== 大标题 Logo：蓝色立体文字 + 风机/地球图标 + 金色星点 ===== */
    .hero-title { display:flex; align-items:center; gap:7px; margin:8px 0 2px; }
    .hero-title .ht-icon { flex:0 0 auto; line-height:0; }
    .hero-title .ht-icon svg { display:block; }
    .hero-title .ht-text {
      font-family:'Noto Serif SC',serif; font-size:17px; font-weight:800; letter-spacing:1px; line-height:1.25;
      background:linear-gradient(180deg,#5fb4ea 0%,#3a95d6 45%,#1a6fb8 100%);
      -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; color:#1a6fb8;
      filter:drop-shadow(0 1px 0 #cfe6f8) drop-shadow(0 2px 3px rgba(10,40,70,.35));
      white-space:nowrap;
    }
    .hero-sub { color:#bcd7e6; font-size:12px; letter-spacing:2px; margin:0 0 2px 2px; }

    
    [data-testid="stMetric"] { background:rgba(5,20,40,.92); border:1px solid rgba(196,168,92,.4); border-top:3px solid #c9a227; border-radius:10px; padding:.85rem 1rem; }
    [data-testid="stMetricLabel"] { color:#ffffff !important; font-size:.8rem; letter-spacing:.03em; }
    [data-testid="stMetricValue"] { color:#ffffff !important; font-weight:800; font-size:1.55rem !important; }
    .stSlider { width:100% !important; }
    .stSlider [data-baseweb="slider"] { width:100% !important; }
    [data-testid="stSelectbox"] > div { width:100% !important; }
    [data-testid="stSelectbox"] [data-baseweb="select"] > div { color:#5ab3f0 !important; font-weight:600; }

    [data-testid="stSlider"] [role="slider"] { cursor:pointer; }
    .param-note { color:#a9c4dc; font-size:.74rem; line-height:1.55; margin-top:5px; padding-left:2px; }
    .stSlider [data-baseweb="slider"] { background:rgba(5,20,40,.6); }

    /* 深底高亮：所有控件文字统一提亮，保证黑底上也看得清 */
    [data-testid="stTabs"] button, [data-testid="stTabs"] [data-baseweb="tab"] { color:#ffffff !important; font-weight:600; font-size:1rem; }
    [data-testid="stTabs"] button[aria-selected="true"], [data-testid="stTabs"] [aria-selected="true"] { color:#ffffff !important; border-bottom:2px solid #c9a227 !important; }
    .stSlider [data-baseweb="slider"] { color:#eaf4fb !important; }
    .stSlider label, [data-testid="stSlider"] p { color:#ffffff !important; }
    [data-testid="stSelectbox"] label, .stSelectbox [data-baseweb="select"] div { color:#ffffff !important; }
    [data-testid="stSelectbox"] [data-baseweb="select"] [data-testid="stMarkdownContainer"] p { color:#ffffff !important; }
    [data-testid="stExpander"] summary, [data-testid="stExpander"] label { color:#ffffff !important; font-weight:600; }
    [data-testid="stCaptionContainer"] p, .stCaption { color:#ffffff !important; }
    [data-testid="stDataFrame"] { background:rgba(6,22,44,.92); }
    [data-testid="stMetricValue"] { color:#ffffff !important; font-weight:800; }
</style>
    """.replace("__PAGE_BACKGROUND__", page_background).replace("__SIDEBAR_BACKGROUND__", sidebar_background),
    unsafe_allow_html=True,
)


with st.sidebar:
    st.markdown(
        '<div class="hero-title">'
        '<span class="ht-text">山东海上风电交互平台</span>'
        '<span class="ht-icon">'
        '<svg viewBox="0 0 64 64" width="34" height="34" aria-hidden="true">'
        '  <circle cx="32" cy="32" r="20" fill="none" stroke="#2f8fd6" stroke-width="3"/>'
        '  <ellipse cx="32" cy="32" rx="20" ry="8.5" fill="none" stroke="#2f8fd6" stroke-width="2"/>'
        '  <line x1="32" y1="12" x2="32" y2="52" stroke="#2f8fd6" stroke-width="2"/>'
        '  <rect x="15" y="30" width="8" height="18" rx="1.5" fill="#3a9bdc"/>'
        '  <rect x="27" y="22" width="8" height="26" rx="1.5" fill="#2f8fd6"/>'
        '  <rect x="39" y="14" width="8" height="34" rx="1.5" fill="#1a6fb8"/>'
        '  <path d="M9 38 l1.2 -2.6 1.2 2.6" fill="#e8c868"/>'
        '  <path d="M53 33 l1.2 -2.6 1.2 2.6" fill="#e8c868"/>'
        '</svg></span>'
        '</div>'
        '<div class="hero-sub">交互式数据可视化平台</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    view = st.radio("平台导航", ["发展总览", "时序发展", "空间分布", "减碳效益"], format_func=lambda x: {"发展总览": "📊 发展总览", "时序发展": "📈 时序发展", "空间分布": "🗺️ 空间分布", "减碳效益": "🌱 减碳效益"}[x], label_visibility="visible")


st.markdown('<div class="topbar"><div class="topbrand"><div class="brand-mark"><svg viewBox="0 0 64 64" width="38" height="38" aria-hidden="true">  <path d="M32 44 L32 25" stroke="#cfe6f8" stroke-width="3.5" stroke-linecap="round" fill="none"/>  <rect x="26" y="21.5" width="12" height="6.5" rx="2.4" fill="#e0c079"/>  <path d="M32 24 C23 21 17 15 14 8" stroke="#cfe6f8" stroke-width="3" stroke-linecap="round" fill="none"/>  <path d="M32 24 C41 21 47 15 50 8" stroke="#cfe6f8" stroke-width="3" stroke-linecap="round" fill="none"/>  <path d="M32 24 V7" stroke="#cfe6f8" stroke-width="3" stroke-linecap="round" fill="none"/>  <circle cx="32" cy="24" r="4.4" fill="#e0c079"/>  <path d="M8 53 Q14 47 20 53 T32 53 T44 53 T56 53" stroke="#8fd0f0" stroke-width="2.6" fill="none" stroke-linecap="round"/></svg></div><div><strong>山东海上风电交互平台</strong><span>OFFSHORE WIND · INTERACTIVE EXPLORER</span></div></div><div class="top-actions"><span>面向公众的绿色数据科普</span><span class="top-status"><i></i>数据可视化</span></div></div>', unsafe_allow_html=True)
top_spacer, top_refresh = st.columns([5.2, 1], gap="small")
with top_refresh:
    if st.button("↻ 重新生成界面", key="refresh_ui", use_container_width=True, help="清除数据缓存并重新运行当前 Streamlit 页面"):
        st.cache_data.clear()
        st.rerun()


def year_navigator(prefix):
    """年份联动视图：点击年份即切换，联动当年指标与趋势高亮。"""
    current = int(st.session_state.get("year", 2024))
    try:
        picked = st.pills("观察年份", YEARS, default=current, key=f"year_nav_{prefix}", label_visibility="collapsed")
    except Exception:
        picked = st.radio("观察年份", YEARS, index=YEARS.index(current), horizontal=True, key=f"year_nav_{prefix}", label_visibility="collapsed")
    if picked is not None:
        picked = int(picked)
        if picked != current:
            st.session_state["year"] = picked
    return int(st.session_state.get("year", 2024))


def trend_figure(highlight_year):
    """2020—2025 装机规模趋势，高亮当前观察年份。"""
    fig = go.Figure()
    fig.add_scatter(x=energy.year, y=energy.capacity_mw, mode="lines", name="装机规模",
                    line=dict(color="#c9a227", width=3), connectgaps=False,
                    hovertemplate="%{x}年 · %{y:,.0f} MW<extra></extra>")
    fig.add_scatter(x=energy.year, y=energy.capacity_mw, mode="markers", name="年度值",
                    marker=dict(color="#c9a227", size=8),
                    hovertemplate="%{x}年 · %{y:,.0f} MW<extra></extra>")
    row = energy[energy.year == highlight_year]
    if len(row) and pd.notna(row.capacity_mw.iloc[0]):
        cap = float(row.capacity_mw.iloc[0])
        fig.add_scatter(x=[highlight_year], y=[cap], mode="markers+text", name="当前年份",
                        text=[f"{cap:,.0f}"], textposition="top center", textfont=dict(size=13, color="#e0b768"),
                        marker=dict(color="#e0b768", size=17, line=dict(color="#ffffff", width=2)),
                        hovertemplate="<b>%{x}年 · %{y:,.0f} MW</b><extra></extra>")
    fig.update_layout(
        height=340, margin=dict(l=15, r=20, t=25, b=30), showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Microsoft YaHei, sans-serif", size=12, color="#7fa8a2"),
        hoverlabel=dict(bgcolor="#163342", font_size=12, font_color="#d9eef4", bordercolor="#305361"),
        xaxis=dict(tickvals=list(YEARS), showgrid=False, zeroline=False),
        yaxis=dict(gridcolor="#213746", zeroline=False, title=dict(text="装机规模 / MW")),
    )
    return fig


def temporal_series():
    series = energy.copy()
    series["year"] = pd.to_numeric(series["year"], errors="coerce").astype("Int64")
    series = series[series["year"].between(2021, 2025)].copy()
    for column in ("new_grid_capacity_mw", "cumulative_grid_capacity_mw"):
        if column not in series:
            series[column] = pd.NA
        series[column] = pd.to_numeric(series[column], errors="coerce")
    if "data_status" not in series:
        series["data_status"] = ""
    return series.sort_values("year")


def temporal_charts(series, highlight_year):
    years = series["year"].astype(int).tolist()
    annual_values = series["new_grid_capacity_mw"].tolist()
    annual_colors = ["#e0b768" if year == highlight_year else "#c9a227" for year in years]
    annual = go.Figure(go.Bar(
        x=years, y=annual_values, marker_color=annual_colors,
        text=["" if pd.isna(value) else f"{value:,.0f}" for value in annual_values],
        textposition="outside", hovertemplate="%{x} 年<br/>年度新增并网 %{y:,.0f} MW<extra></extra>"))
    annual.update_layout(height=320, title="年度新增并网装机", margin=dict(l=10, r=15, t=45, b=25),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#dff8f0"), xaxis=dict(dtick=1, gridcolor="rgba(185,215,210,.10)"),
        yaxis=dict(title="MW", gridcolor="rgba(185,215,210,.16)"))

    cumulative_values = series["cumulative_grid_capacity_mw"].tolist()
    point_colors = ["#e0b768" if year == highlight_year else "#c9a227" for year in years]
    cumulative = go.Figure(go.Scatter(
        x=years, y=cumulative_values, mode="lines+markers+text",
        text=["" if pd.isna(value) else f"{value:,.0f}" for value in cumulative_values],
        textposition="top center", line=dict(color="#c9a227", width=3),
        marker=dict(size=10, color=point_colors), connectgaps=False,
        hovertemplate="%{x} 年<br/>累计并网 %{y:,.0f} MW<extra></extra>"))
    cumulative.update_layout(height=320, title="累计并网装机", margin=dict(l=10, r=15, t=45, b=25),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#dff8f0"), xaxis=dict(dtick=1, gridcolor="rgba(185,215,210,.10)"),
        yaxis=dict(title="MW", gridcolor="rgba(185,215,210,.16)"))
    return annual, cumulative


def temporal():
    st.markdown('<div class="mono section-kicker">02 / TIMELINE</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">时序发展 · 山东海上风电装机变化</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">通过年份联动查看 2021—2025 年已公开并网数据，观察年度新增与累计并网规模。两类统计口径分开展示；缺失年份不插值，项目规划/建设容量不计入并网时序。</div>', unsafe_allow_html=True)
    series = temporal_series()
    with st.container(key="panel_controls2"):
        label_col, year_col = st.columns([1, 4.6], vertical_alignment="center")
        with year_col:
            years = series["year"].astype(int).tolist()
            year = st.radio("年份联动视图", years, index=len(years) - 1,
                            format_func=lambda value: f"{value} 年", horizontal=True,
                            label_visibility="collapsed", key="temporal_year")
        with label_col:
            st.markdown(f'<div class="t2-year-label">年份联动 <strong>{year}</strong></div><div class="t2-year-caption">装机 · 项目进度 · 设计年效益</div>', unsafe_allow_html=True)
    row = series.loc[series["year"] == year].iloc[0]
    cum_wan = row["cumulative_grid_capacity_mw"] / 10 if pd.notna(row["cumulative_grid_capacity_mw"]) else None
    new_mw = row["new_grid_capacity_mw"] if pd.notna(row["new_grid_capacity_mw"]) else None
    if year == 2021:
        date_note = "2021 年 12 月全容量并网"
    elif year in (2022, 2023):
        date_note = f"累计并网至 {year} 年底"
    else:
        date_note = f"统计截至 {year} 年 11 月底"
    if new_mw is not None:
        interpretation = (f"{year} 年全省累计并网规模 {cum_wan:g} 万千瓦，{date_note}，为官方公开口径；"
                          f"全年新增并网约 {new_mw:,.0f} MW（{new_mw / 10:g} 万千瓦）。")
    else:
        interpretation = f"{year} 年全省累计并网规模 {cum_wan:g} 万千瓦，{date_note}，为官方公开口径。"
    st.markdown(
        '<div class="t2-overview">'
        '<div class="t2-metric">'
        f'<div class="t2-metric-label">{year} 年累计并网规模</div>'
        f'<div class="t2-metric-value">{cum_wan:g}<small>万千瓦</small></div>'
        f'<div class="t2-metric-date">{date_note} · <strong>累计并网口径</strong></div></div>'
        '<div class="t2-reading">'
        f'<div class="t2-reading-label">{year} 年 · 数据解读</div>'
        f'<p>{interpretation}</p>'
        f'<div class="t2-reading-note">{row["data_status"] or "官方公开口径"}</div></div>'
        '</div>', unsafe_allow_html=True)
    st.markdown('<div class="t2-heading"><h3>一条时间轴，看见五年装机变化</h3><span>01 / DEVELOPMENT TIMELINE</span></div>', unsafe_allow_html=True)
    with st.container(key="panel_tline2"):
        st.markdown('<div class="t2-panel-title">全省海上风电装机 · 公开观测<em>SHANDONG</em></div>'
                    '<div class="t2-panel-desc">高亮所选年份 · 悬停查看数值与统计日期</div>', unsafe_allow_html=True)
        values = [v / 10 if pd.notna(v) else None for v in series["cumulative_grid_capacity_mw"]]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=years, y=values, mode="lines+markers+text", name="累计并网",
                                 line=dict(color="#73b7db", width=2.5),
                                 marker=dict(size=8, color="#73b7db"),
                                 text=[f"{v:g}" if v is not None else "" for v in values],
                                 textposition="top center", textfont=dict(size=12, color="#d1e9f7"),
                                 fill="tozeroy", fillcolor="rgba(89,227,197,.055)",
                                 hovertemplate="%{x} 年 · %{y:g} 万千瓦<extra></extra>"))
        fig.add_trace(go.Scatter(x=[year], y=[cum_wan], mode="markers", name=f"所选 {year} 年",
                                 marker=dict(size=16, color="#59e3c5", line=dict(color="#e2fff7", width=2)),
                                 hovertemplate="%{x} 年<br/><b>%{y:g} 万千瓦</b><extra></extra>"))
        fig.update_xaxes(tickmode="array", tickvals=years, showgrid=False, zeroline=False, tickfont_color="#a6c2d7")
        fig.update_yaxes(gridcolor="rgba(180,218,239,.10)", zeroline=False, tickfont_color="#a6c2d7",
                         title="万千瓦", range=[0, max(v for v in values if v is not None) * 1.3])
        fig.update_layout(height=330, margin=dict(l=6, r=18, t=20, b=6),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(family='"Microsoft YaHei", sans-serif', color="#e5f1fa", size=13),
                          showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown('<div class="t2-scope"><strong>统计时点：</strong>2021 为 12 月 21 日首批示范项目全容量并网；2022 累计为新增 200 万千瓦后的推算值；2023—2025 累计并网截至当年 11 月底。各年口径与精度存在差异；累计数值由 MW 口径换算为万千瓦展示。</div>', unsafe_allow_html=True)
        with st.expander("查看统计口径与官方年度新增"):
            table = series[["year", "new_grid_capacity_mw", "cumulative_grid_capacity_mw", "data_status"]].rename(columns={
                "year": "年份", "new_grid_capacity_mw": "年度新增并网 MW",
                "cumulative_grid_capacity_mw": "累计并网 MW", "data_status": "公开统计口径"})
            st.dataframe(table, use_container_width=True, hide_index=True)
            st.markdown(f"**{year} 年口径**：{row['data_status'] or '官方公开口径'}。已公开的统计节点截至当年 11 月底；官方未公布或口径不连续的年份保留空缺，不进行插值。")
    st.markdown('<div class="source-box"><b>数据口径</b> 年度新增并网与累计并网分别统计；已公开的统计节点截至当年11月底。官方未公布或口径不连续的年份保留空缺，不进行插值；规划、核准和建设容量不纳入并网时序。' + SOURCE_LINKS_HTML + '</div>', unsafe_allow_html=True)


def project_timeline_legacy():
    st.markdown('<div class="mono section-kicker">03 / PROJECTS</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">项目规模 · 建设状态分析</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">通过比较不同风电场的装机容量与当前建设阶段，直观呈现山东省海上风电项目的规模结构与阶段差异。</div>', unsafe_allow_html=True)
    status_colors = {"运行": "#c9a227", "示范": "#d9b061", "建设": "#619cf1", "核准": "#e57b4c"}
    n_run = int(sites["status"].astype(str).str.contains("运行").sum())
    n_demo = int(sites["status"].astype(str).str.contains("示范").sum())
    n_build = int(sites["status"].astype(str).str.contains("建设").sum())
    total_mw = float(sites["capacity_mw"].sum())
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("收录项目", f"{len(sites)} 个")
    m2.metric("合计装机", f"{total_mw:,.0f} MW")
    m3.metric("运行项目", f"{n_run} 个")
    m4.metric("在建/示范", f"{n_build} 建设 · {n_demo} 示范")
    left, right = st.columns([1.45, 1.0], gap="large")
    with left:
        sites_sorted = sites.sort_values("capacity_mw", ascending=True)
        fig = go.Figure(go.Bar(x=sites_sorted["name"], y=sites_sorted["capacity_mw"],
                               marker_color=[status_colors.get(s, "#c9a227") for s in sites_sorted["status"]],
                               marker_cornerradius=4, text=[f"{v:,.0f}" for v in sites_sorted["capacity_mw"]], textposition="outside", textfont=dict(color="#dff8f0", size=11),
                               hovertemplate="%{x}<br/>装机 %{y:,.0f} MW<extra></extra>"))
        fig.update_layout(title="各风电场装机容量对比（MW）", height=400, margin=dict(l=12, r=12, t=45, b=55), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Microsoft YaHei, sans-serif", size=12, color="#b9d7d2"), xaxis=dict(tickfont=dict(color="#e3eef4")), yaxis=dict(gridcolor="#213746", zeroline=False, tickfont=dict(color="#b9d7d2")))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False, "staticPlot": True})
    with right:
        fig2 = go.Figure(go.Pie(labels=["运行", "示范", "建设"], values=[n_run, n_demo, n_build], hole=.6,
                                marker=dict(colors=[status_colors["运行"], status_colors["示范"], status_colors["建设"]], line=dict(color="#102230", width=3)),
                                textinfo="label+value", textfont=dict(color="#e3eef4", size=12), hovertemplate="%{label} %{value} 个<extra></extra>"))
        fig2.update_layout(title="建设阶段分布（项目数）", height=400, margin=dict(l=0, r=0, t=45, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Microsoft YaHei, sans-serif", size=12, color="#b9d7d2"), legend=dict(font=dict(color="#e3eef4")))
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
    st.dataframe(sites.sort_values("capacity_mw", ascending=False).rename(columns={"name": "风场", "capacity_mw": "装机 MW", "annual_gwh": "年发电 GWh", "wind_speed": "平均风速 m/s", "depth_m": "水深 m", "status": "建设阶段"}), use_container_width=True, hide_index=True)
    st.markdown('<div class="source-box"><b>数据来源</b> 山东沿海项目名称、规划/建设容量与项目状态依据山东省公开项目名单及政府公开资料整理；规划容量不等同于已并网容量。' + SOURCE_LINKS_HTML + '</div>', unsafe_allow_html=True)


def spatial():
    st.markdown('<div class="mono section-kicker">03 / SPATIAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">空间分布 · 风电场布局</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">依托 GIS 地图标注山东沿海风电项目的名称、位置、装机规模与建设状态；支持悬浮查看项目详情，并可按建设状态分类筛选。</div>', unsafe_allow_html=True)

    # ---- 严谨逻辑：筛选 + 实时统计（防空筛选） ----
    status_opts = sites["status"].unique().tolist()
    default_show = [s for s in status_opts if s in ("已并网", "在建·重大实施", "拟建")]
    if not default_show:
        default_show = list(status_opts)
    picked = st.multiselect("按建设状态筛选", status_opts, default=default_show)
    if not picked:
        picked = list(status_opts)
    filtered = sites[sites["status"].isin(picked)].copy()

    n_proj = len(filtered)
    total_mw = filtered["capacity_mw"].sum()
    status_summary = " · ".join(
        f"{s} {int((filtered['status'] == s).sum())}个"
        for s in status_opts if (filtered['status'] == s).any())
    share_rank = filtered.sort_values("capacity_mw", ascending=False)
    max_proj = share_rank.iloc[0]["name"] if n_proj else "—"

    # 状态 -> 颜色（深海蓝金主题协调：已并网=金，在建·重大实施=橙，核准=蓝，重大准备·拟建=钢蓝）
    color_map = {
        "已并网": [237, 132, 40, 235],
        "在建·重大实施": [56, 122, 199, 235],
        "拟建": [52, 158, 96, 235],
    }
    filtered["color"] = filtered["status"].map(lambda s: color_map.get(s, [150, 180, 200, 220]))
    filtered["radius"] = filtered["capacity_mw"].apply(lambda m: (m ** 0.5) * 700)

    # ---- 优美界面：筛选结果概览卡 ----
    st.markdown(
        f'<div class="ov-panel"><div class="ov-title">筛选结果概览</div>'
        f'<div class="ov-grid">'
        f'<div class="ov-item"><div class="lbl">当前显示项目</div><div class="val">{n_proj} <em>个</em></div><div class="note">按所选建设状态</div></div>'
        f'<div class="ov-item"><div class="lbl">合计装机规模</div><div class="val">{total_mw:,.0f} <em>MW</em></div><div class="note">所选项目容量合计（含已并网与规划口径）</div></div>'
        f'<div class="ov-item"><div class="lbl">状态结构</div><div class="val" style="font-size:1rem;">{status_summary}</div><div class="note">状态按官方公开口径分类</div></div>'
        f'</div></div>',
        unsafe_allow_html=True)

    # ---- GIS 地图：点大小按规模、颜色按状态、悬浮查看 ----
    column_layer = pdk.Layer(
        "ColumnLayer", data=filtered,
        get_position="[lon, lat]",
        get_elevation="capacity_mw",
        elevation_scale=45,
        radius=2500,
        get_fill_color="color",
        pickable=True, auto_highlight=True,
        extruded=True,
    )
    dot_layer = pdk.Layer(
        "ScatterplotLayer", data=filtered,
        get_position="[lon, lat]",
        radius=7000,
        get_fill_color=[52, 158, 96, 235],
        stroked=True, get_line_color=[255, 255, 255, 190],
        line_width_min_pixels=1.2,
        pickable=True,
    )
    view_state = pdk.ViewState(latitude=37.0, longitude=120.6, zoom=7.0, pitch=35)
    tooltip_html = (
        "<b>{name}</b><br/>"
        "装机规模：{capacity_mw} MW<br/>"
        "建设状态：{status}<br/>"
        "并网时间：{grid_date}<br/>"
        "容量口径：{capacity_type}<br/>"
        "说明：{position_note}"
    )
    deck = pdk.Deck(
        layers=[column_layer, dot_layer], initial_view_state=view_state, map_style="light",
        tooltip={"html": tooltip_html,
                 "style": {"backgroundColor": "#0d2a4a", "color": "#eef4fa",
                           "fontSize": "12px", "padding": "12px",
                           "border": "1px solid #cfa85c"}},
    )
    st.pydeck_chart(deck, use_container_width=True)

    # ---- 图例 ----
    st.markdown(
        '<div style="display:flex;gap:1.6rem;align-items:center;margin:.4rem 0 .8rem;color:#b8ccdc;font-size:.78rem;flex-wrap:wrap;">'
        '<span style="display:inline-flex;align-items:center;gap:.45rem;"><span style="width:12px;height:12px;border-radius:2px;background:rgba(237,132,40,.95);display:inline-block;"></span>已并网</span>'
        '<span style="display:inline-flex;align-items:center;gap:.45rem;"><span style="width:12px;height:12px;border-radius:2px;background:rgba(56,122,199,.95);display:inline-block;"></span>在建·重大实施</span>'
        '<span style="display:inline-flex;align-items:center;gap:.45rem;"><span style="width:12px;height:12px;border-radius:2px;background:rgba(52,158,96,.95);display:inline-block;"></span>拟建</span>'
        '<span style="color:#8ba6bf;">柱高 ∝ 装机规模</span>'
        '</div>', unsafe_allow_html=True)

    # ---- 项目明细表（按规模降序） ----
    st.markdown('<div class="panel-title" style="margin-top:.4rem;">项目明细</div>', unsafe_allow_html=True)
    st.dataframe(
        filtered[["name", "capacity_mw", "status", "grid_date", "source", "position_note"]]
        .sort_values("capacity_mw", ascending=False)
        .rename(columns={"name": "项目", "capacity_mw": "装机规模 MW", "status": "建设状态",
                         "grid_date": "并网时间", "source": "官方来源", "position_note": "坐标说明"}),
        use_container_width=True, hide_index=True)

    st.markdown('<div class="source-box"><b>数据口径</b> 地图展示山东沿海已并网及在建/拟建类公开项目；装机容量与建设状态均按官方公开口径标注，容量区分"已并网容量/规划建设容量"；点位为海域示意坐标，不代表精确场址边界；明细表附逐项官方来源链接。' + SOURCE_LINKS_HTML + '</div>', unsafe_allow_html=True)


def estimate_carbon(frame, hours, factor):
    result = frame.copy()
    result["annual_generation_mwh"] = result["capacity_mw"] * hours
    result["carbon_t"] = result["annual_generation_mwh"] * factor
    return result


def render_carbon_status(frame, hours, factor, label, note, color):
    """按状态分组渲染减碳测算：概览卡 + 横向柱状图 + 明细，不与其他状态合并总数。"""
    if frame is None or frame.empty:
        st.info(f"当前状态下没有可测算的项目。")
        return
    res = estimate_carbon(frame, hours, factor)
    cap = float(res["capacity_mw"].sum())
    gen_mwh = float(res["annual_generation_mwh"].sum())
    carb_t = float(res["carbon_t"].sum())
    m1, m2, m3 = st.columns(3)
    m1.metric(f"{label} · 项目数", f"{len(res)} 个")
    m2.metric(f"{label} · 合计装机", f"{cap:,.1f} MW")
    m3.metric(f"{label} · 年减碳测算", f"{carb_t / 10000:,.2f} 万吨 CO₂")
    st.caption(f"{label}：{note}；年发电量测算合计约 {gen_mwh / 1000000:,.2f} 亿 kWh。")
    res2 = res.sort_values("annual_generation_mwh", ascending=True)
    res2["disp_name"] = res2["name"].map(lambda n: (str(n)[:11] + "…") if len(str(n)) > 11 else str(n))
    gen_vals = (res2["annual_generation_mwh"] / 1000000).tolist()
    red_vals = (res2["carbon_t"] / 10000).tolist()
    # 年发电量测算（横向柱状图）
    figg = go.Figure(go.Bar(
        x=res2["annual_generation_mwh"] / 1000000, y=res2["disp_name"], orientation="h",
        marker=dict(color=color, cornerradius=3),
        text=[f"{v:,.2f}" for v in gen_vals], textposition="outside",
        textfont=dict(size=10, color="#ffffff"), cliponaxis=False,
        hovertemplate="%{customdata[1]}<br>装机 %{customdata[0]:,.0f} MW<br>年发电量测算 %{x:,.2f} 亿 kWh<extra></extra>",
        customdata=res2[["capacity_mw", "name"]]))
    figg.update_layout(title=dict(text=f"{label} · 各项目年发电量测算（亿 kWh/年）", font=dict(color="#ffffff", size=13, family="Microsoft YaHei, sans-serif")), height=max(280, len(res2) * 30 + 50),
        margin=dict(l=100, r=72, t=40, b=28),
        paper_bgcolor="rgba(8,28,46,0.8)", plot_bgcolor="rgba(6,20,34,0.62)",
        font=dict(family="Microsoft YaHei, sans-serif", size=12, color="#ffffff"),
        xaxis=dict(title="亿 kWh / 年", gridcolor="#213746", range=[0, max(gen_vals) * 1.22]),
        yaxis=dict(showgrid=False, autorange="reversed", tickfont=dict(size=10.5, color="#ffffff")))
    # 年减排量测算（横向柱状图）
    figr = go.Figure(go.Bar(
        x=res2["carbon_t"] / 10000, y=res2["disp_name"], orientation="h",
        marker=dict(color=color, cornerradius=3),
        text=[f"{v:,.1f}" for v in red_vals], textposition="outside",
        textfont=dict(size=10, color="#ffffff"), cliponaxis=False,
        hovertemplate="%{customdata[1]}<br>装机 %{customdata[0]:,.0f} MW<br>年减碳测算 %{x:,.1f} 万吨 CO₂<extra></extra>",
        customdata=res2[["capacity_mw", "name"]]))
    figr.update_layout(title=dict(text=f"{label} · 各项目年减碳测算（万吨 CO₂/年）", font=dict(color="#ffffff", size=13, family="Microsoft YaHei, sans-serif")), height=max(280, len(res2) * 30 + 50),
        margin=dict(l=100, r=72, t=40, b=28),
        paper_bgcolor="rgba(8,28,46,0.8)", plot_bgcolor="rgba(6,20,34,0.62)",
        font=dict(family="Microsoft YaHei, sans-serif", size=12, color="#ffffff"),
        xaxis=dict(title="万吨 CO₂ / 年", gridcolor="#213746", range=[0, max(red_vals) * 1.22]),
        yaxis=dict(showgrid=False, autorange="reversed", tickfont=dict(size=10.5, color="#ffffff")))
    cg, cr = st.columns(2, gap="large")
    with cg:
        st.plotly_chart(figg, use_container_width=True, config={"displayModeBar": False})
    with cr:
        st.plotly_chart(figr, use_container_width=True, config={"displayModeBar": False})
    with st.expander(f"查看 {label} 项目测算明细"):
        disp = res.rename(columns={"name": "项目", "capacity_mw": "装机 MW", "annual_generation_mwh": "年发电量测算 MWh", "carbon_t": "年减碳测算 tCO₂", "status": "状态"})
        st.dataframe(disp[["项目", "装机 MW", "年发电量测算 MWh", "年减碳测算 tCO₂", "状态"]], use_container_width=True, hide_index=True)


def carbon():
    st.markdown('<div class="mono section-kicker">04 / CARBON BENEFIT</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">减碳效益 · 绿色价值核算</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">基于项目装机规模、等效利用小时与公开电力排放因子，测算各项目年发电量和年二氧化碳减排量；按建设状态分步选择与测算，已并网为实际运行测算，在建/拟建为建成后理论测算。</div>', unsafe_allow_html=True)

    def step(n, text):
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:11px;margin:16px 0 6px;">'
            f'<span style="background:#c9a227;color:#0a1e38;border-radius:6px;padding:2px 10px;font-weight:800;font-size:.82rem;letter-spacing:.03em;">{n}</span>'
            f'<span style="color:#ffffff;font-weight:700;letter-spacing:.02em;font-size:1rem;">{text}</span></div>',
            unsafe_allow_html=True)

    # 01 选择参与测算的项目（按建设状态）
    step("01", "选择参与测算的项目 · 按建设状态")
    status_key = st.radio("参与测算的项目状态", ["已并网", "在建·重大实施", "拟建"], horizontal=True, key="carbon_status")

    # 02 设置测算参数
    step("02", "设置测算参数")
    p1, p2 = st.columns(2, gap="large")
    with p1:
        hours = st.slider("年等效利用小时数 / h", 1000, 8760, 3000, 100, key="carbon_hours")
        st.markdown('<div class="param-note">依据：海上风电年等效利用小时常取 3,000 h 作为测算基准，可按项目实际运行情况调整。</div>', unsafe_allow_html=True)
    with p2:
        factor_map = {0.5306: "全国平均 · 2023年", 0.6191: "山东省 · 2023年", 0.6361: "华北区域 · 2023年"}
        factor = st.selectbox("替代电力排放因子 / kgCO₂·kWh⁻¹", list(factor_map.keys()), format_func=lambda x: f"{x} · {factor_map[x]}", key="carbon_factor")
        st.markdown('<div class="param-note">依据：电力排放因子取 2023 年公开电网排放因子（全国 0.5306 / 山东 0.6191 / 华北 0.6361 kgCO₂·kWh⁻¹），用于替代火电的减排测算。</div>', unsafe_allow_html=True)

    # 03 计算公式与测算口径
    step("03", "计算公式与测算口径")
    st.markdown(
        '<div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:4px 0 6px;">'
        '<div style="background:rgba(12,34,52,.85);border:1px solid rgba(196,168,92,.32);border-radius:10px;padding:8px 14px;color:#ffffff;font-size:.85rem;display:inline-flex;gap:8px;align-items:center;">'
        '<b style="color:#e0c079">装机规模 MW</b><span>×</span><b style="color:#e0c079">利用小时 h</b><span>=</span><b style="color:#e0c079">年发电量 MWh</b></div>'
        '<div style="background:rgba(12,34,52,.85);border:1px solid rgba(196,168,92,.32);border-radius:10px;padding:8px 14px;color:#ffffff;font-size:.85rem;display:inline-flex;gap:8px;align-items:center;">'
        '<b style="color:#e0c079">年发电量 MWh</b><span>×</span><b style="color:#e0c079">排放因子 kgCO₂/kWh</b><span>=</span><b style="color:#e0c079">年减排量 tCO₂</b></div>'
        '</div>', unsafe_allow_html=True)

    # 04 汇总测算结果
    step("04", "汇总测算结果")
    groups = {
        "已并网": ("在运项目 · 实际运行测算", "#c9a227"),
        "在建·重大实施": ("建成后理论测算 · 尚未并网发电", "#619cf1"),
        "拟建": ("建成后理论测算 · 尚未并网发电", "#52b07b"),
    }
    note, color = groups[status_key]
    frame = sites[sites["status"] == status_key] if "status" in sites else sites
    render_carbon_status(frame, hours, factor, status_key, note, color)

    st.markdown('<div class="source-box"><b>数据口径</b> 年发电量 = 装机规模 × 等效利用小时；年减碳量 = 年发电量 × 电力排放因子，为替代电力的毛减排估算，未扣除建设、运维与退役排放。已并网项目为在运实际测算；在建/拟建项目按建成后容量作理论测算，不代表现场监测值。各状态分别合计、不合并为总数。' + SOURCE_LINKS_HTML + '</div>', unsafe_allow_html=True)


def overview_page_new():
    """发展总览：趋势、联动指标与摘要结果。"""
    st.markdown('<div class="mono section-kicker">01 / OVERVIEW</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">发展总览 · 山东海上风电绿色成效</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">先看装机规模如何变化，再把年度发电与减碳结果放回项目总体背景中，形成“趋势—结果—口径”的完整阅读路径。</div>', unsafe_allow_html=True)

    valid = energy.dropna(subset=["capacity_mw", "generation_gwh"]).copy()
    valid["year"] = valid["year"].astype(int)
    first_row = valid.iloc[0]
    latest_row = valid.iloc[-1]
    years = valid["year"].tolist()
    selected_year = st.select_slider("重点观察年份", options=years, value=int(latest_row["year"]), key="overview_focus_year")
    current = valid[valid["year"] == selected_year].iloc[0]
    previous = valid[valid["year"] == selected_year - 1]
    yoy = ((float(current["capacity_mw"]) / float(previous.iloc[0]["capacity_mw"]) - 1) * 100) if len(previous) else None

    left, right = st.columns([1.65, .9], gap="large")
    with left:
        st.markdown('<div class="overview-time"><div class="overview-time-head"><div><div class="mono" style="color:#e0bd6f">01 · 装机时序总体结果</div><div class="overview-time-title">装机规模与绿色电量同步增长</div></div><div class="overview-time-note">柱状表示年度发电量，折线表示累计装机；2025 年暂未收录，因此不对缺失年份进行插值。</div></div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_bar(x=valid["year"], y=valid["generation_gwh"], name="年度发电量", marker_color="#c9a227", opacity=.78, hovertemplate="%{x} 年<br/>发电量 %{y:,.0f} GWh<extra></extra>")
        fig.add_scatter(x=valid["year"], y=valid["capacity_mw"], name="累计装机", mode="lines+markers", yaxis="y2", line=dict(color="#e0b768", width=3), marker=dict(size=8, color="#e0b768"), hovertemplate="%{x} 年<br/>装机 %{y:,.0f} MW<extra></extra>")
        fig.add_scatter(x=[selected_year], y=[float(current["capacity_mw"])], mode="markers", yaxis="y2", showlegend=False, marker=dict(size=16, color="#ffffff", line=dict(color="#e0b768", width=3)), hovertemplate="重点年份 %{x}<br/>装机 %{y:,.0f} MW<extra></extra>")
        fig.update_layout(height=360, margin=dict(l=5, r=5, t=25, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Microsoft YaHei, sans-serif", color="#b9d7d2"), legend=dict(orientation="h", y=1.08), xaxis=dict(tickvals=list(range(2020, 2026)), gridcolor="rgba(185,215,210,.12)", zeroline=False), yaxis=dict(title="发电量 / GWh", gridcolor="rgba(185,215,210,.16)", zeroline=False), yaxis2=dict(title="装机 / MW", overlaying="y", side="right", showgrid=False, zeroline=False))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False, "staticPlot": True})
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="overview-insight">', unsafe_allow_html=True)
        st.markdown(f'<div class="eyebrow mono">02 · 观察年份结果</div><h3>{selected_year} 年装机表现</h3><div class="big">{float(current["capacity_mw"]):,.0f}<span class="unit"> MW</span></div><div class="line"><span>年度发电量</span><b>{float(current["generation_gwh"]):,.0f} GWh</b></div><div class="line"><span>折算减排量</span><b>{float(current["carbon_reduction_t"]):,.0f} t</b></div><div class="line"><span>较上年装机变化</span><b>{f"{yoy:+.1f}%" if yoy is not None else "起始年份"}</b></div>', unsafe_allow_html=True)
        if selected_year == int(latest_row["year"]) and int(latest_row["year"]) < 2025:
            st.markdown('<div class="overview-alert">2025 年官方装机数据暂未收录，图表保留空缺，避免把待发布数据误读为零。</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    total_mw = float(sites["capacity_mw"].sum())
    total_gwh = float(sites["annual_gwh"].sum())
    carbon_wan = total_mw * 3000 * 0.5306 / 10000
    ws_mean = sites["wind_speed"].mean()
    ws_text = f"{ws_mean:.1f}" if pd.notna(ws_mean) else "—"
    gwh_text = f"{total_gwh:,.0f}" if total_gwh else "—"
    st.markdown(f'<div class="overview-summary-grid"><div class="overview-summary"><div class="tag">03 · 空间布局结果</div><h3>项目规模与海域布局</h3><div class="stats"><div><b>{len(sites)}</b><span>收录风场</span></div><div><b>{total_mw:,.0f}</b><span>项目合计装机 / MW</span></div><div><b>{ws_text}</b><span>平均风速 / m/s</span></div></div></div><div class="overview-summary"><div class="tag">04 · 减碳效益结果</div><h3>年化绿色能源价值</h3><div class="stats"><div><b>{gwh_text}</b><span>项目年发电 / GWh</span></div><div><b>{carbon_wan:,.1f}</b><span>模型减排 / 万吨</span></div><div><b>3,000</b><span>等效利用小时 / 年</span></div></div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="source-box"><b>数据口径</b> 装机与发电时序使用已处理的年度数据；2025 年暂未收录，不进行插值。减碳结果按 3,000 h/年等效利用小时与 0.5306 kgCO₂/kWh 排放因子进行模型测算。</div>', unsafe_allow_html=True)


def overview_page_legacy():
    st.markdown('<div class="mono section-kicker">01 / OVERVIEW</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">发展总览 · 山东海上风电绿色成效</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">从项目规模、空间布局到减碳效益，三大维度总体结果一览。</div>', unsafe_allow_html=True)
    latest = energy.dropna(subset=["capacity_mw"])
    last_cap = float(latest.capacity_mw.iloc[-1]); last_year = int(latest.year.iloc[-1])
    first_cap = float(latest.capacity_mw.iloc[0])
    total_mw = float(sites["capacity_mw"].sum())
    gen_gwh = total_mw * 3000.0 / 1000.0
    carb_wan = total_mw * 3000.0 * 0.5306 / 10000.0
    n_run = int((sites["status"] == "运行").sum()); n_demo = int((sites["status"] == "示范").sum()); n_build = int((sites["status"] == "建设").sum())

    st.markdown(
        f'<div class="ov-panel"><div class="ov-tag">01 · 时序发展 · 装机规模</div>'
        f'<div class="ov-title">装机时序总体结果</div>'
        f'<div class="ov-grid">'
        f'<div class="ov-item"><div class="lbl">已收录装机（{last_year} 年）</div><div class="val">{last_cap:,.0f} <em>MW</em></div><div class="note">官方最新已收录年份</div></div>'
        f'<div class="ov-item"><div class="lbl">起点装机（2020 年）</div><div class="val">{first_cap:,.0f} <em>MW</em></div><div class="note">起点之后逐年爬升</div></div>'
        f'<div class="ov-item"><div class="lbl">覆盖年份</div><div class="val">{len(latest)} <em>年</em></div><div class="note">2020—2025，2025 待披露</div></div>'
        f'</div></div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="ov-panel"><div class="ov-tag">02 · 空间分布 · 风场布局</div>'
        f'<div class="ov-title">空间布局总体结果</div>'
        f'<div class="ov-grid">'
        f'<div class="ov-item"><div class="lbl">收录风电场</div><div class="val">{len(sites)} <em>个</em></div><div class="note">有名称与规模依据的项目子集</div></div>'
        f'<div class="ov-item"><div class="lbl">合计装机规模</div><div class="val">{total_mw:,.0f} <em>MW</em></div><div class="note">覆盖多个海域</div></div>'
        f'<div class="ov-item"><div class="lbl">建设状态</div><div class="val">{n_run}<em>运行</em> · {n_demo}<em>示范</em> · {n_build}<em>建设</em></div><div class="note">按官方建设状态分类</div></div>'
        f'</div></div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="ov-panel"><div class="ov-tag">03 · 减碳效益 · 绿色价值</div>'
        f'<div class="ov-title">减碳效益总体结果</div>'
        f'<div class="ov-grid">'
        f'<div class="ov-item"><div class="lbl">年发电量测算</div><div class="val">{gen_gwh:,.0f} <em>GWh</em></div><div class="note">合计装机 × 3,000 h/年等效利用小时</div></div>'
        f'<div class="ov-item"><div class="lbl">年减碳潜力测算</div><div class="val">{carb_wan:,.1f} <em>万吨 CO₂</em></div><div class="note">年发电量 × 0.5306 kgCO₂/kWh 排放因子</div></div>'
        f'<div class="ov-item"><div class="lbl">测算口径</div><div class="val">3,000 h<em> /年</em></div><div class="note">等效利用小时 × 电力排放因子</div></div>'
        f'</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="source-box"><b>数据来源</b> 山东省海上风电装机时序依据公开并网口径整理；规划项目容量、项目布局与状态依据山东省公开项目资料整理；减碳结果为模型测算，不等同于现场监测值。' + SOURCE_LINKS_HTML + '</div>', unsafe_allow_html=True)


def overview_page():
    """总览页面：保留原有三段式框架，仅重做装机时序结果。"""
    st.markdown('<div class="mono section-kicker">01 / OVERVIEW</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">发展总览 · 山东海上风电绿色成效</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">从项目规模、空间布局到减碳效益，三大维度总体结果一览。</div>', unsafe_allow_html=True)

    valid = energy.dropna(subset=["capacity_mw"]).copy()
    valid["year"] = valid["year"].astype(int)
    years = list(range(2020, 2026))
    available_years = valid["year"].tolist()
    latest_year = available_years[-1]
    selected_year = latest_year
    selected = valid[valid["year"] == selected_year]
    has_value = False

    time_panel = st.container(border=True)
    with time_panel:
        st.markdown('<div class="time-panel" style="display:none"></div>', unsafe_allow_html=True)
        st.markdown('<div class="ov-tag">01 · 项目规模 · 建设状态</div><div class="ov-title">项目规模结构与阶段差异</div>', unsafe_allow_html=True)
        status_colors = {"运行": "#66d6c2", "示范": "#d9b061", "建设": "#619cf1", "核准": "#e57b4c"}
        sites_sorted = sites.sort_values("capacity_mw", ascending=True)
        fig = go.Figure(go.Bar(x=sites_sorted["name"], y=sites_sorted["capacity_mw"],
                               marker_color=[status_colors.get(s, "#66d6c2") for s in sites_sorted["status"]],
                               marker_cornerradius=4, text=[f"{v:,.0f}" for v in sites_sorted["capacity_mw"]], textposition="outside", textfont=dict(color="#ffffff", size=11),
                               hovertemplate="%{x}<br/>装机 %{y:,.0f} MW<extra></extra>"))
        fig.update_layout(height=340, dragmode=False, margin=dict(l=12, r=12, t=28, b=12), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ffffff"), showlegend=False, xaxis=dict(tickfont=dict(color="#ffffff"), gridcolor="rgba(255,255,255,.16)", zeroline=False), yaxis=dict(title=dict(text="装机容量 / MW", font=dict(color="#ffffff")), tickfont=dict(color="#ffffff"), gridcolor="rgba(255,255,255,.18)", zeroline=False))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False, "staticPlot": True})
        st.markdown('<div style="color:#bcd7d2;font-size:.78rem;line-height:1.7;margin-top:.6rem;padding-top:.7rem;border-top:1px dashed rgba(196,168,92,.3)"><b style="color:#ffffff">官方数据说明</b> 各风电场规划/建设容量与项目状态依据山东省政府、发展改革部门和能源主管部门公开资料整理；柱高表示规划/建设容量，颜色区分项目状态。</div>', unsafe_allow_html=True)

    total_mw = float(sites["capacity_mw"].sum())
    gen_gwh = total_mw * 3000.0 / 1000.0
    carb_wan = total_mw * 3000.0 * 0.5306 / 10000.0
    n_run = int(sites["status"].astype(str).str.contains("运行").sum())
    n_demo = int(sites["status"].astype(str).str.contains("示范").sum())
    n_build = int(sites["status"].astype(str).str.contains("建设").sum())
    st.markdown(f'<div class="ov-panel"><div class="ov-tag">02 · 空间分布 · 风场布局</div><div class="ov-title">空间布局总体结果</div><div class="ov-grid"><div class="ov-item"><div class="lbl">收录风电场</div><div class="val">{len(sites)} <em>个</em></div><div class="note">有名称与规模依据的项目子集</div></div><div class="ov-item"><div class="lbl">合计装机规模</div><div class="val">{total_mw:,.0f} <em>MW</em></div><div class="note">覆盖多个海域</div></div><div class="ov-item"><div class="lbl">建设状态</div><div class="val">{n_run}<em>运行</em> · {n_demo}<em>示范</em> · {n_build}<em>建设</em></div><div class="note">按项目状态分类</div></div></div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="ov-panel"><div class="ov-tag">03 · 减碳效益 · 绿色价值</div><div class="ov-title">减碳效益总体结果</div><div class="ov-grid"><div class="ov-item"><div class="lbl">年发电量测算</div><div class="val">{gen_gwh:,.0f} <em>GWh</em></div><div class="note">合计装机 × 3,000 h/年</div></div><div class="ov-item"><div class="lbl">年减碳潜力测算</div><div class="val">{carb_wan:,.1f} <em>万吨 CO₂</em></div><div class="note">按电力排放因子测算</div></div><div class="ov-item"><div class="lbl">测算口径</div><div class="val">3,000 h<em> /年</em></div><div class="note">等效利用小时 × 排放因子</div></div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="source-box"><b>数据来源</b> 项目布局、规模与减碳核算依据山东省政府、发展改革部门和能源主管部门公开资料整理；减碳结果为模型测算值。</div>', unsafe_allow_html=True)


def overview_summary():
    """发展总览：时序 / 空间 / 减碳 三项核心结果的最终结论，不展开过程交互。"""
    st.markdown('<div class="mono section-kicker">01 / OVERVIEW</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">发展总览 · 山东海上风电</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">按“时序发展—空间分布—减碳效益”汇总山东海上风电公开数据与模型测算的最终结果；完整交互图表与项目地图见左侧对应模块。</div>', unsafe_allow_html=True)

    # ---- 01 时序发展 · 装机规模趋势（最终结果）----
    trend_years = [2021, 2022, 2023, 2024, 2025]
    trend_cap = [60.0, 260.0, 472.0, 542.0, 592.4]  # 累计并网，万千瓦（官方口径）
    latest_cap = trend_cap[-1]
    ratio = latest_cap / trend_cap[0]

    st.markdown('<div class="ov-panel"><div class="ov-tag">01 · 时序发展 · 装机规模</div><div class="ov-title">2021—2025 装机规模变化趋势 · 累计并网</div>', unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_scatter(x=trend_years, y=trend_cap, mode="lines+markers",
                    line=dict(color="#ff8a3d", width=4),
                    marker=dict(size=11, color="#ff6a00", line=dict(width=2, color="#ffffff")),
                    hovertemplate="%{x} 年<br/>累计并网 %{y:,.1f} 万千瓦<extra></extra>")
    for _x, _y in zip(trend_years, trend_cap):
        fig.add_annotation(x=_x, y=_y, text=f"{_y:.1f}", showarrow=False,
                           xanchor="center", yanchor="bottom", yshift=4,
                           bgcolor="rgba(20,55,75,0.78)", bordercolor="rgba(20,55,75,0)",
                           font=dict(size=13, color="#ffffff", family="Microsoft YaHei, sans-serif"))
    fig.update_layout(height=300, margin=dict(l=8, r=8, t=20, b=8),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Microsoft YaHei, sans-serif", color="#ffffff"),
                      xaxis=dict(tickvals=trend_years, tickfont=dict(color="#ffffff", size=13, family="Microsoft YaHei"), gridcolor="rgba(196,168,92,.14)", zeroline=False),
                      yaxis=dict(title=dict(text="累计并网 / 万千瓦", font=dict(color="#ffffff", size=14, family="Microsoft YaHei")), tickfont=dict(color="#ffffff", size=13, family="Microsoft YaHei"), range=[0, 730], gridcolor="rgba(196,168,92,.18)", zeroline=False))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})
    st.markdown(f'<div class="ov-grid">'
                f'<div class="ov-item"><div class="lbl">起步年份（2021）</div><div class="val">60.0 <em>万千瓦</em></div><div class="note">首批并网、实现零突破</div></div>'
                f'<div class="ov-item"><div class="lbl">覆盖区间</div><div class="val">2021—2025 <em>5 年</em></div><div class="note">累计并网约为 2021 年的 {ratio:.1f} 倍</div></div>'
                f'<div class="ov-item"><div class="lbl">最新累计并网（2025）</div><div class="val">{latest_cap:,.1f} <em>万千瓦</em></div><div class="note">累计并网口径，官方公开</div></div>'
                f'</div></div>', unsafe_allow_html=True)

    # ---- 02 空间分布 · 山东沿海项目（最终结果）----
    total_projects = len(sites)
    total_capacity = float(sites["capacity_mw"].sum())
    largest = sites.loc[sites["capacity_mw"].idxmax()]
    status_counts = sites["status"].astype(str).value_counts()
    status_text = " · ".join(f"{n} {c}" for n, c in status_counts.items())
    st.markdown(f'<div class="ov-panel"><div class="ov-tag">02 · 空间分布 · 风场布局</div><div class="ov-title">山东沿海风电项目布局 · 总体结果</div><div class="ov-grid">'
                f'<div class="ov-item"><div class="lbl">纳入公开项目</div><div class="val">{total_projects} <em>个</em></div><div class="note">GIS 地图支持悬浮查看与分类筛选</div></div>'
                f'<div class="ov-item"><div class="lbl">项目规划/建设容量</div><div class="val">{total_capacity:,.0f} <em>MW</em></div><div class="note">不等同于已并网装机容量</div></div>'
                f'<div class="ov-item"><div class="lbl">最大单体项目</div><div class="val">{largest["capacity_mw"]:,.0f} <em>MW</em></div><div class="note">{largest["name"]}</div></div>'
                f'</div><div style="color:#9fb6cd;font-size:.72rem;margin-top:.5rem;">状态结构：{status_text}；项目坐标为海域示意点，详细 GIS 地图见空间分布页。</div></div>', unsafe_allow_html=True)

    # ---- 03 减碳效益 · 绿色价值（最终结果）----
    total_generation_gwh = total_capacity * 3000 / 1000
    total_carbon_wan = total_capacity * 3000 * 0.5306 / 10000
    st.markdown(f'<div class="ov-panel"><div class="ov-tag">03 · 减碳效益 · 绿色价值</div><div class="ov-title">海上风电年化绿色能源价值 · 模型测算</div><div class="ov-grid">'
                f'<div class="ov-item"><div class="lbl">年发电量测算</div><div class="val">{total_generation_gwh:,.0f} <em>GWh</em></div><div class="note">项目容量 × 3,000 h/年等效利用小时</div></div>'
                f'<div class="ov-item"><div class="lbl">年二氧化碳减排测算</div><div class="val">{total_carbon_wan:,.1f} <em>万吨 CO₂</em></div><div class="note">按 0.5306 kgCO₂/kWh 排放因子</div></div>'
                f'<div class="ov-item"><div class="lbl">结果属性</div><div class="val">模型测算</div><div class="note">基于公开参数，不等同于现场监测值</div></div>'
                f'</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="source-box"><b>数据说明</b> 时序为山东省累计并网口径（2021 年首批并网实现零突破）；项目容量与状态依据山东省公开项目资料整理；减碳结果按 3,000 h/年等效利用小时与 0.5306 kgCO₂/kWh 排放因子模型测算，不等同于现场监测值。' + SOURCE_LINKS_HTML + '</div>', unsafe_allow_html=True)





def project_scale():
    """项目级规模与建设状态分析，不虚构缺失的时间节点。"""
    st.markdown('<div class="mono section-kicker">02 / PROJECT STRUCTURE</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">项目规模与建设状态</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">通过比较不同风电场的装机容量与当前建设阶段，展示项目的规模结构与阶段差异。页面只使用资料中已公开的状态，不对未公开的开工或投运时间进行推测。</div>', unsafe_allow_html=True)

    status_options = sorted(sites["status"].dropna().astype(str).unique().tolist())
    selected_status = st.multiselect("按建设状态筛选", status_options, default=status_options)
    filtered = sites[sites["status"].astype(str).isin(selected_status)].copy()
    filtered = filtered.sort_values("capacity_mw", ascending=True)

    total_capacity = float(filtered["capacity_mw"].sum()) if not filtered.empty else 0
    largest = filtered.iloc[-1] if not filtered.empty else None
    m1, m2, m3 = st.columns(3)
    m1.metric("当前项目数", f"{len(filtered)} 个")
    m2.metric("筛选后合计装机", f"{total_capacity:,.0f} MW")
    m3.metric("最大单体项目", f"{largest['capacity_mw']:,.0f} MW" if largest is not None else "暂无")

    chart_col, status_col = st.columns([1.65, .85], gap="large")
    with chart_col:
        fig = go.Figure()
        colors = ["#e0b768" if "核准" in str(s) else "#c9a227" if "在建" in str(s) or "建设" in str(s) else "#619cf1" if "推进" in str(s) else "#e57b4c" for s in filtered["status"]]
        fig.add_bar(x=filtered["capacity_mw"], y=filtered["name"], orientation="h", marker_color=colors, text=[f"{v:,.0f} MW" for v in filtered["capacity_mw"]], textposition="outside", textfont=dict(color="#ffffff", size=12), hovertemplate="%{y}<br/>装机容量 %{x:,.0f} MW<extra></extra>")
        fig.update_layout(height=max(330, 65 * len(filtered)), margin=dict(l=10, r=70, t=20, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ffffff"), showlegend=False, xaxis=dict(title=dict(text="装机容量 / MW", font=dict(color="#ffffff")), tickfont=dict(color="#ffffff"), gridcolor="rgba(255,255,255,.16)", zeroline=False), yaxis=dict(tickfont=dict(color="#ffffff"), automargin=True))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with status_col:
        counts = filtered["status"].astype(str).value_counts().reset_index()
        counts.columns = ["status", "count"]
        st.markdown('<div class="panel"><div class="panel-title">建设状态结构</div><div class="panel-note">状态名称沿用项目资料中的原始分类；“示范”等属性不与建设阶段混作时间节点。</div>', unsafe_allow_html=True)
        if not counts.empty:
            fig_status = go.Figure(go.Bar(x=counts["count"], y=counts["status"], orientation="h", marker_color="#c9a227", text=counts["count"], textposition="outside", textfont=dict(color="#ffffff"), hovertemplate="%{y}<br/>项目数 %{x}<extra></extra>"))
            fig_status.update_layout(height=260, margin=dict(l=5, r=35, t=12, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ffffff"), xaxis=dict(dtick=1, gridcolor="rgba(255,255,255,.14)", tickfont=dict(color="#ffffff")), yaxis=dict(tickfont=dict(color="#ffffff")))
            st.plotly_chart(fig_status, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    table = filtered[["name", "capacity_mw", "status", "position_note"]].rename(columns={"name":"项目", "capacity_mw":"规划/建设 MW", "status":"项目状态", "position_note":"坐标说明"})
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.markdown('<div class="source-box"><b>数据说明</b> 项目规模与建设状态依据山东省公开资料；表中容量为规划/建设容量，不等同于已并网装机；页面不对未公开的开工或投运时间进行推断。' + SOURCE_LINKS_HTML + '</div>', unsafe_allow_html=True)


{"发展总览": overview_summary, "时序发展": temporal, "空间分布": spatial, "减碳效益": carbon}[view]()
st.markdown('<div class="footer">风从海上来 · 山东省海上风电交互式数据可视化平台 · 发展总览 / 时序发展 / 空间分布 / 减碳效益</div>', unsafe_allow_html=True)
