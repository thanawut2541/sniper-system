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

- **V1.0.0** (2026-07-12 21:05:59) — Initial release. Core modules: Signal Engine,
  Volume Profile, Risk Manager, Compounding Calculator, README Manager.

---

## 🕐 Last Run

> 2026-07-12 21:54:17
