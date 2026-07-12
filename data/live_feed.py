import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

class LiveMarketFeed:
    def __init__(self, symbol="EURUSD=X"):
        self.symbol = symbol
        self.candles = []
        
    def fetch_historical_data(self, period="5d") -> list:
        """Fetch recent 1H candles from yfinance"""
        try:
            ticker = yf.Ticker(self.symbol)
            # Fetch 1 hour interval data
            df = ticker.history(period=period, interval="1h")
            
            self.candles = []
            for index, row in df.iterrows():
                # yfinance returns timezone-aware datetimes. 
                # Convert to local time (or keep as naive UTC/local)
                dt = index.to_pydatetime()
                
                # Volume might be 0 for Forex in yfinance. 
                # If 0, we can simulate a tick volume based on High-Low range to make the profile work.
                vol = row['Volume']
                if vol == 0 or pd.isna(vol):
                    vol = int(abs(row['High'] - row['Low']) * 100000)

                candle = {
                    'time': dt,
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': vol
                }
                self.candles.append(candle)
            
            return self.candles
        except Exception as e:
            print(f"Error fetching live data: {e}")
            return self.candles

    def get_recent_candles(self, count=24) -> list:
        """Return the most recent 'count' candles."""
        if not self.candles:
            self.fetch_historical_data()
        return self.candles[-count:] if len(self.candles) >= count else self.candles

    def get_all_candles(self) -> list:
        return self.candles
