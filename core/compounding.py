"""
CompoundingCalculator — Cent-account compounding projections for
Private Sniper System V1.0.

Models lot sizing, monthly profit projections, and balance growth for a
cent-account strategy with regular deposits.
"""

from typing import Dict, List


class CompoundingCalculator:
    """Projects account growth under a cent-account compounding plan."""

    # ------------------------------------------------------------------
    # Constants
    # ------------------------------------------------------------------
    INITIAL_BALANCE_USD: float = 10.0
    MONTHLY_DEPOSIT_USD: float = 15.0
    CENTS_PER_USD: int = 100
    RISK_PERCENT: float = 2.0
    SL_PIPS: int = 50
    PIP_VALUE_PER_MICRO_LOT: float = 0.01  # cents per pip per 0.01 lot

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __init__(
        self,
        initial_balance_usd: float = 10.0,
        monthly_deposit_usd: float = 15.0,
        risk_percent: float = 2.0,
        win_rate: float = 0.55,
        avg_rr: float = 2.0,
    ) -> None:
        """
        Initialise the compounding calculator.

        Args:
            initial_balance_usd: Starting capital in USD.
            monthly_deposit_usd: Fixed monthly deposit in USD.
            risk_percent: Percentage of balance risked per trade.
            win_rate: Assumed win rate (0.0 – 1.0).
            avg_rr: Average reward-to-risk ratio for winning trades.
        """
        self.initial_balance_usd: float = initial_balance_usd
        self.monthly_deposit_usd: float = monthly_deposit_usd
        self.risk_percent: float = risk_percent
        self.win_rate: float = win_rate
        self.avg_rr: float = avg_rr

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate_lot_size(self, balance_cents: float) -> float:
        """
        Compute the micro-lot size for a single trade.

        Formula::

            risk_amount  = balance_cents × (risk_percent / 100)
            pip_value    = SL_PIPS × PIP_VALUE_PER_MICRO_LOT  (cost per 0.01 lot)
            lot_size     = risk_amount / pip_value

        The result is expressed in micro-lots (0.01 increments) and is
        clamped to a minimum of ``0.01``.

        Args:
            balance_cents: Current account balance in **cents**.

        Returns:
            Lot size rounded to two decimal places.
        """
        risk_amount: float = balance_cents * (self.risk_percent / 100.0)
        pip_cost: float = self.SL_PIPS * self.PIP_VALUE_PER_MICRO_LOT

        if pip_cost == 0:
            return 0.01

        lot_size: float = risk_amount / pip_cost

        # Round down to nearest 0.01 and enforce minimum
        lot_size = round(lot_size, 2)
        return max(lot_size, 0.01)

    def generate_projection(self, months: int = 12) -> List[Dict[str, object]]:
        """
        Generate a month-by-month balance-growth projection.

        Assumptions per month:
        - **20 trades** are taken.
        - Winning trades yield ``risk_amount × avg_rr`` profit.
        - Losing trades cost ``risk_amount``.
        - A fixed deposit of *monthly_deposit_usd* is added at the start
          of every month (including month 1, where it supplements the
          initial balance).

        Args:
            months: Number of months to project.

        Returns:
            A list of dicts — one per month — each containing:
            ``month``, ``starting_balance_cents``, ``deposit_cents``,
            ``lot_size``, ``estimated_trades``, ``estimated_profit_cents``,
            ``ending_balance_cents``, ``ending_balance_usd``.
        """
        projections: List[Dict[str, object]] = []
        balance_cents: float = self.initial_balance_usd * self.CENTS_PER_USD
        deposit_cents: float = self.monthly_deposit_usd * self.CENTS_PER_USD
        estimated_trades: int = 20

        for month in range(1, months + 1):
            starting_balance: float = balance_cents

            # Monthly deposit
            balance_cents += deposit_cents

            # Lot size for this month (based on balance after deposit)
            lot_size: float = self.calculate_lot_size(balance_cents)

            # Estimate profit/loss
            risk_per_trade: float = balance_cents * (self.risk_percent / 100.0)
            wins: float = estimated_trades * self.win_rate
            losses: float = estimated_trades * (1.0 - self.win_rate)
            profit: float = (wins * risk_per_trade * self.avg_rr) - (
                losses * risk_per_trade
            )

            balance_cents += profit
            # Prevent balance going negative
            balance_cents = max(balance_cents, 0.0)

            projections.append(
                {
                    "month": month,
                    "starting_balance_cents": round(starting_balance, 2),
                    "deposit_cents": round(deposit_cents, 2),
                    "lot_size": lot_size,
                    "estimated_trades": estimated_trades,
                    "estimated_profit_cents": round(profit, 2),
                    "ending_balance_cents": round(balance_cents, 2),
                    "ending_balance_usd": round(balance_cents / self.CENTS_PER_USD, 2),
                }
            )

        return projections

    def get_current_lot_size(
        self, current_balance_cents: float
    ) -> Dict[str, float]:
        """
        Return lot-size and risk info for the current balance.

        Args:
            current_balance_cents: Account balance in **cents**.

        Returns:
            Dict with ``balance_cents``, ``balance_usd``, ``lot_size``,
            ``risk_per_trade_cents``, ``risk_per_trade_usd``.
        """
        lot_size: float = self.calculate_lot_size(current_balance_cents)
        risk_cents: float = current_balance_cents * (self.risk_percent / 100.0)

        return {
            "balance_cents": round(current_balance_cents, 2),
            "balance_usd": round(current_balance_cents / self.CENTS_PER_USD, 2),
            "lot_size": lot_size,
            "risk_per_trade_cents": round(risk_cents, 2),
            "risk_per_trade_usd": round(risk_cents / self.CENTS_PER_USD, 4),
        }
