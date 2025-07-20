from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import datetime

BOT_TOKEN = "7951346106:AAEws6VRZYcnDCurG1HZpAh-Y4WgA5BQLWI"
CHAT_ID = None  # Will be set from /start command

# Example coin signal data
coin_signals = [
    {
        "name": "PepeCoin",
        "entry_price": 0.0000031,
        "target_price": 0.0000050,
        "stop_loss": 0.0000028,
        "confidence": 92,
        "type": "short"
    },
    {
        "name": "Shiba Inu",
        "entry_price": 0.000017,
        "target_price": 0.000021,
        "stop_loss": 0.000015,
        "confidence": 85,
        "type": "short"
    },
    {
        "name": "Solana",
        "entry_price": 165.0,
        "target_price": 210.0,
        "stop_loss": 150.0,
        "confidence": 78,
        "type": "long"
    }
]

# Sort signals by confidence
coin_signals = sorted(coin_signals, key=lambda x: -x['confidence'])

async def send_signal(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID is None:
        return  # user hasn't started the bot

    best_signal = coin_signals[0]
    msg = f"""💰 *Top Signal Right Now* 💰

📈 Coin: *{best_signal['name']}*
📍 Entry Price: `{best_signal['entry_price']}`
🎯 Target: `{best_signal['target_price']}`
🛑 Stop Loss: `{best_signal['stop_loss']}`
📊 Confidence: *{best_signal['confidence']}%*
🕒 Type: *{best_signal['type'].capitalize()} Trade*

✅ Sent at {datetime.datetime.now(pytz.timezone("Pacific/Auckland")).strftime('%I:%M %p')} NZT
"""
    await context.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    CHAT_ID = update.message.chat_id
    await update.message.reply_text("👋 Welcome! I’ll now send you the best crypto trading signals.")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    best_signal = coin_signals[0]
    msg = f"""💰 *Top Signal Right Now* 💰

📈 Coin: *{best_signal['name']}*
📍 Entry Price: `{best_signal['entry_price']}`
🎯 Target: `{best_signal['target_price']}`
🛑 Stop Loss: `{best_signal['stop_loss']}`
📊 Confidence: *{best_signal['confidence']}%*
🕒 Type: *{best_signal['type'].capitalize()} Trade*
"""
    await update.message.reply_markdown(msg)

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    scheduler = AsyncIOScheduler(timezone="Pacific/Auckland")

    # Send signal every hour from 5am to 10pm NZT
    scheduler.add_job(send_signal, CronTrigger(hour='5-22', minute=0), args=[application.bot])
    scheduler.start()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("signal", signal))

    print("🚀 Bot is live and sending hourly signals (NZ time)...")
    application.run_polling()

if __name__ == "__main__":
    main()
