"""
Private Sniper System V1.0 - Market Simulator
===============================================
Generates realistic OHLCV candlestick data for backtesting and live simulation.
Simulates EUR/USD H1 candles with random walk, trend shifts, breakout patterns,
and volume expansion events.
"""

import numpy as np
from datetime import datetime, timedelta
import random


class MarketSimulator:
    """
    Generates realistic OHLCV candlestick data for simulated trading.

    Simulates EUR/USD price action on H1 timeframe with:
    - Random walk price movement with trend bias
    - Periodic trend shifts every 12-18 candles
    - Forced breakout candles with larger bodies and volume spikes
    - Realistic volume patterns with occasional expansion

    Attributes:
        base_price (float): Starting price level (default EUR/USD ~1.0850).
        volatility (float): Base volatility per candle.
        trend_strength (float): Directional bias magnitude.
        candles (list): All generated candle dicts.
        current_price (float): Latest close price.
        breakout_counter (int): Candles since last breakout.
        force_breakout (bool): Flag to trigger breakout on next candle.
        trend_direction (int): Current trend direction (1=up, -1=down).
    """

    def __init__(self, base_price=1.0850, volatility=0.0015, trend_strength=0.0002):
        """
        Initialize the MarketSimulator.

        Args:
            base_price (float): Starting price level (simulating EUR/USD).
            volatility (float): Base volatility per candle.
            trend_strength (float): Directional bias magnitude per candle.
        """
        self.base_price = base_price
        self.volatility = volatility
        self.trend_strength = trend_strength
        self.candles = []
        self.current_price = base_price
        self.breakout_counter = 0
        self.force_breakout = False
        self.trend_direction = 1  # 1 = up, -1 = down

    def generate_initial_candles(self, count=48):
        """
        Generate historical H1 candles going back in time from now.

        Creates 'count' candles using a random walk with periodic trend shifts
        and occasional volume spikes to simulate realistic market conditions.

        Args:
            count (int): Number of historical candles to generate (default 48).

        Returns:
            list: List of candle dicts, each containing:
                - time (datetime): Candle timestamp.
                - open (float): Opening price.
                - high (float): Highest price.
                - low (float): Lowest price.
                - close (float): Closing price.
                - volume (int): Tick volume.
        """
        self.candles = []
        self.current_price = self.base_price

        # Calculate start time: 'count' hours back from now
        start_time = datetime.now() - timedelta(hours=count)

        # Determine when to shift trend direction
        next_trend_shift = random.randint(12, 18)
        candles_since_shift = 0

        for i in range(count):
            candle_time = start_time + timedelta(hours=i)

            # --- Trend shift logic ---
            candles_since_shift += 1
            if candles_since_shift >= next_trend_shift:
                self.trend_direction *= -1
                next_trend_shift = random.randint(12, 18)
                candles_since_shift = 0

            # --- Price movement (random walk with trend bias) ---
            open_price = self.current_price
            trend_bias = self.trend_strength * self.trend_direction
            random_move = np.random.normal(trend_bias, self.volatility)
            close_price = open_price + random_move

            # High and low with random wicks
            wick_upper = abs(np.random.normal(0, self.volatility * 0.5))
            wick_lower = abs(np.random.normal(0, self.volatility * 0.5))
            high_price = max(open_price, close_price) + wick_upper
            low_price = min(open_price, close_price) - wick_lower

            # --- Volume ---
            base_volume = random.randint(500, 1500)
            # Occasional volume spikes (roughly 15% chance)
            if random.random() < 0.15:
                volume_multiplier = random.uniform(2.0, 3.0)
                volume = int(base_volume * volume_multiplier)
            else:
                volume = base_volume

            # --- Build candle ---
            candle = {
                'time': candle_time,
                'open': round(open_price, 5),
                'high': round(high_price, 5),
                'low': round(low_price, 5),
                'close': round(close_price, 5),
                'volume': volume,
            }

            self.candles.append(candle)
            self.current_price = close_price

        return self.candles

    def generate_next_candle(self):
        """
        Generate the next H1 candle in the sequence.

        Increments the breakout counter and may trigger a forced breakout
        candle (larger body, higher volume) when the counter threshold is
        reached. After a breakout, the trend direction flips.

        Returns:
            dict: The newly generated candle dict with keys:
                - time (datetime): Candle timestamp (last candle + 1 hour).
                - open (float): Opening price.
                - high (float): Highest price.
                - low (float): Lowest price.
                - close (float): Closing price.
                - volume (int): Tick volume.
        """
        # --- Breakout scheduling ---
        self.breakout_counter += 1
        if self.breakout_counter > random.randint(10, 15):
            self.force_breakout = True
            self.breakout_counter = 0

        # --- Time ---
        if self.candles:
            candle_time = self.candles[-1]['time'] + timedelta(hours=1)
        else:
            candle_time = datetime.now()

        open_price = self.current_price

        if self.force_breakout:
            # === Breakout candle ===
            # Larger body: 2x-3x normal volatility in trend direction
            body_multiplier = random.uniform(2.0, 3.0)
            move = self.volatility * body_multiplier * self.trend_direction
            close_price = open_price + move

            # Wicks (smaller relative to body on breakout candles)
            wick_upper = abs(np.random.normal(0, self.volatility * 0.3))
            wick_lower = abs(np.random.normal(0, self.volatility * 0.3))
            high_price = max(open_price, close_price) + wick_upper
            low_price = min(open_price, close_price) - wick_lower

            # High volume: 2x-4x normal
            base_volume = random.randint(500, 1500)
            volume = int(base_volume * random.uniform(2.0, 4.0))

            # Flip trend and reset breakout flag
            self.trend_direction *= -1
            self.force_breakout = False
        else:
            # === Normal candle ===
            trend_bias = self.trend_strength * self.trend_direction
            random_move = np.random.normal(trend_bias, self.volatility)
            close_price = open_price + random_move

            # Normal wicks
            wick_upper = abs(np.random.normal(0, self.volatility * 0.5))
            wick_lower = abs(np.random.normal(0, self.volatility * 0.5))
            high_price = max(open_price, close_price) + wick_upper
            low_price = min(open_price, close_price) - wick_lower

            # Normal volume
            base_volume = random.randint(500, 1500)
            if random.random() < 0.15:
                volume = int(base_volume * random.uniform(2.0, 3.0))
            else:
                volume = base_volume

        # --- Build candle ---
        candle = {
            'time': candle_time,
            'open': round(open_price, 5),
            'high': round(high_price, 5),
            'low': round(low_price, 5),
            'close': round(close_price, 5),
            'volume': volume,
        }

        self.candles.append(candle)
        self.current_price = close_price

        return candle

    def get_daily_candles(self):
        """
        Return only candles from the current simulated day.

        Filters all candles to return only those whose date matches today's
        date in the simulation.

        Returns:
            list: Candle dicts from the current day only.
        """
        today = datetime.now().date()
        return [c for c in self.candles if c['time'].date() == today]

    def get_all_candles(self):
        """
        Return all generated candles.

        Returns:
            list: Complete list of all candle dicts in chronological order.
        """
        return self.candles

    def get_recent_candles(self, count=24):
        """
        Return the most recent candles.

        Args:
            count (int): Number of recent candles to return (default 24).

        Returns:
            list: The last 'count' candle dicts, or all candles if fewer
                  than 'count' exist.
        """
        return self.candles[-count:]
