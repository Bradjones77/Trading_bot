import logging
import random
import requests
import sqlite3
import numpy as np
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters

# --- Config ---
TOKEN = "7951346106:AAEws6VRZYcnDCurG1HZpAh-Y4WgA5BQLWI"
ADMIN_CHAT_ID = 123456789  # Put your Telegram user ID here

# --- Logging ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- Database Setup ---
conn = sqlite3.connect('tradebot.db', check_same_thread=False)
cursor = conn.cursor()

# Create tables if not exist
cursor.executescript("""
CREATE TABLE IF NOT EXISTS stocks (
    ticker TEXT PRIMARY KEY,
    name TEXT,
    sector TEXT,
    category TEXT
);

CREATE TABLE IF NOT EXISTS cryptos (
    symbol TEXT PRIMARY KEY,
    name TEXT,
    coingecko_id TEXT,
    sector TEXT,
    category TEXT
);

CREATE TABLE IF NOT EXISTS ipos (
    ticker TEXT PRIMARY KEY,
    name TEXT,
    date TEXT
);

CREATE TABLE IF NOT EXISTS active_trades (
    key TEXT PRIMARY KEY,
    chat_id INTEGER
);

CREATE TABLE IF NOT EXISTS user_preferences (
    chat_id INTEGER PRIMARY KEY,
    investment_style TEXT
);

CREATE TABLE IF NOT EXISTS signals (
    chat_id INTEGER,
    signal_type TEXT,  -- 'stock' or 'crypto'
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sectors (
    sector TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS categories (
    category TEXT PRIMARY KEY
);
""")
conn.commit()

# --- Predefined sectors and categories ---
SECTORS = [
    # Stocks sectors and subcategories
    "Information Technology", "Software", "Semiconductors", "IT Services",
    "Healthcare", "Pharmaceuticals", "Biotechnology", "Medical Devices",
    "Financials", "Banks", "Insurance", "Investment Services",
    "Consumer Discretionary", "Retail", "Automotive", "Hotels & Leisure",
    "Consumer Staples", "Food & Beverage", "Household Products",
    "Energy", "Oil & Gas", "Renewable Energy",
    "Industrials", "Aerospace & Defense", "Transportation", "Construction",
    "Materials", "Chemicals", "Metals & Mining", "Paper & Packaging",
    "Utilities", "Electric Utilities", "Water Utilities",
    "Real Estate", "REITs",
    "Communication Services", "Media", "Telecom",
    # Thematic or Emerging Categories
    "Artificial Intelligence (AI)", "Technology", "Green Energy / Clean Tech",
    "E-commerce", "Cybersecurity", "Blockchain / Crypto", "Metaverse",
    "Space / Aerospace", "Biotech / Genomics", "ESG (Environmental, Social, Governance)"
]

# Insert sectors into DB (ignore duplicates)
for sector in SECTORS:
    cursor.execute("INSERT OR IGNORE INTO sectors(sector) VALUES (?)", (sector,))
conn.commit()

# --- Helper Functions ---

def db_add_stock(ticker, name, sector=None, category=None):
    cursor.execute(
        "INSERT OR IGNORE INTO stocks(ticker, name, sector, category) VALUES (?, ?, ?, ?)",
        (ticker, name, sector, category)
    )
    conn.commit()

def db_add_crypto(symbol, name, coingecko_id, sector=None, category=None):
    cursor.execute(
        "INSERT OR IGNORE INTO cryptos(symbol, name, coingecko_id, sector, category) VALUES (?, ?, ?, ?, ?)",
        (symbol, name, coingecko_id, sector, category)
    )
    conn.commit()

def db_get_stocks_by_sector(sector):
    cursor.execute("SELECT ticker, name FROM stocks WHERE sector = ?", (sector,))
    return cursor.fetchall()

def db_get_cryptos_by_sector(sector):
    cursor.execute("SELECT symbol, name FROM cryptos WHERE sector = ?", (sector,))
    return cursor.fetchall()

def db_add_ipo(ticker, name, date):
    cursor.execute("INSERT OR IGNORE INTO ipos(ticker, name, date) VALUES (?, ?, ?)", (ticker, name, date))
    conn.commit()

def db_get_ipos():
    cursor.execute("SELECT ticker, name, date FROM ipos")
    return cursor.fetchall()

def db_set_preference(chat_id, style):
    cursor.execute("INSERT OR REPLACE INTO user_preferences(chat_id, investment_style) VALUES (?, ?)", (chat_id, style))
    conn.commit()

def db_get_preference(chat_id):
    cursor.execute("SELECT investment_style FROM user_preferences WHERE chat_id = ?", (chat_id,))
    res = cursor.fetchone()
    return res[0] if res else None

