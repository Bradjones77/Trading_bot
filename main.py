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

a
