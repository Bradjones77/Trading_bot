
# Crypto Trading Bot

### 🔧 Features:
- Sends trade signals to Telegram 3x per day (5am, 3pm, 8pm)
- Ranked signals by confidence
- Prebuilt for Railway.app deployment

---

### 🚀 How to Deploy on Railway

1. Create a new project in [Railway](https://railway.app/)
2. Upload this code or connect to GitHub
3. Add environment variables:

```
BOT_TOKEN=your_telegram_bot_token
CHAT_ID=@your_telegram_username_or_chat_id
```

4. Deploy, and you're done!

---

### ✅ Customization
- Edit `strategies.py` to plug in real data sources (Binance, IntoTheBlock, etc.)
- Add Telegram command handlers for Q&A and tracking
