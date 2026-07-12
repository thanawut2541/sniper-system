"""
ReadmeManager — Manages the README.md file for Private Sniper System V1.0.

Handles reading, creating, and updating the project's README.md with
version info, changelog, system blueprint, and last-run timestamps.
"""

import os
import re
import datetime
from typing import Dict, Optional, List


class ReadmeManager:
    """Manages the README.md lifecycle for the Private Sniper System."""

    def __init__(self, readme_path: str) -> None:
        """
        Initialize the ReadmeManager.

        Args:
            readme_path: Absolute or relative path to the README.md file.
        """
        self.readme_path: str = readme_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def read_readme(self) -> Dict[str, object]:
        """
        Read and parse the README.md file.

        Extracts:
        - **version**: The first semantic-version string matching ``V\\d+\\.\\d+\\.\\d+``.
        - **changelog**: A list of changelog entry strings.
        - **last_run**: The datetime string from the *Last Run* line, or ``None``.
        - **raw_content**: The full text of the file.

        Returns:
            A dict with keys ``'version'``, ``'changelog'``, ``'last_run'``,
            and ``'raw_content'``.  If the file does not exist an empty dict
            with ``None`` / empty values is returned.
        """
        if not os.path.exists(self.readme_path):
            return {
                "version": None,
                "changelog": [],
                "last_run": None,
                "raw_content": "",
            }

        with open(self.readme_path, "r", encoding="utf-8") as fh:
            raw_content: str = fh.read()

        # --- Version ---------------------------------------------------
        version_match = re.search(r"V\d+\.\d+\.\d+", raw_content)
        version: Optional[str] = version_match.group(0) if version_match else None

        # --- Changelog --------------------------------------------------
        changelog: List[str] = self._extract_changelog(raw_content)

        # --- Last Run ---------------------------------------------------
        last_run: Optional[str] = self._extract_last_run(raw_content)

        return {
            "version": version,
            "changelog": changelog,
            "last_run": last_run,
            "raw_content": raw_content,
        }

    def create_default_readme(self) -> None:
        """
        Create a comprehensive default README.md.

        The generated file contains the full system blueprint, risk rules,
        cent-account compounding plan, an initial changelog entry, and a
        *Last Run* timestamp.
        """
        now_str: str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content: str = f"""\
# 🎯 Private Sniper System V1.0

> **Current Version:** V1.0.0

---

## 📋 System Blueprint

### ⏰ Time Filter
- **Trading Window:** 14:00 – 23:00 (UTC+7)
- Only evaluate signals within the active session.

### 📈 Price Action — Breakout + Buffer Zone
- **Buffer Size:** 30 pips above Daily High / below Daily Low.
- A valid breakout is confirmed only when the H1 candle **closes** beyond
  the buffer zone.

### 📊 Volume Profile — POC Validation
- Calculate the **Point of Control (POC)** from the recent volume profile.
- A breakout signal is confirmed when accompanied by **volume expansion**
  (current volume > average × 1.5).

### 💰 Cent Account Risk Management
- **Risk-to-Reward Ratio:** 1 : 2
- **Stop-Loss:** 50 pips
- **Take-Profit:** 100 pips
- **Break-Even Trigger:** Move SL to entry when trade reaches +50 pips.
- **Daily Loss Lock:** Stop trading after **2 consecutive losses** in one day.

---

## 💵 Cent Account Compounding Plan

| Item | Value |
|------|-------|
| Starting Capital | 10 USD (1 000 Cents) |
| Monthly Deposit | +15 USD (1 500 Cents) |
| Risk per Trade | 2 % of account balance |
| Lot Sizing | Dynamic — based on balance & SL |

---

## 📝 Changelog

- **V1.0.0** ({now_str}) — Initial release. Core modules: Signal Engine,
  Volume Profile, Risk Manager, Compounding Calculator, README Manager.

---

## 🕐 Last Run

> {now_str}
"""

        # Ensure parent directory exists
        directory: str = os.path.dirname(self.readme_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        with open(self.readme_path, "w", encoding="utf-8") as fh:
            fh.write(content)

    def update_last_run(self) -> None:
        """
        Update the *Last Run* timestamp inside README.md to the current
        date-time.  If the file does not exist, it is created first via
        :meth:`create_default_readme`.
        """
        if not os.path.exists(self.readme_path):
            self.create_default_readme()
            return

        with open(self.readme_path, "r", encoding="utf-8") as fh:
            content: str = fh.read()

        now_str: str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Try to replace the existing timestamp line after "Last Run"
        updated_content, count = re.subn(
            r"(>\s*)(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
            rf"\g<1>{now_str}",
            content,
        )

        if count == 0:
            # Fallback: append a Last Run section if none was found
            updated_content = content.rstrip() + f"\n\n## 🕐 Last Run\n\n> {now_str}\n"

        with open(self.readme_path, "w", encoding="utf-8") as fh:
            fh.write(updated_content)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_changelog(text: str) -> List[str]:
        """Return a list of changelog bullet-point entries from *text*."""
        entries: List[str] = []
        in_changelog = False

        for line in text.splitlines():
            stripped = line.strip()

            # Detect the changelog heading
            if re.match(r"^#{1,3}\s+.*[Cc]hangelog", stripped):
                in_changelog = True
                continue

            # Stop when we hit the next heading after the changelog section
            if in_changelog and re.match(r"^#{1,3}\s+", stripped):
                break

            if in_changelog and stripped.startswith("-"):
                entries.append(stripped.lstrip("- ").strip())

        return entries

    @staticmethod
    def _extract_last_run(text: str) -> Optional[str]:
        """Return the *Last Run* datetime string, or ``None``."""
        match = re.search(
            r"Last\s+Run.*?\n>\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        return match.group(1) if match else None
