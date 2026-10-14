import datetime as dt
import html
from typing import Dict, List
from urllib.parse import quote_plus

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="Market Intelligence | Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# App configuration / universe
# -----------------------------
SECTOR_ETFS = {
    "Communication Services": "XLC",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Energy": "XLE",
    "Financials": "XLF",
    "Health Care": "XLV",
    "Industrials": "XLI",
    "Information Technology": "XLK",
    "Materials": "XLB",
    "Real Estate": "XLRE",
    "Utilities": "XLU",
}

# Human-readable names for the curated company watchlist. Tickers remain visible
# alongside names so users can identify the listed security unambiguously.
COMPANY_DISPLAY_NAMES: Dict[str, str] = {
    "META": "Meta Platforms", "GOOGL": "Alphabet (Class A)", "GOOG": "Alphabet (Class C)",
    "NFLX": "Netflix", "TMUS": "T-Mobile US", "DIS": "Walt Disney", "CMCSA": "Comcast",
    "VZ": "Verizon", "T": "AT&T", "EA": "Electronic Arts",
    "AMZN": "Amazon", "TSLA": "Tesla", "HD": "Home Depot", "MCD": "McDonald's",
    "TJX": "TJX Companies", "LOW": "Lowe's", "BKNG": "Booking Holdings", "NKE": "Nike",
    "SBUX": "Starbucks", "ORLY": "O'Reilly Automotive",
    "WMT": "Walmart", "COST": "Costco", "PG": "Procter & Gamble", "KO": "Coca-Cola",
    "PEP": "PepsiCo", "PM": "Philip Morris International", "MDLZ": "Mondelez International",
    "CL": "Colgate-Palmolive", "MO": "Altria Group", "KHC": "Kraft Heinz",
    "XOM": "Exxon Mobil", "CVX": "Chevron", "COP": "ConocoPhillips", "SLB": "SLB",
    "EOG": "EOG Resources", "MPC": "Marathon Petroleum", "PSX": "Phillips 66",
    "VLO": "Valero Energy", "OXY": "Occidental Petroleum", "WMB": "Williams Companies",
    "BRK-B": "Berkshire Hathaway (B)", "JPM": "JPMorgan Chase", "V": "Visa",
    "MA": "Mastercard", "BAC": "Bank of America", "WFC": "Wells Fargo",
    "GS": "Goldman Sachs", "MS": "Morgan Stanley", "C": "Citigroup", "AXP": "American Express",
    "LLY": "Eli Lilly", "JNJ": "Johnson & Johnson", "ABBV": "AbbVie", "MRK": "Merck",
    "UNH": "UnitedHealth Group", "ABT": "Abbott Laboratories", "ISRG": "Intuitive Surgical",
    "TMO": "Thermo Fisher Scientific", "AMGN": "Amgen", "PFE": "Pfizer",
    "GE": "GE Aerospace", "CAT": "Caterpillar", "RTX": "RTX", "HON": "Honeywell",
    "UNP": "Union Pacific", "ETN": "Eaton", "BA": "Boeing", "DE": "Deere & Company",
    "UPS": "UPS", "LMT": "Lockheed Martin",
    "NVDA": "NVIDIA", "AAPL": "Apple", "MSFT": "Microsoft", "AVGO": "Broadcom",
    "ORCL": "Oracle", "CRM": "Salesforce", "AMD": "Advanced Micro Devices",
    "CSCO": "Cisco Systems", "IBM": "IBM", "QCOM": "Qualcomm",
    "LIN": "Linde", "SHW": "Sherwin-Williams", "APD": "Air Products",
    "ECL": "Ecolab", "NEM": "Newmont", "FCX": "Freeport-McMoRan",
    "CTVA": "Corteva", "NUE": "Nucor", "VMC": "Vulcan Materials", "MLM": "Martin Marietta",
    "PLD": "Prologis", "AMT": "American Tower", "EQIX": "Equinix", "WELL": "Welltower",
    "CCI": "Crown Castle", "CBRE": "CBRE Group",
    "SPG": "Simon Property Group", "PSA": "Public Storage", "O": "Realty Income",
    "DLR": "Digital Realty", "AVB": "AvalonBay Communities", "EQR": "Equity Residential",
    "NEE": "NextEra Energy", "SO": "Southern Company", "DUK": "Duke Energy",
    "CEG": "Constellation Energy", "AEP": "American Electric Power", "SRE": "Sempra",
    "VST": "Vistra", "EXC": "Exelon", "D": "Dominion Energy", "PEG": "Public Service Enterprise Group",
}

