import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import random

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Example trading signals (mock data)
trades = [
    {"symbol": "BTCUSDT", "buy_price": 30000, "target_profit": 5, "stop_loss": 2},
    {"symbol": "ETHUSDT", "buy_price": 2000, "target_profit": 4, "stop_loss": 1.5},
    {"symbol": "SOLUSDT", "buy_price": 35, "target_profit": 6, "stop_loss": 3},
]

# This dict will hold active trades for follow-up
active_trades = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to the Trading Signals Bot!\n"
        "Use /signal to get a new trade signal.\n"
        "You will receive buy, stop loss, target profit, and follow-ups."
    )

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Randomly pick a trade signal from our mock list
    trade = random.choice(trades)
    symbol = trade["symbol"]
    buy_price = trade["buy_price"]
    profit = trade["target_profit"]
    stop_loss = trade["stop_loss"]

    # Save this trade as active for follow-up
    active_trades[symbol] = {
        "buy_price": buy_price,
        "target_profit": profit,
        "stop_loss": stop_loss,
        "status": "Open",
        "updates_sent": 0,
    }

    msg = (
        f"📈 New Trade Signal 📈\n"
        f"Symbol: {symbol}\n"
        f"Buy Price: ${buy_price}\n"
        f"Target Profit: {profit}%\n"
