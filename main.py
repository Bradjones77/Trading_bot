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

# Crypto coins
CRYPTO_COINS = [
    {"id": "bitcoin", "symbol": "BTC"},
    {"id": "ethereum", "symbol": "ETH"},
    {"id": "solana", "symbol": "SOL"},
    {"id": "pepe", "symbol": "PEPE"},
    {"id": "dogecoin", "symbol": "DOGE"},
    {"id": "shiba-inu", "symbol": "SHIB"},
    {"id": "floki", "symbol": "FLOKI"},
    {"id": "bonk", "symbol": "BONK"},
    {"id": "aptos", "symbol": "APT"},
]

# Stock watchlist (start empty, can add)
STOCKS = {}

# IPO list: ticker -> {"name": str, "date": str}
IPOS = {}

# Active trades: key format "crypto:<symbol>" or "stock:<ticker>"
active_trades = {}

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
    # For now return random price to simulate
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
        "/cryptosignal — Get crypto trade signals\n"
        "/stocksignal — Get stock trade signals\n"
        "/investcrypto <coin> — Mark crypto investment\n"
        "/investstock <ticker> — Mark stock investment\n"
        "/techcryptosignal <coin> — Crypto technical analysis\n"
        "/techstocksignal <ticker> — Stock technical analysis\n"
        "/followup — Check all active trades\n"
        "/buy — Simulate buy order\n"
        "/sell — Simulate sell order\n"
        "/addstock <ticker> <name> — Add new stock to watchlist\n"
        "/liststocks — List all stocks tracked\n"
        "/addipo <ticker> <name> <YYYY-MM-DD> — Add upcoming IPO\n"
        "/listipos — List upcoming IPOs\n"
    )
    await update.message.reply_markdown(help_text)

# Crypto signals
async def cryptosignal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected = random.sample(CRYPTO_COINS, min(3, len(CRYPTO_COINS)))
    message = "📊 *Top Crypto Trade Signals*\n"
    for coin in selected:
        price = get_crypto_price(coin['id'])
        if price is None:
            continue
        profit = round(random.uniform(5, 20), 2)
        stop_loss = round(random.uniform(2, 5), 2)
        message += (
            f"\n🔹 {coin['symbol']} – *{profit}%* profit target\n"
            f"Direction: *BUY*\n"
            f"Entry: *${price}*\n"
            f"Stop Loss: *{stop_loss}%*\n"
        )
    await update.message.reply_markdown(message)

# Stock signals (simulated)
async def stocksignal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not STOCKS:
        await update.message.reply_text("⚠️ No stocks tracked yet. Add with /addstock")
        return

    selected = random.sample(list(STOCKS.items()), min(3, len(STOCKS)))
    message = "📊 *Top Stock Trade Signals*\n"
    for ticker, name in selected:
        price = get_stock_price(ticker)
        profit = round(random.uniform(3, 15), 2)
        stop_loss = round(random.uniform(1, 5), 2)
        message += (
            f"\n🔹 {ticker} ({name}) – *{profit}%* profit target\n"
            f"Direction: *BUY*\n"
            f"Entry: *${price}*\n"
            f"Stop Loss: *{stop_loss}%*\n"
        )
    await update.message.reply_markdown(message)

# Invest in crypto
async def investcrypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Please specify a crypto coin. Example: /investcrypto BTC")
        return
    coin_symbol = context.args[0].upper()
    match = next((c for c in CRYPTO_COINS if c['symbol'] == coin_symbol), None)
    if not match:
        await update.message.reply_text(f"❌ Unknown crypto coin: {coin_symbol}")
        return
    price = get_crypto_price(match['id'])
    if price is None:
        await update.message.reply_text("⚠️ Could not fetch live price. Try again later.")
        return
    key = f"crypto:{coin_symbol}"
    active_trades[key] = {
        "entry_price": price,
        "status": "active",
        "profit_target": 8.0,
        "stop_loss": 5.0
    }
    await update.message.reply_markdown(
        f"✅ Crypto {coin_symbol} marked as invested at *${price}*.\n"
        f"Profit target: {active_trades[key]['profit_target']}%\n"
        f"Stop loss: {active_trades[key]['stop_loss']}%"
    )

