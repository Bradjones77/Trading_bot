import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from telegram.ext import Application, CommandHandler, ContextTypes

# New Zealand timezone
NZ_TZ = pytz.timezone('Pacific/Auckland')

CHAT_ID = None  # Will be set after /start command

async def start(update, context):
    global CHAT_ID
    CHAT_ID = update.message.chat_id
    print(f"Chat ID set to: {CHAT_ID}")  # Debug
    await update.message.reply_text("👋 Welcome! I’ll now send you the best crypto trading signals hourly between 5 AM and 10 PM NZ time.")

async def signal(update, context):
    # Manual trigger for a signal
    now = datetime.now(NZ_TZ).strftime('%Y-%m-%d %H:%M:%S')
    await update.message.reply_text(f"Here’s your trading signal! 🕒 {now}")

async def send_signal(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID is None:
        print("CHAT_ID not set yet, skipping signal.")
        return
    now = datetime.now(NZ_TZ).strftime('%Y-%m-%d %H:%M:%S')
    print(f"Sending scheduled signal to chat ID {CHAT_ID} at {now}")
    await context.bot.send_message(chat_id=CHAT_ID, text=f"🚀 Best trading signal for you! Time: {now}")

def main():
    application = Application.builder().token("7951346106:AAEws6VRZYcnDCurG1HZpAh-Y4WgA5BQLWI").build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('signal', signal))

    scheduler = AsyncIOScheduler(timezone=NZ_TZ)
    # Every hour on the hour from 5 AM to 10 PM NZ time
    scheduler.add_job(send_signal, CronTrigger(hour='5-22', minute=0), args=[application])
    scheduler.start()

    print("🚀 Bot is live and sending hourly signals (NZ time)...")
    application.run_polling()

if __name__ == "__main__":
    main()
