import datetime as dt
from typing import Dict, List

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
    "USD/JPY (alternate feed)": "JPY=X",
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
# Styling
# -----------------------------
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.25rem; padding-bottom: 2rem; max-width: 1500px;}
    [data-testid="stMetric"] {background: rgba(128,128,128,0.07); padding: 14px 16px; border-radius: 12px; border: 1px solid rgba(128,128,128,0.15);}
    [data-testid="stSidebar"] {border-right: 1px solid rgba(128,128,128,0.18);}
    .small-muted {font-size: 0.82rem; opacity: 0.72;}
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
            "As of": pd.Timestamp(hist["Date"].iloc[-1]).strftime("%Y-%m-%d %H:%M"),
        })
    return pd.DataFrame(rows)


def format_price(value, ticker: str) -> str:
    if pd.isna(value):
        return "—"
    return f"{value:,.4f}" if "=X" in ticker or ticker.endswith("=X") else f"{value:,.2f}"


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
        template="plotly_dark" if st.get_option("theme.base") == "dark" else "plotly_white",
        height=390, margin=dict(l=8, r=8, t=22, b=8),
        xaxis_title=None, yaxis_title="Price",
        hovermode="x unified", showlegend=False,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.15)")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Chart interval: {interval_label}. Historical data and quote timing depend on Yahoo Finance coverage; not an exchange-licensed real-time feed.")


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
    m3.metric("Last data point", pd.Timestamp(data["Date"].iloc[-1]).strftime("%d %b %Y %H:%M"))
    render_price_chart(data, ticker, interval)
    st.markdown("#### Historical returns")
    table = returns_table(data)
    st.dataframe(
        table.style.format({"Reference close": "{:,.4f}", "Latest close": "{:,.4f}", "Return (%)": "{:+.2f}%"}, na_rep="—"),
        use_container_width=True, hide_index=True
    )
    csv = table.to_csv(index=False).encode("utf-8")
    st.download_button("Download return table (CSV)", csv, file_name=f"{ticker.replace('=', '_')}_returns.csv", mime="text/csv")
    st.caption("Returns use adjusted closing prices where the provider supplies them. Intraday periods can have limited history; unavailable reference dates are shown as insufficient history.")


