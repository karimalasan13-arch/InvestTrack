
import streamlit as st
import requests
import json
import os
import datetime as dt
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Investrack (Stable Persistent)", layout="wide")

# ---- Files ----
USER_DATA_FILE = "user_data.json"
HISTORY_FILE = "portfolio_history.json"

def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_user_data(d):
    try:
        with open(USER_DATA_FILE, "w") as f:
            json.dump(d, f, indent=2)
    except:
        pass

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(h):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(h, f, indent=2)
    except:
        pass

# ---- Default data load ----
_user = load_user_data()
history = load_history()

# ---- Sidebar (Option A - Simple) ----
st.sidebar.title("Portfolio Settings (Persistent)")

coins = ["BTC","ETH","USDT","USDC","BNB","SOL","XRP","ADA","DOGE","TRX"]
# defaults
saved_holdings = _user.get("holdings", {})
holdings = {}
st.sidebar.subheader("Holdings")
for c in coins:
    default = float(saved_holdings.get(c, 0))
    holdings[c] = st.sidebar.number_input(f"{c} Holding", value=default, min_value=0.0, key=f"hold_{c}")

fx_default = float(_user.get("fx_rate", 15.0))
fx_rate = st.sidebar.number_input("FX Rate (USD → GHS)", value=fx_default, min_value=0.01, key="fx_rate")

invested_default = float(_user.get("total_invested", 0.0))
total_invested = st.sidebar.number_input("Total All-Time Investment (GHS)", value=invested_default, min_value=0.0, key="total_invested")

# Save user data immediately
_user["holdings"] = holdings
_user["fx_rate"] = fx_rate
_user["total_invested"] = total_invested
save_user_data(_user)

# ---- Price fetching (CoinGecko ids) ----
coin_ids = {
    "BTC":"bitcoin","ETH":"ethereum","USDT":"tether","USDC":"usd-coin","BNB":"binancecoin",
    "SOL":"solana","XRP":"ripple","ADA":"cardano","DOGE":"dogecoin","TRX":"tron"
}
ids = ",".join(coin_ids.values())
try:
    resp = requests.get("https://api.coingecko.com/api/v3/simple/price", params={"ids": ids, "vs_currencies":"usd"}, timeout=10)
    price_json = resp.json()
except Exception:
    price_json = {}

prices = {}
for sym, cid in coin_ids.items():
    if sym in ["USDT","USDC"]:
        prices[sym] = 1.0
    else:
        prices[sym] = float(price_json.get(cid, {}).get("usd", 0) or 0)

# ---- Calculations ----
total_usd = 0.0
rows = []
for sym in coins:
    amt = holdings.get(sym, 0)
    price = prices.get(sym, 0)
    val_usd = amt * price
    val_ghs = val_usd * fx_rate
    total_usd += val_usd
    rows.append({"coin": sym, "amount": amt, "price_usd": price, "value_usd": val_usd, "value_ghs": val_ghs})

total_ghs = total_usd * fx_rate
pnl = total_ghs - total_invested
pnl_pct = (pnl / total_invested * 100) if total_invested > 0 else 0

# ---- Save history snapshot on every load ----
try:
    timestamp = dt.datetime.utcnow().isoformat()
    history.append({"timestamp": timestamp, "value_ghs": total_ghs})
    save_history(history)
except Exception:
    pass

# ---- UI ----
st.title("📊 Investrack — Stable Persistent")

c1, c2, c3 = st.columns(3)
c1.metric("Total Value (GHS)", f"GHS {total_ghs:,.2f}")
c2.metric("Total Invested (GHS)", f"GHS {total_invested:,.2f}")
delta_all_time = f"{pnl_pct:.2f}%"
c3.metric("All-Time PNL (GHS)", f"GHS {pnl:,.2f}", delta=delta_all_time)

# ---- MTD & YTD PNL ----
st.subheader("Performance — MTD / YTD")

dfh = pd.DataFrame(history)
dfh['timestamp'] = pd.to_datetime(dfh['timestamp'])

latest_val = total_ghs

current_month = dt.datetime.utcnow().month
current_year = dt.datetime.utcnow().year

df_mtd = dfh[(dfh['timestamp'].dt.year == current_year) &
             (dfh['timestamp'].dt.month == current_month)]

if len(df_mtd) > 1:
    start_mtd = df_mtd.iloc[0]['value_ghs']
    pnl_mtd = latest_val - start_mtd
    pnl_pct_mtd = (pnl_mtd / start_mtd * 100) if start_mtd > 0 else 0
else:
    pnl_mtd = 0
    pnl_pct_mtd = 0

df_ytd = dfh[dfh['timestamp'].dt.year == current_year]

if len(df_ytd) > 1:
    start_ytd = df_ytd.iloc[0]['value_ghs']
    pnl_ytd = latest_val - start_ytd
    pnl_pct_ytd = (pnl_ytd / start_ytd * 100) if start_ytd > 0 else 0
else:
    pnl_ytd = 0
    pnl_pct_ytd = 0

c4, c5 = st.columns(2)
delta_mtd = f"{pnl_pct_mtd:.2f}%"
c4.metric("MTD PNL", f"GHS {pnl_mtd:,.2f}", delta=delta_mtd)
delta_ytd = f"{pnl_pct_ytd:.2f}%"
c5.metric("YTD PNL", f"GHS {pnl_ytd:,.2f}", delta=delta_ytd)

st.subheader("Portfolio Value Over Time (GHS)")
if len(history) > 1:
    dfh = pd.DataFrame(history)
    dfh['timestamp'] = pd.to_datetime(dfh['timestamp'])
    fig = px.line(dfh, x='timestamp', y='value_ghs', title='Portfolio Value (GHS)')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Line chart will appear once enough data is recorded (two points minimum).")

st.subheader("Portfolio Breakdown")
df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True)

st.subheader("Asset Allocation (%)")
alloc = df[df['value_ghs']>0].copy()
if not alloc.empty:
    fig2 = px.pie(alloc, names='coin', values='value_ghs', title='Allocation (GHS)')
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Enter holdings to see allocation chart.")
