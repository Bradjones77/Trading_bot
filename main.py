import telegram
import schedule
import time
from datetime import datetime
from strategies import get_trade_signals
from utils import format_signals

# Embedded credentials (less secure — use with caution)
TOKEN = "7951346106:AAEws6VRZYcnDCurG1HZpAh-Y4WgA5BQLWI"
CHAT_ID = "@Bradjones77_bot"

bot = telegram.Bot(token=TOKEN)

def send_signals():
    signals = get_trade_signals()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"📈 *Crypto Signals - {now}*\n\n"
    message += format_signals(signals)
    bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=telegram.ParseMode.MARKDOWN)

# Schedule signals every hour between 5 AM and 10 PM
for hour in range(5, 22):  # 5 to 21 inclusive
    schedule.every().day.at(f"{hour:02}:00").do(send_signals)

print("📡 Bot running with hourly signals from 5 AM to 10 PM...")
while True:
    schedule.run_pending()
    time.sleep(60)
