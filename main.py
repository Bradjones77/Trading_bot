from telegram.ext import ApplicationBuilder, CommandHandler
import logging

# Your bot token (hardcoded here for testing only)
TOKEN = "7951346106:AAEws6VRZYcnDCurG1HZpAh-Y4WgA5BQLWI"

# Basic logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update, context):
    await update.message.reply_text("Hello! I am bradjones77_bot.")

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    print("Bot started")
    application.run_polling()

if __name__ == '__main__':
    main()
