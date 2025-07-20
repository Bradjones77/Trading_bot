from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

BOT_TOKEN = "7951346106:AAEws6VRZYcnDCurG1HZpAh-Y4WgA5BQLWI"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is working! Use /signal to get a trading signal.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("🚀 Bot started.")
    app.run_polling()

if __name__ == "__main__":
    main()
