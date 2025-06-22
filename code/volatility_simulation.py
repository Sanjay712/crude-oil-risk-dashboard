import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf


df = pd.read_csv('C:/Users/Rajan S/OneDrive/Documents/crude-oil-volatility-sim/data/crude_oil_prices.csv')

df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date', inplace=True)

df['Price'] = df['Price'].replace(',', '', regex=True).astype(float)

df['Daily Return'] = df['Price'].pct_change()
df['10D Volatility'] = df['Daily Return'].rolling(10).std()
df['VaR_95'] = df['Daily Return'].rolling(10).quantile(0.05)
portfolio_value = 1_000_000
df['P&L'] = df['Daily Return'] * portfolio_value

print("\n📉 Stress Testing - Portfolio P&L Impact")
shock_levels = [-0.2, -0.1, -0.05, 0.05, 0.1, 0.2]
for shock in shock_levels:
    pnl = portfolio_value * shock
    direction = "drop" if shock < 0 else "rise"
    print(f"➡️  If crude oil has a {abs(shock)*100:.0f}% {direction}, estimated P&L = {'-' if pnl < 0 else '+'}${abs(pnl):,.0f}")


print("\n🌍 Fetching gold and USD index data...")
gold = yf.download('GC=F', start=df.index.min(), end=df.index.max())['Close']
usd = yf.download('DX-Y.NYB', start=df.index.min(), end=df.index.max())['Close']
df['Gold'] = gold
df['USD'] = usd
df['Oil-Gold Correlation'] = df['Price'].pct_change().rolling(10).corr(df['Gold'].pct_change())
df['Oil-USD Correlation'] = df['Price'].pct_change().rolling(10).corr(df['USD'].pct_change())


print("\n📈 Backtesting Price Momentum Strategy...")

df['Price_SMA_10'] = df['Price'].rolling(window=10).mean()

df['Momentum Signal'] = np.where(df['Price'] > df['Price_SMA_10'], 1, -1)

df['Momentum Strategy Return'] = df['Momentum Signal'].shift(1) * df['Daily Return']

df['Cumulative Market Return'] = (1 + df['Daily Return']).cumprod()
df['Cumulative Momentum Return'] = (1 + df['Momentum Strategy Return']).cumprod()


print("\n🗓️ Mapping key geopolitical events...")
event_dates = {
    '2024-04-13': 'Iran attacks Israel',
    '2024-04-15': 'US/NATO response',
    '2024-04-18': 'Crude oil spike',
    '2024-05-05': 'Oil supply disruption'
}
df['Event'] = df.index.strftime('%Y-%m-%d').map(event_dates)

df.to_excel('output/oil_volatility_analysis.xlsx')
print("✅ Analysis saved to output/oil_volatility_analysis.xlsx")

plt.figure(figsize=(12, 6))
plt.plot(df.index, df['10D Volatility'], label='10-Day Volatility', color='orange')
plt.plot(df.index, df['VaR_95'], label='VaR (95%)', linestyle='--', color='red')
for date, label in event_dates.items():
    if pd.to_datetime(date) in df.index:
        plt.axvline(x=pd.to_datetime(date), color='gray', linestyle=':', linewidth=1)
        plt.text(pd.to_datetime(date), df['10D Volatility'].max() * 0.8, label, rotation=90, fontsize=8, color='gray')
plt.title("Crude Oil Volatility & VaR with Geopolitical Events")
plt.xlabel("Date")
plt.ylabel("Volatility / Risk")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('output/volatility_event_chart.png')
plt.show()

plt.figure(figsize=(12, 6))
plt.plot(df.index, df['Oil-Gold Correlation'], label='Oil-Gold Correlation', color='gold')
plt.plot(df.index, df['Oil-USD Correlation'], label='Oil-USD Correlation', color='blue')
plt.title("Crude Oil Correlation with Gold & USD Index (10-day Rolling)")
plt.xlabel("Date")
plt.ylabel("Correlation")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('output/macro_correlation_chart.png')
plt.show()

plt.figure(figsize=(12, 6))
plt.plot(df.index, df['Cumulative Market Return'], label='Market Return', color='black')
plt.plot(df.index, df['Cumulative Momentum Return'], label='Momentum Strategy', color='green')
plt.title("Cumulative Returns: Momentum Strategy vs Market")
plt.xlabel("Date")
plt.ylabel("Growth (1 = baseline)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('output/strategy_backtest_chart.png')
plt.show()
