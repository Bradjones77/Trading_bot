from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
import random
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import numpy as np

TOKEN = "7951346106:AAEws6VRZYcnDCurG1HZpAh-Y4WgA5BQLWI"
ADMIN_CHAT_ID = 123456789  # Replace with your Telegram user ID

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Crypto coins (default list)
CRYPTO_COINS = [
    {"id": "bitcoin", "symbol": "BTC", "name": "Bitcoin"},
    {"id": "ethereum", "symbol": "ETH", "name": "Ethereum"},
    {"id": "solana", "symbol": "SOL", "name": "Solana"},
    {"id": "pepe", "symbol": "PEPE", "name": "Pepe"},
    {"id": "dogecoin", "symbol": "DOGE", "name": "Dogecoin"},
    {"id": "shiba-inu", "symbol": "SHIB", "name": "Shiba Inu"},
    {"id": "floki", "symbol": "FLOKI", "name": "Floki"},
    {"id": "bonk", "symbol": "BONK", "name": "Bonk"},
    {"id": "aptos", "symbol": "APT", "name": "Aptos"},
]

# Stock watchlist (ticker -> name)
STOCKS = {}

# IPO list: ticker -> {"name": str, "date": str}
IPOS = {}

# Active trades: key format "crypto:<symbol>" or "stock:<ticker>"
active_trades = {}

# User data for preferences and signals
USER_PREFERENCES = {}  # chat_id -> {"category": "short" or "long"}
USER_STOCK_SIGNALS = {}  # chat_id -> list of stock signal messages
USER_CRYPTO_SIGNALS = {}  # chat_id -> list of crypto signal messages

# For new stocks and cryptos added since bot start
NEW_STOCKS = []
NEW_CRYPTOS = []

# === Helper functions ===

def get_crypto_price(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        r = requests.get(url, timeout=10)
        data = r.json()
        return data[coin_id]['usd']
    except Exception:
        return None

def get_stock_price(ticker):
    # Placeholder: implement with real stock price API or mock
    return round(random.uniform(50, 500), 2)

def get_historical_prices(coin_id, days=30):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
        response = requests.get(url)
        data = response.json()
        prices = [p[1] for p in data['prices']]
        volumes = [v[1] for v in data['total_volumes']]
        return prices, volumes
    except Exception:
        return None, None

def moving_average(data, window):
    return np.convolve(data, np.ones(window)/window, mode='valid')

def compute_rsi(prices, window=14):
    deltas = np.diff(prices)
    seed = deltas[:window]
    up = seed[seed >= 0].sum() / window
    down = -seed[seed < 0].sum() / window if any(seed < 0) else 0
    rs = up / down if down != 0 else 0
    rsi = 100 - (100 / (1 + rs)) if down != 0 else 100

    rsi_values = [rsi]
    for delta in deltas[window:]:
        upval = max(delta, 0)
        downval = -min(delta, 0)
        up = (up * (window - 1) + upval) / window
        down = (down * (window - 1) + downval) / window
        rs = up / down if down != 0 else 0
        rsi = 100 - (100 / (1 + rs)) if down != 0 else 100
        rsi_values.append(rsi)
    return rsi_values[-1]

def analyze_coin(coin_id):
    prices, volumes = get_historical_prices(coin_id, days=30)
    if not prices or len(prices) < 21:
        return None

    ma_short = moving_average(prices, 7)[-1]
    ma_long = moving_average(prices, 21)[-1]
    rsi = compute_rsi(prices)
    avg_volume = np.mean(volumes[:-1])
    current_volume = volumes[-1]

    signals = []

    if ma_short > ma_long:
        signals.append("📈 Bullish Moving Average crossover")
    else:
        signals.append("📉 Bearish Moving Average crossover")

    if rsi < 30:
        signals.append("⚠️ RSI indicates Oversold (Potential Buy)")
    elif rsi > 70:
        signals.append("⚠️ RSI indicates Overbought (Potential Sell)")

    if current_volume > avg_volume * 1.5:
        signals.append("🔊 Volume Spike Detected")

    return signals

# === Commands ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Bradjones77 AI Trade Bot!\n\n"
        "Type /help to see all commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📚 *Available Commands*\n\n"
        "/start — Welcome message\n"
        "/help — Show this help message\n\n"
        "/addstock <ticker> <name> — Add a stock to watchlist\n"
        "/addipo <ticker> <name> <YYYY-MM-DD> — Add a new IPO\n"
        "/addcrypto <ticker> <name> — Add a crypto to watchlist\n\n"
        "/signal <ticker> — Generate a stock signal\n"
        "/cryptosignal <ticker> — Generate a crypto signal\n"
        "/allsignals — View all your stock signals\n"
        "/allcryptosignals — View all your crypto signals\n"
        "/ipos — View upcoming IPOs\n\n"
        "/setcategory <short|long> — Set your investment style for stocks\n"
        "/stockcategoriesignal — Get stock signals based on your preference\n\n"
        "/newstocks — View newly added stocks\n"
        "/newcryptos — View newly added cryptos\n\n"
        "/investcrypto <coin> — Mark crypto investment\n"
        "/investstock <ticker> — Mark stock investment\n"
        "/followup — Check all active trades\n"
        "/buy — Simulate buy order\n"
        "/sell — Simulate sell order\n"
    )
    await update.message.reply_markdown(help_text)

