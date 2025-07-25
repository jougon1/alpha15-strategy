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


## 🛠️ Setup Instructions

1. **Install Dependencies**

   Run the following command to install required packages:

   ```bash
   pip install -r requriments.txt
Prepare credentials.txt

2. Create a file named credentials.txt in the root folder and fill in your details:


API_KEY=your_angel_api_key
CLIENT_CODE=your_client_code
PIN=your_pin
TOTP_SECRET=your_totp_secret
bot_token=your_telegram_bot_token
chat_id=your_telegram_chat_id
csv_path=absolute_path_to_futures_masterlist.csv

3. masterlist.py
Inside masterlist.py, you'll find a section where you can customize your preferred stock list (e.g., ["HDFCBANK", "RELIANCE", "INFY"]).

The script will download and create a file like futures_masterlist.csv.

4.Populate symbols.txt

Open the generated futures_masterlist.csv.

Copy the exact symbol names (e.g., RELIANCE31JUL25FUT) of the futures you want to track.

Paste each symbol on a new line in symbols.txt.

Example:

RELIANCE31JUL25FUT
INFY31JUL25FUT
HDFCBANK31JUL25FUT

5.Run the Bot

Once setup is complete and market is open:


python main.py


## 📢 Disclaimer

This tool is built for educational and experimental purposes only.  
It is **not financial advice**. Use at your own risk.

---

© 2025 – Alpha15
