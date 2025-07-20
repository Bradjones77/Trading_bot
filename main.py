import os
import pytz
from datetime import datetime
from telegram.ext import Application, CommandHandler, ContextTypes

NZ_TZ = pytz.timezone('Pacific/Auckland')
CHAT_ID = None

async def start(update, context):
    global CHAT_ID
    CHAT_ID = update.message.chat_id
    print(f"Chat ID set to: {CHAT_ID}")
    await update.message.reply_text("👋 Welcome! I’ll now send you the best crypto trading signals hourly between 5 AM and 10 PM NZ time.")

async def signal(update, context):
    now = datetime.now(NZ_TZ).strftime('%Y-%m-%d %H:%M:%S')
    await update.message.reply_text(f"Here’s your trading signal! 🕒 {now}")

async def send_signal(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID is None:
        print("CHAT_ID not set yet, skipping signal.")
        return
    now = datetime.now(NZ_TZ).strftime('%Y-%m-%d %H:%M:%S')
    print(f"Sending scheduled signal to chat ID {CHAT_ID} at {now}")
    await context.bot.send_message(chat_id=CHAT_ID, text=f"🚀 Best trading signal for you! Time: {now}")

def schedule_hourly_signals(app: Application):
    job_queue = app.job_queue
    job_queue.jobs().clear()
    for hour in range(5, 23):
        job_queue.run_daily(send_signal, time=datetime.time(hour=hour, minute=0, tzinfo=NZ_TZ))

def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('signal', signal))

    application.job_queue.run_once(lambda ctx: schedule_hourly_signals(application), when=0)

    print("🚀 Bot is live and sending hourly signals (NZ time)...")
    application.run_polling()

if __name__ == "__main__":
    main()
