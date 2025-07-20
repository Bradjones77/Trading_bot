
def format_signals(signals):
    message = ""
    for i, sig in enumerate(signals):
        action = "💰 *Buy Now!*" if sig['type'] == "BUY" else "⚠️ *Consider Selling!*"
        message += f"{i+1}. *{sig['symbol']}* | {sig['type']}\n"
        message += f"   - Confidence: {sig['confidence']}%\n"
        message += f"   - Stop Loss: {sig['stop_loss']}\n"
        message += f"   - Target: {sig['target']}\n"
        message += f"   - {action}\n"
        message += f"   - 💡 Follow-up: Bot will notify when target is near or if stop-loss is triggered.\n\n"
    return message
