# Market Intelligence Dashboard

A beginner-friendly personal market dashboard built with Streamlit.

## Included in this starter version

- Market overview with S&P 500, major ETFs and selected FX pairs
- ETF explorer
- Sector monitor for all 11 GICS sectors using sector ETFs
- Starter company constituent lists for each sector
- G10 FX monitor
- Historical price charts and return tables
- CSV export
- Five-minute caching and a manual refresh button
- Responsive layout for desktop and mobile browsers

## Important data limitation

This version uses Yahoo Finance through `yfinance`. Quote timing, symbol coverage and intraday availability vary by instrument. Do not assume quotes are guaranteed real-time or exchange-licensed. The sector company lists are representative starter lists, **not guaranteed current top-10 market-cap rankings**. Dynamic top-10 rankings should be added after selecting a dependable market-cap/constituent data provider.

## Files

- `app.py` — Streamlit app
- `requirements.txt` — Python dependencies

## Deploy using GitHub and Streamlit Community Cloud

1. Create a new GitHub repository named `market-intelligence-dashboard`.
2. Keep the repository private while you are learning, unless you want the code to be public.
3. Add `app.py` and `requirements.txt` to the repository root.
4. Open Streamlit Community Cloud and connect your GitHub account.
5. Create an app from the new repository, branch `main`, file path `app.py`.
6. Deploy. Open the app URL on your iPhone or computer.

No API key is required for this starter version. Do not put any future API keys or passwords in source code or a public repository; use Streamlit Secrets.

## Run locally (optional)

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Return methodology

The app calculates percentage changes from the latest available adjusted close to a reference observation at or before each lookback target. Actual available observations depend on the data returned by the provider. Intraday history may not include enough data for all return periods.

## Disclaimer

For personal research and educational use only. Not investment advice. Market data may be delayed, incomplete or inaccurate. Verify with your broker or licensed data provider.
