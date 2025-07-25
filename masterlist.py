import pandas as pd
import requests
from datetime import datetime, timedelta
import calendar

# Disable SSL warnings (for testing only)
requests.packages.urllib3.disable_warnings()

print("📥 Downloading masterlist...")
response = requests.get(
    'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json',
    verify=False
)

if response.status_code != 200:
    print("❌ Failed to download masterlist.")
    exit()

# Save masterlist.csv
df = pd.DataFrame(response.json())
df.to_csv('masterlist.csv', index=False)
print("✅ Saved 'masterlist.csv'")

# Step 1: Filter where exch_seg == 'NFO'
df_nfo = df[df['exch_seg'] == 'NFO']

# Step 2: Filter by valid names
valid_names = [
    "ACC", "ANGELONE", "ASIANPAINT", "ASTRAL", "AUROPHARMA", "DMART", "AXISBANK", "BSE",
    "BAJAJ_AUTO", "BAJFINANCE", "BAJAJFINSV", "BHARATFORG", "BHARTIARTL", "BRITANNIA",
    "CDSL", "CHOLAFIN", "CIPLA", "COALINDIA", "COFORGE", "COLPAL", "CAMS", "COROMANDEL",
    "CUMMINSIND", "CYIENT", "DLF", "DABUR", "DALBHARAT", "DEEPAKNTR", "DIVISLAB", "DIXON",
    "LALPATHLAB", "DRREDDY", "EICHERMOT", "ESCORTS", "GODREJCP", "GODREJPROP", "GRASIM",
    "HCLTECH", "HDFCAMC", "HDFCBANK", "HDFCLIFE", "HAVELLS", "HEROMOTOCO", "HINDALCO",
    "HAL", "HINDUNILVR", "ICICIBANK", "ICICIGI", "ICICIPRULI", "IRCTC", "INDUSINDBK",
    "NAUKRI", "INFY", "INDIGO", "JKCEMENT", "JSWSTEEL", "JSL", "JINDALSTEL", "JUBLFOOD",
    "KOTAKBANK", "LTF", "LTTS", "LTIM", "LT", "LUPIN", "MGL", "M_M", "MFSL", "METROPOLIS",
    "MPHASIS", "MCX", "MUTHOOTFIN", "NESTLEIND", "OBEROIRLTY", "PVRINOX", "PERSISTENT",
    "POLYCAB", "RELIANCE", "SBICARD", "SBILIFE", "SRF", "SHRIRAMFIN", "SBIN", "SUNPHARMA",
    "TATACONSUM", "TVSMOTOR", "TATACHEM", "TCS", "TATAMOTORS", "TECHM", "INDHOTEL",
    "TITAN", "TORNTPHARM", "TORNTPOWER", "TRENT", "TIINDIA", "UBL", "UNITDSPR", "VOLTAS",
    "ZYDUSLIFE"
]
df_nfo = df_nfo[df_nfo['name'].isin(valid_names)]

# Step 3: Ask for manual month input
manual_month = input("📅 Enter the 3-letter expiry month (e.g., JUN, JUL, AUG): ").strip().upper()

# Filter by the manually entered month
df_expiry = df_nfo[df_nfo['expiry'].str.contains(manual_month, na=False, case=False)]

if df_expiry.empty:
    print(f"❌ No matching expiry data found for month: {manual_month}")
    exit()

# Step 4: Split into options and futures

df_futures = df_expiry[df_expiry['instrumenttype'] == 'FUTSTK'].sort_values(by='name')

# Step 5: Save to separate CSV files

df_futures.to_csv('futures_masterlist.csv', index=False)


print(f"✅ Saved {len(df_futures)} futures to 'futures_masterlist.csv'")

