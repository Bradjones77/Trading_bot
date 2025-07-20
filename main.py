from telegram import Bot
from telegram.ext import Updater, CommandHandler

def start(update, context):
    update.message.reply_text("Hello! Bot is running.")

def main():
    # Replace YOUR_TOKEN_HERE with your actual Telegram bot token
    updater = Updater("YOUR_TOKEN_HERE", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
