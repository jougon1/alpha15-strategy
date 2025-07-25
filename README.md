# 🔺 Alpha15 Strategy

**Alpha15** is a real-time options signal engine for the Indian stock market based on futures data and intraday price action.

This system monitors the **second 15-minute candle** of the trading day to detect directional breakout signals on selected futures contracts. When a valid signal is detected, the bot sends **ATM option trade alerts** to a Telegram channel (Buy → ATM CE, Sell → ATM PE).

---

## ⚙️ Features

- ✅ Works with **Angel One SmartAPI**
- ✅ Analyzes real-time **15-minute candles**
- ✅ Applies **ATR** and **POC (Point of Control)** logic
- ✅ Implements **TPO (Time-Price-Opportunity)** market profiling concepts
- ✅ Sends actionable alerts via **Telegram**
- ✅ External config via `credentials.txt` and `symbols.txt` (not exposed)

---

## 🧠 Strategy Logic

This bot internally uses:
- Volume-based **POC** identification
- Volatility filters using **ATR (Average True Range)**
- **TPO profiling** for price activity clustering
- Realtime LTP comparisons to high/low ranges for **breakout confirmation**

These concepts are inspired by institutional market profiling and price action frameworks.

📩 Want to know the inner workings or research the logic?  
**Email me** at: `tobiramalovesmadara@gmail.com` for further details and discussion.

## 📢 Disclaimer

This tool is built for educational and experimental purposes only.  
It is **not financial advice**. Use at your own risk.

---

© 2025 – Alpha15
