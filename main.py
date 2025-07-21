import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import yfinance as yf
import ccxt
import pandas as pd

# --- Setup logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Your Telegram Bot Token ---
TOKEN = "7951346106:AAEws6VRZYcnDCurG1HZpAh-Y4WgA5BQLWI"

# --- Stock and Crypto Data ---
stock_list = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA"]
crypto_list = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "DOGE/USDT", "PEPE/USDT"]

exchange = ccxt.binance()

# --- Stock Signal Functions ---
def get_top_gainer():
    top = None
    best = -999
    for ticker in stock_list:
        df = yf.download(ticker, period="2d", interval="1d", progress=False)
        if len(df) < 2:
            continue
        change = (df['Close'][-1] - df['Close'][-2]) / df['Close'][-2]
        if change > best:
            best = change
            top = ticker
    if top:
        return f"📈 Best performing stock today: {top} (+{round(best*100,2)}%)"
    else:
        return "❌ Could not fetch stock data."

def get_long_term_pick():
    return "📊 Long-term stock pick: AAPL (Strong earnings, reliable growth)"

def get_short_term_pick():
    return "💥 Short-term trade idea: NVDA (High momentum, near breakout zone)"

# --- Crypto Signal Functions ---
def get_ohlcv(symbol):
    try:
        data = exchange.fetch_ohlcv(symbol, timeframe='1d', limit=2)
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return None, None
    if len(data) < 2:
        return None, None
    df = pd.DataFrame(data, columns=['ts','open','high','low','close','volume'])
    return df['close'].iloc[-1], df['close'].iloc[-2]

def get_top_crypto():
    best = -999
    top = None
    for coin in crypto_list:
        last, prev = get_ohlcv(coin)
        if not last or not prev:
            continue
        change = (last - prev) / prev
        if change > best:
            best = change
            top = coin
    if top:
        return f"📈 Best performing crypto today: {top} (+{round(best*100,2)}%)"
    else:
        return "❌ Could not fetch crypto data."

def get_long_term_crypto():
    return "🧠 Long-term crypto idea: ETH/USDT (Leading L1 smart contract platform)"

def get_short_term_crypto():
    return "💣 Short-term crypto trade: PEPE/USDT (Meme coin with breakout potential)"

# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Smart Trading Bot!\n"
        "Use /help to see available commands.\n"
        "This bot scans the market 24/7 for smart trade signals in stocks & crypto."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📘 Available Commands:\n\n"
        "📈 Stock Signals:\n"
        "  /signalstock     - Top stock gainer today\n"
        "  /signalstock_l   - Long-term investment stock\n"
        "  /signalstock_s   - Short-term/day trading stock\n\n"
        "💰 Crypto Signals:\n"
        "  /signalcrypto    - Top crypto gainer today\n"
        "  /signalcrypto_l  - Long-term crypto pick\n"
        "  /signalcrypto_s  - Short-term crypto play\n\n"
        "🔍 Other:\n"
        "  /start           - Bot introduction\n"
        "  /help            - List of all commands"
    )

async def signalstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_top_gainer())

async def signalstock_l(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_long_term_pick())

async def signalstock_s(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_short_term_pick())

async def signalcrypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_top_crypto())

async def signalcrypto_l(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_long_term_crypto())

async def signalcrypto_s(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_short_term_crypto())

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Register commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(CommandHandler("signalstock", signalstock))
    app.add_handler(CommandHandler("signalstock_l", signalstock_l))
    app.add_handler(CommandHandler("signalstock_s", signalstock_s))

    app.add_handler(CommandHandler("signalcrypto", signalcrypto))
    app.add_handler(CommandHandler("signalcrypto_l", signalcrypto_l))
    app.add_handler(CommandHandler("signalcrypto_s", signalcrypto_s))

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
