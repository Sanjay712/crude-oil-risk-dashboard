import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
import os
import requests
from dotenv import load_dotenv

st.set_page_config(page_title="Crude Oil Risk Dashboard", layout="wide")
st.title("🛢️ Crude Oil Volatility & Risk Intelligence Dashboard")

# 🔄 Auto-refresh every 10 minutes
st_autorefresh(interval=600000, key="auto_refresh")

# 📡 Load environment for NewsAPI
load_dotenv()
NEWS_API_KEY = os.getenv("NEWSAPI_KEY")

def get_commodity_news():
    url = (
        f"https://newsapi.org/v2/everything?q=crude+oil+OR+gold+OR+commodity+OR+OPEC"
        f"&sortBy=publishedAt&language=en&pageSize=5&apiKey={NEWS_API_KEY}"
    )
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("articles", [])
    return []

# 🆕 Download latest data (last 60 days)
st.info("🔄 Fetching latest crude oil, gold, and USD index data...")
oil = yf.download("CL=F", period="60d", interval="1d")["Close"]
gold = yf.download("GC=F", period="60d", interval="1d")["Close"]
usd = yf.download("DX-Y.NYB", period="60d", interval="1d")["Close"]

if oil.empty or gold.empty or usd.empty:
    st.error("❌ Failed to fetch data from Yahoo Finance. Please check your internet connection or ticker symbols.")
    st.stop()

# Combine into one DataFrame
df = pd.concat([oil, gold, usd], axis=1)
df.columns = ["Price", "Gold", "USD"]
df.index.name = "Date"

# Calculate metrics
df["Daily Return"] = df["Price"].pct_change()
df["10D Volatility"] = df["Daily Return"].rolling(10).std()
df["VaR_95"] = df["Daily Return"].rolling(10).quantile(0.05)

# Add Event Markers
event_dates = {
    '2024-04-13': 'Iran attacks Israel',
    '2024-04-15': 'US/NATO response',
    '2024-04-18': 'Crude oil spike',
    '2024-05-05': 'Oil supply disruption'
}
df['Event'] = df.index.strftime('%Y-%m-%d').map(event_dates)

# Momentum Strategy
sma = df['Price'].rolling(10).mean()
df['Momentum Signal'] = (df['Price'] > sma).astype(int).replace(0, -1)
df['Momentum Strategy Return'] = df['Momentum Signal'].shift(1) * df['Daily Return']
df['Cumulative Market Return'] = (1 + df['Daily Return']).cumprod()
df['Cumulative Momentum Return'] = (1 + df['Momentum Strategy Return']).cumprod()

# Entry/Exit Markers
df['Signal Change'] = df['Momentum Signal'].diff()
entries = df[df['Signal Change'] == 2]
exits = df[df['Signal Change'] == -2]

# Top Risk Days: highest volatility or VaR spikes
top_risk_days = df.sort_values(by='10D Volatility', ascending=False).head(3)

# --- Tabs Layout ---
tabs = st.tabs(["🏠 Overview", "📉 Volatility & Risk", "📈 Strategy Backtest", "🌐 Macro Correlation", "🗞️ Market News"])