# Invest in stock
async def investstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Please specify a stock ticker. Example: /investstock AAPL")
        return
    ticker = context.args[0].upper()
    if ticker not in STOCKS:
        await update.message.reply_text(f"❌ Stock {ticker} is not in watchlist. Add it first with /addstock.")
        return
    price = get_stock_price(ticker)
    key = f"stock:{ticker}"
    active_trades[key] = {
        "entry_price": price,
        "status": "active",
        "profit_target": 8.0,
        "stop_loss": 5.0
    }
    await update.message.reply_markdown(
        f"✅ Stock {ticker} marked as invested at *${price}*.\n"
        f"Profit target: {active_trades[key]['profit_target']}%\n"
        f"Stop loss: {active_trades[key]['stop_loss']}%"
    )

# Technical analysis crypto
async def techcryptosignal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Specify crypto coin. Example: /techcryptosignal BTC")
        return
    coin_symbol = context.args[0].upper()
    match = next((c for c in CRYPTO_COINS if c['symbol'] == coin_symbol), None)
    if not match:
        await update.message.reply_text(f"❌ Unknown crypto coin: {coin_symbol}")
        return
    signals = analyze_coin(match['id'])
    if not signals:
        await update.message.reply_text("⚠️ Not enough data for analysis.")
        return
    msg = f"🔍 *Technical Analysis for {coin_symbol}*\n\n" + "\n".join(signals)
    await update.message.reply_markdown(msg)

# Technical analysis stocks (simulate)
async def techstocksignal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Specify stock ticker. Example: /techstocksignal AAPL")
        return
    ticker = context.args[0].upper()
    if ticker not in STOCKS:
        await update.message.reply_text(f"❌ Stock {ticker} not tracked. Add it with /addstock.")
        return
    # Simulated signals
    signals = [
        "📈 Moving Average crossover (simulated)",
        "⚠️ RSI neutral (simulated)",
        "🔊 Volume steady (simulated)"
    ]
    msg = f"🔍 *Technical Analysis for {ticker}*\n\n" + "\n".join(signals)
    await update.message.reply_markdown(msg)

# Follow up on active trades (both stocks and cryptos)
async def followup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not active_trades:
        await update.message.reply_text("📭 No active trades at the moment.")
        return
    message = "📬 *Trade Follow-Up*\n"
    alerts = []
    to_remove = []
    for key, trade in active_trades.items():
        asset_type, symbol = key.split(":")
        if asset_type == "crypto":
            coin = next((c for c in CRYPTO_COINS if c['symbol'] == symbol), None)
            if not coin:
                continue
            current_price = get_crypto_price(coin['id'])
        else:
            if symbol not in STOCKS:
                continue
            current_price = get_stock_price(symbol)
        if current_price is None:
            continue

        entry = trade['entry_price']
        profit_target = trade.get('profit_target', 8.0)
        stop_loss = trade.get('stop_loss', 5.0)
        change_percent = round(((current_price - entry) / entry) * 100, 2)
        status = "⏳ Still Active"

        if change_percent <= -stop_loss:
            alerts.append(f"⚠️ *Risk Alert*: {symbol} down *{change_percent}%*. Consider exiting!")
            status = "🔴 Stopped Out"
            to_remove.append(key)
        elif change_percent >= profit_target:
            alerts.append(f"✅ *Profit Alert*: {symbol} up *{change_percent}%*. Time to consider taking profit!")
            status = "🟢 Profit Hit"
            to_remove.append(key)

        message += f"\n🔹 {symbol} | Entry: ${entry} | Current: ${current_price} | Change: {change_percent}% | Status: {status}"

    if alerts:
        message += "\n\n" + "\n".join(alerts)
    else:
        message += "\n\nNo alerts at this time."

    # Remove stopped trades
    for key in to_remove:
        del active_trades[key]

    await update.message.reply_markdown(message)

# Buy simulation
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛒 Buy order placed (simulation).")

# Sell simulation
async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 Sell order placed (simulation).")

# Add stock to watchlist
async def addstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Usage: /addstock <ticker> <name>")
        return
    ticker = context.args[0].upper()
    name = " ".join(context.args[1:])
    STOCKS[ticker] = name
    await update.message.reply_text(f"✅ Stock {ticker} ({name}) added to watchlist.")

# List stocks tracked
async def liststocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not STOCKS:
        await update.message.reply_text("No stocks tracked yet.")
        return
    message = "📋 *Tracked Stocks*\n"
    for ticker, name in STOCKS.items():
        message += f"\n- {ticker}: {name}"
    await update.message.reply_markdown(message)

