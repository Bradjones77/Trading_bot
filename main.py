from flask import Flask
import yfinance as yf
import ccxt
import pandas as pd

app = Flask(__name__)

# --- STOCKS SECTION ---

stock_list = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA"]

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
    return f"📈 Best performing stock today: {top} (+{round(best*100,2)}%)"

def get_long_term_pick():
    # Placeholder for long-term logic
    return "📊 Long-term stock pick: AAPL (Strong earnings, reliable growth)"

def get_short_term_pick():
    return "💥 Short-term trade idea: NVDA (High momentum, near breakout zone)"

# --- CRYPTO SECTION ---

exchange = ccxt.binance()
crypto_list = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "DOGE/USDT", "PEPE/USDT"]

def get_ohlcv(symbol):
    data = exchange.fetch_ohlcv(symbol, timeframe='1d', limit=2)
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
    return f"📈 Best performing crypto today: {top} (+{round(best*100,2)}%)"

def get_long_term_crypto():
    return "🧠 Long-term crypto idea: ETH/USDT (Leading L1 smart contract platform)"

def get_short_term_crypto():
    return "💣 Short-term crypto trade: PEPE/USDT (Meme coin with breakout potential)"

# --- FLASK ROUTES ---

@app.route("/")
def home():
    return "🚀 Smart Trading Bot is running"

@app.route("/signalstock")
def signal_stock():
    return get_top_gainer()

@app.route("/signalstock.l")
def signal_stock_long():
    return get_long_term_pick()

@app.route("/signalstock.s")
def signal_stock_short():
    return get_short_term_pick()

@app.route("/signalcrypto")
def signal_crypto():
    return get_top_crypto()

@app.route("/signalcrypto.l")
def signal_crypto_long():
    return get_long_term_crypto()

@app.route("/signalcrypto.s")
def signal_crypto_short():
    return get_short_term_crypto()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
