import yfinance as yf
import pandas as pd

# Download WTI Crude Oil prices (up to today)
oil = yf.download('CL=F', start='2024-03-01', interval='1d')

# Keep only relevant columns
oil = oil[['Open', 'High', 'Low', 'Close', 'Volume']]

# Save to CSV
oil.to_csv('../data/crude_oil_prices.csv')
print("Data saved to data/crude_oil_prices.csv")