# Starter constituent universe. These are representative large-cap names, not a
# guaranteed live market-cap ranking. A later version can add a licensed screener.
SECTOR_COMPANIES: Dict[str, List[str]] = {
    "Communication Services": ["META", "GOOGL", "GOOG", "NFLX", "TMUS", "DIS", "CMCSA", "VZ", "T", "EA"],
    "Consumer Discretionary": ["AMZN", "TSLA", "HD", "MCD", "TJX", "LOW", "BKNG", "NKE", "SBUX", "ORLY"],
    "Consumer Staples": ["WMT", "COST", "PG", "KO", "PEP", "PM", "MDLZ", "CL", "MO", "KHC"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "WMB"],
    "Financials": ["BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "C", "AXP"],
    "Health Care": ["LLY", "JNJ", "ABBV", "MRK", "UNH", "ABT", "ISRG", "TMO", "AMGN", "PFE"],
    "Industrials": ["GE", "CAT", "RTX", "HON", "UNP", "ETN", "BA", "DE", "UPS", "LMT"],
    "Information Technology": ["NVDA", "AAPL", "MSFT", "AVGO", "ORCL", "CRM", "AMD", "CSCO", "IBM", "QCOM"],
    "Materials": ["LIN", "SHW", "APD", "ECL", "FCX", "NEM", "NUE", "VMC", "MLM", "DOW"],
    "Real Estate": ["PLD", "AMT", "EQIX", "WELL", "SPG", "PSA", "O", "DLR", "CCI", "CBRE"],
    "Utilities": ["NEE", "SO", "DUK", "CEG", "AEP", "SRE", "VST", "EXC", "PEG", "XEL"],
}

ETF_UNIVERSE = {
    "SPY — S&P 500": "SPY",
    "VOO — S&P 500": "VOO",
    "QQQ — Nasdaq 100": "QQQ",
    "IWM — Russell 2000": "IWM",
    "DIA — Dow Jones": "DIA",
    "EFA — Developed Markets": "EFA",
    "EEM — Emerging Markets": "EEM",
    "TLT — 20+ Year Treasuries": "TLT",
    "IEF — 7–10 Year Treasuries": "IEF",
    "SHY — 1–3 Year Treasuries": "SHY",
    "LQD — Investment Grade Credit": "LQD",
    "HYG — High Yield Credit": "HYG",
    "GLD — Gold": "GLD",
    "SLV — Silver": "SLV",
    "USO — Oil": "USO",
    **{f"{name} ETF ({ticker})": ticker for name, ticker in SECTOR_ETFS.items()},
}

FX_UNIVERSE = {
    "EUR/USD": "EURUSD=X",
    "USD/JPY": "JPY=X",
    "GBP/USD": "GBPUSD=X",
    "USD/CHF": "CHF=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "CAD=X",
    "NZD/USD": "NZDUSD=X",
    "USD/NOK": "NOK=X",
    "USD/SEK": "SEK=X",
}

# Major commodity futures benchmarks available through Yahoo Finance.
# This is a practical watchlist of liquid global contracts, not a live ranking
# by current exchange trading volume. Futures prices may be delayed.
COMMODITY_UNIVERSE = {
    # Precious metals are grouped separately from the broader commodity complex.
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Platinum": "PL=F",
    # Energy
    "WTI Crude Oil": "CL=F",
    "Brent Crude Oil": "BZ=F",
    "Natural Gas": "NG=F",
    # Industrial metals
    "Copper": "HG=F",
    # Agriculture
    "Corn": "ZC=F",
    "Soybeans": "ZS=F",
    "Wheat": "ZW=F",
    "Coffee": "KC=F",
    "Sugar": "SB=F",
    "Cotton": "CT=F",
}

PRECIOUS_METALS = ["Gold", "Silver", "Platinum"]
OTHER_COMMODITIES = [name for name in COMMODITY_UNIVERSE if name not in PRECIOUS_METALS]
COMMODITY_CATEGORIES = {
    "Precious Metals": PRECIOUS_METALS,
    "Energy": ["WTI Crude Oil", "Brent Crude Oil", "Natural Gas"],
    "Industrial Metals": ["Copper"],
    "Agriculture": ["Corn", "Soybeans", "Wheat", "Coffee", "Sugar", "Cotton"],
}

PERIOD_OPTIONS = {
    "1D": ("1d", "5m"),
    "5D": ("5d", "15m"),
    "1M": ("1mo", "1d"),
    "3M": ("3mo", "1d"),
    "6M": ("6mo", "1d"),
    "YTD": ("ytd", "1d"),
    "1Y": ("1y", "1d"),
    "5Y": ("5y", "1wk"),
    "10Y": ("10y", "1mo"),
}

# -----------------------------
# Styling — dark market terminal
# -----------------------------
st.markdown(
    """
    <style>
      .mi-trend-summary-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; margin:10px 0 8px; }
      .mi-trend-tile { min-width:0; border:1px solid #26364F; border-radius:12px; padding:10px 9px; background:linear-gradient(145deg,#142036,#101827); }
      .mi-trend-tile-label { color:#9FB2CB; font-size:10px; font-weight:800; letter-spacing:.07em; line-height:1.3; }
      .mi-trend-tile-name { color:#E7EDF7; font-size:12px; font-weight:700; margin-top:7px; line-height:1.3; overflow-wrap:anywhere; }
      .mi-trend-tile-detail { color:#6EE7A0; font-size:16px; font-weight:800; margin-top:4px; }
      .mi-trend-tile-ticker { color:#91A2BA; font-size:10px; margin-top:2px; }
      .mi-event-summary-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; margin:10px 0 16px; }
      .mi-event-summary-card { min-width:0; background:linear-gradient(145deg,#142036,#101827); border:1px solid #26364F; border-radius:11px; padding:10px 11px; }
      .mi-event-summary-label { color:#9FB2CB; font-size:10px; font-weight:750; letter-spacing:.035em; line-height:1.35; }
      .mi-event-summary-name { color:#E7EDF7; font-size:12px; font-weight:700; line-height:1.35; margin-top:5px; overflow-wrap:anywhere; }
      .mi-event-summary-value { font-size:16px; font-weight:800; line-height:1.25; margin-top:5px; }
      .mi-event-summary-value.positive { color:#6EE7A0; }
      .mi-event-summary-value.negative { color:#FDA4AF; }
      .mi-event-summary-value.neutral { color:#E7EDF7; }
      @media (max-width: 520px) { .mi-trend-summary-grid { gap:6px; } .mi-trend-tile { padding:8px 6px; } .mi-trend-tile-label { font-size:9px; letter-spacing:.02em; } .mi-trend-tile-name { font-size:11px; } .mi-trend-tile-detail { font-size:14px; } .mi-event-summary-grid { gap:6px; } .mi-event-summary-card { padding:9px 7px; } .mi-event-summary-label { font-size:9px; letter-spacing:0; } .mi-event-summary-name { font-size:10px; } .mi-event-summary-value { font-size:14px; } }
    :root {
      --mi-bg: #0b1120;
      --mi-panel: #111b2e;
      --mi-panel-2: #162238;
      --mi-border: #26364f;
      --mi-text: #e7edf7;
      --mi-muted: #91a1b9;
      --mi-accent: #60a5fa;
      --mi-green: #34d399;
      --mi-red: #fb7185;
    }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
      background: var(--mi-bg) !important;
      color: var(--mi-text) !important;
    }
    [data-testid="stHeader"] { background: rgba(11,17,32,0.92) !important; }
    [data-testid="stSidebar"] { background: #0e1728 !important; border-right: 1px solid var(--mi-border); }
    [data-testid="stSidebar"] * { color: var(--mi-text); }
    .block-container { padding-top: 1.15rem; padding-bottom: 2rem; max-width: 1500px; }
    h1, h2, h3 { letter-spacing: -0.025em; color: #f3f6fc !important; }
    h1 { font-size: clamp(1.55rem, 3vw, 2.15rem) !important; }
    h2 { font-size: clamp(1.2rem, 2.4vw, 1.55rem) !important; }
    h3 { font-size: 1.08rem !important; }
    p, label, [data-testid="stMarkdownContainer"] { color: var(--mi-text); }
    [data-testid="stCaptionContainer"] { color: var(--mi-muted) !important; }
    [data-testid="stMetric"] {
      background: linear-gradient(145deg, #142039, #10192a) !important;
      padding: 15px 17px; border-radius: 13px;
      border: 1px solid var(--mi-border); box-shadow: 0 6px 18px rgba(0,0,0,.12);
    }
    [data-testid="stMetricLabel"] { color: var(--mi-muted) !important; font-size: .84rem !important; }
    [data-testid="stMetricValue"] { color: #f8fafc !important; font-weight: 650; }
    [data-testid="stMetricDelta"] { font-weight: 650; }
    [data-testid="stDataFrame"] { border: 1px solid var(--mi-border); border-radius: 10px; overflow: hidden; }
    [data-testid="stDataFrame"] iframe { border-radius: 10px; }
    [data-testid="stVerticalBlockBorderWrapper"] { border-color: var(--mi-border) !important; background: var(--mi-panel); }
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
      background: var(--mi-panel) !important; border-color: var(--mi-border) !important;
    }
    /* High-contrast search field for the market scanner, including iOS Safari. */
    [data-testid="stTextInput"] div[data-baseweb="input"] > div {
      background: #111b2e !important;
      border: 1px solid #3a4b66 !important;
      border-radius: 10px !important;
      box-shadow: none !important;
    }
    [data-testid="stTextInput"] input {
      color: #f3f6fc !important;
      -webkit-text-fill-color: #f3f6fc !important;
      caret-color: #93c5fd !important;
      background: transparent !important;
    }
    [data-testid="stTextInput"] input::placeholder {
      color: #a8b5c8 !important;
      -webkit-text-fill-color: #a8b5c8 !important;
      opacity: 1 !important;
    }
    [data-testid="stTextInput"] div[data-baseweb="input"]:focus-within > div {
      border-color: #60a5fa !important;
      box-shadow: 0 0 0 1px #60a5fa !important;
    }
    /* Keep the chart and instrument controls visually grouped on mobile. */
    [data-testid="stPlotlyChart"] { margin-bottom: -.35rem; }
    [data-testid="stExpander"] { margin-top: .2rem; }
    /* Keep native Streamlit expanders readable against the navy terminal theme. */
    [data-testid="stExpander"] details,
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary:hover,
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
      background: #0f192b !important;
      color: #e7edf7 !important;
      border-color: #26364f !important;
    }
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary span,
    [data-testid="stExpander"] summary svg,
    [data-testid="stExpander"] summary * {
      color: #e7edf7 !important;
      fill: #e7edf7 !important;
      -webkit-text-fill-color: #e7edf7 !important;
    }
    .mi-brief-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; margin:.7rem 0 .35rem; }
    .mi-brief-card { min-width:0; background:linear-gradient(145deg,#142039,#10192a); border:1px solid #26364f; border-radius:12px; padding:11px 12px; }
    .mi-brief-label { color:#9fb2cb; font-size:.76rem; line-height:1.3; }
    .mi-brief-value { color:#f3f6fc; font-size:1.2rem; line-height:1.3; font-weight:750; margin-top:5px; overflow-wrap:anywhere; }
    .mi-brief-move { display:inline-block; border-radius:7px; padding:3px 7px; margin-top:6px; font-size:.85rem; font-weight:750; }
    .mi-brief-move.positive { color:#6ee7a0; background:rgba(52,211,153,.12); }
    .mi-brief-move.negative { color:#fda4af; background:rgba(251,113,133,.12); }
    .mi-brief-move.neutral { color:#cbd5e1; background:rgba(148,163,184,.12); }
    .mi-brief-detail { color:#91a1b9; font-size:.75rem; margin-top:5px; line-height:1.3; }
    .mi-event-list { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:7px; margin:.45rem 0 .6rem; }
    .mi-event-item { min-width:0; padding:9px 10px; background:#111b2e; border:1px solid #26364f; border-radius:9px; }
    .mi-event-date { color:#93c5fd; font-size:.76rem; font-weight:800; }
    .mi-event-name { color:#e7edf7; font-size:.85rem; line-height:1.35; margin-top:3px; overflow-wrap:anywhere; }
    .mi-event-source { color:#91a1b9; font-size:.72rem; margin-top:4px; }
    @media (max-width: 520px) {
      .mi-brief-grid { grid-template-columns:repeat(2,minmax(0,1fr)); gap:7px; }
      .mi-brief-card { padding:9px 10px; }
      .mi-brief-value { font-size:1.05rem; }
      .mi-brief-grid .mi-brief-card:last-child { grid-column:1 / -1; }
      .mi-event-list { grid-template-columns:repeat(2,minmax(0,1fr)); gap:6px; }
      .mi-event-item { padding:8px; }
      .mi-event-name { font-size:.8rem; }
    }
    /* Consistent dark-theme buttons, including the main Refresh market data control. */
    .stButton > button, [data-testid="stFormSubmitButton"] button {
      background: #17345a !important;
      color: #f8fafc !important;
      -webkit-text-fill-color: #f8fafc !important;
      border: 1px solid #3b82f6 !important;
      border-radius: 9px !important;
      font-weight: 650 !important;
      box-shadow: none !important;
    }
    .stButton > button *, [data-testid="stFormSubmitButton"] button * {
      color: #f8fafc !important;
      -webkit-text-fill-color: #f8fafc !important;
    }
    .stButton > button:hover, [data-testid="stFormSubmitButton"] button:hover {
      background: #214775 !important;
      border-color: #60a5fa !important;
    }
    .stButton > button:focus-visible, [data-testid="stFormSubmitButton"] button:focus-visible {
      outline: 2px solid #93c5fd !important;
      outline-offset: 2px !important;
    }
    button[kind="secondary"], button[kind="primary"] { border-radius: 9px !important; }
    div[data-testid="stDownloadButton"] button {
      background: #17345a !important; color: #f8fafc !important;
      border: 1px solid #3b82f6 !important; font-weight: 650 !important;
    }
    div[data-testid="stDownloadButton"] button * { color: #f8fafc !important; }
    div[data-testid="stDownloadButton"] button:hover { background: #214775 !important; border-color: #60a5fa !important; }
    /* Dark-theme styling for external news search links (Streamlit link buttons). */
    div[data-testid="stLinkButton"] a,
    div[data-testid="stLinkButton"] a:link,
    div[data-testid="stLinkButton"] a:visited {
      background: #17345a !important;
      color: #f8fafc !important;
      -webkit-text-fill-color: #f8fafc !important;
      border: 1px solid #3b82f6 !important;
      border-radius: 9px !important;
      font-weight: 650 !important;
      box-shadow: none !important;
      text-decoration: none !important;
    }
    div[data-testid="stLinkButton"] a *,
    div[data-testid="stLinkButton"] a p,
    div[data-testid="stLinkButton"] a span {
      color: #f8fafc !important;
      -webkit-text-fill-color: #f8fafc !important;
    }
    div[data-testid="stLinkButton"] a:hover,
    div[data-testid="stLinkButton"] a:focus-visible {
      background: #214775 !important;
      border-color: #60a5fa !important;
      color: #ffffff !important;
      -webkit-text-fill-color: #ffffff !important;
    }
    .mi-brand { display:flex; align-items:center; gap:.7rem; margin:.15rem 0 .35rem; }
    .mi-mark { display:inline-flex; align-items:center; justify-content:center; width:38px; height:38px; border-radius:11px; background:#17345a; color:#93c5fd; font-size:1.25rem; border:1px solid #2a4c78; }
    .mi-title { font-size:1.35rem; font-weight:750; letter-spacing:.045em; color:#f8fafc; }
    .mi-subtitle { color:var(--mi-muted); font-size:.86rem; margin-top:.1rem; }
    .mi-eyebrow { color:#7dd3fc; font-size:.72rem; font-weight:750; letter-spacing:.13em; text-transform:uppercase; }
    .mi-section-note { color:var(--mi-muted); font-size:.82rem; margin-top:-.4rem; margin-bottom:.65rem; }
    .mi-market-section-title { margin:.1rem 0 .45rem !important; font-size:1.22rem !important; line-height:1.25 !important; color:#e7edf7 !important; }
    @media (max-width: 768px) { .mi-market-section-title { font-size:1.12rem !important; } }
    .mi-chip { display:inline-block; padding:.2rem .5rem; border-radius:6px; background:#172944; border:1px solid #294568; color:#93c5fd; font-size:.73rem; }
    .mi-jump-nav { position:sticky; top:.25rem; z-index:50; display:flex; gap:.45rem; overflow-x:auto; white-space:nowrap; padding:.55rem; margin:.6rem 0 1rem; border:1px solid #26364f; border-radius:12px; background:rgba(17,27,46,.98); -webkit-backdrop-filter:none; backdrop-filter:none; }
    .mi-jump-nav a { display:inline-block; text-decoration:none !important; color:#dbeafe !important; background:#172944; border:1px solid #294568; border-radius:8px; padding:.42rem .7rem; font-size:.82rem; font-weight:650; }
    .mi-jump-nav a:active, .mi-jump-nav a:hover { background:#24456d; }
    .mi-section-band { --section-accent:#60a5fa; display:flex; align-items:center; gap:.75rem; padding:.8rem .85rem; margin:1.35rem 0 .7rem; border:1px solid var(--mi-border); border-left:4px solid var(--section-accent); border-radius:11px; background:linear-gradient(100deg, color-mix(in srgb, var(--section-accent) 10%, #111b2e), #111b2e 70%); scroll-margin-top:7rem; }
    .mi-section-icon { display:flex; align-items:center; justify-content:center; width:2.4rem; height:2.4rem; flex:0 0 2.4rem; border-radius:9px; background:color-mix(in srgb, var(--section-accent) 18%, #111b2e); color:var(--section-accent); font-size:1.25rem; }
    .mi-section-kicker { color:var(--section-accent) !important; opacity:1 !important; font-size:.72rem; font-weight:800; letter-spacing:.13em; text-transform:uppercase; text-shadow:0 0 1px rgba(255,255,255,.10); }
    .mi-section-band h2 { margin:.08rem 0 0 !important; font-size:1.18rem !important; }
    @media (max-width: 768px) {
      .block-container { padding: 1rem .7rem 1.5rem .7rem; }
      .mi-section-band { scroll-margin-top: 7.5rem; }
      [data-testid="stMetric"] { padding: 10px 11px; }
      [data-testid="stMetricValue"] { font-size: 1.35rem !important; }
      [data-testid="stDataFrame"] { font-size: .82rem; filter:none !important; opacity:1 !important; }
      [data-testid="stDataFrame"] canvas { image-rendering:auto; }
      [data-testid="stDataFrame"] [role="columnheader"],
      [data-testid="stDataFrame"] [role="columnheader"] *,
      [data-testid="stTable"] thead th,
      [data-testid="stTable"] thead th *,
      table thead th,
      table thead th * {
        color:#FFFFFF !important;
        font-weight:800 !important;
      }
      /* Hide pandas row-index headers/cells if a renderer ignores Styler.hide(). */
      [data-testid="stTable"] th.row_heading,
      [data-testid="stTable"] th.blank,
      [data-testid="stTable"] th.row_heading + td,
      [data-testid="stTable"] thead th.blank {
        display:none !important;
      }
      [data-testid="stDataFrame"] [role="grid"] { filter:none !important; opacity:1 !important; }
      .mi-title { font-size: 1.1rem; }
      .mi-mark { width:32px; height:32px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Data functions
# -----------------------------
@st.cache_data(ttl=300, show_spinner=False)
def get_history(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Download history. Cache for five minutes to reduce repeat requests."""
    try:
        data = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
            threads=False,
        )
        if data is None or data.empty:
            return pd.DataFrame()
        # yfinance may return a MultiIndex even for one ticker.
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        data = data.rename_axis("Date").reset_index()
        if "Date" not in data.columns:
            data = data.rename(columns={data.columns[0]: "Date"})
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
        data = data.dropna(subset=["Date", "Close"])
        return data
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=900, show_spinner=False)
def get_recent_news(ticker: str, limit: int = 5) -> list:
    """Fetch recent Yahoo Finance headlines; gracefully handle provider schema changes."""
    try:
        items = yf.Ticker(ticker).news or []
        parsed = []
        for item in items:
            if not isinstance(item, dict):
                continue
            content = item.get("content", item)
            if not isinstance(content, dict):
                continue
            title = content.get("title") or item.get("title")
            if not title:
                continue
            url_data = content.get("canonicalUrl") or content.get("clickThroughUrl") or {}
            url = url_data.get("url") if isinstance(url_data, dict) else url_data
            provider_data = content.get("provider") or item.get("publisher") or {}
            provider = provider_data.get("displayName") if isinstance(provider_data, dict) else provider_data
            published = content.get("pubDate") or item.get("providerPublishTime")
            if isinstance(published, (int, float)):
                published = dt.datetime.fromtimestamp(published, tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            elif isinstance(published, str) and "T" in published:
                try:
                    published = dt.datetime.fromisoformat(published.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M UTC")
                except Exception:
                    pass
            parsed.append({"title": str(title), "url": url, "provider": provider or "Yahoo Finance", "published": published or "Date unavailable"})
            if len(parsed) >= limit:
                break
        return parsed
    except Exception:
        return []


def classify_news_context(title: str) -> str:
    """Label headline themes without asserting that they caused a price move."""
    text = title.lower()
    themes = [
        (("earnings", "quarterly results", "revenue", "profit", "eps", "results beat", "results miss"), "Earnings / financial results"),
        (("forecast", "guidance", "outlook", "raises full-year", "cuts full-year"), "Company outlook / guidance"),
        (("upgrade", "downgrade", "price target", "analyst rating", "initiates coverage"), "Analyst view / price target"),
        (("acquisition", "merger", "buyout", "takeover", "deal to buy", "divest"), "M&A / corporate action"),
        (("regulator", "lawsuit", "investigation", "court", "antitrust", "fda"), "Regulatory / legal development"),
        (("interest rate", "federal reserve", "fed signals", "inflation", "treasury yield", "jobs report"), "Macro / interest-rate backdrop"),
        (("oil price", "crude", "opec", "natural gas", "copper prices", "gold prices"), "Commodity / input-price backdrop"),
        (("launches", "product launch", "new product", "contract win", "partnership"), "Product / commercial development"),
    ]
    for keywords, label in themes:
        if any(keyword in text for keyword in keywords):
            return label
    return "General company / market headline — inspect the article for context"


@st.cache_data(ttl=900, show_spinner=False)
def get_return_history(ticker: str) -> pd.DataFrame:
    """Fetch enough daily history to calculate all historical return horizons."""
    return get_history(ticker, "2y", "1d")


@st.cache_data(ttl=900, show_spinner=False)
def get_30d_trend_data(instrument_specs: tuple) -> pd.DataFrame:
    """Fetch daily history in batches and calculate rolling trend/activity indicators."""
    if not instrument_specs:
        return pd.DataFrame()

    ticker_to_spec = {ticker: (display_name, ticker, asset_class)
                      for display_name, ticker, asset_class in instrument_specs}
    tickers = list(ticker_to_spec.keys())
    histories = {}

    # Batch requests to reduce latency and provider load.
    for start in range(0, len(tickers), 25):
        chunk = tickers[start:start + 25]
        try:
            raw = yf.download(
                tickers=chunk, period="3mo", interval="1d", auto_adjust=True,
                progress=False, threads=True, group_by="ticker", multi_level_index=True,
            )
            if raw is None or raw.empty:
                continue
            for ticker in chunk:
                try:
                    if isinstance(raw.columns, pd.MultiIndex):
                        if ticker in raw.columns.get_level_values(0):
                            one = raw[ticker].copy()
                        elif ticker in raw.columns.get_level_values(1):
                            one = raw.xs(ticker, axis=1, level=1).copy()
                        else:
                            continue
                    else:
                        if len(chunk) != 1:
                            continue
                        one = raw.copy()
                    one.columns = [str(c[0] if isinstance(c, tuple) else c).title() for c in one.columns]
                    if "Close" not in one.columns:
                        continue
                    one = one[[c for c in ["Close", "Volume"] if c in one.columns]].copy()
                    one = one.dropna(subset=["Close"]).sort_index()
                    if not one.empty:
                        histories[ticker] = one
                except Exception:
                    continue
        except Exception:
            continue

    rows = []
    for ticker, (display_name, _, asset_class) in ticker_to_spec.items():
        hist = histories.get(ticker)
        if hist is None or hist.empty:
            rows.append({
                "Instrument": display_name, "Ticker": ticker, "Asset class": asset_class,
                "Last": None, "Daily %": None, "5D %": None, "30D %": None,
                "Acceleration": None, "Volume ratio": None, "20D volatility": None,
                "Signal": "Data unavailable", "As of": "Unavailable",
            })
            continue

        close = pd.to_numeric(hist["Close"], errors="coerce").dropna()
        if close.empty:
            continue
        latest = float(close.iloc[-1])
        daily = (latest / float(close.iloc[-2]) - 1) * 100 if len(close) >= 2 and close.iloc[-2] else None
        five_day = (latest / float(close.iloc[-6]) - 1) * 100 if len(close) >= 6 and close.iloc[-6] else None
        thirty_day = (latest / float(close.iloc[-22]) - 1) * 100 if len(close) >= 22 and close.iloc[-22] else None
        acceleration = (five_day - thirty_day / 6.0) if five_day is not None and thirty_day is not None else None

        volume_ratio = None
        if "Volume" in hist.columns:
            volume = pd.to_numeric(hist["Volume"], errors="coerce").dropna()
            # Compare latest 5 sessions with the preceding 20 sessions.
            if len(volume) >= 25:
                recent_vol = float(volume.iloc[-5:].mean())
                baseline_vol = float(volume.iloc[-25:-5].mean())
                if baseline_vol > 0:
                    volume_ratio = recent_vol / baseline_vol

        daily_returns = close.pct_change().dropna()
        volatility = float(daily_returns.iloc[-20:].std() * (252 ** 0.5) * 100) if len(daily_returns) >= 20 else None

        if thirty_day is not None and five_day is not None and thirty_day > 0 and five_day > 0 and acceleration is not None and acceleration > 0:
            signal = "Strengthening"
        elif thirty_day is not None and thirty_day > 0 and five_day is not None and five_day < 0:
            signal = "Cooling"
        elif thirty_day is not None and thirty_day < 0 and five_day is not None and five_day > 0:
            signal = "Rebounding"
        elif thirty_day is not None and thirty_day < 0 and five_day is not None and five_day < 0:
            signal = "Weakening"
        else:
            signal = "Mixed"

        # Spot FX turnover is decentralised; do not treat Yahoo FX volume as global activity.
        if asset_class in ("Stocks", "ETFs", "Sectors") and volume_ratio is not None and volume_ratio >= 1.5:
            signal = "Unusual activity"

        rows.append({
            "Instrument": display_name, "Ticker": ticker, "Asset class": asset_class,
            "Last": latest, "Daily %": daily, "5D %": five_day, "30D %": thirty_day,
            "Acceleration": acceleration, "Volume ratio": volume_ratio,
            "20D volatility": volatility, "Signal": signal,
            "As of": pd.Timestamp(close.index[-1]).strftime("%Y-%m-%d"),
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=900, show_spinner=False)
def get_snapshot(tickers: tuple) -> pd.DataFrame:
    """Build a simple latest-price snapshot for a set of tickers."""
    rows = []
    for ticker in tickers:
        hist = get_history(ticker, "5d", "1d")
        if hist.empty:
            rows.append({"Ticker": ticker, "Last": None, "Daily %": None, "As of": "Unavailable"})
            continue
        hist = hist.sort_values("Date")
        last = float(hist["Close"].iloc[-1])
        previous = float(hist["Close"].iloc[-2]) if len(hist) > 1 else None
        change = ((last / previous) - 1) * 100 if previous else None
        rows.append({
            "Ticker": ticker,
            "Last": last,
            "Daily %": change,
            "As of": pd.Timestamp(hist["Date"].iloc[-1]).strftime("%Y-%m-%d"),
        })
    return pd.DataFrame(rows)


def color_daily_pct(value):
    """Color daily percentage changes green for gains and red for losses."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if pd.isna(number):
        return ""
    if number > 0:
        return "color: #34d399; font-weight: 700;"
    if number < 0:
        return "color: #fb7185; font-weight: 700;"
    return "color: #94a3b8;"




def style_market_table(data: pd.DataFrame, formats: dict | None = None) -> pd.io.formats.style.Styler:
    """Apply consistent dark terminal styling to all dataframe tables."""
    # Reset inherited indices (e.g. after filtering/sorting) and hide the index
    # in the Styler. The CSS below also hides any index cells Streamlit may render.
    clean_data = data.reset_index(drop=True)
    styler = clean_data.style.hide(axis="index")
    if formats:
        styler = styler.format(formats, na_rep="—")
    # Explicit cell backgrounds are needed because pandas Styler otherwise
    # renders light cells that clash with the app's dark theme on some versions.
    styler = styler.set_properties(**{
        "background-color": "#111B2E",
        "color": "#E7EDF7",
        "border-color": "#26364F",
    })
    styler = styler.set_table_styles([
        {"selector": "th", "props": [
            ("background-color", "#162238"),
            ("color", "#FFFFFF"),
            ("font-weight", "800"),
            ("border-color", "#26364F"),
        ]},
        {"selector": "thead th", "props": [
            ("color", "#FFFFFF"),
            ("font-weight", "800"),
        ]},
        {"selector": "td", "props": [("border-color", "#26364F")]},
    ], overwrite=False)
    if "Daily %" in data.columns:
        styler = styler.map(color_daily_pct, subset=["Daily %"])
    return styler

def format_price(value, ticker: str) -> str:
    if pd.isna(value):
        return "—"
    return f"{value:,.4f}" if "=X" in ticker or ticker.endswith("=X") else f"{value:,.2f}"


def render_compact_market_rows(data: pd.DataFrame, label_column: str) -> str:
    """Render a compact, dark-themed market table that stays readable on phones."""
    rows_html = []
    for _, row in data.iterrows():
        label = html.escape(str(row.get(label_column, "—")))
        latest = html.escape(str(row.get("Latest", "—")))
        move = str(row.get("Daily move", "—"))
        safe_move = html.escape(move)
        stripped = move.strip()
        if stripped.startswith("+"):
            move_class = "positive"
        elif stripped.startswith("-") and not stripped.startswith(("-0.0", "-0.00", "-0.0 bps")):
            move_class = "negative"
        else:
            move_class = "neutral"
        rows_html.append(
            "<div class='mi-market-row'>"
            f"<div class='mi-market-name'>{label}</div>"
            f"<div class='mi-market-latest'>{latest}</div>"
            f"<div class='mi-market-move {move_class}'>{safe_move}</div>"
            "</div>"
        )
    body = "".join(rows_html)
    return (
        "<style>"
        ".mi-market-table{width:100%;overflow:hidden;border:1px solid #26364f;border-radius:12px;"
        "background:#111b2e;color:#e7edf7;font-size:.88rem;line-height:1.25;margin:.35rem 0 .6rem;}"
        ".mi-market-head,.mi-market-row{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,.78fr) minmax(0,.72fr);"
        "gap:.35rem;align-items:center;padding:.68rem .7rem;}"
        ".mi-market-head{background:#162238;color:#9fb0c8;font-size:.7rem;font-weight:750;letter-spacing:.04em;"
        "text-transform:uppercase;border-bottom:1px solid #26364f;}"
        ".mi-market-row{border-bottom:1px solid #223149;min-height:42px;}"
        ".mi-market-row:last-child{border-bottom:0;}"
        ".mi-market-name{font-weight:600;color:#e7edf7;overflow-wrap:anywhere;}"
        ".mi-market-latest{font-variant-numeric:tabular-nums;white-space:nowrap;color:#dbe5f3;}"
        ".mi-market-move{justify-self:start;font-size:.76rem;font-weight:750;font-variant-numeric:tabular-nums;"
        "white-space:nowrap;padding:.25rem .38rem;border-radius:6px;}"
        ".mi-market-move.positive{color:#6ee7a8;background:#12352e;}"
        ".mi-market-move.negative{color:#fda4af;background:#3a202e;}"
        ".mi-market-move.neutral{color:#b7c3d4;background:#202d42;}"
        "@media(max-width:480px){.mi-market-table{font-size:.82rem}.mi-market-head,.mi-market-row{gap:.25rem;padding:.62rem .48rem;"
        "grid-template-columns:minmax(0,1.12fr) minmax(0,.75fr) minmax(0,.72fr)}"
        ".mi-market-head{font-size:.64rem}.mi-market-move{font-size:.7rem;padding:.22rem .28rem}}"
        "</style>"
        "<div class='mi-market-table'>"
        "<div class='mi-market-head'><div>" + html.escape(label_column) + "</div><div>Latest</div><div>Daily move</div></div>"
        + body + "</div>"
    )


def compact_observation_times(data: pd.DataFrame) -> pd.DataFrame:
    """Shorten provider observation timestamps for narrow mobile tables."""
    result = data.copy()
    if "As of" in result.columns:
        def short_time(value):
            try:
                stamp = pd.to_datetime(value, errors="raise")
                return stamp.strftime("%d %b %Y")
            except (TypeError, ValueError, OverflowError):
                return value
        result["As of"] = result["As of"].map(short_time)
    return result


def returns_table(data: pd.DataFrame) -> pd.DataFrame:
    """Returns based on latest available adjusted close and historical reference."""
    if data.empty or "Close" not in data:
        return pd.DataFrame(columns=["Period", "Reference date", "Reference close", "Latest close", "Return"])
    d = data.dropna(subset=["Close"]).sort_values("Date").copy()
    if d.empty:
        return pd.DataFrame()
    latest_date = pd.Timestamp(d["Date"].iloc[-1])
    latest = float(d["Close"].iloc[-1])
    rows = []
    lookbacks = [
        ("1D", pd.Timedelta(days=1)),
        ("5D", pd.Timedelta(days=7)),
        ("1M", pd.DateOffset(months=1)),
        ("3M", pd.DateOffset(months=3)),
        ("6M", pd.DateOffset(months=6)),
        ("YTD", dt.datetime(latest_date.year, 1, 1)),
        ("1Y", pd.DateOffset(years=1)),
    ]
    for label, delta in lookbacks:
        if label == "YTD":
            target = pd.Timestamp(delta) - pd.Timedelta(days=1)
        else:
            target = latest_date - delta
        eligible = d[d["Date"] <= target]
        if eligible.empty:
            ref_date, ref_price, ret = "Insufficient history", None, None
        else:
            ref = eligible.iloc[-1]
            ref_date = pd.Timestamp(ref["Date"]).strftime("%Y-%m-%d")
            ref_price = float(ref["Close"])
            ret = (latest / ref_price - 1) * 100 if ref_price else None
        rows.append({
            "Period": label,
            "Reference date": ref_date,
            "Reference close": ref_price,
            "Latest close": latest,
            "Return (%)": ret,
        })
    return pd.DataFrame(rows)


def render_price_chart(data: pd.DataFrame, ticker: str, interval_label: str):
    if data.empty:
        st.warning("No price history was returned for this instrument. Try another period or ticker.")
        return
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data["Date"], y=data["Close"], mode="lines",
        name=ticker, line=dict(width=2, color="#16A085"),
        fill="tozeroy", fillcolor="rgba(22,160,133,0.08)",
        hovertemplate="%{x}<br>Price: %{y:,.4f}<extra></extra>",
    ))
    fig.update_layout(
        template="plotly_dark",
        # Explicitly set both chart backgrounds: Streamlit's default Plotly theme
        # can otherwise render this chart with a white canvas on a dark page.
        paper_bgcolor="#0B1220",
        plot_bgcolor="#0B1220",
        font=dict(color="#F8FAFC", size=12),
        hoverlabel=dict(bgcolor="#172033", bordercolor="#475569", font=dict(color="#FFFFFF", size=12)),
        height=340, margin=dict(l=42, r=12, t=12, b=36),
        xaxis_title=None, yaxis_title="Price",
        hovermode="x unified", showlegend=False,
    )
    fig.update_xaxes(
        showgrid=False, color="#F8FAFC", linecolor="#475569",
        tickfont=dict(color="#F8FAFC", size=11), ticks="outside", tickcolor="#64748B",
    )
    fig.update_yaxes(
        gridcolor="rgba(148,163,184,0.20)", color="#F8FAFC",
        zeroline=False, tickfont=dict(color="#F8FAFC", size=11), ticks="outside", tickcolor="#64748B",
    )
    st.plotly_chart(fig, width="stretch", theme=None, config={"responsive": True, "displayModeBar": False})
    st.caption(f"Chart interval: {interval_label}. For daily bars, the x-axis date represents the trading session; the 00:00 timestamp is not the market-close time. Data timing depends on Yahoo Finance and is not guaranteed real-time.")


def render_instrument(ticker: str, period_label: str, name: str = ""):
    period, interval = PERIOD_OPTIONS[period_label]
    with st.spinner(f"Loading {ticker} history…"):
        data = get_history(ticker, period, interval)
    if data.empty:
        st.error(f"Unable to retrieve history for {ticker}. The data provider may not support this symbol or interval.")
        return
    data = data.sort_values("Date").reset_index(drop=True)
    latest = float(data["Close"].iloc[-1])
    prev = float(data["Close"].iloc[-2]) if len(data) > 1 else None
    daily_change = ((latest / prev) - 1) * 100 if prev else None
    title = name or ticker
    st.subheader(title)
    m1, m2, m3 = st.columns(3)
    m1.metric("Latest available price", format_price(latest, ticker))
    m2.metric("Last bar move", f"{daily_change:+.2f}%" if daily_change is not None else "—")
    last_stamp = pd.Timestamp(data["Date"].iloc[-1])
    if interval == "1d":
        m3.metric("Last session date", last_stamp.strftime("%d %b %Y"))
    else:
        m3.metric("Last data point", last_stamp.strftime("%d %b %Y %H:%M"))
    render_price_chart(data, ticker, interval)
    st.markdown("#### Historical returns")
    with st.spinner("Loading daily history for return calculations…"):
        return_data = get_return_history(ticker)
    table = returns_table(return_data if not return_data.empty else data)
    st.dataframe(
        style_market_table(table, {"Reference close": "{:,.4f}", "Latest close": "{:,.4f}", "Return (%)": "{:+.2f}%"}),
        use_container_width=True, hide_index=True
    )
    csv = table.to_csv(index=False).encode("utf-8")
    st.download_button("Download return table (CSV)", csv, file_name=f"{ticker.replace('=', '_')}_returns.csv", mime="text/csv")
    st.caption("Returns use adjusted closing prices where the provider supplies them. Intraday periods can have limited history; unavailable reference dates are shown as insufficient history.")


def render_explorer_view(ticker: str, period_label: str, name: str = ""):
    """Mobile-friendly Instrument Explorer layout inspired by the design mock-up."""
    period, interval = PERIOD_OPTIONS[period_label]
    with st.spinner(f"Loading {ticker} history…"):
        data = get_history(ticker, period, interval)
    if data.empty:
        st.warning(f"No price history was returned for {ticker}. Try another period or instrument.")
        return

    data = data.sort_values("Date").reset_index(drop=True)
    latest = float(data["Close"].iloc[-1])
    previous = float(data["Close"].iloc[-2]) if len(data) > 1 else None
    bar_move = ((latest / previous) - 1) * 100 if previous else None
    display_name = name or ticker

    # Compact summary row instead of the large three-metric layout used elsewhere.
    p1, p2 = st.columns([1.3, 1])
    with p1:
        st.metric("Latest available price", format_price(latest, ticker))
    with p2:
        st.metric("Last bar move", f"{bar_move:+.2f}%" if bar_move is not None else "—")

    with st.container(border=True):
        head_left, head_right = st.columns([5, 1])
        with head_left:
            st.markdown(f"### {display_name}")
            st.caption(f"{mode_label} · {period_label} view" if (mode_label := st.session_state.get("explorer_mode_label")) else f"{period_label} view")
        with head_right:
            st.markdown("📈")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data["Date"], y=data["Close"], mode="lines", name=ticker,
            line=dict(width=2.5, color="#429E88"),
            fill="tozeroy", fillcolor="rgba(66,158,136,0.12)",
            hovertemplate="%{x}<br>Price: %{y:,.4f}<extra></extra>",
        ))
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#111C2E", plot_bgcolor="#111C2E",
            font=dict(color="#F8FAFC", size=12),
            hoverlabel=dict(bgcolor="#172033", bordercolor="#475569", font=dict(color="#FFFFFF", size=12)),
            height=300, margin=dict(l=10, r=10, t=8, b=24),
            xaxis_title=None, yaxis_title=None, showlegend=False, hovermode="x unified",
        )
        fig.update_xaxes(showgrid=False, showline=False, color="#F8FAFC",
                         tickfont=dict(color="#F8FAFC", size=11), ticks="outside", tickcolor="#64748B")
        fig.update_yaxes(showgrid=True, gridcolor="rgba(148,163,184,0.20)", zeroline=False,
                         color="#F8FAFC", tickfont=dict(color="#F8FAFC", size=11), ticks="outside", tickcolor="#64748B")
        st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False, "responsive": True})
        st.caption("Illustrative layout · actual chart uses retrieved market history. Data may be delayed and is not guaranteed real-time.")

    show_returns = st.checkbox("Show return calculations table", value=True, key=f"show_returns_{ticker}")
    if show_returns:
        st.markdown("#### Historical returns")
        with st.spinner("Loading daily history for return calculations…"):
            return_data = get_return_history(ticker)
        table = returns_table(return_data if not return_data.empty else data)
        st.dataframe(
            style_market_table(table[["Period", "Reference date", "Return (%)"]], {"Return (%)": "{:+.2f}%"}),
            use_container_width=True, hide_index=True
        )
        csv = table.to_csv(index=False).encode("utf-8")
        st.download_button("Download return table (CSV)", csv, file_name=f"{ticker.replace('=', '_')}_returns.csv", mime="text/csv")
    last_stamp = pd.Timestamp(data["Date"].iloc[-1])
    last_stamp_text = last_stamp.strftime("%d %b %Y (daily session)") if interval == "1d" else last_stamp.strftime("%d %b %Y %H:%M")
    st.caption(f"Last data point returned: {last_stamp_text} · Chart interval: {interval}.")


# -----------------------------
# Sidebar / navigation
# -----------------------------
st.sidebar.markdown(
    "<div class='mi-brand'><span class='mi-mark'>↗</span><div><div style='font-weight:750;letter-spacing:.06em'>MARKET INTEL</div><div style='font-size:.75rem;color:#91a1b9'>MULTI-ASSET MONITOR</div></div></div>",
    unsafe_allow_html=True,
)
page = st.sidebar.radio(
    "WORKSPACE",
    ["Overview", "Macro & Event Analysis", "ETF Explorer", "Sector Monitor", "G10 FX", "Commodities", "Instrument Explorer"],
)
st.sidebar.divider()
period_label = st.sidebar.selectbox("Chart period", list(PERIOD_OPTIONS.keys()), index=2)
st.sidebar.caption("Data cache: 5 minutes · quotes may be delayed")
if st.sidebar.button("↻ Refresh data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.markdown(
    "<div class='mi-brand'><span class='mi-mark'>↗</span><div><div class='mi-eyebrow'>MARKET INTELLIGENCE / GLOBAL MARKETS</div><div class='mi-title'>Market Intelligence</div><div class='mi-subtitle'>US equities · ETFs · GICS sectors · G10 FX · Precious metals · Commodities</div></div></div>",
    unsafe_allow_html=True,
)
refresh_col, refresh_note_col = st.columns([1, 2])
with refresh_col:
    if st.button("↻ Refresh market data", use_container_width=True, key="main_refresh_data"):
        st.cache_data.clear()
        st.rerun()
with refresh_note_col:
    st.caption("Requests the latest data available from Yahoo Finance. Daily chart dates identify the trading session, not a midnight quote time.")
st.markdown("<div class='mi-section-note'>Market data is sourced via Yahoo Finance and is not guaranteed real-time. Verify prices with your broker or licensed provider.</div>", unsafe_allow_html=True)

if page == "Overview":
    st.markdown("<div class='mi-eyebrow'>MARKET PULSE</div><h2 class='mi-market-section-title'>Market snapshot</h2>", unsafe_allow_html=True)
    overview_tickers = tuple(dict.fromkeys(("^GSPC", "^NDX", "^TNX", "DX-Y.NYB", "SPY", "QQQ", "IWM", "TLT", "GLD", *FX_UNIVERSE.values(), *COMMODITY_UNIVERSE.values())))
    snap = get_snapshot(overview_tickers)
    display_names = {
        "^GSPC": "S&P 500", "^NDX": "Nasdaq 100", "^TNX": "US 10Y Yield", "DX-Y.NYB": "US Dollar Index",
        "SPY": "SPY", "QQQ": "QQQ", "IWM": "IWM",
        "TLT": "TLT", "GLD": "GLD", "EURUSD=X": "EUR/USD", "JPY=X": "USD/JPY",
        "GBPUSD=X": "GBP/USD", "AUDUSD=X": "AUD/USD", "CHF=X": "USD/CHF",
        "CAD=X": "USD/CAD", "NZDUSD=X": "NZD/USD", "NOK=X": "USD/NOK", "SEK=X": "USD/SEK",
        **{ticker: name for name, ticker in COMMODITY_UNIVERSE.items()},
    }

    # Compact market snapshot tables avoid four full-height metric cards on mobile.
    snapshot_rows = []
    for ticker, label in [("^GSPC", "S&P 500"), ("^NDX", "Nasdaq 100"), ("DX-Y.NYB", "US Dollar Index")]:
        row_data = snap.loc[snap["Ticker"] == ticker]
        if not row_data.empty:
            item = row_data.iloc[0]
            last_value = item.get("Last")
            daily_pct = item.get("Daily %")
            snapshot_rows.append({
                "Market": label,
                "Latest": format_price(last_value, ticker) if pd.notna(last_value) else "—",
                "Daily move": f"{daily_pct:+.2f}%" if pd.notna(daily_pct) else "—",
            })
        else:
            snapshot_rows.append({"Market": label, "Latest": "—", "Daily move": "Unavailable"})

    # Yahoo's ^TNX is quoted as yield multiplied by ten (e.g. 42.0 = 4.20%).
    tnx_hist = get_history("^TNX", "5d", "1d")
    if not tnx_hist.empty:
        tnx_hist = tnx_hist.sort_values("Date")
        yield_pct = float(tnx_hist["Close"].iloc[-1]) / 10.0
        if len(tnx_hist) > 1:
            yield_change_bps = (float(tnx_hist["Close"].iloc[-1]) - float(tnx_hist["Close"].iloc[-2])) * 10.0
            yield_delta = f"{yield_change_bps:+.1f} bps"
        else:
            yield_delta = "—"
        yield_value = f"{yield_pct:.2f}%"
    else:
        yield_value, yield_delta = "—", "Unavailable"
    snapshot_rows.insert(2, {"Market": "US 10Y Yield", "Latest": yield_value, "Daily move": yield_delta})
    snapshot_df = pd.DataFrame(snapshot_rows)
    st.markdown(render_compact_market_rows(snapshot_df, "Market"), unsafe_allow_html=True)
    st.caption("Daily moves compare the latest available trading session with the previous session. Data may be delayed; refresh to request a new provider response.")

    # Compact macro context table replaces four full-height cards on small screens.
    st.markdown("<h3 style='font-size:1.08rem;margin:.9rem 0 .35rem;color:#e7edf7'>Macro context</h3>", unsafe_allow_html=True)
    macro_rows = []
    overview_macro_specs = [("US 10Y yield", "^TNX", "yield"), ("US Dollar Index", "DX-Y.NYB", "price"), ("Gold futures", "GC=F", "price"), ("WTI crude", "CL=F", "price")]
    for macro_label, macro_ticker, macro_kind in overview_macro_specs:
        macro_hist = get_history(macro_ticker, "5d", "1d")
        if not macro_hist.empty:
            macro_hist = macro_hist.sort_values("Date")
            macro_last = float(macro_hist["Close"].iloc[-1])
            macro_prev = float(macro_hist["Close"].iloc[-2]) if len(macro_hist) >= 2 else None
            if macro_kind == "yield":
                macro_value = f"{macro_last / 10.0:.2f}%"
                macro_delta = f"{(macro_last - macro_prev) * 10.0:+.1f} bps" if macro_prev is not None else "—"
            else:
                macro_value = f"{macro_last:,.2f}"
                macro_delta = f"{((macro_last / macro_prev) - 1) * 100:+.2f}%" if macro_prev not in (None, 0) else "—"
            macro_rows.append({"Indicator": macro_label, "Latest": macro_value, "Daily move": macro_delta})
        else:
            macro_rows.append({"Indicator": macro_label, "Latest": "—", "Daily move": "Unavailable"})
    st.markdown(render_compact_market_rows(pd.DataFrame(macro_rows), "Indicator"), unsafe_allow_html=True)
    st.caption("Macro context is a market snapshot, not an official economic calendar. Open Macro & Event Analysis in the sidebar to study historical release windows.")

    # Compact jump navigation makes the long Overview easier to scan on mobile.
    st.markdown(
        "<nav class='mi-jump-nav' aria-label='Market sections'>"
        "<a href='#overview-briefing'>◷ Daily Briefing</a>"
        "<a href='#overview-trends'>↗ 30D Trends</a>"
        "<a href='#overview-etfs'>▦ ETFs</a>"
        "<a href='#overview-sectors'>▥ Sectors</a>"
        "<a href='#overview-fx'>⇄ FX</a>"
        "<a href='#overview-metals'>◆ Precious metals</a>"
        "<a href='#overview-commodities'>◈ Commodities</a>"
        "</nav>",
        unsafe_allow_html=True,
    )

    # Each asset class has its own visual section, accent colour and anchor.
    fx_tickers = tuple(dict.fromkeys(FX_UNIVERSE.values()))
    etf_tickers = ("SPY", "QQQ", "IWM", "TLT", "GLD")

    # Rolling 30-day market trends data is prepared here; its visual section appears after the Daily Market Briefing.

    trend_specs = []
    seen_trend_tickers = set()

    def add_trend_spec(display_name, ticker, asset_class):
        if ticker not in seen_trend_tickers:
            trend_specs.append((display_name, ticker, asset_class))
            seen_trend_tickers.add(ticker)

    for label, ticker in ETF_UNIVERSE.items():
        add_trend_spec(label, ticker, "ETFs")
    for sector_name, ticker in SECTOR_ETFS.items():
        add_trend_spec(sector_name, ticker, "Sectors")
    for pair_name, ticker in FX_UNIVERSE.items():
        add_trend_spec(pair_name, ticker, "FX")
    for instrument_name, ticker in COMMODITY_UNIVERSE.items():
        asset_class = "Precious Metals" if instrument_name in PRECIOUS_METALS else "Commodities"
        add_trend_spec(instrument_name, ticker, asset_class)
    for sector_name, company_list in SECTOR_COMPANIES.items():
        for company_ticker in company_list:
            add_trend_spec(company_ticker, company_ticker, "Stocks")

    with st.spinner("Building the rolling 30-day market dataset…"):
        trend_data = get_30d_trend_data(tuple(trend_specs))

    if not trend_data.empty:
        # Add plain-English names and sector/category labels for easier interpretation.
        ticker_to_sector = {
            ticker: sector_name
            for sector_name, tickers_in_sector in SECTOR_COMPANIES.items()
            for ticker in tickers_in_sector
        }
        trend_data["Company"] = trend_data.apply(
            lambda row: COMPANY_DISPLAY_NAMES.get(row["Ticker"], row["Instrument"])
            if row["Asset class"] == "Stocks" else row["Instrument"],
            axis=1,
        )
        trend_data["Sector"] = trend_data.apply(
            lambda row: ticker_to_sector.get(row["Ticker"], row["Asset class"])
            if row["Asset class"] == "Stocks"
            else (row["Instrument"] if row["Asset class"] == "Sectors" else row["Asset class"]),
            axis=1,
        )

    # -----------------------------
    # Daily market briefing
    # -----------------------------
    st.markdown(
        "<div id='overview-briefing' class='mi-section-band' style='--section-accent:#60a5fa'>"
        "<span class='mi-section-icon'>◷</span><div><div class='mi-section-kicker'>DAILY RESEARCH</div>"
        "<h2>Daily Market Briefing</h2></div></div>",
        unsafe_allow_html=True,
    )
    st.caption(
        "A concise read of the latest available market session. Price moves are observations; "
        "headlines are research leads, not proof of causation."
    )

    briefing_stock_data = trend_data.loc[trend_data["Asset class"] == "Stocks"].copy() if not trend_data.empty else pd.DataFrame()
    briefing_sector_data = trend_data.loc[trend_data["Asset class"] == "Sectors"].copy() if not trend_data.empty else pd.DataFrame()
    if not briefing_stock_data.empty and briefing_stock_data["Daily %"].notna().any():
        briefing_stocks = briefing_stock_data.dropna(subset=["Daily %"]).sort_values("Daily %", ascending=False)
        best_stock = briefing_stocks.iloc[0]
        worst_stock = briefing_stocks.iloc[-1]
        stock_gainers = briefing_stocks.head(3)
        stock_losers = briefing_stocks.tail(3).sort_values("Daily %")
    else:
        best_stock = worst_stock = None
        stock_gainers = stock_losers = pd.DataFrame()

    if not briefing_sector_data.empty and briefing_sector_data["Daily %"].notna().any():
        briefing_sectors = briefing_sector_data.dropna(subset=["Daily %"]).sort_values("Daily %", ascending=False)
        best_sector = briefing_sectors.iloc[0]
        worst_sector = briefing_sectors.iloc[-1]
    else:
        best_sector = worst_sector = None

    # If the batched trend download misses sector ETF prices, retry the sector funds
    # individually. This prevents a missing sector summary from being shown when
    # individual Yahoo Finance history is available.
    if best_sector is None:
        fallback_sector_rows = []
        for sector_name, sector_ticker in SECTOR_ETFS.items():
            try:
                sector_hist = get_history(sector_ticker, "5d", "1d")
                if sector_hist is None or sector_hist.empty or "Close" not in sector_hist.columns:
                    continue
                sector_hist = sector_hist.sort_values("Date") if "Date" in sector_hist.columns else sector_hist.sort_index()
                close_values = pd.to_numeric(sector_hist["Close"], errors="coerce").dropna()
                if len(close_values) >= 2 and float(close_values.iloc[-2]) != 0:
                    daily_move = (float(close_values.iloc[-1]) / float(close_values.iloc[-2]) - 1) * 100
                    fallback_sector_rows.append({"Instrument": sector_name, "Ticker": sector_ticker,
                                                  "Asset class": "Sectors", "Sector": sector_name,
                                                  "Daily %": daily_move})
            except Exception:
                continue
        if fallback_sector_rows:
            briefing_sector_data = pd.DataFrame(fallback_sector_rows)
            briefing_sectors = briefing_sector_data.sort_values("Daily %", ascending=False)
            best_sector = briefing_sectors.iloc[0]
            worst_sector = briefing_sectors.iloc[-1]

    def brief_card(label, value, move, detail="", direction="neutral"):
        move_class = "positive" if direction == "positive" else "negative" if direction == "negative" else "neutral"
        detail_html = f"<div class='mi-brief-detail'>{html.escape(str(detail))}</div>" if detail else ""
        return (
            "<div class='mi-brief-card'>"
            f"<div class='mi-brief-label'>{html.escape(str(label))}</div>"
            f"<div class='mi-brief-value'>{html.escape(str(value))}</div>"
            f"<div class='mi-brief-move {move_class}'>{html.escape(str(move))}</div>"
            f"{detail_html}</div>"
        )

    best_stock_card = brief_card("Top stock · daily", best_stock["Ticker"],
                                 f"↑ {best_stock['Daily %']:+.2f}%", best_stock["Company"], "positive" if best_stock["Daily %"] >= 0 else "negative") if best_stock is not None else brief_card("Top stock · daily", "—", "Unavailable")
    worst_stock_card = brief_card("Weakest stock · daily", worst_stock["Ticker"],
                                  f"↓ {worst_stock['Daily %']:+.2f}%", worst_stock["Company"], "negative" if worst_stock["Daily %"] < 0 else "positive") if worst_stock is not None else brief_card("Weakest stock · daily", "—", "Unavailable")
    sector_card = brief_card("Leading sector", best_sector["Sector"],
                             f"↑ {best_sector['Daily %']:+.2f}%",
                             f"Lagging: {worst_sector['Sector']} ({worst_sector['Daily %']:+.2f}%)" if worst_sector is not None else "Sector ETF data", 
                             "positive" if best_sector["Daily %"] >= 0 else "negative") if best_sector is not None else brief_card("Leading sector", "—", "Sector data unavailable", "Retry after refreshing market data")
    st.markdown("<div class='mi-brief-grid'>" + best_stock_card + worst_stock_card + sector_card + "</div>", unsafe_allow_html=True)

    # Cross-asset snapshot uses the same cached price series as the Overview.
    cross_asset_names = {
        "^GSPC": "S&P 500", "^NDX": "Nasdaq 100", "DX-Y.NYB": "US Dollar Index",
        "GC=F": "Gold futures", "CL=F": "WTI crude", "EURUSD=X": "EUR/USD",
        "JPY=X": "USD/JPY", "^TNX": "US 10Y yield",
    }
    cross_asset_rows = []
    for ticker, label in cross_asset_names.items():
        item_rows = snap.loc[snap["Ticker"] == ticker] if "snap" in locals() and not snap.empty else pd.DataFrame()
        if ticker == "^TNX":
            yield_hist = get_history("^TNX", "5d", "1d")
            if not yield_hist.empty:
                yield_hist = yield_hist.sort_values("Date")
                latest_yield = float(yield_hist["Close"].iloc[-1]) / 10.0
                yield_move = ((float(yield_hist["Close"].iloc[-1]) - float(yield_hist["Close"].iloc[-2])) * 10.0) if len(yield_hist) > 1 else None
                cross_asset_rows.append({"Market": label, "Last": f"{latest_yield:.2f}%", "Daily move": f"{yield_move:+.1f} bps" if yield_move is not None else "—"})
            continue
        if not item_rows.empty and pd.notna(item_rows.iloc[0]["Last"]):
            item = item_rows.iloc[0]
            last_text = f"{item['Last']:,.3f}" if ticker in FX_UNIVERSE.values() else f"{item['Last']:,.2f}"
            move_text = f"{item['Daily %']:+.2f}%" if pd.notna(item["Daily %"]) else "—"
            cross_asset_rows.append({"Market": label, "Last": last_text, "Daily move": move_text})
    if cross_asset_rows:
        with st.expander("Cross-asset pulse", expanded=False):
            cross_asset_frame = pd.DataFrame(cross_asset_rows)
            st.table(cross_asset_frame)

    left_brief, right_brief = st.columns([1, 1])
    with left_brief:
        with st.expander("Stock movers", expanded=True):
            if not stock_gainers.empty:
                st.markdown("**Top gainers**")
                for _, item in stock_gainers.iterrows():
                    st.markdown(f"- **{item['Ticker']}** · {item['Company']} — {item['Daily %']:+.2f}%")
            if not stock_losers.empty:
                st.markdown("**Top decliners**")
                for _, item in stock_losers.iterrows():
                    st.markdown(f"- **{item['Ticker']}** · {item['Company']} — {item['Daily %']:+.2f}%")
            if stock_gainers.empty and stock_losers.empty:
                st.info("Stock movers are temporarily unavailable.")
    with right_brief:
        with st.expander("Headlines to investigate", expanded=False):
            news_tickers = []
            if best_stock is not None:
                news_tickers.append((str(best_stock["Ticker"]), str(best_stock["Company"]), float(best_stock["Daily %"])))
            if worst_stock is not None and (best_stock is None or str(worst_stock["Ticker"]) != str(best_stock["Ticker"])):
                news_tickers.append((str(worst_stock["Ticker"]), str(worst_stock["Company"]), float(worst_stock["Daily %"])))
            found_news = False
            for news_ticker, company_name, move in news_tickers:
                headlines = get_recent_news(news_ticker, limit=2)
                if headlines:
                    found_news = True
                    st.markdown(f"**{company_name} ({news_ticker}) · {move:+.2f}% daily**")
                    for headline in headlines:
                        title_text = html.escape(str(headline["title"]))
                        url = headline.get("url")
                        if url:
                            st.markdown(f"- [{title_text}]({url}) · {html.escape(str(headline.get('provider', 'News')))}")
                        else:
                            st.markdown(f"- {title_text} · {html.escape(str(headline.get('provider', 'News')))}")
            if not found_news:
                st.info("No recent headlines were returned for the biggest movers. This does not mean there is no news; use the official company site or a trusted news search.")
                if best_stock is not None:
                    st.markdown(f"[Search news for {best_stock['Ticker']}]({ 'https://news.google.com/search?q=' + quote_plus(str(best_stock['Ticker']) + ' stock news') })")

    st.markdown("**What to watch next**")
    st.caption("Starter schedule based on official calendars; dates can change. Confirm with the source before relying on a release time.")
    upcoming_events = [
        ("US CPI · September 2026", "2026-10-14", "https://www.bls.gov/schedule/news_release/cpi.htm", "BLS CPI calendar"),
        ("FOMC decision", "2026-10-28", "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm", "Federal Reserve"),
        ("US GDP · Q3 advance estimate", "2026-10-29", "https://www.bea.gov/news/schedule", "BEA release schedule"),
        ("US Employment Situation · October", "2026-11-06", "https://www.bls.gov/schedule/news_release/empSit.htm", "BLS jobs calendar"),
        ("US CPI · October 2026", "2026-11-10", "https://www.bls.gov/schedule/news_release/cpi.htm", "BLS CPI calendar"),
        ("FOMC decision", "2026-12-09", "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm", "Federal Reserve"),
        ("US Employment Situation · November", "2026-12-04", "https://www.bls.gov/schedule/news_release/empSit.htm", "BLS jobs calendar"),
        ("US CPI · November 2026", "2026-12-10", "https://www.bls.gov/schedule/news_release/cpi.htm", "BLS CPI calendar"),
    ]
    today_for_events = dt.date.today()
    future_events = sorted(
        [(dt.date.fromisoformat(date_text), label, url, source) for label, date_text, url, source in upcoming_events if dt.date.fromisoformat(date_text) >= today_for_events],
        key=lambda event: event[0],
    )[:4]
    if future_events:
        event_cards = []
        for event_date, event_label, event_url, event_source in future_events:
            event_cards.append(
                "<div class='mi-event-item'>"
                f"<div class='mi-event-date'>{event_date:%d %b %Y}</div>"
                f"<div class='mi-event-name'>{html.escape(event_label)}</div>"
                f"<div class='mi-event-source'><a href='{html.escape(event_url, quote=True)}' target='_blank' rel='noopener noreferrer'>{html.escape(event_source)}</a></div>"
                "</div>"
            )
        st.markdown("<div class='mi-event-list'>" + "".join(event_cards) + "</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            "- [BLS CPI calendar](https://www.bls.gov/schedule/news_release/cpi.htm) · "
            "[BLS employment calendar](https://www.bls.gov/schedule/news_release/empSit.htm) · "
            "[Federal Reserve FOMC calendar](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) · "
            "[BEA release schedule](https://www.bea.gov/news/schedule)"
        )
    st.caption("Observed moves are shown separately from possible explanations. A headline appearing near a move does not establish that it caused the move. Data is sourced from Yahoo Finance and may be delayed or incomplete.")

    # -----------------------------
    # Rolling 30-day market trends (visual section)
    # -----------------------------
    st.markdown(
        "<div id='overview-trends' class='mi-section-band' style='--section-accent:#fbbf24'>"
        "<span class='mi-section-icon'>↗</span><div><div class='mi-section-kicker'>Market intelligence</div>"
        "<h2>30-Day Market Trends</h2></div></div>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Find leaders, emerging momentum and unusual activity across the dashboard watchlist. "
        "30D uses approximately 21 trading sessions. Volume signals are only interpreted for stocks, ETFs and sector funds."
    )

    if trend_data.empty or trend_data["30D %"].notna().sum() == 0:
        st.warning("The 30-day dataset is temporarily unavailable. Please try refreshing market data.")
    else:
        valid_trends = trend_data.dropna(subset=["30D %"]).copy()
        leaders = valid_trends.sort_values("30D %", ascending=False).head(1)
        emerging = valid_trends.dropna(subset=["Acceleration"]).sort_values("Acceleration", ascending=False).head(1)
        activity = valid_trends.dropna(subset=["Volume ratio"])
        activity = activity.loc[activity["Volume ratio"] >= 1.5].sort_values("Volume ratio", ascending=False)
        positive_share = (valid_trends["30D %"] > 0).mean() * 100 if not valid_trends.empty else None

        # Compact HTML summary strip stays in three columns on narrow mobile screens.
        leader = leaders.iloc[0] if not leaders.empty else None
        momentum = emerging.iloc[0] if not emerging.empty else None
        unusual = activity.iloc[0] if not activity.empty else None
        def summary_tile(label, name, ticker, detail):
            return (
                "<div class='mi-trend-tile'><div class='mi-trend-tile-label'>" + str(label) +
                "</div><div class='mi-trend-tile-name'>" + str(name) +
                "</div><div class='mi-trend-tile-detail'>" + str(detail) +
                "</div><div class='mi-trend-tile-ticker'>" + str(ticker) + "</div></div>"
            )
        leader_html = summary_tile("30D LEADER", leader["Company"], leader["Ticker"], f"{leader['30D %']:+.1f}%") if leader is not None else summary_tile("30D LEADER", "—", "", "No data")
        momentum_html = summary_tile("MOMENTUM", momentum["Company"], momentum["Ticker"], f"{momentum['Acceleration']:+.1f} pp") if momentum is not None else summary_tile("MOMENTUM", "—", "", "No data")
        unusual_html = summary_tile("VOLUME ALERT", unusual["Company"], unusual["Ticker"], f"{unusual['Volume ratio']:.1f}× avg") if unusual is not None else summary_tile("VOLUME ALERT", "None", "", "No alert")
        st.markdown(
            "<div class='mi-trend-summary-grid'>" + leader_html + momentum_html + unusual_html + "</div>",
            unsafe_allow_html=True,
        )
        st.caption(f"{positive_share:.0f}% of instruments with available data have positive 30D returns." if positive_share is not None else "Positive-return breadth unavailable.")

        # Search is visible; advanced filters remain tucked away to save mobile space.
        search_query = st.text_input(
            "Find a stock, ticker or instrument",
            placeholder="Search e.g. AMD, Crown Castle, MPC",
            key="trend_search_query",
            label_visibility="collapsed",
        ).strip().lower()
        with st.expander("Filters and ranking", expanded=False):
            filter_cols = st.columns(2)
            with filter_cols[0]:
                trend_asset_filter = st.selectbox(
                    "Asset class",
                    ["Stocks", "All asset classes", "ETFs", "Sectors", "FX", "Precious Metals", "Commodities"],
                    index=0, key="trend_asset_class_filter_v21",
                    help="Stocks is the default. Choose All asset classes for a cross-market scan.",
                )
            industry_options = ["All industries"]
            if trend_asset_filter == "Stocks":
                industry_options += list(SECTOR_ETFS.keys())
            elif trend_asset_filter == "Sectors":
                industry_options += list(SECTOR_ETFS.keys())
            with filter_cols[1]:
                trend_industry_filter = st.selectbox(
                    "Industry / sector", industry_options,
                    key="trend_industry_filter",
                )
            with filter_cols[0]:
                trend_signal_filter = st.selectbox(
                    "Trend signal",
                    ["All signals", "Strengthening", "Cooling", "Rebounding", "Weakening", "Unusual activity", "Mixed", "Data unavailable"],
                    key="trend_signal_filter",
                )
            with filter_cols[1]:
                trend_sort = st.selectbox(
                    "Rank by",
                    ["30D %", "5D %", "Daily %", "Acceleration", "Volume ratio", "20D volatility"],
                    key="trend_sort_metric",
                )
            trend_direction = st.radio(
                "Direction", ["Top gainers", "Top losers", "All"], horizontal=True,
                key="trend_direction_filter",
            )
            result_limit = st.selectbox(
                "Results to show", [5, 10, 15, "All filtered"], index=0,
                key="trend_chart_size",
            )

        filtered_trends = trend_data.copy()
        if search_query:
            search_mask = (
                filtered_trends["Company"].astype(str).str.lower().str.contains(search_query, regex=False)
                | filtered_trends["Ticker"].astype(str).str.lower().str.contains(search_query, regex=False)
                | filtered_trends["Instrument"].astype(str).str.lower().str.contains(search_query, regex=False)
            )
            filtered_trends = filtered_trends.loc[search_mask]
        if trend_asset_filter != "All asset classes":
            filtered_trends = filtered_trends.loc[filtered_trends["Asset class"] == trend_asset_filter]
        if trend_industry_filter != "All industries":
            filtered_trends = filtered_trends.loc[filtered_trends["Sector"] == trend_industry_filter]
        if trend_signal_filter != "All signals":
            filtered_trends = filtered_trends.loc[filtered_trends["Signal"] == trend_signal_filter]
        active_asset_label = trend_asset_filter
        active_industry_label = trend_industry_filter if trend_industry_filter != "All industries" else "All industries"
        active_signal_label = trend_signal_filter if trend_signal_filter != "All signals" else "All signals"
        active_direction_label = trend_direction
        view_summary = f"View: {active_asset_label} · {active_industry_label} · {active_signal_label} · {trend_sort} · {active_direction_label}"
        if search_query:
            # Keep the active query visible so filtered rankings remain interpretable.
            view_summary += f" · Search: {search_query}"
        st.caption(view_summary)
        ascending = trend_direction == "Top losers"
        filtered_trends = filtered_trends.sort_values(trend_sort, ascending=ascending, na_position="last")
        if trend_direction != "All":
            filtered_trends = filtered_trends.loc[filtered_trends[trend_sort] >= 0] if trend_direction == "Top gainers" else filtered_trends.loc[filtered_trends[trend_sort] < 0]

        st.caption(f"{len(filtered_trends)} instruments · sorted by {trend_sort}")
        chart_rows = filtered_trends.dropna(subset=[trend_sort]).copy()
        if result_limit != "All filtered":
            chart_rows = chart_rows.head(int(result_limit))
        chart_rows = chart_rows.iloc[::-1]
        if not chart_rows.empty:
            chart_labels = [f"{row['Ticker']} · {row['Company']}" for _, row in chart_rows.iterrows()]
            metric_values = chart_rows[trend_sort].astype(float)
            if trend_sort == "Volume ratio":
                value_labels = [f"{value:.1f}×" for value in metric_values]
                axis_title = "Volume ratio (× average)"
                hover_label = "Volume ratio"
            elif trend_sort == "20D volatility":
                value_labels = [f"{value:.1f}%" for value in metric_values]
                axis_title = "20D volatility (%)"
                hover_label = "20D volatility"
            elif trend_sort == "Acceleration":
                value_labels = [f"{value:+.1f} pp" for value in metric_values]
                axis_title = "Momentum acceleration (pp)"
                hover_label = "Acceleration"
            else:
                value_labels = [f"{value:+.1f}%" for value in metric_values]
                axis_title = f"{trend_sort} return (%)" if trend_sort in ["Daily %", "5D %", "30D %"] else trend_sort
                hover_label = trend_sort
            colors = ["#34d399" if value >= 0 else "#fb7185" for value in metric_values]
            chart = go.Figure(go.Bar(
                x=metric_values, y=chart_labels, orientation="h", marker_color=colors,
                customdata=chart_rows["Ticker"].astype(str).tolist(),
                text=value_labels, textposition="inside", insidetextanchor="end", cliponaxis=True,
                textfont=dict(color="#0b1120", size=10),
                hovertemplate=f"%{{y}}<br>{hover_label}: %{{x:.2f}}<extra></extra>",
            ))
            max_abs = max([abs(float(x)) for x in metric_values] + [1.0])
            chart.update_layout(
                template="plotly_dark", height=max(210, 27 * len(chart_rows)),
                margin=dict(l=4, r=8, t=4, b=8), xaxis_title=axis_title,
                yaxis_title=None, showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e7edf7", size=10), bargap=.22,
            )
            chart.update_xaxes(
                range=[min(0, float(metric_values.min()) - max_abs * .12), max(0, float(metric_values.max()) + max_abs * .12)],
                gridcolor="rgba(148,163,184,.14)", zeroline=True, zerolinecolor="#64748b",
                tickfont=dict(color="#F8FAFC", size=10),
            )
            chart.update_yaxes(showgrid=False, automargin=True, tickfont=dict(color="#F8FAFC", size=10))
            st.caption("Select a bar to inspect that instrument below. If your browser does not register chart selection, use the instrument selector.")
            chart_event = st.plotly_chart(
                chart, width="stretch", theme=None,
                config={"displayModeBar": False, "responsive": True},
                on_select="rerun", selection_mode="points", key="trend_ranking_chart",
            )
            try:
                selected_points = chart_event.selection.points
                if selected_points:
                    selected_point = selected_points[0]
                    clicked_ticker = selected_point.get("customdata")
                    if isinstance(clicked_ticker, (list, tuple)):
                        clicked_ticker = clicked_ticker[0] if clicked_ticker else None
                    if not clicked_ticker and selected_point.get("point_index") is not None:
                        point_index = int(selected_point["point_index"])
                        if 0 <= point_index < len(chart_rows):
                            clicked_ticker = str(chart_rows.iloc[point_index]["Ticker"])
                    if clicked_ticker:
                        st.session_state["trend_inspect_ticker"] = str(clicked_ticker)
            except (AttributeError, KeyError, TypeError, ValueError):
                pass
        else:
            st.info("No instruments match these filters. Try a broader industry, asset class or search term.")

        # Select a result to reveal its price chart and synchronize the news investigation panel.
        if not filtered_trends.empty:
            inspect_options = {}
            for _, row in filtered_trends.iterrows():
                label = f"{row['Company']} ({row['Ticker']}) · {row['Sector']}"
                inspect_options[label] = str(row["Ticker"])
            inspect_labels = list(inspect_options.keys())
            requested_ticker = st.session_state.get("trend_inspect_ticker")
            if requested_ticker:
                matching_label = next(
                    (label for label, ticker in inspect_options.items() if ticker == str(requested_ticker)),
                    None,
                )
                if matching_label is not None:
                    st.session_state["trend_inspect_selection"] = matching_label
            selected_inspect_label = st.selectbox(
                "Inspect instrument", inspect_labels, key="trend_inspect_selection",
                help="Choose an instrument to open its price chart and news context below.",
            )
            selected_inspect_ticker = inspect_options[selected_inspect_label]
            selected_inspect_row = filtered_trends.loc[filtered_trends["Ticker"].astype(str) == selected_inspect_ticker].iloc[0]
            with st.expander(f"Price chart · {selected_inspect_ticker}", expanded=False):
                st.caption(f"{selected_inspect_row['Company']} · {selected_inspect_row['Sector']} · {selected_inspect_row['Asset class']}")
                with st.spinner(f"Loading {selected_inspect_ticker} price history…"):
                    inspect_history = get_history(selected_inspect_ticker, "3mo", "1d")
                if not inspect_history.empty:
                    render_price_chart(inspect_history.sort_values("Date").reset_index(drop=True), selected_inspect_ticker, "3 months · daily")
                else:
                    st.info("Price history is unavailable for this instrument right now.")
            # Keep the headline investigation selection in sync with the selected scanner result.
            st.session_state["trend_inspect_ticker"] = selected_inspect_ticker
        else:
            st.session_state["trend_inspect_ticker"] = None

        visible_cols = [
            "Company", "Ticker", "Sector", "Asset class", "Last", "Daily %", "5D %", "30D %",
            "Acceleration", "Volume ratio", "20D volatility", "Signal", "As of",
        ]
        visible = filtered_trends[visible_cols].copy()
        with st.expander(f"Detailed results ({len(visible)} instruments)", expanded=False):
            trend_styler = style_market_table(visible, {
                "Last": "{:,.3f}", "Daily %": "{:+.2f}%", "5D %": "{:+.2f}%",
                "30D %": "{:+.2f}%", "Acceleration": "{:+.2f}", "Volume ratio": "{:.2f}×",
                "20D volatility": "{:.1f}%",
            })
            for return_column in ["Daily %", "5D %", "30D %", "Acceleration"]:
                trend_styler = trend_styler.map(color_daily_pct, subset=[return_column])
            st.table(trend_styler)
        csv_data = visible.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download filtered results (CSV)", csv_data,
            file_name="market_trends_30d_filtered.csv", mime="text/csv",
            key="download_market_trends_30d",
        )
        st.caption(
            "Acceleration = 5D return minus one-sixth of the 30D return. "
            "Volume ratio compares the latest five-session average with the preceding 20-session average. "
            "Yahoo Finance coverage can be incomplete; futures volume and spot FX activity are not directly comparable."
        )

        # Compact mobile-first headline context panel.
        st.markdown("### Why might it be moving?")
        st.caption(
            "Price signals are observations, not explanations. Headlines can provide clues, but do not prove causation; "
            "Yahoo Finance coverage may be incomplete or delayed."
        )
        candidate_rows = filtered_trends.loc[filtered_trends["Ticker"].notna()].copy()
        candidate_rows = candidate_rows.sort_values("30D %", ascending=False, na_position="last")
        candidate_options = {}
        for _, candidate in candidate_rows.iterrows():
            ticker = str(candidate["Ticker"])
            company_name = COMPANY_DISPLAY_NAMES.get(ticker, str(candidate.get("Company", candidate["Instrument"])))
            label = f"{company_name} ({ticker}) · {candidate['Sector']}"
            candidate_options[label] = ticker

        if candidate_options:
            preferred_ticker = st.session_state.get("trend_inspect_ticker")
            selected_news_ticker = preferred_ticker if preferred_ticker in candidate_options.values() else next(iter(candidate_options.values()))
            selected_news_label = next(
                (label for label, ticker in candidate_options.items() if ticker == selected_news_ticker),
                selected_news_ticker,
            )
            st.caption(f"Investigating: **{selected_news_label}** · selected in the market scanner above")
            selected_news_row = candidate_rows.loc[
                candidate_rows["Ticker"].astype(str) == selected_news_ticker
            ].iloc[0]
            daily_value = selected_news_row["Daily %"]
            five_value = selected_news_row["5D %"]
            thirty_value = selected_news_row["30D %"]
            daily_text = f"{daily_value:+.2f}%" if pd.notna(daily_value) else "—"
            five_text = f"{five_value:+.2f}%" if pd.notna(five_value) else "—"
            thirty_text = f"{thirty_value:+.2f}%" if pd.notna(thirty_value) else "—"

            metric_cols = st.columns(3, gap="small", wrap=False)
            metric_cols[0].metric("Daily", daily_text, delta_color="normal", border=True)
            metric_cols[1].metric("5 sessions", five_text, delta_color="normal", border=True)
            metric_cols[2].metric("30 days", thirty_text, delta_color="normal", border=True)
            signal = str(selected_news_row.get("Signal", "Signal unavailable"))
            as_of = selected_news_row.get("As of")
            as_of_text = str(as_of) if pd.notna(as_of) else "date unavailable"
            st.caption(f"**Observed signal:** {signal} · **Data date:** {as_of_text}")

            with st.spinner(f"Checking recent headlines for {selected_news_ticker}…"):
                recent_news = get_recent_news(selected_news_ticker, 5)

            if recent_news:
                with st.container(border=True, gap="small"):
                    st.markdown("**Recent headlines to investigate**")
                    for news_item in recent_news:
                        theme = classify_news_context(news_item["title"])
                        safe_title = news_item["title"].replace("<", "&lt;").replace(">", "&gt;")
                        if news_item["url"]:
                            st.markdown(f"- **[{safe_title}]({news_item['url']})**")
                        else:
                            st.markdown(f"- **{safe_title}**")
                        st.caption(f"Possible theme: {theme} · {news_item['provider']} · {news_item['published']}")
            else:
                company_name = COMPANY_DISPLAY_NAMES.get(selected_news_ticker, selected_news_ticker)
                search_query = quote_plus(f'"{company_name}" {selected_news_ticker} market news')
                yahoo_url = f"https://finance.yahoo.com/quote/{quote_plus(selected_news_ticker)}/news/"
                google_news_url = f"https://news.google.com/search?q={search_query}"
                st.info(
                    "No headlines were returned by the in-app feed. This does not mean there is no news. "
                    "Use one of the search links below; price and volume signals above remain available."
                )
                link_cols = st.columns(2, gap="small")
                with link_cols[0]:
                    st.link_button("Search Yahoo Finance news", yahoo_url, use_container_width=True)
                with link_cols[1]:
                    st.link_button("Search Google News", google_news_url, use_container_width=True)

            st.caption(
                "Interpretation tip: compare the company’s move with its sector ETF and the S&P 500. "
                "If both rise or fall together, the move may reflect broader market or sector factors; "
                "if the stock diverges, investigate company-specific developments. This is a research framework, not a causal conclusion."
            )

    st.markdown("<div id='overview-etfs' class='mi-section-band' style='--section-accent:#93c5fd'><span class='mi-section-icon'>▦</span><div><div class='mi-section-kicker'>Cross-asset benchmarks</div><h2>Major ETFs</h2></div></div>", unsafe_allow_html=True)
    etf_markets = snap.loc[snap["Ticker"].isin(etf_tickers)].copy()
    if not etf_markets.empty:
        etf_markets["Instrument"] = etf_markets["Ticker"].map(display_names).fillna(etf_markets["Ticker"])
        etf_markets = compact_observation_times(etf_markets)
        st.table(
            style_market_table(
                etf_markets[["Instrument", "Ticker", "Last", "Daily %", "As of"]],
                {"Last": "{:,.4f}", "Daily %": "{:+.2f}%"},
            )
        )

    st.markdown("<div id='overview-sectors' class='mi-section-band' style='--section-accent:#6ee7b7'><span class='mi-section-icon'>▥</span><div><div class='mi-section-kicker'>Equity breadth</div><h2>Sector performance</h2></div></div>", unsafe_allow_html=True)
    sector_tickers = tuple(SECTOR_ETFS.values())
    sector_data = get_snapshot(sector_tickers)
    name_by_ticker = {v: k for k, v in SECTOR_ETFS.items()}
    if not sector_data.empty:
        sector_data["Sector"] = sector_data["Ticker"].map(name_by_ticker)
        sector_data = sector_data.sort_values("Daily %", ascending=False, na_position="last")
        # Compact ranked bars use abbreviated chart labels; the full names remain in the table.
        chart_sector = sector_data.dropna(subset=["Daily %"]).sort_values("Daily %", ascending=True).copy()
        if not chart_sector.empty:
            chart_sector["Chart sector"] = chart_sector["Sector"].replace({
                "Information Technology": "Technology",
                "Consumer Discretionary": "Cons. Disc.",
                "Communication Services": "Comm. Services",
                "Consumer Staples": "Cons. Staples",
                "Health Care": "Healthcare",
            })
            bar_values = chart_sector["Daily %"].astype(float).tolist()
            bar_colors = ["#34d399" if x >= 0 else "#fb7185" for x in bar_values]
            sector_labels = [f"{x:+.2f}%" if abs(x) >= 0.30 else "" for x in bar_values]
            # Keep labels inside bars to avoid clipping at either chart edge on mobile.
            fig_sector = go.Figure(go.Bar(
                x=bar_values, y=chart_sector["Chart sector"], orientation="h",
                marker_color=bar_colors, text=sector_labels, textposition="inside",
                insidetextanchor="end", cliponaxis=True,
                textfont=dict(color="#0b1120", size=11),
                hovertemplate="%{y}<br>Daily move: %{x:+.2f}%<extra></extra>",
            ))
            max_abs = max([abs(x) for x in bar_values] + [0.5])
            fig_sector.update_layout(
                template="plotly_dark", height=350, margin=dict(l=4, r=6, t=4, b=8),
                xaxis_title="Daily change (%)", yaxis_title=None, showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#cbd5e1", size=10), bargap=0.22,
            )
            fig_sector.update_xaxes(
                range=[-max_abs * 1.12, max_abs * 1.12],
                gridcolor="rgba(148,163,184,.14)", zeroline=True, zerolinecolor="#64748b",
                tickfont=dict(color="#F8FAFC", size=10),
            )
            fig_sector.update_yaxes(showgrid=False, automargin=True, tickfont=dict(color="#F8FAFC", size=10))
            st.plotly_chart(fig_sector, width="stretch", theme=None, config={"displayModeBar": False, "responsive": True})
        sector_table = compact_observation_times(sector_data[["Sector", "Ticker", "Last", "Daily %", "As of"]])
        st.table(style_market_table(sector_table, {"Last": "{:,.2f}", "Daily %": "{:+.2f}%"}))

    # Company-level view: filter a sector, then compare prices and trailing returns.
    st.markdown(
        "<div id='overview-companies' class='mi-section-band' style='--section-accent:#c4b5fd'>"
        "<span class='mi-section-icon'>▤</span><div><div class='mi-section-kicker'>Company performance</div>"
        "<h2>Sector constituents — top 10 watchlist</h2></div></div>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Ten representative large-cap constituents per sector, ordered by the selected return metric. "
        "This is a curated watchlist, not a live market-cap ranking. Prices and returns use Yahoo Finance adjusted daily closes."
    )
    company_filter_col, sort_filter_col = st.columns([1.3, 1])
    with company_filter_col:
        overview_company_sector = st.selectbox(
            "Filter by sector",
            list(SECTOR_COMPANIES.keys()),
            key="overview_company_sector_filter",
        )
    with sort_filter_col:
        company_sort_metric = st.selectbox(
            "Rank companies by",
            ["Daily %", "1W %", "1M %", "YTD %", "1Y %"],
            key="overview_company_sort_metric",
        )

    company_tickers = tuple(SECTOR_COMPANIES[overview_company_sector])
    company_rows = []
    with st.spinner(f"Loading {overview_company_sector} company prices and returns…"):
        for company_ticker in company_tickers:
            hist = get_return_history(company_ticker)
            if hist.empty:
                company_rows.append({
                    "Company": COMPANY_DISPLAY_NAMES.get(company_ticker, company_ticker),
                    "Ticker": company_ticker, "Last": None,
                    "Daily %": None, "1W %": None, "1M %": None, "YTD %": None, "1Y %": None,
                    "As of": "Unavailable",
                })
                continue

            hist = hist.dropna(subset=["Close"]).sort_values("Date").copy()
            latest_row = hist.iloc[-1]
            latest_date = pd.Timestamp(latest_row["Date"])
            latest_close = float(latest_row["Close"])

            def trailing_return(target_date):
                eligible = hist[hist["Date"] <= pd.Timestamp(target_date)]
                if eligible.empty:
                    return None
                reference_close = float(eligible.iloc[-1]["Close"])
                return (latest_close / reference_close - 1) * 100 if reference_close else None

            previous_rows = hist[hist["Date"] < latest_date]
            daily_ret = (
                (latest_close / float(previous_rows.iloc[-1]["Close"]) - 1) * 100
                if not previous_rows.empty and float(previous_rows.iloc[-1]["Close"]) else None
            )
            ytd_target = pd.Timestamp(year=latest_date.year, month=1, day=1) - pd.Timedelta(days=1)
            company_rows.append({
                "Company": COMPANY_DISPLAY_NAMES.get(company_ticker, company_ticker),
                "Ticker": company_ticker,
                "Last": latest_close,
                "Daily %": daily_ret,
                "1W %": trailing_return(latest_date - pd.Timedelta(days=7)),
                "1M %": trailing_return(latest_date - pd.DateOffset(months=1)),
                "YTD %": trailing_return(ytd_target),
                "1Y %": trailing_return(latest_date - pd.DateOffset(years=1)),
                "As of": latest_date.strftime("%Y-%m-%d"),
            })

    company_performance = pd.DataFrame(company_rows)
    if not company_performance.empty:
        company_performance = company_performance.sort_values(
            company_sort_metric, ascending=False, na_position="last"
        )
        company_performance = compact_observation_times(company_performance)
        company_formats = {
            "Last": "{:,.2f}",
            "Daily %": "{:+.2f}%",
            "1W %": "{:+.2f}%",
            "1M %": "{:+.2f}%",
            "YTD %": "{:+.2f}%",
            "1Y %": "{:+.2f}%",
        }
        # Apply the same gain/loss colours to all return horizons.
        company_styler = style_market_table(company_performance, company_formats)
        return_columns = ["Daily %", "1W %", "1M %", "YTD %", "1Y %"]
        for return_column in return_columns:
            company_styler = company_styler.map(color_daily_pct, subset=[return_column])
        st.table(company_styler)

    st.markdown("<div id='overview-fx' class='mi-section-band' style='--section-accent:#fdba74'><span class='mi-section-icon'>⇄</span><div><div class='mi-section-kicker'>Currency markets</div><h2>FX performance</h2></div></div>", unsafe_allow_html=True)
    fx_data = snap.loc[snap["Ticker"].isin(fx_tickers)].copy()
    if not fx_data.empty:
        fx_data["Pair"] = fx_data["Ticker"].map(display_names).fillna(fx_data["Ticker"])
        fx_chart = fx_data.dropna(subset=["Daily %"]).sort_values("Daily %", ascending=True).copy()
        if not fx_chart.empty:
            fx_colors = ["#34d399" if x >= 0 else "#fb7185" for x in fx_chart["Daily %"]]
            fx_labels = [f"{x:+.2f}%" if abs(x) >= 0.15 else "" for x in fx_chart["Daily %"]]
            fig_fx = go.Figure(go.Bar(
                x=fx_chart["Daily %"], y=fx_chart["Pair"], orientation="h",
                marker_color=fx_colors, text=fx_labels, textposition="inside",
                insidetextanchor="end", cliponaxis=False,
                hovertemplate="%{y}<br>Daily move: %{x:+.2f}%<extra></extra>",
            ))
            fig_fx.update_layout(
                template="plotly_dark", height=300, margin=dict(l=4, r=6, t=4, b=8),
                xaxis_title="Daily change (%)", yaxis_title=None, showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#cbd5e1", size=10), bargap=0.24,
            )
            fig_fx.update_xaxes(gridcolor="rgba(148,163,184,.20)", zeroline=True, zerolinecolor="#94A3B8", tickfont=dict(color="#F8FAFC", size=10))
            fig_fx.update_yaxes(showgrid=False, automargin=True, tickfont=dict(color="#F8FAFC", size=10))
            st.plotly_chart(fig_fx, width="stretch", theme=None, config={"displayModeBar": False, "responsive": True})
        fx_table = compact_observation_times(fx_data[["Pair", "Ticker", "Last", "Daily %", "As of"]])
        st.table(
            style_market_table(fx_table, {"Last": "{:,.4f}", "Daily %": "{:+.2f}%"})
        )

    # Keep precious metals distinct from the broader commodity complex.
    precious_tickers = tuple(COMMODITY_UNIVERSE[name] for name in PRECIOUS_METALS)
    st.markdown("<div id='overview-metals' class='mi-section-band' style='--section-accent:#fcd34d'><span class='mi-section-icon'>◆</span><div><div class='mi-section-kicker'>Precious metals</div><h2>Gold, silver & platinum</h2></div></div>", unsafe_allow_html=True)
    metals_data = snap.loc[snap["Ticker"].isin(precious_tickers)].copy()
    if not metals_data.empty:
        metals_names = {ticker: name for name, ticker in COMMODITY_UNIVERSE.items() if name in PRECIOUS_METALS}
        metals_data["Instrument"] = metals_data["Ticker"].map(metals_names)
        metals_data["Instrument"] = pd.Categorical(metals_data["Instrument"], categories=PRECIOUS_METALS, ordered=True)
        metals_data = metals_data.sort_values("Instrument")
        metals_table = compact_observation_times(metals_data[["Instrument", "Ticker", "Last", "Daily %", "As of"]])
        st.table(style_market_table(metals_table, {"Last": "{:,.2f}", "Daily %": "{:+.2f}%"}))
    st.caption("Precious metals are grouped separately because gold and silver often respond to real yields, the US dollar and safe-haven demand. Platinum is included in the same metals group.")

    st.markdown("<div id='overview-commodities' class='mi-section-band' style='--section-accent:#c4b5fd'><span class='mi-section-icon'>◈</span><div><div class='mi-section-kicker'>Real assets</div><h2>Commodity futures</h2></div></div>", unsafe_allow_html=True)
    commodity_tickers = tuple(COMMODITY_UNIVERSE[name] for name in OTHER_COMMODITIES)
    commodity_data = snap.loc[snap["Ticker"].isin(commodity_tickers)].copy()
    if not commodity_data.empty:
        commodity_names = {ticker: name for name, ticker in COMMODITY_UNIVERSE.items() if name in OTHER_COMMODITIES}
        commodity_data["Commodity"] = commodity_data["Ticker"].map(commodity_names)
        commodity_data = commodity_data.sort_values("Daily %", ascending=False, na_position="last")
        commodity_table = compact_observation_times(commodity_data[["Commodity", "Ticker", "Last", "Daily %", "As of"]])
        st.table(
            style_market_table(commodity_table, {"Last": "{:,.2f}", "Daily %": "{:+.2f}%"})
        )
    st.caption("Commodity futures are grouped into energy, industrial metals and agriculture. This is a practical watchlist, not a verified live ranking by trading volume. Quotes may be delayed; futures contracts differ in units and expiry.")

    st.markdown("<div class='mi-section-band' style='--section-accent:#60a5fa'><span class='mi-section-icon'>⌁</span><div><div class='mi-section-kicker'>Charting</div><h2>Quick chart</h2></div></div>", unsafe_allow_html=True)
    st.caption("Choose an asset group first, then select the instrument you want to inspect.")
    quick_group = st.selectbox(
        "Asset group",
        ["Major ETFs", "Sectors", "FX", "Precious Metals", "Commodities"],
        key="overview_quick_chart_group",
    )
    if quick_group == "Major ETFs":
        quick_options = {
            "SPY — S&P 500 ETF": "SPY",
            "QQQ — Nasdaq-100 ETF": "QQQ",
            "IWM — Russell 2000 ETF": "IWM",
            "TLT — 20+ Year Treasury ETF": "TLT",
            "GLD — Gold ETF": "GLD",
        }
    elif quick_group == "FX":
        quick_options = FX_UNIVERSE
    elif quick_group == "Precious Metals":
        quick_options = {name: COMMODITY_UNIVERSE[name] for name in PRECIOUS_METALS}
    elif quick_group == "Commodities":
        quick_options = {name: COMMODITY_UNIVERSE[name] for name in OTHER_COMMODITIES}
    else:
        quick_options = {f"{sector} ({ticker})": ticker for sector, ticker in SECTOR_ETFS.items()}
    quick_label = st.selectbox(
        "Instrument",
        list(quick_options.keys()),
        key="overview_quick_chart_instrument",
    )
    render_instrument(quick_options[quick_label], period_label, quick_label)

elif page == "Macro & Event Analysis":
    st.markdown("<div class='mi-eyebrow'>MACRO RESEARCH</div><h2>Macro & Event Analysis</h2>", unsafe_allow_html=True)
    st.caption("Explore how US-listed sectors and major ETFs behaved around verified historical macro releases.")

    # Curated historical dates transcribed from official BLS and Federal Reserve calendars.
    # This is a starter library, not a live calendar feed; always verify dates at the source.
    cpi_source = "https://www.bls.gov/schedule/news_release/cpi.htm"
    jobs_source = "https://www.bls.gov/schedule/news_release/empSit.htm"
    fomc_source = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
    bea_source = "https://www.bea.gov/news/schedule"
    event_library = [
        # CPI release dates confirmed on the BLS CPI schedule.
        {"type": "CPI / inflation", "date": "2025-01-15", "label": "CPI · December 2024", "source": cpi_source, "source_name": "BLS CPI calendar"},
        {"type": "CPI / inflation", "date": "2025-04-10", "label": "CPI · March 2025", "source": cpi_source, "source_name": "BLS CPI calendar"},
        {"type": "CPI / inflation", "date": "2025-05-13", "label": "CPI · April 2025", "source": cpi_source, "source_name": "BLS CPI calendar"},
        {"type": "CPI / inflation", "date": "2025-08-12", "label": "CPI · July 2025", "source": cpi_source, "source_name": "BLS CPI calendar"},
        {"type": "CPI / inflation", "date": "2025-09-11", "label": "CPI · August 2025", "source": cpi_source, "source_name": "BLS CPI calendar"},
        {"type": "CPI / inflation", "date": "2025-10-24", "label": "CPI · September 2025 (rescheduled)", "source": cpi_source, "source_name": "BLS CPI calendar"},
        {"type": "CPI / inflation", "date": "2025-12-18", "label": "CPI · November 2025", "source": cpi_source, "source_name": "BLS CPI calendar"},
        {"type": "CPI / inflation", "date": "2026-01-13", "label": "CPI · December 2025", "source": cpi_source, "source_name": "BLS CPI calendar"},
        {"type": "CPI / inflation", "date": "2026-02-13", "label": "CPI · January 2026", "source": cpi_source, "source_name": "BLS CPI calendar"},
        {"type": "CPI / inflation", "date": "2026-03-11", "label": "CPI · February 2026", "source": cpi_source, "source_name": "BLS CPI calendar"},
        {"type": "CPI / inflation", "date": "2026-04-10", "label": "CPI · March 2026", "source": cpi_source, "source_name": "BLS CPI calendar"},
        {"type": "CPI / inflation", "date": "2026-05-12", "label": "CPI · April 2026", "source": cpi_source, "source_name": "BLS CPI calendar"},
        {"type": "CPI / inflation", "date": "2026-06-10", "label": "CPI · May 2026", "source": cpi_source, "source_name": "BLS CPI calendar"},
        {"type": "CPI / inflation", "date": "2026-07-14", "label": "CPI · June 2026", "source": cpi_source, "source_name": "BLS CPI calendar"},
        {"type": "CPI / inflation", "date": "2026-08-12", "label": "CPI · July 2026", "source": cpi_source, "source_name": "BLS CPI calendar"},
        {"type": "CPI / inflation", "date": "2026-09-11", "label": "CPI · August 2026", "source": cpi_source, "source_name": "BLS CPI calendar"},
        # Employment Situation dates from the BLS release calendar.
        {"type": "Employment / payrolls", "date": "2025-01-10", "label": "Employment Situation · December 2024", "source": jobs_source, "source_name": "BLS Employment Situation calendar"},
        {"type": "Employment / payrolls", "date": "2025-04-04", "label": "Employment Situation · March 2025", "source": jobs_source, "source_name": "BLS Employment Situation calendar"},
        {"type": "Employment / payrolls", "date": "2025-05-02", "label": "Employment Situation · April 2025", "source": jobs_source, "source_name": "BLS Employment Situation calendar"},
        {"type": "Employment / payrolls", "date": "2025-08-01", "label": "Employment Situation · July 2025", "source": jobs_source, "source_name": "BLS Employment Situation calendar"},
        {"type": "Employment / payrolls", "date": "2025-09-05", "label": "Employment Situation · August 2025", "source": jobs_source, "source_name": "BLS Employment Situation calendar"},
        {"type": "Employment / payrolls", "date": "2025-11-20", "label": "Employment Situation · September 2025 (rescheduled)", "source": jobs_source, "source_name": "BLS Employment Situation calendar"},
        {"type": "Employment / payrolls", "date": "2026-07-02", "label": "Employment Situation · June 2026", "source": jobs_source, "source_name": "BLS Employment Situation calendar"},
        {"type": "Employment / payrolls", "date": "2026-09-04", "label": "Employment Situation · August 2026", "source": jobs_source, "source_name": "BLS Employment Situation calendar"},
        {"type": "Employment / payrolls", "date": "2026-10-02", "label": "Employment Situation · September 2026", "source": jobs_source, "source_name": "BLS Employment Situation calendar"},
        # FOMC decision dates are the second day of each scheduled two-day meeting.
        {"type": "FOMC / interest rates", "date": "2025-01-29", "label": "FOMC decision · January 2025", "source": fomc_source, "source_name": "Federal Reserve FOMC calendar"},
        {"type": "FOMC / interest rates", "date": "2025-03-19", "label": "FOMC decision · March 2025", "source": fomc_source, "source_name": "Federal Reserve FOMC calendar"},
        {"type": "FOMC / interest rates", "date": "2025-05-07", "label": "FOMC decision · May 2025", "source": fomc_source, "source_name": "Federal Reserve FOMC calendar"},
        {"type": "FOMC / interest rates", "date": "2025-06-18", "label": "FOMC decision · June 2025", "source": fomc_source, "source_name": "Federal Reserve FOMC calendar"},
        {"type": "FOMC / interest rates", "date": "2025-07-30", "label": "FOMC decision · July 2025", "source": fomc_source, "source_name": "Federal Reserve FOMC calendar"},
        {"type": "FOMC / interest rates", "date": "2025-09-17", "label": "FOMC decision · September 2025", "source": fomc_source, "source_name": "Federal Reserve FOMC calendar"},
        {"type": "FOMC / interest rates", "date": "2025-10-29", "label": "FOMC decision · October 2025", "source": fomc_source, "source_name": "Federal Reserve FOMC calendar"},
        {"type": "FOMC / interest rates", "date": "2025-12-10", "label": "FOMC decision · December 2025", "source": fomc_source, "source_name": "Federal Reserve FOMC calendar"},
        {"type": "FOMC / interest rates", "date": "2026-01-28", "label": "FOMC decision · January 2026", "source": fomc_source, "source_name": "Federal Reserve FOMC calendar"},
        {"type": "FOMC / interest rates", "date": "2026-03-18", "label": "FOMC decision · March 2026", "source": fomc_source, "source_name": "Federal Reserve FOMC calendar"},
        {"type": "FOMC / interest rates", "date": "2026-04-29", "label": "FOMC decision · April 2026", "source": fomc_source, "source_name": "Federal Reserve FOMC calendar"},
        {"type": "FOMC / interest rates", "date": "2026-06-17", "label": "FOMC decision · June 2026", "source": fomc_source, "source_name": "Federal Reserve FOMC calendar"},
        {"type": "FOMC / interest rates", "date": "2026-07-29", "label": "FOMC decision · July 2026", "source": fomc_source, "source_name": "Federal Reserve FOMC calendar"},
        {"type": "FOMC / interest rates", "date": "2026-09-16", "label": "FOMC decision · September 2026", "source": fomc_source, "source_name": "Federal Reserve FOMC calendar"},
    ]

    st.markdown("##### Choose an event")
    event_mode = st.radio(
        "Event source",
        ["Historical event library", "Enter date manually"],
        horizontal=True,
        key="macro_event_source_mode",
        label_visibility="collapsed",
    )
    event_col1, event_col2 = st.columns([1, 1.15])
    with event_col1:
        event_type = st.selectbox(
            "Event type",
            ["CPI / inflation", "FOMC / interest rates", "Employment / payrolls", "GDP / growth", "Other / custom"],
            key="macro_event_type",
        )
    source_by_type = {
        "CPI / inflation": (cpi_source, "BLS CPI calendar"),
        "Employment / payrolls": (jobs_source, "BLS Employment Situation calendar"),
        "FOMC / interest rates": (fomc_source, "Federal Reserve FOMC calendar"),
        "GDP / growth": (bea_source, "BEA release schedule"),
        "Other / custom": (bea_source, "Official release calendar"),
    }
    event_date = None
    selected_event = None
    if event_mode == "Historical event library":
        matching_events = [e for e in event_library if e["type"] == event_type and dt.date.fromisoformat(e["date"]) <= dt.date.today()]
        matching_events = sorted(matching_events, key=lambda e: e["date"], reverse=True)
        if matching_events:
            event_labels = [f"{e['label']} · {dt.date.fromisoformat(e['date']):%d %b %Y}" for e in matching_events]
            with event_col2:
                selected_label = st.selectbox("Historical release", event_labels, key="macro_historical_event")
            selected_event = matching_events[event_labels.index(selected_label)]
            event_date = dt.date.fromisoformat(selected_event["date"])
            st.markdown(
                f"<div style='background:#111C30;border:1px solid #263650;border-radius:10px;padding:12px 14px;color:#E2E8F0;'>Selected release: <strong>{selected_event['label']}</strong> · {event_date:%d %B %Y}<br>Source: <a style='color:#93C5FD' href='{selected_event['source']}' target='_blank'>{selected_event['source_name']}</a></div>",
                unsafe_allow_html=True,
            )
        else:
            st.info("There are no curated dates for this category in the starter library yet. Switch to ‘Enter date manually’ and verify the date with the official calendar.")
            with event_col2:
                event_date = st.date_input(
                    "Release date (manual fallback)", value=dt.date.today() - dt.timedelta(days=30),
                    min_value=dt.date.today() - dt.timedelta(days=720), max_value=dt.date.today(), key="macro_event_date_fallback",
                )
            source_url, source_name = source_by_type[event_type]
            st.markdown(f"Source to verify: [{source_name}]({source_url})")
    else:
        with event_col2:
            event_date = st.date_input(
                "Release date", value=dt.date.today() - dt.timedelta(days=30),
                min_value=dt.date.today() - dt.timedelta(days=720), max_value=dt.date.today(),
                help="Choose the actual publication date from the official calendar. Non-trading dates map to the next available trading session.",
                key="macro_event_date_manual",
            )
        source_url, source_name = source_by_type[event_type]
        st.markdown(f"Verify the date with the [ {source_name} ]({source_url}). The app does not independently validate manual dates.")

    if event_date is None:
        event_date = dt.date.today() - dt.timedelta(days=30)
    if event_mode == "Historical event library" and selected_event is not None:
        st.caption("This release is included in the app's curated starter library. Calendar schedules can change; use the official source link above to confirm details.")

    if event_date.weekday() >= 5:
        st.warning("The selected date falls on a weekend. Confirm the release date; the study maps it to the next available trading session.")
    elif event_mode == "Enter date manually" or selected_event is None:
        st.caption(f"Selected date: {event_date:%A, %d %B %Y}. Manual dates are not independently verified by the app.")
    else:
        st.caption(f"Selected historical release: {event_date:%A, %d %B %Y}. The event library is a curated starter set, not a live calendar feed.")

    st.markdown("##### Event-study settings")
    left_setting, right_setting = st.columns(2)
    with left_setting:
        event_window = st.selectbox("Post-event horizon", ["T+1 session", "T+3 sessions", "T+5 sessions"], index=2, key="macro_post_horizon")
    with right_setting:
        compare_group = st.selectbox("Compare", ["Sectors + benchmarks", "Sectors only", "Major ETFs only"], key="macro_compare_group")

    post_sessions = {"T+1 session": 1, "T+3 sessions": 3, "T+5 sessions": 5}[event_window]
    sector_specs = [(sector, ticker) for sector, ticker in SECTOR_ETFS.items()]
    benchmark_specs = [("S&P 500", "SPY"), ("Nasdaq 100", "QQQ"), ("Small caps", "IWM"), ("Long Treasuries", "TLT"), ("Gold ETF", "GLD")]
    if compare_group == "Sectors only":
        study_specs = sector_specs
    elif compare_group == "Major ETFs only":
        study_specs = benchmark_specs
    else:
        study_specs = sector_specs + benchmark_specs

    event_ts = pd.Timestamp(event_date)
    event_rows = []
    event_paths = []
    skipped = []
    progress = st.progress(0, text="Loading historical price data…")
    for idx, (display_name, ticker) in enumerate(study_specs):
        hist = get_return_history(ticker)
        progress.progress((idx + 1) / max(len(study_specs), 1), text=f"Loading {ticker} ({idx + 1}/{len(study_specs)})…")
        if hist.empty or "Close" not in hist.columns:
            skipped.append(f"{display_name} ({ticker})")
            continue
        hist = hist.dropna(subset=["Date", "Close"]).sort_values("Date").reset_index(drop=True)
        hist["Date"] = pd.to_datetime(hist["Date"]).dt.tz_localize(None)
        event_pos = int(hist["Date"].searchsorted(event_ts, side="left"))
        if event_pos >= len(hist) or event_pos < 5 or event_pos + post_sessions >= len(hist):
            skipped.append(f"{display_name} ({ticker})")
            continue
        mapped_date = pd.Timestamp(hist.loc[event_pos, "Date"])
        baseline = float(hist.loc[event_pos - 1, "Close"])
        if not baseline:
            skipped.append(f"{display_name} ({ticker})")
            continue
        horizon_close = float(hist.loc[event_pos + post_sessions, "Close"])
        horizon_return = (horizon_close / baseline - 1) * 100
        event_day_return = (float(hist.loc[event_pos, "Close"]) / baseline - 1) * 100
        pre_event_return = (float(hist.loc[event_pos - 1, "Close"]) / float(hist.loc[event_pos - 5, "Close"]) - 1) * 100
        event_rows.append({
            "Group": "Sector" if ticker in SECTOR_ETFS.values() else "Benchmark",
            "Instrument": display_name,
            "Ticker": ticker,
            "T0 return (%)": event_day_return,
            f"T+{post_sessions} return (%)": horizon_return,
            "T-5 to T-1 (%)": pre_event_return,
            "Event session": mapped_date.strftime("%Y-%m-%d"),
        })
        for offset in range(-5, post_sessions + 1):
            close = float(hist.loc[event_pos + offset, "Close"])
            event_paths.append({
                "Instrument": display_name,
                "Ticker": ticker,
                "Session": f"T{offset:+d}" if offset != 0 else "T0",
                "Offset": offset,
                "Return from T-1 close (%)": (close / baseline - 1) * 100,
            })
    progress.empty()

    st.markdown("##### Results")
    if not event_rows:
        st.warning("No event window could be calculated. Choose a historical release date with at least five trading sessions before it and enough sessions after it. Yahoo Finance history may also be unavailable.")
    else:
        event_df = pd.DataFrame(event_rows)
        mapped_sessions = sorted(event_df["Event session"].unique())
        if len(mapped_sessions) == 1:
            st.caption(f"{event_type} · selected release date: {event_date:%Y-%m-%d} · mapped trading session: {mapped_sessions[0]} · T0 is the mapped session. Returns are measured from the prior session's close.")
        else:
            st.caption(f"{event_type} · selected release date: {event_date:%Y-%m-%d}. Some instruments mapped to different next available sessions; check the Event session column.")

        chosen_return_col = f"T+{post_sessions} return (%)"
        sectors_only_df = event_df[event_df["Group"] == "Sector"]
        if not sectors_only_df.empty:
            best = sectors_only_df.sort_values(chosen_return_col, ascending=False).iloc[0]
            worst = sectors_only_df.sort_values(chosen_return_col, ascending=True).iloc[0]
            best_name = str(best["Instrument"])
            best_value = float(best[chosen_return_col])
            worst_name = str(worst["Instrument"])
            worst_value = float(worst[chosen_return_col])
        else:
            best_name, best_value = "No sector data", None
            worst_name, worst_value = "No sector data", None
        spy_row = event_df[event_df["Ticker"] == "SPY"]
        spy_value = float(spy_row.iloc[0][chosen_return_col]) if not spy_row.empty else None

        def event_value_class(value):
            if value is None:
                return "neutral"
            return "positive" if value > 0 else ("negative" if value < 0 else "neutral")

        def event_value_text(value):
            return f"{value:+.2f}%" if value is not None else "Not included"

        # HTML summary tiles stay side-by-side on narrow mobile screens, unlike
        # Streamlit metric columns which may stack vertically in mobile Safari.
        summary_cards = [
            (f"BEST SECTOR · T+{post_sessions}", best_name, best_value),
            (f"WEAKEST SECTOR · T+{post_sessions}", worst_name, worst_value),
            ("S&P 500 PROXY", "SPY", spy_value),
        ]
        card_html = []
        for label, name, value in summary_cards:
            card_html.append(
                "<div class='mi-event-summary-card'>"
                f"<div class='mi-event-summary-label'>{html.escape(label)}</div>"
                f"<div class='mi-event-summary-name'>{html.escape(name)}</div>"
                f"<div class='mi-event-summary-value {event_value_class(value)}'>{html.escape(event_value_text(value))}</div>"
                "</div>"
            )
        st.markdown("<div class='mi-event-summary-grid'>" + "".join(card_html) + "</div>", unsafe_allow_html=True)

        plot_df = pd.DataFrame(event_paths)
        if not plot_df.empty:
            st.markdown("##### Return path around the event")
            focus_names = ["S&P 500", "Nasdaq 100", "Long Treasuries", "Gold ETF"]
            if compare_group == "Sectors only":
                focus_names = ["Information Technology", "Financials", "Energy", "Health Care", "Real Estate"]
            focus_df = plot_df[plot_df["Instrument"].isin(focus_names)].copy()
            if focus_df.empty:
                focus_df = plot_df
            order = [f"T{i:+d}" if i != 0 else "T0" for i in range(-5, post_sessions + 1)]
            fig = px.line(
                focus_df, x="Offset", y="Return from T-1 close (%)", color="Instrument", markers=True,
                hover_data={"Instrument": True, "Ticker": True, "Session": True, "Offset": False, "Return from T-1 close (%)": ":+.2f"},
            )
            fig.update_layout(
                template="plotly_dark", paper_bgcolor="#0B1220", plot_bgcolor="#0B1220",
                font=dict(color="#F8FAFC", size=11), height=300,
                margin=dict(l=8, r=8, t=12, b=58), legend_title_text="",
                legend=dict(orientation="h", yanchor="top", y=-0.20, xanchor="left", x=0, font=dict(size=10)),
                hoverlabel=dict(bgcolor="#172033", bordercolor="#475569", font=dict(color="#FFFFFF", size=12)),
            )
            fig.update_xaxes(tickmode="array", tickvals=list(range(-5, post_sessions + 1)), ticktext=order, title=None, color="#F8FAFC", gridcolor="rgba(148,163,184,.15)")
            fig.update_yaxes(title="Return vs T-1 close (%)", color="#F8FAFC", gridcolor="rgba(148,163,184,.20)", zeroline=True, zerolinecolor="#64748B")
            st.plotly_chart(fig, width="stretch", theme=None, config={"responsive": True, "displayModeBar": False})

        st.markdown(f"##### Sector and benchmark comparison · {chosen_return_col}")
        display_event = event_df.sort_values(chosen_return_col, ascending=False).reset_index(drop=True)
        st.dataframe(
            style_market_table(display_event, {"T0 return (%)": "{:+.2f}%", chosen_return_col: "{:+.2f}%", "T-5 to T-1 (%)": "{:+.2f}%"}),
            width="stretch", hide_index=True,
        )
        st.download_button(
            "Download event-study results (CSV)", display_event.to_csv(index=False).encode("utf-8"),
            file_name=f"event_study_{event_type.split('/')[0].strip().lower().replace(' ', '_')}_{event_date:%Y%m%d}.csv",
            mime="text/csv", key="download_macro_event_study",
        )
        if skipped:
            st.caption("Unavailable or insufficient history: " + ", ".join(skipped))

    st.markdown("##### Macro market context")
    st.caption("These are market proxies, not official macroeconomic releases. They can help frame the event but do not prove causation.")
    proxy_cols = st.columns(4)
    proxy_specs = [("US 10Y yield", "^TNX", "yield"), ("US Dollar Index", "DX-Y.NYB", "price"), ("Gold futures", "GC=F", "price"), ("WTI crude", "CL=F", "price")]
    for col, (label, ticker, kind) in zip(proxy_cols, proxy_specs):
        with col:
            proxy = get_history(ticker, "5d", "1d")
            if not proxy.empty and len(proxy) >= 2:
                proxy = proxy.sort_values("Date")
                latest_value = float(proxy["Close"].iloc[-1])
                previous_value = float(proxy["Close"].iloc[-2])
                if kind == "yield":
                    change_text = f"{(latest_value - previous_value) * 100:+.0f} bps"
                    value_text = f"{latest_value:.2f}%"
                else:
                    change_text = f"{((latest_value / previous_value) - 1) * 100:+.2f}%" if previous_value else "—"
                    value_text = f"{latest_value:,.2f}"
                st.metric(label, value_text, change_text)
            else:
                st.metric(label, "—", "Unavailable")
    st.caption("Interpretation: compare the event-window returns with the pre-event path, then investigate whether yields, the dollar or commodity prices moved at the same time. Event studies show association, not causation. Historical prices and market proxies come from Yahoo Finance and may be delayed or revised.")

elif page == "ETF Explorer":
    st.markdown("<div class='mi-eyebrow'>RESEARCH</div><h2>ETF Explorer</h2>", unsafe_allow_html=True)
    etf_label = st.selectbox("ETF universe", list(ETF_UNIVERSE.keys()))
    ticker = ETF_UNIVERSE[etf_label]
    render_instrument(ticker, period_label, etf_label)

elif page == "Sector Monitor":
    st.markdown("<div class='mi-eyebrow'>EQUITY RESEARCH</div><h2>Sector Monitor</h2>", unsafe_allow_html=True)
    sector = st.selectbox("Select GICS sector", list(SECTOR_ETFS.keys()))
    sector_etf = SECTOR_ETFS[sector]
    st.markdown("#### Sector ETF")
    render_instrument(sector_etf, period_label, f"{sector} ({sector_etf})")
    st.markdown("#### Company constituents")
    st.caption("Representative large-cap names, not a guaranteed current market-cap ranking.")
    company_tickers = SECTOR_COMPANIES[sector]
    company_snap = get_snapshot(tuple(company_tickers))
    company_snap = company_snap.sort_values("Daily %", ascending=False, na_position="last")
    company_snap = compact_observation_times(company_snap)
    st.dataframe(style_market_table(company_snap, {"Last": "{:,.2f}", "Daily %": "{:+.2f}%"}), width="stretch", hide_index=True)
    selected_company = st.selectbox("Open company chart", company_tickers)
    render_instrument(selected_company, period_label)

elif page == "G10 FX":
    st.markdown("<div class='mi-eyebrow'>CURRENCY MARKETS</div><h2>G10 FX Monitor</h2>", unsafe_allow_html=True)
    st.caption("Yahoo Finance symbols and quote conventions vary by pair. Always verify the displayed pair and last-updated timestamp.")
    fx_label = st.selectbox("Currency pair", list(FX_UNIVERSE.keys()))
    ticker = FX_UNIVERSE[fx_label]
    render_instrument(ticker, period_label, fx_label)
    st.markdown("#### G10 watchlist")
    fx_snap = get_snapshot(tuple(dict.fromkeys(FX_UNIVERSE.values())))
    fx_names = {v: k for k, v in FX_UNIVERSE.items()}
    fx_snap["Pair"] = fx_snap["Ticker"].map(fx_names)
    fx_table = compact_observation_times(fx_snap[["Pair", "Ticker", "Last", "Daily %", "As of"]])
    st.table(style_market_table(fx_table, {"Last": "{:,.4f}", "Daily %": "{:+.2f}%"}))

elif page == "Commodities":
    st.markdown("<div class='mi-section-band' style='--section-accent:#c4b5fd'><span class='mi-section-icon'>◈</span><div><div class='mi-section-kicker'>Real assets</div><h2>Commodity & metals monitor</h2></div></div>", unsafe_allow_html=True)
    st.caption("Precious metals are grouped separately from energy, industrial metals and agricultural futures. This is a practical market watchlist, not a verified live ranking by trading volume.")
    commodity_category = st.selectbox("Market group", ["All markets", *COMMODITY_CATEGORIES.keys()], key="commodity_group")
    if commodity_category == "All markets":
        commodity_options = COMMODITY_UNIVERSE
    else:
        commodity_options = {name: COMMODITY_UNIVERSE[name] for name in COMMODITY_CATEGORIES[commodity_category]}
    commodity_label = st.selectbox("Commodity", list(commodity_options.keys()), key="commodity_instrument")
    render_instrument(commodity_options[commodity_label], period_label, commodity_label)
    st.markdown("#### Market watchlist")
    commodity_snap = get_snapshot(tuple(COMMODITY_UNIVERSE.values()))
    commodity_names = {ticker: name for name, ticker in COMMODITY_UNIVERSE.items()}
    commodity_snap["Commodity"] = commodity_snap["Ticker"].map(commodity_names)
    commodity_snap = commodity_snap.sort_values("Daily %", ascending=False, na_position="last")
    commodity_table = compact_observation_times(commodity_snap[["Commodity", "Ticker", "Last", "Daily %", "As of"]])
    st.table(style_market_table(commodity_table, {"Last": "{:,.2f}", "Daily %": "{:+.2f}%"}))
    st.caption("Prices are futures quotes from Yahoo Finance and may be delayed. Futures contracts can have different units, expiries and roll characteristics; do not compare nominal prices across commodities directly.")

else:
    st.markdown("<div class='mi-eyebrow'>CHARTING & RETURNS</div><h2>Instrument Explorer</h2>", unsafe_allow_html=True)
    st.caption("Explore one instrument at a time using a consistent layout for ETFs, stocks, currencies and indices.")
    mode = st.radio("Asset class", ["ETF", "Stock", "G10 FX", "Precious Metals", "Commodities", "Index"], horizontal=True, key="explorer_asset_class")
    if mode == "ETF":
        options = ETF_UNIVERSE
    elif mode == "Stock":
        all_companies = sorted({x for names in SECTOR_COMPANIES.values() for x in names})
        options = {x: x for x in all_companies}
    elif mode == "G10 FX":
        options = FX_UNIVERSE
    elif mode == "Precious Metals":
        options = {name: COMMODITY_UNIVERSE[name] for name in PRECIOUS_METALS}
    elif mode == "Commodities":
        options = {name: COMMODITY_UNIVERSE[name] for name in OTHER_COMMODITIES}
    else:
        options = {"S&P 500": "^GSPC", "Dow Jones Industrial Average": "^DJI", "Nasdaq Composite": "^IXIC", "Russell 2000": "^RUT"}

    label = st.selectbox("Instrument", list(options.keys()), key="explorer_instrument")
    period_choices = ["1D", "5D", "1M", "3M", "YTD", "1Y"]
    default_period = period_label if period_label in period_choices else "1Y"
    explorer_period = st.radio("Historical period", period_choices, index=period_choices.index(default_period), horizontal=True, key="explorer_period")
    st.session_state["explorer_mode_label"] = "FX" if mode == "G10 FX" else mode
    render_explorer_view(options[label], explorer_period, label)

st.divider()
st.caption("Built with Streamlit, Plotly, pandas and yfinance · Personal research only, not investment advice · Futures data may be delayed; verify market data with your broker or licensed provider before making decisions.")
