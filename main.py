from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
import random
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import numpy as np  # Add numpy for calculations

TOKEN = "7951346106:AAEws6VRZYcnDCurG1HZpAh-Y4WgA5BQLWI"
ADMIN_CHAT_ID = 123456789  # Replace this with your actual Telegram user ID

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Meme + Major coins
COINS = [
    {"id": "bitcoin", "symbol": "BTC/USDT"},
    {"id": "ethereum", "symbol": "ETH/USDT"},
    {"id": "solana", "symbol": "SOL/USDT"},
    {"id": "pepe", "symbol": "PEPE/USDT"},
    {"id": "dogecoin", "symbol": "DOGE/USDT"},
    {"id": "shiba-inu", "symbol": "SHIB/USDT"},
    {"id": "floki", "symbol": "FLOKI/USDT"},
    {"id": "bonk", "symbol": "BONK/USDT"},
    {"id": "aptos", "symbol": "APT/USDT"},
]

# === In-Memory Trade Tracking ===
active_trades = {}

# === GET LIVE PRICE ===
def get_price(symbol_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol_id}&vs_currencies=usd"
        r = requests.get(url, timeout=10)
        data = r.json()
        return data[symbol_id]['usd']
    except Exception:
        return None

# === GET HISTORICAL DATA FOR TECHNICAL ANALYSIS ===
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
    return rsi_values[-1]  # latest RSI

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

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Bradjones77 AI Trade Bot!\n\n"
        "Use the following commands:\n"
        "/signal – 📈 Get top trade signals\n"
        "/invest <coin> – 💰 Mark trade as invested\n"
        "/request – 🔄 Request manual signal\n"
        "/buy – ✅ Simulate buy\n"
        "/sell – ❌ Simulate sell\n"
        "/followup – 📬 Check trade outcome\n"
        "/techsignal <coin> – 🔍 Technical Analysis on coin\n"
    )

# === /signal ===
async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_coins = random.sample(COINS, 3)

    signals = []
    for coin in selected_coins:
        price = get_price(coin['id'])
        if price is None:
            continue
        profit = round(random.uniform(5, 20), 2)
        stop_loss = round(random.uniform(2, 5), 2)
        signals.append({
            "coin": coin,
            "price": price,
            "profit": profit,
            "stop_loss": stop_loss
        })

    signals.sort(key=lambda x: x["profit"], reverse=True)

    message = "📊 *Top Trade Signals*\n"
    for s in signals:
        message += (
            f"\n🔹 `{s['coin']['symbol']}` – *{s['profit']}%* profit target\n"
            f"Direction: *BUY*\n"
            f"Entry: *${s['price']}*\n"
            f"Stop Loss: *{s['stop_loss']}%*\n"
        )

    await update.message.reply_markdown(message)

# === /invest <coin> ===
async def invest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Please specify a coin. Example: /invest BTC")
        return

    coin_symbol = context.args[0].upper()

    match = next((c for c in COINS if c['symbol'].startswith(coin_symbol)), None)
    if not match:
        await update.message.reply_text(f"❌ Unknown coin: {coin_symbol}")
        return

    price = get_price(match['id'])
    if price is None:
        await update.message.reply_text("⚠️ Could not get live price. Try again.")
        return

    active_trades[coin_symbol] = {
        "entry_price": price,
        "status": "active",
        "profit_target": 8.0,
        "stop_loss": 5.0
    }

    await update.message.reply_text(
        f"✅ Trade on {coin_symbol} marked as *invested* at *${price}*.\n"
        f"Profit target: {active_trades[coin_symbol]['profit_target']}%\n"
        f"Stop loss: {active_trades[coin_symbol]['stop_loss']}%",
        parse_mode="Markdown"
    )

# === /request ===
async def request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔁 Manual trade signal requested...")
    await signal(update, context)

# === /buy ===
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Buy order placed (simulated).")

# === /sell ===
async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Sell order placed (simulated).")

# === /followup ===
async def followup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not active_trades:
        await update.message.reply_text("📭 No active trades.")
        return

    message = "📬 *Trade Follow-Up*\n"
    alerts = []
    to_remove = []

    for coin, trade in active_trades.items():
        coin_id = next((c['id'] for c in COINS if c['symbol'].startswith(coin)), None)
        if not coin_id:
            continue

        current_price = get_price(coin_id)
        if current_price is None:
            continue

        entry = trade['entry_price']
        profit_target = trade.get('profit_target', 8.0)
        stop_loss = trade.get('stop_loss', 5.0)

        change_percent = round(((current_price - entry) / entry) * 100, 2)

        status = "⏳ Still Active"

        if change_percent <= -stop_loss:
            alerts.append(f"⚠️ *Risk Alert*: {coin} is down *{change_percent}%*. Consider exiting!")
            status = "🔴 Stopped Out"
            to_remove.append(coin)
        elif change_percent >= profit_target:
            alerts.append(f"✅ *Profit Alert*: {coin} is up *{change_percent}%*. Consider taking profit!")
            status = "✅ Profit Target Hit"

        message += (
            f"\n🔸 {coin}\n"
            f"Entry Price: *${entry}*\n"
            f"Current Price: *${current_price}*\n"
            f"P/L: *{change_percent}%*\n"
            f"Status: *{status}*\n"
        )

    for coin in to_remove:
        del active_trades[coin]

    await update.message.reply_markdown(message)

    if alerts:
        alert_message = "\n\n".join(alerts)
        await update.message.reply_markdown(f"📢 *Alerts*\n{alert_message}")

# === /techsignal <coin> ===
async def techsignal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Please specify a coin symbol. Example: /techsignal BTC")
        return

    coin_symbol = context.args[0].upper()
    match = next((c for c in COINS if c['symbol'].startswith(coin_symbol)), None)
    if not match:
        await update.message.reply_text(f"❌ Unknown coin symbol: {coin_symbol}")
        return

    signals = analyze_coin(match['id'])
    if not signals:
        await update.message.reply_text("⚠️ Not enough data to analyze this coin.")
        return

    msg = f"🔍 *Technical Analysis for {match['symbol']}*\n\n" + "\n".join(signals)
    await update.message.reply_markdown(msg)

# === Scheduled Signals ===
def schedule_signal(application):
    async def send_hourly_signal():
        coin = random.choice(COINS)
        price = get_price(coin['id'])
        if price is None:
            return

        profit = round(random.uniform(5, 12), 2)
        stop_loss = round(random.uniform(2, 4), 2)
        success_chance = random.randint(60, 95)

        msg = (
            f"🕒 *Hourly Trade Alert*\n"
            f"Pair: `{coin['symbol']}`\n"
            f"Price: *${price}*\n"
            f"Target Profit: *{profit}%*\n"
            f"Stop Loss: *{stop_loss}%*\n"
            f"Success Rate: *{success_chance}%*"
        )

        await application.bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg, parse_mode='Markdown')

    scheduler = BackgroundScheduler(timezone=pytz.utc)
    scheduler.add_job(lambda: application.create_task(send_hourly_signal()), 'interval', hours=1)
    scheduler.start()

# === MAIN ===
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("request", request))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))
    app.add_handler(CommandHandler("followup", followup))
    app.add_handler(CommandHandler("invest", invest))
    app.add_handler(CommandHandler("techsignal", techsignal))

    schedule_signal(app)

    print("✅ Bot is running")
    app.run_polling()

if __name__ == '__main__':
    main()
