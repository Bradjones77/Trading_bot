from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
import random
import datetime

BOT_TOKEN = "7951346106:AAEws6VRZYcnDCurG1HZpAh-Y4WgA5BQLWI"

# Example coin signal data (to be replaced with real API signals)
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

# Sort by most profitable/confident first
coin_signals = sorted(coin_signals, key=lambda x: -x['confidence'])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! I’ll now send you the best crypto trading signals.")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.datetime.now().time()
    if not (datetime.time(5, 0) <= now <= datetime.time(22, 0)):
        await update.message.reply_text("⏱ Signals are only sent between 5am and 10pm.")
        return

    best_signal = coin_signals[0]
    msg = f"""💰 *Top Signal Right Now* 💰

📈 Coin: *{best_signal['name']}*
📍 Entry Price: `{best_signal['entry_price']}`
🎯 Target: `{best_signal['target_price']}`
🛑 Stop Loss: `{best_signal['stop_loss']}`
📊 Confidence: *{best_signal['confidence']}%*
🕒 Type: *{best_signal['type'].capitalize()} Trade*

I'll let you know when to sell or buy based on the market. ✅
"""
    await update.message.reply_markdown(msg)

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("signal", signal))

    print("🚀 Bot is live and waiting...")
    application.run_polling()

if __name__ == "__main__":
    main()
