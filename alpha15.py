import pandas as pd
import numpy as np
import requests
import logging
from SmartApi import SmartConnect
from datetime import datetime, timedelta
import time
import pytz
import pyotp
import sys
import re
import string

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"ANGEL_WEBSOCKET_{datetime.today().date()}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def clean_stock_name(fut_symbol):
    split_number = input("Enter the expiry day of curren month eg 31 : ")
    return re.split(split_number, fut_symbol, maxsplit=1)[0]
# Angel One API credentials

import pandas as pd

def load_credentials(file_path="credentials.txt"):
    creds = {}
    with open(file_path, "r") as file:
        for line in file:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                creds[key] = value
    return creds

creds = load_credentials()

API_KEY = creds["API_KEY"]
CLIENT_CODE = creds["CLIENT_CODE"]
PIN = creds["PIN"]
TOTP_SECRET = creds["TOTP_SECRET"]
bot_token = creds["bot_token"]
chat_id = creds["chat_id"]
csv_path = creds["csv_path"]

futures_df = pd.read_csv(csv_path)



# Futures symbols (July 2025)
def load_symbols(file_path="symbols.txt"):
    with open(file_path, "r") as file:
        return [line.strip() for line in file if line.strip()]

symbols = load_symbols()



# Initialize Angel One API client
client = SmartConnect(api_key=API_KEY)
try:
    totp = pyotp.TOTP(TOTP_SECRET)
    totp_code = totp.now()
    logger.info(f"Generated TOTP: {totp_code}")
    session = client.generateSession(CLIENT_CODE, PIN, totp_code)
    if session['status']:
        logger.info("Successfully logged into Angel One API")
    else:
        logger.error(f"Authentication failed: {session['message']}")
        exit()
except Exception as e:
    logger.error(f"Error during authentication: {e}")
    exit()

# Time zone setup
TIME_ZONE = pytz.timezone('Asia/Kolkata')

# Function to get the last trading day
def get_last_trading_day(current_date):
    """Returns the most recent trading day (Monday to Friday) before the given date."""
    last_day = current_date - timedelta(days=1)
    # Placeholder for holidays (update with actual NSE holidays for 2025)
    holidays = ['2025-01-26', '2025-08-15']  # Example: Republic Day, Independence Day
    while last_day.weekday() >= 5 or last_day.strftime('%Y-%m-%d') in holidays:
        last_day -= timedelta(days=1)
    return last_day

# Function to send Telegram message
def send_telegram_message(message):

    max_retries = 3
    for retry in range(max_retries):
        try:
            url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
            payload = {'chat_id': chat_id, 'text': message}
            response = requests.post(url, data=payload)
            return response
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            if retry < max_retries - 1:
                logger.info("Retrying...")
                time.sleep(1)
            else:
                logger.error("Max retries exceeded for Telegram message.")

