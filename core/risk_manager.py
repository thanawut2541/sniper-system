"""
RiskManager — Trade-risk management for Private Sniper System V1.0.

Handles SL/TP/BE calculations, daily loss tracking, and the 2-loss
daily lock-out rule.
"""

from typing import Dict, List


class RiskManager:
    """Enforces risk rules and manages trade-level calculations."""

    # ------------------------------------------------------------------
    # Constants
    # ------------------------------------------------------------------
    SL_PIPS: int = 50
    TP_PIPS: int = 100
    BE_TRIGGER_PIPS: int = 50
    MAX_DAILY_LOSSES: int = 2
    PIP_VALUE: float = 0.0001  # Standard forex pip for 4-decimal pairs

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        """Initialise the RiskManager with a clean daily slate."""
        self.daily_losses: int = 0
        self.is_locked: bool = False
        self.active_trades: List[Dict[str, object]] = []
        self.trade_history: List[Dict[str, object]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate_entry_levels(
        self, entry_price: float, direction: str
    ) -> Dict[str, float]:
        """
        Compute SL and TP prices for a new trade.

        Args:
            entry_price: Planned entry price.
            direction: ``'BUY'`` or ``'SELL'``.

        Returns:
            Dict with ``entry``, ``sl``, ``tp``, ``direction``.

        Raises:
            ValueError: If *direction* is not ``'BUY'`` or ``'SELL'``.
        """
        direction = direction.upper()
        if direction not in ("BUY", "SELL"):
            raise ValueError(f"direction must be 'BUY' or 'SELL', got '{direction}'")

        sl_distance: float = self.SL_PIPS * self.PIP_VALUE
        tp_distance: float = self.TP_PIPS * self.PIP_VALUE

        if direction == "BUY":
            sl: float = round(entry_price - sl_distance, 5)
            tp: float = round(entry_price + tp_distance, 5)
        else:
            sl = round(entry_price + sl_distance, 5)
            tp = round(entry_price - tp_distance, 5)

        return {
            "entry": round(entry_price, 5),
            "sl": sl,
            "tp": tp,
            "direction": direction,
        }

    def check_break_even(
        self, entry_price: float, current_price: float, direction: str
    ) -> bool:
        """
        Determine whether the trade has reached the break-even trigger
        (+50 pips of profit).

        Args:
            entry_price: The original entry price.
            current_price: The current market price.
            direction: ``'BUY'`` or ``'SELL'``.

        Returns:
            ``True`` if profit ≥ BE_TRIGGER_PIPS.
        """
        direction = direction.upper()
        be_distance: float = self.BE_TRIGGER_PIPS * self.PIP_VALUE

        if direction == "BUY":
            profit: float = current_price - entry_price
        else:
            profit = entry_price - current_price

        return profit >= be_distance

    def record_loss(self) -> bool:
        """
        Record a losing trade for the current day.

        Increments ``daily_losses``.  If the count reaches
        ``MAX_DAILY_LOSSES`` (2), the manager enters the **locked** state,
        blocking further trades for the rest of the day.

        Returns:
            ``True`` if the manager is now locked (i.e. daily limit hit).
        """
        self.daily_losses += 1
        self.trade_history.append({"result": "LOSS"})

        if self.daily_losses >= self.MAX_DAILY_LOSSES:
            self.is_locked = True

        return self.is_locked

    def record_win(self) -> None:
        """Record a winning trade to the trade history."""
        self.trade_history.append({"result": "WIN"})

    def reset_daily(self) -> None:
        """
        Reset the daily loss counter and unlock the manager.

        Call this at the start of each new trading day.
        """
        self.daily_losses = 0
        self.is_locked = False

    def get_status(self) -> Dict[str, object]:
        """
        Return a snapshot of the current risk-management state.

        Returns:
            Dict with ``daily_losses``, ``is_locked``, ``total_trades``,
            ``wins``, and ``losses``.
        """
        wins: int = sum(1 for t in self.trade_history if t.get("result") == "WIN")
        losses: int = sum(1 for t in self.trade_history if t.get("result") == "LOSS")

        return {
            "daily_losses": self.daily_losses,
            "is_locked": self.is_locked,
            "total_trades": len(self.trade_history),
            "wins": wins,
            "losses": losses,
        }
