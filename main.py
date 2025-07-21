import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import yfinance as yf
import ccxt
import pandas as pd
import asyncio

# --- Setup logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Your Telegram Bot Token ---
TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace with your actual token!

# --- Stock and Crypto Data ---
stock_list = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA"]
crypto_list = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "DOGE/USDT", "PEPE/USDT"]

exchange = ccxt.binance()

# --- Stock Signal Functions ---
def get_top_gainer():
    top = None
    best = -999
    for ticker in stock_list:
        try:
            df = yf.download(ticker, period="2d", interval="1d", progress=False)
            logger.info(f"Fetched stock data for {ticker}: {df.tail(2)}")
        except Exception as e:
            logger.error(f"Failed to download stock data for {ticker}: {e}")
            continue
        if len(df) < 2:
            logger.warning(f"Not enough stock data for {ticker}")
            continue
        try:
            change = (df['Close'][-1] - df['Close'][-2]) / df['Close'][-2]
        except Exception as e:
            logger.error(f"Error calculating change for {ticker}: {e}")
            continue
        if change > best:
            best = change
            top = ticker
    if top:
        return f"📈 Best performing stock today: {top} (+{round(best*100, 2)}%)"
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
    return "
