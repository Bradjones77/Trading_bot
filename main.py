from telegram.ext import ApplicationBuilder, CommandHandler
import logging

# Your bot token (hardcoded here for testing only)
TOKEN = "7951346106:AAEws6VRZYcnDCurG1HZpAh-Y4WgA5BQLWI"

# Basic logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update, context):
    await update.message.reply_text("Hello! I am bradjones77_bot.")

async def signal(update, context):
    # Example signal message
    await update.message.reply_text("New trade signal: Buy BTC at $30,000. Expected profit: 5%. Stop loss: $29,000.")

async def request(update, context):
    await update.message.reply_text("Trade signal requested! Generating your signal...")

async def buy(update, context):
    await update.message.reply_text("Buy alert! Consider buying now.")

async def sell(update, context):
    await update.message.reply_text("Sell alert! Consider selling now.")

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("signal", signal))
    application.add_handler(CommandHandler("request", request))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("sell", sell))

    print("Bot started")
    application.run_polling()

if __name__ == '__main__':
    main()
