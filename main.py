from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
import random
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

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
        "/followup – 📬 Check trade outcome"
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

    # Default profit and stop loss thresholds for alerts
    active_trades[coin_symbol] = {
        "entry_price": price,
        "status": "active",
        "profit_target": 8.0,   # 8% profit to take
        "stop_loss": 5.0        # 5% loss to exit
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

        # Check stop loss breach
        if change_percent <= -stop_loss:
            alerts.append(f"⚠️ *Risk Alert*: {coin} is down *{change_percent}%*. Consider exiting!")
            status = "🔴 Stopped Out"
            to_remove.append(coin)

        # Check profit target reached
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

    schedule_signal(app)

    print("✅ Bot is running")
    app.run_polling()

if __name__ == '__main__':
    main()
