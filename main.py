import requests
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
import datetime

BOT_TOKEN = "7951346106:AAEws6VRZYcnDCurG1HZpAh-Y4WgA5BQLWI"

WATCHLIST = ['pepe', 'shiba-inu', 'solana']
LONG_TERM = ['bitcoin', 'ethereum', 'solana']

def fetch_top_signal():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": "false"
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        candidates = [coin for coin in data if coin['id'] in WATCHLIST]
        if not candidates:
            return None

        # Sort by % gain in last 24h
        best = sorted(candidates, key=lambda x: x['price_change_percentage_24h'] or 0, reverse=True)[0]

        return {
            "name": best["name"],
            "symbol": best["symbol"].upper(),
            "price": best["current_price"],
            "change": best["price_change_percentage_24h"],
            "market_cap": best["market_cap"],
            "confidence": round(min(max(best["price_change_percentage_24h"] * 3, 60), 95), 2),  # simple confidence model
        }

    except Exception as e:
        print("Error:", e)
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Send /signal to get the top crypto to trade now.")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.datetime.now().time()
    if not (datetime.time(5, 0) <= now <= datetime.time(22, 0)):
        await update.message.reply_text("⏱ Signals are only active between 5am and 10pm.")
        return

    signal = fetch_top_signal()
    if not signal:
        await update.message.reply_text("❌ No strong signals right now.")
        return

    msg = f"""📡 *Signal Alert*

💸 Coin: *{signal['name']}* (`{signal['symbol']}`)
💰 Current Price: `${signal['price']}`
📈 24h Change: `{signal['change']}%`
📊 Confidence: *{signal['confidence']}%*

Set alerts! I'll follow up if it flips trend. ✅
"""
    await update.message.reply_markdown(msg)

async def longterm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coins = ', '.join([name.capitalize() for name in LONG_TERM])
    await update.message.reply_text(f"📦 Long-term holds: {coins}")

async def watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coins = ', '.join([name.capitalize() for name in WATCHLIST])
    await update.message.reply_text(f"🔍 Current watchlist: {coins}")

async def confidence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❓ Usage: /confidence [coin]")
        return

