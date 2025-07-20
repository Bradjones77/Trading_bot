import os
import pytz
import datetime
from telegram.ext import Application, CommandHandler, ContextTypes

# Use NZ timezone
NZ_TZ = pytz.timezone("Pacific/Auckland")
CHAT_ID = None  # Will be set after /start command

async def start(update, context):
    global CHAT_ID
    CHAT_ID = update.message.chat_id
    print(f"[DEBUG] Chat ID set to: {CHAT_ID}")
    await update.message.reply_text(
        "👋 Welcome! I’ll send you crypto trading signals hourly between 5 AM and 10 PM NZ time."
    )

async def signal(update, context):
    now = datetime.datetime.now(NZ_TZ).strftime('%Y-%m-%d %H:%M:%S')
    await update.message.reply_text(f"Here’s your trading signal! 🕒 {now}")

async def send_signal(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID is None:
        print("[DEBUG] CHAT_ID not set yet, skipping signal.")
        return
    now = datetime.datetime.now(NZ_TZ).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[DEBUG] Sending signal to chat ID {CHAT_ID} at {now}")
    await context.bot.send_message(chat_id=CHAT_ID, text=f"🚀 Signal for {now}")

def schedule_signals(application):
    job_queue = application.job_queue
    for hour in range(5, 23):  # 5 AM to 10 PM inclusive
        job_queue.run_daily(send_signal, time=datetime.time(hour=hour, minute=0, tzinfo=NZ_TZ))

def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set in environment variables!")

    print("[DEBUG] Loaded token.")
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('signal', signal))

    # Schedule signals after bot starts
    application.job_queue.run_once(lambda ctx: schedule_signals(application), when=0)

    print("🚀 Bot is live and sending hourly signals (NZ time)...")
    application.run_polling()

if __name__ == "__main__":
    main()
