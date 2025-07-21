import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import ccxt
import pandas as pd
import asyncio

# --- Setup logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Load Telegram Bot Token ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7951346106:AAEws6VRZYcnDCurG1HZpAh-Y4WgA5BQLWI")

if not TOKEN:
    logger.error("Telegram bot token not found! Please set the TELEGRAM_BOT_TOKEN environment variable.")
    exit(1)

# --- Crypto Data ---
crypto_list = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "DOGE/USDT", "PEPE/USDT"]
exchange = ccxt.binance()

# --- Crypto Signal Functions ---
def get_ohlcv(symbol):
    try:
        data = exchange.fetch_ohlcv(symbol, timeframe='1d', limit=2)
        logger.info(f"Fetched crypto OHLCV for {symbol}: {data}")
    except Exception as e:
        logger.error(f"Error fetching OHLCV for {symbol}: {e}")
        return None, None
    if len(data) < 2:
        logger.warning(f"Not enough OHLCV data for {symbol}")
        return None, None
    df = pd.DataFrame(data, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
    return df['close'].iloc[-1], df['close'].iloc[-2]

def get_top_crypto():
    best = -999
    top = None
    for coin in crypto_list:
        last, prev = get_ohlcv(coin)
        if last is None or prev is None:
            logger.warning(f"Skipping {coin} due to missing data")
            continue
        try:
            change = (last - prev) / prev
        except Exception as e:
            logger.error(f"Error calculating change for {coin}: {e}")
            continue
        if change > best:
            best = change
            top = coin
    if top:
        return f"📈 Best performing crypto today: {top} (+{round(best*100, 2)}%)"
    else:
        return "❌ Could not fetch crypto data."

def get_long_term_crypto():
    return "🧠 Long-term crypto idea: ETH/USDT (Leading L1 smart contract platform)"

def get_short_term_crypto():
    return "💣 Short-term crypto trade: PEPE/USDT (Meme coin with breakout potential)"

# --- Telegram Bot Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Smart Trading Bot!\n"
        "Use /help to see available commands.\n"
        "This bot scans the market 24/7 for smart trade signals in crypto."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📘 Available Commands:\n\n"
        "💰 Crypto Signals:\n"
        "  /signalcrypto    - Top crypto gainer today\n"
        "  /signalcrypto_l  - Long-term crypto pick\n"
        "  /signalcrypto_s  - Short-term crypto play\n\n"
        "🔍 Other:\n"
        "  /start           - Bot introduction\n"
        "  /help            - List of all commands"
    )

async def signalcrypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_top_crypto())

async def signalcrypto_l(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_long_term_crypto())

async def signalcrypto_s(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_short_term_crypto())

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Register commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(CommandHandler("signalcrypto", signalcrypto))
    app.add_handler(CommandHandler("signalcrypto_l", signalcrypto_l))
    app.add_handler(CommandHandler("signalcrypto_s", signalcrypto_s))

    logger.info("Bot started...")
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (RuntimeError, KeyboardInterrupt) as e:
        logger.error(f"Bot stopped: {e}")
