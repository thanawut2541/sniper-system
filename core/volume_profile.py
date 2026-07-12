"""
VolumeProfile — Volume-profile analysis for Private Sniper System V1.0.

Builds a histogram of tick-volume distributed across price bins, identifies
the Point of Control (POC), and checks for volume expansion.
"""

import numpy as np
from typing import Dict, List, Tuple


class VolumeProfile:
    """Volume-profile calculator with POC detection and expansion check."""

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __init__(
        self,
        num_bins: int = 50,
        expansion_multiplier: float = 1.5,
        lookback: int = 20,
    ) -> None:
        """
        Initialise the VolumeProfile analyser.

        Args:
            num_bins: Number of horizontal price bins for the profile.
            expansion_multiplier: Multiplier over the average volume that
                qualifies as "volume expansion".
            lookback: Number of recent candles used to compute the average
                volume for expansion comparison.
        """
        self.num_bins: int = num_bins
        self.expansion_multiplier: float = expansion_multiplier
        self.lookback: int = lookback

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate_profile(self, candles: List[Dict[str, object]]) -> Dict[str, object]:
        """
        Build the volume profile from a list of candle dicts.

        Each candle must contain at least:
        ``'open'``, ``'high'``, ``'low'``, ``'close'``, ``'volume'``.

        The overall price range (min low → max high) is divided into
        *num_bins* equal-width bins.  Each candle's tick volume is
        **uniformly** distributed across every bin that overlaps with that
        candle's high–low range.

        Returns:
            A dict with keys:
            - ``bins``        — list of ``(price_low, price_high)`` tuples
            - ``volumes``     — list of float volumes per bin
            - ``poc_price``   — centre price of the highest-volume bin
            - ``poc_volume``  — volume at POC
            - ``total_volume``— sum of all distributed volume
        """
        if not candles:
            return {
                "bins": [],
                "volumes": [],
                "poc_price": 0.0,
                "poc_volume": 0.0,
                "total_volume": 0.0,
            }

        # Gather price extremes
        highs: np.ndarray = np.array([float(c["high"]) for c in candles])
        lows: np.ndarray = np.array([float(c["low"]) for c in candles])
        volumes: np.ndarray = np.array([float(c["volume"]) for c in candles])

        overall_low: float = float(lows.min())
        overall_high: float = float(highs.max())

        # Guard against zero-range edge case
        if overall_high == overall_low:
            overall_high += 0.0001

        bin_edges: np.ndarray = np.linspace(overall_low, overall_high, self.num_bins + 1)
        bin_volumes: np.ndarray = np.zeros(self.num_bins, dtype=np.float64)

        # Distribute volume into overlapping bins
        for candle_low, candle_high, vol in zip(lows, highs, volumes):
            if candle_high == candle_low:
                candle_high = candle_low + 0.0001

            # Find bins that overlap with [candle_low, candle_high]
            overlap_start: np.ndarray = np.maximum(bin_edges[:-1], candle_low)
            overlap_end: np.ndarray = np.minimum(bin_edges[1:], candle_high)
            overlap: np.ndarray = np.maximum(overlap_end - overlap_start, 0.0)

            total_overlap: float = float(overlap.sum())
            if total_overlap > 0:
                bin_volumes += overlap / total_overlap * vol

        # Build output
        bins: List[Tuple[float, float]] = [
            (float(bin_edges[i]), float(bin_edges[i + 1]))
            for i in range(self.num_bins)
        ]

        poc_index: int = int(np.argmax(bin_volumes))
        poc_price: float = float((bin_edges[poc_index] + bin_edges[poc_index + 1]) / 2.0)
        poc_volume: float = float(bin_volumes[poc_index])
        total_volume: float = float(bin_volumes.sum())

        return {
            "bins": bins,
            "volumes": [float(v) for v in bin_volumes],
            "poc_price": round(poc_price, 5),
            "poc_volume": round(poc_volume, 2),
            "total_volume": round(total_volume, 2),
        }

    def check_volume_expansion(
        self, candles: List[Dict[str, object]], current_volume: float
    ) -> bool:
        """
        Check whether *current_volume* qualifies as volume expansion.

        Expansion is defined as:
        ``current_volume > avg(last *lookback* candles' volume) × expansion_multiplier``

        Args:
            candles: Historical candle list (most-recent last).
            current_volume: Tick volume of the current candle.

        Returns:
            ``True`` if expansion criteria are met.
        """
        if not candles:
            return False

        recent: List[Dict[str, object]] = candles[-self.lookback :]
        avg_volume: float = float(
            np.mean([float(c["volume"]) for c in recent])
        )

        if avg_volume == 0:
            return current_volume > 0

        return current_volume > avg_volume * self.expansion_multiplier

    def get_profile_for_display(
        self, candles: List[Dict[str, object]]
    ) -> Dict[str, object]:
        """
        Return profile data formatted for chart rendering.

        Returns:
            A dict with:
            - ``bin_centers`` — list of float centre prices
            - ``bin_volumes`` — list of float volumes normalised to [0, 1]
            - ``poc_price``   — float
            - ``poc_index``   — int index of the POC bin
        """
        profile: Dict[str, object] = self.calculate_profile(candles)

        if not profile["bins"]:
            return {
                "bin_centers": [],
                "bin_volumes": [],
                "poc_price": 0.0,
                "poc_index": 0,
            }

        bin_centers: List[float] = [
            round((lo + hi) / 2.0, 5) for lo, hi in profile["bins"]
        ]

        raw_volumes: np.ndarray = np.array(profile["volumes"], dtype=np.float64)
        max_vol: float = float(raw_volumes.max()) if raw_volumes.max() > 0 else 1.0
        normalised: List[float] = [round(float(v / max_vol), 4) for v in raw_volumes]

        poc_index: int = int(np.argmax(raw_volumes))

        return {
            "bin_centers": bin_centers,
            "bin_volumes": normalised,
            "poc_price": profile["poc_price"],
            "poc_index": poc_index,
        }