# Add crypto to watchlist
async def addcrypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Usage: /addcrypto <ticker> <name>")
        return
    ticker = context.args[0].upper()
    name = " ".join(context.args[1:])
    # Check if already exists
    if any(c['symbol'] == ticker for c in CRYPTO_COINS):
        await update.message.reply_text(f"⚠️ Crypto {ticker} already in watchlist.")
        return
    # We add it as a new crypto with dummy id = ticker.lower() (since no CoinGecko id)
    CRYPTO_COINS.append({"id": ticker.lower(), "symbol": ticker, "name": name})
    NEW_CRYPTOS.append(f"{ticker} ({name})")
    await update.message.reply_text(f"✅ Crypto {ticker} ({name}) added to watchlist.")

# Generate stock signal for specific ticker
async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Please specify a stock ticker. Example: /signal AAPL")
        return
    ticker = context.args[0].upper()
    if ticker not in STOCKS:
        await update.message.reply_text(f"❌ Stock {ticker} not tracked. Add it first with /addstock.")
        return
    price = get_stock_price(ticker)
    profit = round(random.uniform(3, 15), 2)
    stop_loss = round(random.uniform(1, 5), 2)
    msg = (
        f"📊 Stock Signal for {ticker} ({STOCKS[ticker]}):\n"
        f"Direction: *BUY*\n"
        f"Entry Price: ${price}\n"
        f"Profit Target: {profit}%\n"
        f"Stop Loss: {stop_loss}%"
    )
    # Save user signal
    chat_id = update.effective_chat.id
    USER_STOCK_SIGNALS.setdefault(chat_id, []).append(msg)
    await update.message.reply_markdown(msg)

# Generate crypto signal for specific coin
async def cryptosignal_ticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Please specify a crypto symbol. Example: /cryptosignal BTC")
        return
    coin_symbol = context.args[0].upper()
    coin = next((c for c in CRYPTO_COINS if c['symbol'] == coin_symbol), None)
    if not coin:
        await update.message.reply_text(f"❌ Unknown crypto coin: {coin_symbol}")
        return
    price = get_crypto_price(coin['id'])
    if price is None:
        await update.message.reply_text("⚠️ Could not fetch live price. Try again later.")
        return
    profit = round(random.uniform(5, 20), 2)
    stop_loss = round(random.uniform(2, 5), 2)
    msg = (
        f"📊 Crypto Signal for {coin_symbol}:\n"
        f"Direction: *BUY*\n"
        f"Entry Price: ${price}\n"
        f"Profit Target: {profit}%\n"
        f"Stop Loss: {stop_loss}%"
    )
    # Save user signal
    chat_id = update.effective_chat.id
    USER_CRYPTO_SIGNALS.setdefault(chat_id, []).append(msg)
    await update.message.reply_markdown(msg)

# View all stock signals for user
async def allsignals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    signals = USER_STOCK_SIGNALS.get(chat_id, [])
    if not signals:
        await update.message.reply_text("ℹ️ You have no saved stock signals yet.")
        return
    reply = "📈 *Your Stock Signals:*\n\n" + "\n\n".join(signals)
    await update.message.reply_markdown(reply)

# View all crypto signals for user
async def allcryptosignals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    signals = USER_CRYPTO_SIGNALS.get(chat_id, [])
    if not signals:
        await update.message.reply_text("ℹ️ You have no saved crypto signals yet.")
        return
    reply = "🪙 *Your Crypto Signals:*\n\n" + "\n\n".join(signals)
    await update.message.reply_markdown(reply)

# View upcoming IPOs (alias /ipos)
async def ipos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not IPOS:
        await update.message.reply_text("ℹ️ No upcoming IPOs at the moment.")
        return
    lines = ["📅 *Upcoming IPOs:*"]
    for ticker, info in IPOS.items():
        lines.append(f"- {ticker} ({info['name']}) on {info['date']}")
    await update.message.reply_markdown("\n".join(lines))

# Set user investment style category (short or long)
async def setcategory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /setcategory <short|long>")
        return
    category = context.args[0].lower()
    if category not in ["short", "long"]:
        await update.message.reply_text("⚠️ Invalid category. Choose 'short' or 'long'.")
        return
    chat_id = update.effective_chat.id
    USER_PREFERENCES[chat_id] = {"category": category}
    await update.message.reply_text(f"✅ Investment style set to '{category}'.")

