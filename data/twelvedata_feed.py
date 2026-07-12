import requests
import pandas as pd
from datetime import datetime
import time

FETCH_INTERVAL_SEC = 60  # Only call API at most once per minute


class TwelveDataFeed:
    """Live market data feed using Twelve Data API with rate-limit caching."""

    BASE_URL = "https://api.twelvedata.com"

    def __init__(self, symbol="EUR/USD", api_key="7d1d88bd94fa4ba0bdabf73846f779bb"):
        self.symbol = symbol
        self.api_key = api_key
        self.candles = []
        self._last_fetch_time = 0  # unix timestamp of last successful fetch

    def fetch_historical_data(self, outputsize=120) -> list:
        """Fetch recent 1H candles. Returns cached data if called within 60s."""
        now = time.time()
        if self.candles and (now - self._last_fetch_time) < FETCH_INTERVAL_SEC:
            return self.candles  # Return cached data — don't burn API credits

        try:
            url = f"{self.BASE_URL}/time_series"
            params = {
                "symbol": self.symbol,
                "interval": "1h",
                "outputsize": outputsize,
                "apikey": self.api_key,
                "format": "JSON",
                "order": "ASC"
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get("status") == "error":
                print(f"Twelve Data API error: {data.get('message')}")
                return self.candles

            values = data.get("values", [])
            if not values:
                print("Twelve Data: No values returned.")
                return self.candles

            self.candles = []
            for v in values:
                dt = datetime.strptime(v["datetime"], "%Y-%m-%d %H:%M:%S")
                volume = int(v.get("volume", 0)) if v.get("volume") else 0
                if volume == 0:
                    volume = int(abs(float(v["high"]) - float(v["low"])) * 100000)

                candle = {
                    "time": dt,
                    "open": float(v["open"]),
                    "high": float(v["high"]),
                    "low": float(v["low"]),
                    "close": float(v["close"]),
                    "volume": volume,
                }
                self.candles.append(candle)

            self._last_fetch_time = time.time()  # Record fetch time
            print(f"Twelve Data: Loaded {len(self.candles)} candles for {self.symbol}")
            return self.candles

        except Exception as e:
            print(f"Twelve Data fetch error: {e}")
            return self.candles

    def get_recent_candles(self, count=24) -> list:
        """Return the most recent 'count' candles."""
        if not self.candles:
            self.fetch_historical_data()
        return self.candles[-count:] if len(self.candles) >= count else self.candles

    def get_all_candles(self) -> list:
        return self.candles
