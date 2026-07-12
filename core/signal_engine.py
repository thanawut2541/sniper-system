"""
SignalEngine — Core signal-generation logic for Private Sniper System V1.0.

Evaluates H1 candle data against the daily range + 30-pip buffer zone and
produces actionable trade signals (BUY / SELL / TESTING / STANDBY).
"""

import datetime
from typing import Dict, List, Optional


class SignalEngine:
    """Generates trade signals based on price-action breakout rules."""

    # ------------------------------------------------------------------
    # Constants
    # ------------------------------------------------------------------
    BUFFER_PIPS: int = 30
    TRADE_START_HOUR: int = 14  # UTC+7
    TRADE_END_HOUR: int = 23   # UTC+7
    PIP_VALUE: float = 0.0001  # Standard forex pip (4-decimal pairs)

    # Signal states
    STANDBY: str = "STANDBY"
    TESTING_ZONE: str = "TESTING_ZONE"
    EXECUTE_BUY: str = "EXECUTE_BUY"
    EXECUTE_SELL: str = "EXECUTE_SELL"

    # Buffer-zone labels (internal)
    _ABOVE_BUFFER: str = "ABOVE_BUFFER"
    _BELOW_BUFFER: str = "BELOW_BUFFER"
    _IN_BUFFER_HIGH: str = "IN_BUFFER_HIGH"
    _IN_BUFFER_LOW: str = "IN_BUFFER_LOW"
    _IN_RANGE: str = "IN_RANGE"

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        """Initialise the engine in STANDBY with no daily range."""
        self.current_state: str = self.STANDBY
        self.daily_high: Optional[float] = None
        self.daily_low: Optional[float] = None
        self.signal_details: Dict[str, object] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_daily_range(self, candles: List[Dict[str, object]]) -> None:
        """
        Compute the daily high and low from a list of candle dicts.

        Each candle is expected to have at least the keys:
        ``'open'``, ``'high'``, ``'low'``, ``'close'``, ``'volume'``, ``'time'``.

        Args:
            candles: List of candle dictionaries.
        """
        if not candles:
            return

        highs: List[float] = [float(c["high"]) for c in candles]
        lows: List[float] = [float(c["low"]) for c in candles]

        self.daily_high = max(highs)
        self.daily_low = min(lows)

    def is_trading_hours(self) -> bool:
        """
        Check whether the current moment falls inside the trading window
        (14:00 – 23:00 UTC+7).

        Returns:
            ``True`` if within the allowed trading window.
        """
        utc_now: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
        utc7: datetime.timezone = datetime.timezone(datetime.timedelta(hours=7))
        now_utc7: datetime.datetime = utc_now.astimezone(utc7)
        return self.TRADE_START_HOUR <= now_utc7.hour < self.TRADE_END_HOUR

    def check_buffer_zone(self, close_price: float) -> str:
        """
        Classify *close_price* relative to the daily range + buffer.

        Returns one of:
        - ``'ABOVE_BUFFER'``  — price closed above daily high + 30-pip buffer
        - ``'BELOW_BUFFER'``  — price closed below daily low  − 30-pip buffer
        - ``'IN_BUFFER_HIGH'``— price above daily high but still within buffer
        - ``'IN_BUFFER_LOW'`` — price below daily low  but still within buffer
        - ``'IN_RANGE'``      — price inside the daily range

        Args:
            close_price: The H1 candle close price.
        """
        if self.daily_high is None or self.daily_low is None:
            return self._IN_RANGE

        buffer: float = self.BUFFER_PIPS * self.PIP_VALUE
        upper_limit: float = self.daily_high + buffer
        lower_limit: float = self.daily_low - buffer

        if close_price > upper_limit:
            return self._ABOVE_BUFFER
        if close_price < lower_limit:
            return self._BELOW_BUFFER
        if close_price > self.daily_high:
            return self._IN_BUFFER_HIGH
        if close_price < self.daily_low:
            return self._IN_BUFFER_LOW
        return self._IN_RANGE

    def evaluate_signal(
        self,
        candles: List[Dict[str, object]],
        current_candle: Dict[str, object],
        volume_confirmed: bool,
    ) -> Dict[str, object]:
        """
        Main evaluation pipeline — returns a complete signal dict.

        Steps:
        1. Check trading hours  → STANDBY if outside window.
        2. Update daily high/low from *candles*.
        3. Classify the close of *current_candle* against the buffer zone.
        4. Combine zone classification with *volume_confirmed* to decide
           the final signal state.

        Args:
            candles: Historical H1 candles for daily-range calculation.
            current_candle: The latest (current) H1 candle dict.
            volume_confirmed: Whether the Volume Profile confirms expansion.

        Returns:
            A dict with keys: ``state``, ``entry``, ``daily_high``,
            ``daily_low``, ``buffer_high``, ``buffer_low``, ``message``.
        """
        # 1. Trading-hours gate
        if not self.is_trading_hours():
            return self._build_result(
                state=self.STANDBY,
                entry=None,
                message="Outside trading hours (14:00–23:00 UTC+7). Standing by.",
            )

        # 2. Daily range
        self.update_daily_range(candles)

        close_price: float = float(current_candle["close"])
        zone: str = self.check_buffer_zone(close_price)

        # 3-8. Zone → state mapping
        if zone == self._IN_RANGE:
            state = self.STANDBY
            entry = None
            message = "Price is inside the daily range. No signal."

        elif zone in (self._IN_BUFFER_HIGH, self._IN_BUFFER_LOW):
            state = self.TESTING_ZONE
            entry = None
            side = "HIGH" if zone == self._IN_BUFFER_HIGH else "LOW"
            message = f"Price entered the {side} buffer zone. Watching for breakout."

        elif zone == self._ABOVE_BUFFER:
            if volume_confirmed:
                state = self.EXECUTE_BUY
                entry = close_price
                message = "Breakout ABOVE buffer confirmed with volume expansion → BUY."
            else:
                state = self.TESTING_ZONE
                entry = None
                message = (
                    "Price above buffer but volume NOT confirmed. "
                    "Waiting for volume expansion."
                )

        elif zone == self._BELOW_BUFFER:
            if volume_confirmed:
                state = self.EXECUTE_SELL
                entry = close_price
                message = "Breakout BELOW buffer confirmed with volume expansion → SELL."
            else:
                state = self.TESTING_ZONE
                entry = None
                message = (
                    "Price below buffer but volume NOT confirmed. "
                    "Waiting for volume expansion."
                )
        else:
            # Defensive fallback
            state = self.STANDBY
            entry = None
            message = "Unrecognised zone. Standing by."

        self.current_state = state
        return self._build_result(state=state, entry=entry, message=message)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_result(
        self,
        state: str,
        entry: Optional[float],
        message: str,
    ) -> Dict[str, object]:
        """Assemble a uniform signal-result dictionary."""
        buffer: float = self.BUFFER_PIPS * self.PIP_VALUE

        result: Dict[str, object] = {
            "state": state,
            "entry": entry,
            "daily_high": self.daily_high,
            "daily_low": self.daily_low,
            "buffer_high": (
                round(self.daily_high + buffer, 5) if self.daily_high is not None else None
            ),
            "buffer_low": (
                round(self.daily_low - buffer, 5) if self.daily_low is not None else None
            ),
            "message": message,
        }

        self.signal_details = result
        return result