# Stock signals based on user investment style
async def stockcategoriesignal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    pref = USER_PREFERENCES.get(chat_id)
    if not pref:
        await update.message.reply_text("⚠️ You have not set an investment style yet. Use /setcategory.")
        return

    category = pref["category"]
    if not STOCKS:
        await update.message.reply_text("ℹ️ No stocks added yet.")
        return

    # For demo, send bullish signals for 'long', bearish for 'short'
    signals = []
    for ticker, name in STOCKS.items():
        direction = "BUY" if category == "long" else "SELL"
        price = get_stock_price(ticker)
        profit = round(random.uniform(5, 20), 2)
        stop_loss = round(random.uniform(1, 10), 2)
        signal_msg = (
            f"{ticker} ({name}):\n"
            f"Direction: *{direction}*\n"
            f"Entry Price: ${price}\n"
            f"Profit Target: {profit}%\n"
            f"Stop Loss: {stop_loss}%"
        )
        signals.append(signal_msg)
    reply = f"📊 *Stock Signals for {category.title()} term investors:*\n\n" + "\n\n".join(signals)
    # Save signals for user
    USER_STOCK_SIGNALS[chat_id] = signals
    await update.message.reply_markdown(reply)

# View newly added stocks
async def newstocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not NEW_STOCKS:
        await update.message.reply_text("ℹ️ No new stocks added since bot started.")
        return
    await update.message.reply_text("🆕 Newly added stocks:\n" + "\n".join(NEW_STOCKS))

# View newly added cryptos
async def newcryptos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not NEW_CRYPTOS:
        await update.message.reply_text("ℹ️ No new cryptos added since bot started.")
        return
    await update.message.reply_text("🆕 Newly added cryptos:\n" + "\n".join(NEW_CRYPTOS))

# Keep your existing /addstock, /addipo, /investcrypto, /investstock, /followup, /buy, /sell commands here from your original code

# Add your original handlers below
# For brevity, I will just add placeholders here — replace with your original handlers:

async def addstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Usage: /addstock <ticker> <name>")
        return
    ticker = context.args[0].upper()
    name = " ".join(context.args[1:])
    if ticker in STOCKS:
        await update.message.reply_text(f"⚠️ Stock {ticker} already in watchlist.")
        return
    STOCKS[ticker] = name
    NEW_STOCKS.append(f"{ticker} ({name})")
    await update.message.reply_text(f"✅ Stock {ticker} ({name}) added to watchlist.")

async def addipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("⚠️ Usage: /addipo <ticker> <name> <YYYY-MM-DD>")
        return
    ticker = context.args[0].upper()
    name = context.args[1]
    date = context.args[2]
    IPOS[ticker] = {"name": name, "date": date}
    await update.message.reply_text(f"✅ IPO {ticker} ({name}) added for {date}.")

async def investcrypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /investcrypto <coin>")
        return
    coin = context.args[0].upper()
    if not any(c['symbol'] == coin for c in CRYPTO_COINS):
        await update.message.reply_text("❌ Unknown crypto coin.")
        return
    chat_id = update.effective_chat.id
    key = f"crypto:{coin}"
    active_trades[key] = chat_id
    await update.message.reply_text(f"✅ Marked {coin} investment active.")

async def investstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /investstock <ticker>")
        return
    ticker = context.args[0].upper()
    if ticker not in STOCKS:
        await update.message.reply_text("❌ Stock not tracked.")
        return
    chat_id = update.effective_chat.id
    key = f"stock:{ticker}"
    active_trades[key] = chat_id
    await update.message.reply_text(f"✅ Marked {ticker} investment active.")

async def followup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not active_trades:
        await update.message.reply_text("ℹ️ No active trades currently.")
        return
    msg = "📋 *Active Trades:*\n\n"
    for key, chat_id in active_trades.items():
        typ, sym = key.split(":")
        msg += f"- {typ.capitalize()} {sym}, User chat_id: {chat_id}\n"
    await update.message.reply_markdown(msg)

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Simulated Buy order executed.")

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Simulated Sell order executed.")

# === Main setup ===

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(CommandHandler("addstock", addstock))
    app.add_handler(CommandHandler("addipo", addipo))
    app.add_handler(CommandHandler("addcrypto", addcrypto))

    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("cryptosignal", cryptosignal_ticker))
    app.add_handler(CommandHandler("allsignals", allsignals))
    app.add_handler(CommandHandler("allcryptosignals", allcryptosignals))
    app.add_handler(CommandHandler("ipos", ipos_command))

    app.add_handler(CommandHandler("setcategory", setcategory))
    app.add_handler(CommandHandler("stockcategoriesignal", stockcategoriesignal))

    app.add_handler(CommandHandler("newstocks", newstocks))
    app.add_handler(CommandHandler("newcryptos", newcryptos))

    app.add_handler(CommandHandler("investcrypto", investcrypto))
    app.add_handler(CommandHandler("investstock", investstock))

    app.add_handler(CommandHandler("followup", followup))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