# Add IPO
async def addipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("⚠️ Usage: /addipo <ticker> <name> <YYYY-MM-DD>")
        return
    ticker = context.args[0].upper()
    name = context.args[1]
    date = context.args[2]
    IPOS[ticker] = {"name": name, "date": date}
    await update.message.reply_text(f"✅ IPO {ticker} ({name}) added for {date}.")

# List IPOs
async def listipos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not IPOS:
        await update.message.reply_text("No upcoming IPOs.")
        return
    message = "📅 *Upcoming IPOs*\n"
    for ticker, data in IPOS.items():
        message += f"\n- {ticker}: {data['name']} on {data['date']}"
    await update.message.reply_markdown(message)

# Scheduled jobs

async def send_hourly_crypto_signal(context: ContextTypes.DEFAULT_TYPE):
    chat_id = ADMIN_CHAT_ID
    selected = random.sample(CRYPTO_COINS, min(2, len(CRYPTO_COINS)))
    message = "⏰ *Hourly Crypto Signal*\n"
    for coin in selected:
        price = get_crypto_price(coin['id'])
        if price is None:
            continue
        profit = round(random.uniform(5, 15), 2)
        stop_loss = round(random.uniform(2, 5), 2)
        message += (
            f"\n🔹 {coin['symbol']} – *{profit}%* profit target\n"
            f"Direction: *BUY*\n"
            f"Entry: *${price}*\n"
            f"Stop Loss: *{stop_loss}%*\n"
        )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

async def scheduled_followup(context: ContextTypes.DEFAULT_TYPE):
    chat_id = ADMIN_CHAT_ID
    if not active_trades:
        await context.bot.send_message(chat_id=chat_id, text="📭 No active trades for follow-up.")
        return

    message = "⏳ *Scheduled Trade Follow-Up*\n"
    alerts = []
    to_remove = []

    for key, trade in active_trades.items():
        asset_type, symbol = key.split(":")
        if asset_type == "crypto":
            coin = next((c for c in CRYPTO_COINS if c['symbol'] == symbol), None)
            if not coin:
                continue
            current_price = get_crypto_price(coin['id'])
        else:
            if symbol not in STOCKS:
                continue
            current_price = get_stock_price(symbol)
        if current_price is None:
            continue

        entry = trade['entry_price']
        profit_target = trade.get('profit_target', 8.0)
        stop_loss = trade.get('stop_loss', 5.0)
        change_percent = round(((current_price - entry) / entry) * 100, 2)
        status = "⏳ Active"

        if change_percent <= -stop_loss:
            alerts.append(f"⚠️ *Risk Alert*: {symbol} down *{change_percent}%* - consider exiting.")
            status = "🔴 Stopped Out"
            to_remove.append(key)
        elif change_percent >= profit_target:
            alerts.append(f"✅ *Profit Alert*: {symbol} up *{change_percent}%* - consider taking profit.")
            status = "🟢 Profit Hit"
            to_remove.append(key)

        message += f"\n- {symbol} | Entry: ${entry} | Current: ${current_price} | Change: {change_percent}% | Status: {status}"

    if alerts:
        message += "\n\n" + "\n".join(alerts)
    else:
        message += "\n\nNo alerts at this time."

    # Remove stopped trades
    for key in to_remove:
        del active_trades[key]

    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

# === Main ===

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cryptosignal", cryptosignal))
    application.add_handler(CommandHandler("stocksignal", stocksignal))
    application.add_handler(CommandHandler("investcrypto", investcrypto))
    application.add_handler(CommandHandler("investstock", investstock))
    application.add_handler(CommandHandler("techcryptosignal", techcryptosignal))
    application.add_handler(CommandHandler("techstocksignal", techstocksignal))
    application.add_handler(CommandHandler("followup", followup))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("sell", sell))
    application.add_handler(CommandHandler("addstock", addstock))
    application.add_handler(CommandHandler("liststocks", liststocks))
    application.add_handler(CommandHandler("addipo", addipo))
    application.add_handler(CommandHandler("listipos", listipos))

    # Setup APScheduler to run scheduled jobs (hourly)
    scheduler = BackgroundScheduler(timezone=pytz.UTC)
    scheduler.add_job(lambda: application.create_task(send_hourly_crypto_signal(application.bot)), 'cron', minute=0)
    scheduler.add_job(lambda: application.create_task(scheduled_followup(application.bot)), 'cron', minute=5)
    scheduler.start()

    application.run_polling()

if __name__ == "__main__":
    main()