def db_add_active_trade(key, chat_id):
    cursor.execute("INSERT OR REPLACE INTO active_trades(key, chat_id) VALUES (?, ?)", (key, chat_id))
    conn.commit()

def db_get_active_trades():
    cursor.execute("SELECT key, chat_id FROM active_trades")
    return cursor.fetchall()

def db_remove_active_trade(key):
    cursor.execute("DELETE FROM active_trades WHERE key = ?", (key,))
    conn.commit()

def db_add_signal(chat_id, signal_type, message):
    cursor.execute("INSERT INTO signals(chat_id, signal_type, message) VALUES (?, ?, ?)", (chat_id, signal_type, message))
    conn.commit()

def db_get_signals(chat_id, signal_type):
    cursor.execute("SELECT message FROM signals WHERE chat_id = ? AND signal_type = ?", (chat_id, signal_type))
    return [row[0] for row in cursor.fetchall()]

# --- Price APIs ---

def get_crypto_price(coingecko_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coingecko_id}&vs_currencies=usd"
        r = requests.get(url, timeout=10)
        data = r.json()
        return data[coingecko_id]['usd']
    except Exception:
        return None

def get_stock_price(ticker):
    # Implement real API or use mock random price for now
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

# --- Meme Coins Dynamic Load ---
def fetch_meme_coins():
    try:
        url = "https://api.coingecko.com/api/v3/coins/list"
        r = requests.get(url)
        all_coins = r.json()
        meme_coins = []
        for coin in all_coins:
            # Basic filter: name or symbol contains common meme coin keywords (like doge, shiba, pepe, floki, bonk, etc.)
            if any(k in coin['id'] for k in ['doge', 'shiba', 'pepe', 'floki', 'bonk', 'meme']):
                meme_coins.append(coin)
        return meme_coins
    except Exception as e:
        logging.warning(f"Failed to fetch meme coins: {e}")
        return []

def populate_meme_coins():
    meme_coins = fetch_meme_coins()
    for coin in meme_coins:
        db_add_crypto(
            symbol=coin['symbol'].upper(),
            name=coin['name'],
            coingecko_id=coin['id'],
            sector="Blockchain / Crypto",
            category="Meme Coin"
        )
    logging.info(f"Populated {len(meme_coins)} meme coins")

# --- Telegram Commands ---

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
        "/addstock <ticker> <name> [sector] [category] — Add a stock\n"
        "/addcrypto <symbol> <name> <coingecko_id> [sector] [category] — Add a crypto\n"
        "/addipo <ticker> <name> <YYYY-MM-DD> — Add a new IPO\n\n"
        "/signal <ticker> — Generate stock signal\n"
        "/cryptosignal <symbol> — Generate crypto signal\n"
        "/allsignals — View your stock signals\n"
        "/allcryptosignals — View your crypto signals\n"
        "/ipos — View upcoming IPOs\n\n"
        "/setcategory <short|long> — Set your investment style\n"
        "/stockcategoriesignal — Stock signals based on your style\n\n"
        "/newstocks — Show newly added stocks\n"
        "/newcryptos — Show newly added cryptos\n\n"
        "/listsectors — List all sectors\n"
        "/liststocks <sector> — List stocks in sector\n"
        "/listcryptos <sector> — List cryptos in sector\n\n"
        "/investcrypto <symbol> — Mark crypto investment active\n"
        "/investstock <ticker> — Mark stock investment active\n"
        "/followup — List active trades\n"
        "/buy — Simulate buy order\n"
        "/sell — Simulate sell order\n"
    )
    await update.message.reply_markdown(help_text)

async def addstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Usage: /addstock <ticker> <name> [sector] [category]")
        return
    ticker = context.args[0].upper()
    name = context.args[1]
    sector = context.args[2] if len(context.args) > 2 else None
    category = context.args[3] if len(context.args) > 3 else None
    db_add_stock(ticker, name, sector, category)
    await update.message.reply_text(f"✅ Stock {ticker} ({name}) added with sector '{sector}' and category '{category}'.")

async def addcrypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("⚠️ Usage: /addcrypto <symbol> <name> <coingecko_id> [sector] [category]")
        return
    symbol = context.args[0].upper()
    name = context.args[1]
    coingecko_id = context.args[2]
    sector = context.args[3] if len(context.args) > 3 else None
    category = context.args[4] if len(context.args) > 4 else None
    db_add_crypto(symbol, name, coingecko_id, sector, category)
    await update.message.reply_text(f"✅ Crypto {symbol} ({name}) added with sector '{sector}' and category '{category}'.")

