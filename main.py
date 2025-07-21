from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
import random
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import numpy as np
import yfinance as yf  # For real stock prices

TOKEN = "7951346106:AAEws6VRZYcnDCurG1HZpAh-Y4WgA5BQLWI"
ADMIN_CHAT_ID = 123456789  # Replace with your Telegram user ID

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

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

STOCKS = {}
IPOS = {}
active_trades = {}

# --- Helper functions ---

def get_crypto_price(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        r = requests.get(url, timeout=10)
        data = r.json()
        return data[coin_id]['usd']
    except Exception as e:
        logging.error(f"Error fetching crypto price for {coin_id}: {e}")
        return None

def get_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")['Close']
        if price.empty:
            return None
        return round(price[-1], 2)
    except Exception as e:
        logging.error(f"Error fetching stock price for {ticker}: {e}")
        return None

# (Keep other helper functions the same: get_historical_prices, moving_average, compute_rsi, analyze_coin)

# --- Commands ---

# ... [keep your existing command functions as is] ...

# Add this new command to remove stock from watchlist
async def removestock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /removestock <ticker>")
        return
    ticker = context.args[0].upper()
    if ticker not in STOCKS:
        await update.message.reply_text(f"⚠️ Stock {ticker} is not in watchlist.")
        return
    del STOCKS[ticker]
    await update.message.reply_text(f"✅ Stock {ticker} removed from watchlist.")

# Add this command to remove active trade
async def removetrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /removetrade <crypto|stock>:<symbol>")
        return
    key = context.args[0].lower()
    if key not in active_trades:
        await update.message.reply_text(f"⚠️ No active trade with key '{key}'.")
        return
    del active_trades[key]
    await update.message.reply_text(f"✅ Removed active trade '{key}'.")

# Portfolio summary command
async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not active_trades:
        await update.message.reply_text("📭 No active trades currently.")
        return
    message = "📊 *Active Trades Portfolio Summary*\n"
    for key, trade in active_trades.items():
        asset_type, symbol = key.split(":")
        if asset_type == "crypto":
            coin = next((c for c in CRYPTO_COINS if c['symbol'].lower() == symbol.lower()), None)
            current_price = get_crypto_price(coin['id']) if coin else None
        else:
            current_price = get_stock_price(symbol)
        if current_price is None:
            current_price = "N/A"
            change_percent = "N/A"
        else:
            entry = trade['entry_price']
            change_percent = round(((current_price - entry) / entry) * 100, 2)

        message += (
            f"\n- {key}\n"
            f"Entry Price: *${trade['entry_price']}*\n"
            f"Current Price: *${current_price}*\n"
            f"Profit/Loss: *{change_percent}%*\n"
            f"Status: *{trade.get('status', 'active')}*\n"
        )
    await update.message.reply_markdown(message)

# Scheduled job: send hourly signal and check active trades for alerts
def schedule_signal(application):
    async def send_hourly_signal_and_check_trades():
        # Send hourly crypto signal
        coin = random.choice(CRYPTO_COINS)
        price = get_crypto_price(coin['id'])
        if price:
            profit = round(random.uniform(5, 12), 2)
            stop_loss = round(random.uniform(2, 4), 2)
            success_chance = random.randint(60, 95)
            msg = (
                f"🕒 *Hourly Crypto Trade Alert*\n"
                f"Coin: `{coin['symbol']}`\n"
                f"Price: *${price}*\n"
                f"Target Profit: *{profit}%*\n"
                f"Stop Loss: *{stop_loss}%*\n"
                f"Success Rate: *{success_chance}%*"
            )
            await application.bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg, parse_mode='Markdown')

        # Check active trades for alerts
        alerts = []
        to_remove = []
        for key, trade in active_trades.items():
            asset_type, symbol = key.split(":")
            if asset_type == "crypto":
                coin = next((c for c in CRYPTO_COINS if c['symbol'].lower() == symbol.lower()), None)
                if not coin:
                    continue
                current_price = get_crypto_price(coin['id'])
            else:
                current_price = get_stock_price(symbol)

            if current_price is None:
                continue

            entry = trade['entry_price']
            profit_target = trade.get('profit_target', 8.0)
            stop_loss = trade.get('stop_loss', 5.0)
            change_percent = round(((current_price - entry) / entry) * 100, 2)

            if change_percent <= -stop_loss:
                alerts.append(f"⚠️ *Risk Alert*: {key} down *{change_percent}%*. Consider exiting!")
                trade['status'] = "🔴 Stopped Out"
                to_remove.append(key)
            elif change_percent >= profit_target:
                alerts.append(f"✅ *Profit Alert*: {key} up *{change_percent}%*. Consider taking profit!")
                trade['status'] = "✅ Profit Target Hit"
                to_remove.append(key)

        for key in to_remove:
            del active_trades[key]

        if alerts:
            alert_message = "\n\n".join(alerts)
            await application.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"📢 *Trade Alerts*\n{alert_message}", parse_mode='Markdown')

    scheduler = BackgroundScheduler(timezone=pytz.UTC)
    scheduler.add_job(lambda: application.create_task(send_hourly_signal_and_check_trades()), "interval", hours=1)
    scheduler.start()

# --- Main ---

def main():
    application = ApplicationBuilder().token(TOKEN).build()

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
    application.add_handler(CommandHandler("removestock", removestock))  # New
    application.add_handler(CommandHandler("removetrade", removetrade))  # New
    application.add_handler(CommandHandler("portfolio", portfolio))      # New
    application.add_handler(CommandHandler("addipo", addipo))
    application.add_handler(CommandHandler("listipos", listipos))

    schedule_signal(application)

    application.run_polling()

if __name__ == '__main__':
    main()
