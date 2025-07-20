from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

BOT_TOKEN = "7951346106:AAEws6VRZYcnDCurG1HZpAh-Y4WgA5BQLWI"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! Your trading bot is online and working.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Add /start command handler
    application.add_handler(CommandHandler("start", start))

    print("🤖 Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
