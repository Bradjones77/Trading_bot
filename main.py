from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
import random
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

TOKEN = "7951346106:AAEws6VRZYcnDCurG1HZpAh-Y4WgA5BQLWI"
ADMIN_CHAT_ID = 123456789  # Replace with your actual Telegram user ID

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Meme + Major coins
COINS = [
    {"id": "bitcoin", "symbol": "BTC/USDT"},
    {"id": "ethereum", "symbol": "ETH/USDT"},
    {"id": "solana", "symbol": "SOL/USDT"},
    {"id": "pepe", "symbol": "PEPE/USDT"},
    {"id": "dogecoin", "symbol": "DOGE/USDT"},
    {"id": "shiba-inu", "symbol": "SHIB/USDT"},
    {"id": "floki", "symbol": "FLOKI/USDT"},
    {"id": "bonk", "symbol": "BONK/USDT"},
    {"id": "aptos", "symbol": "APT/USDT"},
]

# === GET LIVE PRICE ===
def get_price(symbol_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol_id}&vs_currencies=usd"
        r = requests.get(url, timeout=10)
        data = r.json()
        return data[symbol_id]['usd']
    except Exception as e:
        return None

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Bradjones77 AI Trade Bot!\n\n"
        "Use the following commands:\n"
        "/signal – 📈 Get a trade signal\n"
        "/request – 🔄 Request manual signal\n"
        "/buy – ✅ Simulate buy\n"
        "/sell – ❌ Simulate sell\n"
        "/followup – 📬 Check trade outcome"
    )

# === /signal ===
async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coin = random.choice(COINS)
    price = get_price(coin['id'])

    if price is None:
        await update.message.reply_text("⚠️ Could not fetch price. Try again.")
        return

    direction = random.choice(["BUY", "SELL"])
    profit = round(random.uniform(5, 15), 2)
    stop_loss = round(random.uniform(2, 5), 2)

    msg = (
        f"📊 *Live Trade Signal*\n"
        f"Pair: `{coin['symbol']}`\n"
        f"Direction: *{direction}*\n"
        f"Price: *${price}*\n"
        f"Target Profit: *{profit}%*\n"
        f"Stop Loss: *{stop_loss}%*"
    )

    await update.message.reply_markdown(msg)

# === /request ===
async def request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔁 Manual trade signal requested...")
    await signal(update, context)

# === /buy ===
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Buy order placed (simulated).")

# === /sell ===
async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Sell order placed (simulated).")

# === /followup ===
async def followup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = random.choice(["✅ Hit target", "🔴 Stopped out", "⏳ Still active"])
    result = round(random.uniform(-5, 12), 2)

    msg = f"📬 *Trade Update*\nStatus: *{status}*\nP/L: *{result}%*"
    await update.message.reply_markdown(msg)

# === Scheduled Signals ===
def schedule_signal(application):
    async def send_hourly_signal():
        coin = random.choice(COINS)
        price = get_price(coin['id'])

        if price is None:
            return

        profit = round(random.uniform(5, 12), 2)
        stop_loss = round(random.uniform(2, 4), 2)
        success_chance = random.randint(60, 95)

        msg = (
            f"🕒 *Hourly Trade Alert*\n"
            f"Pair: `{coin['symbol']}`\n"
            f"Price: *${price}*\n"
            f"Target Profit: *{profit}%*\n"
            f"Stop Loss: *{stop_loss}%*\n"
            f"Success Rate: *{success_chance}%*"
        )

        await application.bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg, parse_mode='Markdown')

    scheduler = BackgroundScheduler(timezone=pytz.utc)
    scheduler.add_job(lambda: application.create_task(send_hourly_signal()), 'interval', hours=1)
    scheduler.start()

# === MAIN ===
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("request", request))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))
    app.add_handler(CommandHandler("followup", followup))

    schedule_signal(app)

    print("✅ Bot is running")
    app.run_polling()

if __name__ == '__main__':
    main()
