import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

class MT5LiveFeed:
    def __init__(self, symbol="EURUSD"):
        self.symbol = symbol
        self.candles = []
        self.initialized = False
        self.broker_name = "Unknown"
        self._initialize_mt5()

    def _initialize_mt5(self):
        # Establish connection to the MetaTrader 5 terminal
        if not mt5.initialize():
            print("initialize() failed, error code =", mt5.last_error())
            self.initialized = False
        else:
            self.initialized = True
            terminal_info = mt5.terminal_info()
            if terminal_info is not None:
                self.broker_name = terminal_info.company
            print(f"Connected to MT5 - Broker: {self.broker_name}")

    def fetch_historical_data(self, count=120) -> list:
        """Fetch recent 1H candles from MT5"""
        if not self.initialized:
            # Try to re-initialize
            self._initialize_mt5()
            if not self.initialized:
                return self.candles

        # Fetch rates from MT5 (TIMEFRAME_H1 = 16385 in MT5 enum, but mt5.TIMEFRAME_H1 is 16385)
        # We request 'count' candles from the current position (0) backwards
        rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_H1, 0, count)
        
        if rates is None or len(rates) == 0:
            print(f"Failed to fetch rates for {self.symbol}, error code: {mt5.last_error()}")
            return self.candles

        self.candles = []
        for rate in rates:
            # rate is a tuple/structured numpy array: (time, open, high, low, close, tick_volume, spread, real_volume)
            # time is in unix timestamp
            dt = datetime.fromtimestamp(rate['time'])
            candle = {
                'time': dt,
                'open': float(rate['open']),
                'high': float(rate['high']),
                'low': float(rate['low']),
                'close': float(rate['close']),
                'volume': int(rate['tick_volume'])
            }
            self.candles.append(candle)
            
        return self.candles

    def get_recent_candles(self, count=24) -> list:
        """Return the most recent 'count' candles."""
        if not self.candles:
            self.fetch_historical_data()
        return self.candles[-count:] if len(self.candles) >= count else self.candles

    def get_all_candles(self) -> list:
        return self.candles

    def shutdown(self):
        if self.initialized:
            mt5.shutdown()
