import streamlit as st
import requests
import datetime as dt
import plotly.express as px

st.set_page_config(page_title="InvésTrack", layout="wide")
st.title("InvésTrack – Portfolio Tracker")

# ---- Sidebar Inputs ----
coins = ["BTC","ETH","USDT","USDC","BNB","SOL","XRP","ADA","DOGE","TRX"]

st.sidebar.header("Holdings")
holdings = {c: st.sidebar.number_input(f"{c} Holding", 0.0) for c in coins}

fx_rate = st.sidebar.number_input("FX Rate (USD → GHS)", value=15.0)
total_invested = st.sidebar.number_input("Total All-Time Investment (GHS)", value=0.0)

# ---- Fetch Prices ----
def get_price(symbol):
    if symbol in ["USDT", "USDC"]:
        return 1.0
    url=f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
    try:
        data = requests.get(url, timeout=5).json()
        return float(data.get("price", 0))
    except:
        return 0

prices = {c: get_price(c) for c in coins}

# ---- Calculate Portfolio Value ----
usd_value = sum(holdings[c] * prices[c] for c in coins)
ghs_value = usd_value * fx_rate
pnl_total = ghs_value - total_invested
pnl_total_pct = (pnl_total / total_invested * 100) if total_invested > 0 else 0

st.subheader("Portfolio Overview")
col1,col2,col3=st.columns(3)
col1.metric("Total Value (GHS)", f"{ghs_value:,.2f}")
col2.metric("Total Invested (GHS)", f"{total_invested:,.2f}")
col3.metric("Total PNL", f"{pnl_total:,.2f}", f"{pnl_total_pct:.2f}%")

# ---- WTD / MTD / YTD PNL ----
today = dt.date.today()
start_week = today - dt.timedelta(days=today.weekday())
start_month = today.replace(day=1)
start_year = today.replace(month=1, day=1)

def pnl_est(start_date):
    days = (today - start_date).days or 1
    return pnl_total * (1/days)

def pnl_est_pct(start_date):
    pnl = pnl_est(start_date)
    return (pnl / total_invested * 100) if total_invested > 0 else 0

st.subheader("Performance")
colw,colm,coly = st.columns(3)

wtd_val = pnl_est(start_week)
wtd_pct = pnl_est_pct(start_week)
colw.metric("WTD PNL (est.)", f"{wtd_val:,.2f}", f"{wtd_pct:.2f}%")

mtd_val = pnl_est(start_month)
mtd_pct = pnl_est_pct(start_month)
colm.metric("MTD PNL (est.)", f"{mtd_val:,.2f}", f"{mtd_pct:.2f}%")

ytd_val = pnl_est(start_year)
ytd_pct = pnl_est_pct(start_year)
coly.metric("YTD PNL (est.)", f"{ytd_val:,.2f}", f"{ytd_pct:.2f}%")

# ---- Pie Chart ----
st.subheader("Asset Allocation")
alloc = {c: holdings[c]*prices[c] for c in coins if holdings[c]*prices[c] > 0}

if alloc:
    fig = px.pie(names=list(alloc.keys()), values=list(alloc.values()))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Enter holdings to see allocation chart.")