# --- OVERVIEW TAB ---
with tabs[0]:
    st.header("Overview")
    st.markdown("""
    Welcome to the **Crude Oil Risk Intelligence Dashboard**.

    This platform simulates financial risk metrics and trading strategy performance around crude oil price movements. It integrates geopolitical events, volatility metrics, macroeconomic correlations, and systematic trading logic into a single interactive tool.
    """)

    st.subheader("📌 Current Market Snapshot")
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Crude Oil Price", f"${df['Price'].iloc[-1]:.2f}")
    col2.metric("10D Volatility", f"{df['10D Volatility'].iloc[-1]:.2%}")
    col3.metric("Latest 95% VaR", f"{df['VaR_95'].iloc[-1]:.2%}")

    try:
        with open("output/oil_volatility_analysis.xlsx", "rb") as f:
            st.download_button(
                label="📥 Download Excel Analysis",
                data=f,
                file_name="oil_volatility_analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except:
        st.warning("Excel report not found. Generate output/oil_volatility_analysis.xlsx first.")

# --- VOLATILITY TAB ---
with tabs[1]:
    st.header("Volatility & Value at Risk")
    fig = px.line(df, x=df.index, y=["10D Volatility", "VaR_95"], title="Volatility & VaR with Geopolitical Events")
    for i, row in df[df['Event'].notnull()].iterrows():
        fig.add_vline(x=i, line_width=1, line_dash="dash", line_color="gray")
        fig.add_annotation(x=i, y=df['10D Volatility'].max()*0.85, text=row['Event'],
                           showarrow=False, yanchor="bottom", font=dict(size=9, color="gray"))
    st.plotly_chart(fig, use_container_width=True)

    try:
        st.download_button(
            label="📸 Download Chart as PNG",
            data=fig.to_image(format="png"),
            file_name="volatility_chart.png",
            mime="image/png"
        )
    except:
        st.warning("Plot image export needs 'kaleido'. Run: pip install -U kaleido")

# --- STRATEGY TAB ---
with tabs[2]:
    st.header("Backtested Momentum Strategy")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Cumulative Market Return'], name='Market Return', line=dict(color='gray')))
    fig.add_trace(go.Scatter(x=df.index, y=df['Cumulative Momentum Return'], name='Strategy Return', line=dict(color='green')))
    fig.add_trace(go.Scatter(x=entries.index, y=entries['Cumulative Momentum Return'], mode='markers',
                             marker=dict(symbol='triangle-up', size=10, color='blue'), name='Buy Signal'))
    fig.add_trace(go.Scatter(x=exits.index, y=exits['Cumulative Momentum Return'], mode='markers',
                             marker=dict(symbol='triangle-down', size=10, color='red'), name='Sell Signal'))
    for idx, row in top_risk_days.iterrows():
        fig.add_vline(x=idx, line_width=1.2, line_dash="dot", line_color="orange")
        fig.add_annotation(x=idx, y=row['Cumulative Momentum Return'],
                           text=f"High Risk\n({row['10D Volatility']:.2%})",
                           showarrow=True, arrowhead=1, ax=0, ay=-40, font=dict(color="orange"))
    fig.update_layout(title="Momentum Strategy with Entry/Exit & Top Risk Days",
                      xaxis_title="Date", yaxis_title="Cumulative Return",
                      legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, use_container_width=True)

    try:
        st.download_button(
            label="📸 Download Chart as PNG",
            data=fig.to_image(format="png"),
            file_name="strategy_chart.png",
            mime="image/png"
        )
    except Exception as e:
        st.warning("📦 Plot export needs 'kaleido'. Run: pip install -U kaleido")

# --- MACRO CORRELATION TAB ---
with tabs[3]:
    st.header("Macro Correlation Analysis")
    window = st.slider("Rolling Window (days)", 5, 30, 10, key="corr_slider")
    df['Oil-Gold Corr'] = df['Daily Return'].rolling(window).corr(df['Gold'].pct_change())
    df['Oil-USD Corr'] = df['Daily Return'].rolling(window).corr(df['USD'].pct_change())
    fig = px.line(df, x=df.index, y=["Oil-Gold Corr", "Oil-USD Corr"],
                  title=f"Oil-Gold and Oil-USD Rolling {window}-Day Correlations")
    st.plotly_chart(fig, use_container_width=True)

    try:
        st.download_button(
            label="📸 Download Chart as PNG",
            data=fig.to_image(format="png"),
            file_name="correlation_chart.png",
            mime="image/png"
        )
    except:
        st.warning("📦 Plot export needs 'kaleido'. Run: pip install -U kaleido")

# --- NEWS TAB ---
with tabs[4]:
    st.header("🗞️ Latest Commodity & Macro Market News")
    st.markdown("Stay informed with recent headlines influencing crude oil, gold, and global markets.")
    news_items = get_commodity_news()
    if news_items:
        for article in news_items:
            st.markdown(f"**[{article['title']}]({article['url']})**")
            st.markdown(f"*{article['source']['name']} | {article['publishedAt'][:10]}*")
            st.markdown(f"> {article['description'] or 'No summary available.'}")
            st.markdown("---")
    else:
        st.warning("No news available at the moment. Please try again later.")

# --- Footer ---
st.markdown("---")
st.caption("Crafted with 🔍 by Sanjay Rajan • Streamlit + Plotly + Python")