# -----------------------------
# Sidebar / navigation
# -----------------------------
st.sidebar.markdown("## MARKET INTELLIGENCE")
st.sidebar.caption("A personal multi-asset market monitor")
page = st.sidebar.radio(
    "Navigation",
    ["Overview", "ETF Explorer", "Sector Monitor", "G10 FX", "Instrument Explorer"],
)
st.sidebar.divider()
period_label = st.sidebar.selectbox("Chart period", list(PERIOD_OPTIONS.keys()), index=2)
st.sidebar.caption("Data refresh: cached for 5 minutes. Use the refresh button to request new data.")
if st.sidebar.button("↻ Refresh data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.title("Market Intelligence")
st.caption("US equity markets • ETFs • GICS sectors • G10 FX")
st.info("Data notice: this starter version uses Yahoo Finance via yfinance. Quote delays, symbol coverage and intraday availability vary. Prices are for information only and should not be treated as guaranteed real-time exchange quotes.")

if page == "Overview":
    st.markdown("### Market snapshot")
    overview_tickers = ("^GSPC", "SPY", "QQQ", "IWM", "TLT", "GLD", "EURUSD=X", "JPY=X", "GBPUSD=X", "AUDUSD=X")
    snap = get_snapshot(overview_tickers)
    display_names = {
        "^GSPC": "S&P 500", "SPY": "SPY", "QQQ": "QQQ", "IWM": "IWM",
        "TLT": "TLT", "GLD": "GLD", "EURUSD=X": "EUR/USD", "JPY=X": "USD/JPY",
        "GBPUSD=X": "GBP/USD", "AUDUSD=X": "AUD/USD",
    }
    for start in (0, 5):
        cols = st.columns(5)
        for col, (_, row) in zip(cols, snap.iloc[start:start+5].iterrows()):
            with col:
                val = row["Last"]
                change = row["Daily %"]
                col.metric(display_names.get(row["Ticker"], row["Ticker"]), format_price(val, row["Ticker"]) if pd.notna(val) else "—",
                           f"{change:+.2f}%" if pd.notna(change) else "—")
    st.markdown("### Sector performance")
    sector_tickers = tuple(SECTOR_ETFS.values())
    sector_data = get_snapshot(sector_tickers)
    name_by_ticker = {v: k for k, v in SECTOR_ETFS.items()}
    if not sector_data.empty:
        sector_data["Sector"] = sector_data["Ticker"].map(name_by_ticker)
        sector_data = sector_data.sort_values("Daily %", ascending=False, na_position="last")
        st.dataframe(sector_data[["Sector", "Ticker", "Last", "Daily %", "As of"]].style.format({"Last": "{:,.2f}", "Daily %": "{:+.2f}%"}, na_rep="—"), use_container_width=True, hide_index=True)
    st.markdown("### Quick chart")
    quick = st.selectbox("Choose a market instrument", ["^GSPC", "SPY", "QQQ", "IWM", "TLT", "GLD", "EURUSD=X", "JPY=X"])
    render_instrument(quick, period_label)

elif page == "ETF Explorer":
    st.markdown("### ETF Explorer")
    etf_label = st.selectbox("ETF universe", list(ETF_UNIVERSE.keys()))
    ticker = ETF_UNIVERSE[etf_label]
    render_instrument(ticker, period_label, etf_label)

elif page == "Sector Monitor":
    st.markdown("### Sector Monitor")
    sector = st.selectbox("Select GICS sector", list(SECTOR_ETFS.keys()))
    sector_etf = SECTOR_ETFS[sector]
    left, right = st.columns([1, 2])
    with left:
        st.markdown("#### Sector ETF")
        render_instrument(sector_etf, period_label, f"{sector} ({sector_etf})")
    with right:
        st.markdown("#### Company constituents")
        st.caption("Starter list of representative large-cap constituents. This list is not guaranteed to be the current top 10 by market capitalisation; dynamic rankings require a reliable constituent/market-cap data source.")
        company_tickers = SECTOR_COMPANIES[sector]
        company_snap = get_snapshot(tuple(company_tickers))
        company_snap = company_snap.sort_values("Daily %", ascending=False, na_position="last")
        st.dataframe(company_snap.style.format({"Last": "{:,.2f}", "Daily %": "{:+.2f}%"}, na_rep="—"), use_container_width=True, hide_index=True)
        selected_company = st.selectbox("Open company chart", company_tickers)
        render_instrument(selected_company, period_label)

elif page == "G10 FX":
    st.markdown("### G10 FX Monitor")
    st.caption("Yahoo Finance symbols and quote conventions vary by pair. Always verify the displayed pair and last-updated timestamp.")
    fx_label = st.selectbox("Currency pair", list(FX_UNIVERSE.keys()))
    ticker = FX_UNIVERSE[fx_label]
    render_instrument(ticker, period_label, fx_label)
    st.markdown("#### G10 watchlist")
    fx_snap = get_snapshot(tuple(dict.fromkeys(FX_UNIVERSE.values())))
    fx_names = {v: k for k, v in FX_UNIVERSE.items()}
    fx_snap["Pair"] = fx_snap["Ticker"].map(fx_names)
    st.dataframe(fx_snap[["Pair", "Ticker", "Last", "Daily %", "As of"]].style.format({"Last": "{:,.4f}", "Daily %": "{:+.2f}%"}, na_rep="—"), use_container_width=True, hide_index=True)

else:
    st.markdown("### Instrument Explorer")
    mode = st.radio("Asset type", ["ETF", "Stock", "FX", "Index"], horizontal=True)
    if mode == "ETF":
        options = ETF_UNIVERSE
    elif mode == "Stock":
        all_companies = sorted({x for names in SECTOR_COMPANIES.values() for x in names})
        options = {x: x for x in all_companies}
    elif mode == "FX":
        options = FX_UNIVERSE
    else:
        options = {"S&P 500": "^GSPC", "Dow Jones Industrial Average": "^DJI", "Nasdaq Composite": "^IXIC", "Russell 2000": "^RUT"}
    label = st.selectbox("Instrument", list(options.keys()))
    render_instrument(options[label], period_label, label)

st.divider()
st.caption("Built with Streamlit, Plotly, pandas and yfinance. This is a personal research dashboard, not investment advice. Verify market data with your broker or licensed data provider before making decisions.")
