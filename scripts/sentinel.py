#!/usr/bin/env python3
import yfinance as yf
import pandas as pd
from datetime import datetime, timezone
import pytz
import os

# Settings
SYMBOL = "TSLA"
PERCENT_TRIGGER = 5
VOLUME_TRIGGER_MULTIPLIER = 2
LOG_DIR = "log"
LOG_FILE = os.path.join(LOG_DIR, "alerts.csv")
LATEST_FILE = "latest_alert.md"

# Ensure log dir exists
os.makedirs(LOG_DIR, exist_ok=True)

# Timezone
PT = pytz.timezone("America/Los_Angeles")
now = datetime.now(timezone.utc).astimezone(PT)

# Fetch intraday data
ticker = yf.Ticker(SYMBOL)
hist = ticker.history(period="1d", interval="1m")

if hist.empty:
    print("⚠️ Could not fetch TSLA data.")
    exit(1)

# Latest price and volume
current_price = hist["Close"].iloc[-1]
day_open = hist["Open"].iloc[0]
change_pct = (current_price - day_open) / day_open * 100
intraday_high = hist["High"].max()
intraday_low = hist["Low"].min()
intraday_volume = hist["Volume"].sum()

# 30-day average daily volume
hist30 = ticker.history(period="30d", interval="1d")
avg30_vol = hist30["Volume"].mean()

# Trigger checks
price_trigger = abs(change_pct) >= PERCENT_TRIGGER
volume_trigger = intraday_volume >= VOLUME_TRIGGER_MULTIPLIER * avg30_vol

if price_trigger or volume_trigger:
    alert_text = (
        f"Tesla Market Sentinel Alert - {now.strftime('%Y-%m-%d %H:%M %Z')}\n\n"
        f"**TSLA Price:** ${current_price:.2f}\n"
        f"**Change from open:** {change_pct:.2f}%\n"
        f"**Day range:** {intraday_low:.2f} – {intraday_high:.2f}\n"
        f"**Intraday volume:** {intraday_volume:,.0f}\n"
        f"**30-day avg volume:** {avg30_vol:,.0f}\n\n"
        f"→ Trigger met: {'Price' if price_trigger else ''} {'Volume' if volume_trigger else ''}\n"
    )
else:
    alert_text = "No new credible information or significant stock movement since last alert."

# Write to latest_alert.md
with open(LATEST_FILE, "w") as f:
    f.write(alert_text)

# Append to CSV log
row = {
    "timestamp": now.isoformat(),
    "price": current_price,
    "change_pct": change_pct,
    "volume": intraday_volume,
    "avg30_vol": avg30_vol,
    "price_trigger": price_trigger,
    "volume_trigger": volume_trigger,
    "text": alert_text.replace("\n", " ")
}
df = pd.DataFrame([row])

if not os.path.exists(LOG_FILE):
    df.to_csv(LOG_FILE, index=False)
else:
    df.to_csv(LOG_FILE, mode="a", header=False, index=False)

print(alert_text)