# Function to calculate ATR
def calculate_atr(symbol_token, exchange="NFO"):
    ist = pytz.timezone('Asia/Kolkata')
    today = datetime.now(ist).date()
    from_date = today - timedelta(days=30)
    fromdate = f"{from_date.strftime('%Y-%m-%d')} 09:15"
    todate = f"{today.strftime('%Y-%m-%d')} 15:30"
    historic_param = {
        "exchange": exchange,
        "symboltoken": str(int(symbol_token)),
        "interval": "ONE_DAY",
        "fromdate": fromdate,
        "todate": todate
    }
    try:
        df = pd.DataFrame(client.getCandleData(historic_param)['data'],
                          columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['H-L'] = df['high'] - df['low']
        df['H-PC'] = abs(df['high'] - df['close'].shift(1))
        df['L-PC'] = abs(df['low'] - df['close'].shift(1))
        df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
        atr = [df['TR'].iloc[:14].mean()]
        for i in range(14, len(df)):
            atr.append((atr[-1] * (14 - 1) + df['TR'].iloc[i]) / 14)
        df['ATR'] = pd.Series(atr, index=df.index[13:])
        atr_value = df['ATR'].iloc[-1]
        logger.info(f"ATR for token {symbol_token}: {atr_value}")
        return atr_value
    except Exception as e:
        logger.error(f"Error fetching ATR for {symbol_token}: {e}")
        return None

# Function to calculate POC
def calculate_poc(symbol_token, tick_size, exchange="NFO"):
    ist = pytz.timezone('Asia/Kolkata')
    today = datetime.now(ist).date()
    yesterday = get_last_trading_day(today)  # Use the last trading day
    fromdate = f"{yesterday.strftime('%Y-%m-%d')} 09:15"
    todate = f"{yesterday.strftime('%Y-%m-%d')} 15:30"
    historic_param = {
        "exchange": exchange,
        "symboltoken": str(int(symbol_token)),
        "interval": "FIFTEEN_MINUTE",
        "fromdate": fromdate,
        "todate": todate
    }
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching 15-min candle data for token {symbol_token} from {fromdate} to {todate}")
            hist_data = client.getCandleData(historic_param)
            if hist_data['status'] and hist_data['data']:
                df = pd.DataFrame(hist_data['data'],
                                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                if df.empty:
                    logger.error(f"No 15-min candle data for POC calculation for token {symbol_token}")
                    return None
                tick_size = tick_size * 0.05
                min_price = np.floor(df['low'].min() / tick_size) * tick_size
                max_price = np.ceil(df['high'].max() / tick_size) * tick_size
                price_bins = np.arange(min_price, max_price + tick_size, tick_size)
                letters = list(string.ascii_uppercase) + list(string.ascii_lowercase)
                market_profile = {price: "" for price in price_bins}
                tpo_count = {price: 0 for price in price_bins}
                for i, row in df.iterrows():
                    letter = letters[i] if i < len(letters) else '?'
                    for price in price_bins:
                        price_range_low = price
                        price_range_high = price + tick_size
                        if row['low'] <= price_range_high and row['high'] >= price_range_low:
                            market_profile[price] += letter
                            tpo_count[price] += 1
                profile_df = pd.DataFrame(list(market_profile.items()), columns=['Price', 'TPO'])
                profile_df['TPO_count'] = profile_df['Price'].map(tpo_count)
                profile_df = profile_df[profile_df['TPO'] != ""]
                if profile_df.empty:
                    logger.error(f"No valid TPO profile for token {symbol_token}")
                    return None
                poc = profile_df.loc[profile_df['TPO_count'].idxmax(), 'Price']
                logger.info(f"POC for token {symbol_token}: {poc}")
                return poc
            else:
                logger.error(f"API error for token {symbol_token}: {hist_data.get('message', 'Unknown error')}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying POC calculation for token {symbol_token} (Attempt {attempt + 2}/{max_retries})")
                    time.sleep(2)
                else:
                    logger.error(f"Max retries exceeded for POC calculation for token {symbol_token}")
                    return None
        except Exception as e:
            logger.error(f"Error calculating POC for {symbol_token}: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying POC calculation for token {symbol_token} (Attempt {attempt + 2}/{max_retries})")
                time.sleep(2)
            else:
                logger.error(f"Max retries exceeded for POC calculation for token {symbol_token}")
                return None

# Function to get 15-minute candles
def get_15min_candles(symbol_token, exchange="NFO"):
    ist = pytz.timezone('Asia/Kolkata')
    today = datetime.now(ist).date()
    current_time = datetime.now(ist)
    if current_time.hour < 9 or (current_time.hour == 9 and current_time.minute < 30):
        logger.warning(f"Skipping data fetch for token {symbol_token}: First 15-min candle not yet complete")
        return None
    fromdate = f"{today.strftime('%Y-%m-%d')} 09:15"
    todate = f"{today.strftime('%Y-%m-%d')} 15:30"
    try:
        hist_data = client.getCandleData({
            "exchange": exchange,
            "symboltoken": str(int(symbol_token)),
            "interval": "FIFTEEN_MINUTE",
            "fromdate": fromdate,
            "todate": todate
        })
        if hist_data['status'] and hist_data['data']:
            candles = pd.DataFrame(hist_data['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            logger.info(f"15-min candles for token {symbol_token}: {len(candles)} candles retrieved")
            return candles
        else:
            logger.error(f"No 15-min candle data for token {symbol_token}: {hist_data}")
            return None
    except Exception as e:
        logger.error(f"Error fetching 15-min candles for {symbol_token}: {e}")
        return None

# Function to check trading conditions
def check_trading_conditions(symbol, symbol_token, tick_size, exchange="NFO"):
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    logger.info(f"Checking trading conditions for {symbol} at {current_time}")

    # Ensure we're in the monitoring window (9:30 AM - 9:45 AM)
    if not (current_time.hour == 9 and 30 <= current_time.minute <= 45):
        logger.info(f"Outside monitoring window for {symbol}")
        return None

    # Get POC
    poc = calculate_poc(symbol_token, tick_size, exchange)
    if poc is None:
        logger.info(f"Skipping {symbol} due to missing POC")
        return None

    # Get first two 15-minute candles
    candles_15min = get_15min_candles(symbol_token, exchange)
    if candles_15min is None or len(candles_15min) < 2:
        logger.info(f"Skipping {symbol} due to missing first or second 15-min candle")
        return None

    # Get ATR
    atr = calculate_atr(symbol_token, exchange)
    if atr is None:
        logger.info(f"Skipping {symbol} due to missing ATR")
        return None

    # First candle details
    first_candle = candles_15min.iloc[0]
    fc_open = float(first_candle['open'])
    fc_low = float(first_candle['low'])
    fc_high = float(first_candle['high'])
    fc_close = float(first_candle['close'])
    logger.info(f"{symbol} - First candle: Open: {fc_open}, Low: {fc_low}, High: {fc_high}, Close: {fc_close}")

    # Get current LTP for real-time breakout check
    try:
        ltp_data = client.ltpData(exchange=exchange, tradingsymbol=symbol, symboltoken=str(int(symbol_token)))
        if ltp_data['status'] and ltp_data['data']:
            current_ltp = ltp_data['data']['ltp']
            logger.info(f"Current LTP for {symbol}: {current_ltp}")
        else:
            logger.error(f"Failed to fetch LTP for {symbol}: {ltp_data.get('message', 'Unknown error')}")
            return None
    except Exception as e:
        logger.error(f"Error fetching LTP for {symbol}: {str(e)}")
        return None

    open_to_high = fc_high - fc_open
    open_to_low = fc_open - fc_low
    signal = None

    if fc_open > poc:
        buy_conditions = [
            fc_open > poc,
            atr > open_to_high,
            current_ltp > fc_high  # Breakout above first candle high
        ]
        logger.info(f"{symbol} - Buy conditions: Open > POC: {fc_open > poc}, "
                    f"ATR > Range: {atr > open_to_high}, "
                    f"Breakout: {current_ltp > fc_high} (LTP: {current_ltp}, First High: {fc_high})")
        if all(buy_conditions):
            symbol2 = clean_stock_name(symbol)
            message = f"BUY : {symbol2} at LTP: {current_ltp}"
            send_telegram_message(message)
            signal = "BUY"
        else:
            logger.info(f"No buy signal for {symbol}")
    elif fc_open < poc:
        sell_conditions = [
            fc_open < poc,
            atr > open_to_low,
            current_ltp < fc_low  # Breakout below first candle low
        ]
        logger.info(f"{symbol} - Sell conditions: Open < POC: {fc_open < poc}, "
                    f"ATR > Range: {atr > open_to_low}, "
                    f"Breakout: {current_ltp < fc_low} (LTP: {current_ltp}, First Low: {fc_low})")
        if all(sell_conditions):
            symbol1 = clean_stock_name(symbol)
            message = f"SELL: {symbol1} at LTP: {current_ltp}"
            send_telegram_message(message)
            signal = "SELL"
        else:
            logger.info(f"No sell signal for {symbol}")
    else:
        logger.info(f"No signal for {symbol}: Open equals POC ({fc_open})")

    return signal

# Signal Detection
def signal_detection():
    ist = pytz.timezone('Asia/Kolkata')
    try:
        futures_df = pd.read_csv(csv_path)
        futures_df = futures_df[futures_df['symbol'].isin(symbols)]
        logger.info(f"Loaded {len(futures_df)} symbols from 15futures_masterlist.csv")
    except Exception as e:
        logger.error(f"Error reading 15futures_masterlist.csv: {e}")
        return
    if futures_df.empty:
        logger.error("No valid symbols found in 15futures_masterlist.csv")
        return

    alerted_symbols = set()  # Track symbols alerted today
    current_date = datetime.now(ist).date()

    while True:
        current_time = datetime.now(ist)
        # Reset alerted symbols if it's a new day
        if current_time.date() > current_date:
            logger.info("New trading day detected. Resetting alerted symbols.")
            alerted_symbols.clear()
            current_date = current_time.date()

        # Restrict to 9:30 AM - 9:45 AM
        if current_time.hour > 9 or (current_time.hour == 9 and current_time.minute > 45):
            logger.info("Monitoring window (9:30 AM - 9:45 AM) ended. Stopping signal detection.")
            break
        if current_time.hour < 9 or (current_time.hour == 9 and current_time.minute < 30):
            logger.info(f"Waiting for 9:30 AM: {current_time}")
            time.sleep(60)
            continue

        logger.info(f"Checking signals at {current_time}")
        failed_symbols = []
        for _, row in futures_df.iterrows():
            symbol = row['symbol']
            token = row['token']
            tick_size = row['tick_size']
            if symbol in alerted_symbols:
                logger.info(f"Skipping {symbol}: Already alerted today")
                continue
            logger.info(f"Processing symbol: {symbol} (Token: {token}, Tick Size: {tick_size})")
            try:
                signal = check_trading_conditions(symbol, token, tick_size, exchange="NFO")
                if signal:
                    alerted_symbols.add(symbol)
                time.sleep(2)  # Increased delay to avoid API rate limits
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                failed_symbols.append((symbol, token, tick_size))
                time.sleep(2)

        # Retry failed symbols
        if failed_symbols:
            logger.info(f"Retrying {len(failed_symbols)} failed symbols")
            for symbol, token, tick_size in failed_symbols:
                if symbol in alerted_symbols:
                    logger.info(f"Skipping retry for {symbol}: Already alerted today")
                    continue
                logger.info(f"Retrying symbol: {symbol}")
                try:
                    signal = check_trading_conditions(symbol, token, tick_size, exchange="NFO")
                    if signal:
                        alerted_symbols.add(symbol)
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"Error retrying {symbol}: {e}")
                    time.sleep(2)

        if len(alerted_symbols) == len(symbols):
            logger.info("All symbols processed. Stopping signal detection.")
            break

        time.sleep(5)  # Check every 5 seconds for responsiveness
    logger.info("Signal detection completed.")

# Main execution
if __name__ == "__main__":
    try:
        signal_detection()
    except KeyboardInterrupt:
        logger.info("Script terminated by user (KeyboardInterrupt).")
        sys.exit(0)
