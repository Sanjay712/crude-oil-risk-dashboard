import yfinance as yf
import pandas as pd

oil = yf.download('CL=F', start='2024-03-01', interval='1d')

oil = oil[['Open', 'High', 'Low', 'Close', 'Volume']]

oil.to_csv('../data/crude_oil_prices.csv')
print("Data saved to data/crude_oil_prices.csv")