async def addipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("⚠️ Usage: /addipo <ticker> <name> <YYYY-MM-DD>")
        return
    ticker = context.args[0].upper()
    name = context.args[1]
    date = context.args[2]
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        await update.message.reply_text("⚠️ Date format must be YYYY-MM-DD")
        return
    db_add_ipo(ticker, name, date)
    await update.message.reply_text(f"✅ IPO {ticker} ({name}) added for {date}")

async def ipos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ipos = db_get_ipos()
    if not ipos:
        await update.message.reply_text("No IPOs found.")
        return
    text = "Upcoming IPOs:\n\n"
    for ticker, name, date in ipos:
        text += f"{ticker} ({name}) — {date}\n"
    await update.message.reply_text(text)

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /signal <ticker>")
        return
    ticker = context.args[0].upper()
    price = get_stock_price(ticker)
    if price is None:
        await update.message.reply_text(f"Could not get price for {ticker}")
        return
    # Dummy signal logic for stocks: random signal
    signal_msg = f"Signal for {ticker}:\nCurrent Price: ${price}\n"
    signal_msg += random.choice([
        "Buy signal: Strong momentum 📈",
        "Sell signal: Overbought 🚨",
        "Hold signal: Wait for confirmation ⏳"
    ])
    db_add_signal(update.message.chat_id, 'stock', signal_msg)
    await update.message.reply_text(signal_msg)

async def cryptosignal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /cryptosignal <symbol>")
        return
    symbol = context.args[0].upper()
    cursor.execute("SELECT coingecko_id FROM cryptos WHERE symbol = ?", (symbol,))
    res = cursor.fetchone()
    if not res:
        await update.message.reply_text(f"Crypto {symbol} not found.")
        return
    coin_id = res[0]
    price = get_crypto_price(coin_id)
    if price is None:
        await update.message.reply_text(f"Could not fetch price for {symbol}")
        return
    signals = analyze_coin(coin_id)
    if not signals:
        await update.message.reply_text("Not enough data for analysis.")
        return
    msg = f"Crypto Signal for {symbol}:\nPrice: ${price:.4f}\n\n" + "\n".join(signals)
    db_add_signal(update.message.chat_id, 'crypto', msg)
    await update.message.reply_text(msg)

async def allsignals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    signals = db_get_signals(chat_id, 'stock')
    if not signals:
        await update.message.reply_text("No stock signals found.")
        return
    msg = "Your Stock Signals:\n\n" + "\n\n".join(signals)
    await update.message.reply_text(msg)

async def allcryptosignals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    signals = db_get_signals(chat_id, 'crypto')
    if not signals:
        await update.message.reply_text("No crypto signals found.")
        return
    msg = "Your Crypto Signals:\n\n" + "\n\n".join(signals)
    await update.message.reply_text(msg)

async def setcategory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or context.args[0].lower() not in ['short', 'long']:
        await update.message.reply_text("⚠️ Usage: /setcategory <short|long>")
        return
    style = context.args[0].lower()
    db_set_preference(update.message.chat_id, style)
    await update.message.reply_text(f"Your investment style is set to: {style}")

async def stockcategoriesignal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    style = db_get_preference(update.message.chat_id)
    if not style:
        await update.message.reply_text("Please set your investment style first using /setcategory <short|long>")
        return
    # Dummy implementation: Fetch 2 random stocks from DB matching sector or category for style
    # For simplicity, just pick any 2
    cursor.execute("SELECT ticker, name FROM stocks ORDER BY RANDOM() LIMIT 2")
    stocks = cursor.fetchall()
    if not stocks:
        await update.message.reply_text("No stocks available.")
        return
    msg = f"Stock signals for your '{style}' investment style:\n"
    for ticker, name in stocks:
        price = get_stock_price(ticker)
        signal = random.choice(["Buy 📈", "Sell 📉", "Hold ⏳"])
        msg += f"{ticker} ({name}): Price ${price} — Signal: {signal}\n"
    await update.message.reply_text(msg)

async def newstocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT ticker, name FROM stocks ORDER BY rowid DESC LIMIT 5")
    stocks = cursor.fetchall()
    if not stocks:
        await update.message.reply_text("No stocks found.")
        return
    msg = "Recently Added Stocks:\n"
    for ticker, name in stocks:
        msg += f"{ticker} — {name}\n"
    await update.message.reply_text(msg)

async def newcryptos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT symbol, name FROM cryptos ORDER BY rowid DESC LIMIT 5")
    cryptos = cursor.fetchall()
    if not cryptos:
        await update.message.reply_text("No cryptos found.")
        return
    msg = "Recently Added Cryptos:\n"
    for symbol, name in cryptos:
        msg += f"{symbol} — {name}\n"
    await update.message.reply_text(msg)

async def listsectors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT sector FROM sectors ORDER BY sector")
    sectors = cursor.fetchall()
    msg = "Sectors:\n" + "\n".join(s[0] for s in sectors)
    await update.message.reply_text(msg)

