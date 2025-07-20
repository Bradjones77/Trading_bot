from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
import random
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

TOKEN = "7951346106:AAEws6VRZYcnDCurG1HZpAh-Y4WgA5BQLWI"
ADMIN_CHAT_ID = 123456789  # Replace this with YOUR Telegram user ID

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# === GET LIVE PRICE ===
def get_price(symbol):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
    r = requests.get(url)
    data = r.json()
    return data[symbol]['usd']

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bradjones77 Trade Bot Ready!\n\n"
        "Commands:\n"
        "/signal – Get a trade signal\n"
        "/request – Request manual signal\n"
        "/buy – Simulate buy\n"
        "/sell – Simulate sell"
    )

# === /signal ===
async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coin = random.choice([
        {"id": "bitcoin", "symbol": "BTC/USDT"},
        {"id": "ethereum", "symbol": "ETH/USDT"},
        {"id": "solana", "symbol": "SOL/USDT"}
    ])
    price = get_price(coin['id'])
    direction = random.choice(["BUY", "SELL"])
    profit = round(random.uniform(5, 15), 2)
    stop_loss = round(random.uniform(2, 4), 2)

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
    await signal(update, context)

# === /buy ===
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Simulated Buy Placed.")

# === /sell ===
async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Simulated Sell Executed.")

# === SCHEDULED SIGNALS ===
def schedule_signal(application):
    async def send_scheduled_signal():
        coin = {"id": "bitcoin", "symbol": "BTC/USDT"}
        price = get_price(coin['id'])
        profit = round(random.uniform(5, 15), 2)
        stop_loss = round(random.uniform(2, 4), 2)

        msg = (
            f"🕒 *Hourly Trade Alert*\n"
            f"Pair: `{coin['symbol']}`\n"
            f"Price: *${price}*\n"
            f"Profit Target: *{profit}%*\n"
            f"Stop Loss: *{stop_loss}%*"
        )
        await application.bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg, parse_mode='Markdown')

    scheduler = BackgroundScheduler(timezone=pytz.utc)
    scheduler.add_job(lambda: application.create_task(send_scheduled_signal()), 'interval', hours=1)
    scheduler.start()

# === MAIN ===
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("request", request))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))

    schedule_signal(app)

    print("✅ Bot started.")
    app.run_polling()

if __name__ == '__main__':
    main()