async def liststocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /liststocks <sector>")
        return
    sector = " ".join(context.args)
    stocks = db_get_stocks_by_sector(sector)
    if not stocks:
        await update.message.reply_text(f"No stocks found in sector '{sector}'.")
        return
    msg = f"Stocks in sector '{sector}':\n"
    for ticker, name in stocks:
        msg += f"{ticker} — {name}\n"
    await update.message.reply_text(msg)

async def listcryptos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /listcryptos <sector>")
        return
    sector = " ".join(context.args)
    cryptos = db_get_cryptos_by_sector(sector)
    if not cryptos:
        await update.message.reply_text(f"No cryptos found in sector '{sector}'.")
        return
    msg = f"Cryptos in sector '{sector}':\n"
    for symbol, name in cryptos:
        msg += f"{symbol} — {name}\n"
    await update.message.reply_text(msg)

# Active trades commands

async def investcrypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /investcrypto <symbol>")
        return
    symbol = context.args[0].upper()
    db_add_active_trade(f"crypto:{symbol}", update.message.chat_id)
    await update.message.reply_text(f"Active crypto investment: {symbol}")

async def investstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /investstock <ticker>")
        return
    ticker = context.args[0].upper()
    db_add_active_trade(f"stock:{ticker}", update.message.chat_id)
    await update.message.reply_text(f"Active stock investment: {ticker}")

async def followup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    trades = db_get_active_trades()
    if not trades:
        await update.message.reply_text("No active trades.")
        return
    msg = "Active Trades:\n"
    for key, chat_id in trades:
        msg += f"{key} (chat_id {chat_id})\n"
    await update.message.reply_text(msg)

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Buy order executed (simulated).")

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sell order executed (simulated).")

# Admin-only commands decorator
def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.message.from_user.id
        if user_id != ADMIN_CHAT_ID:
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        await func(update, context)
    return wrapper

@admin_only
async def clear_signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("DELETE FROM signals")
    conn.commit()
    await update.message.reply_text("All signals cleared.")

# Scheduled Notifications

async def scheduled_signal_notifications(app):
    trades = db_get_active_trades()
    for key, chat_id in trades:
        typ, symbol = key.split(":")
        if typ == 'stock':
            price = get_stock_price(symbol)
            signal_msg = f"Scheduled Signal for stock {symbol}:\nPrice: ${price}\n"
            signal_msg += random.choice([
                "Buy signal: Strong momentum 📈",
                "Sell signal: Overbought 🚨",
                "Hold signal: Wait for confirmation ⏳"
            ])
        elif typ == 'crypto':
            cursor.execute("SELECT coingecko_id FROM cryptos WHERE symbol = ?", (symbol,))
            res = cursor.fetchone()
            if not res:
                continue
            coin_id = res[0]
            price = get_crypto_price(coin_id)
            signals = analyze_coin(coin_id)
            if not signals:
                continue
            signal_msg = f"Scheduled Signal for crypto {symbol}:\nPrice: ${price}\n" + "\n".join(signals)
        else:
            continue
        try:
            await app.bot.send_message(chat_id=chat_id, text=signal_msg)
        except Exception as e:
            logging.error(f"Error sending scheduled notification to {chat_id}: {e}")

# --- Main ---

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("addstock", addstock))
    app.add_handler(CommandHandler("addcrypto", addcrypto))
    app.add_handler(CommandHandler("addipo", addipo))
    app.add_handler(CommandHandler("ipos", ipos))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("cryptosignal", cryptosignal))
    app.add_handler(CommandHandler("allsignals", allsignals))
    app.add_handler(CommandHandler("allcryptosignals", allcryptosignals))
    app.add_handler(CommandHandler("setcategory", setcategory))
    app.add_handler(CommandHandler("stockcategoriesignal", stockcategoriesignal))
    app.add_handler(CommandHandler("newstocks", newstocks))
    app.add_handler(CommandHandler("newcryptos", newcryptos))
    app.add_handler(CommandHandler("listsectors", listsectors))
    app.add_handler(CommandHandler("liststocks", liststocks))
    app.add_handler(CommandHandler("listcryptos", listcryptos))
    app.add_handler(CommandHandler("investcrypto", investcrypto))
    app.add_handler(CommandHandler("investstock", investstock))
    app.add_handler(CommandHandler("followup", followup))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))
    app.add_handler(CommandHandler("clearsignals", clear_signals))

    # Populate meme coins at startup
    populate_meme_coins()

    # Schedule periodic notifications every 30 minutes
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: app.create_task(scheduled_signal_notifications(app)), 'interval', minutes=30)
    scheduler.start()

    print("Bot started...")
    app.run_polling()

if __name__ == '__main__':
    main()
