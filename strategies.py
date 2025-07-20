
def get_trade_signals():
    # Simulate example signals
    signals = [
        {"symbol": "DOGE", "type": "BUY", "confidence": 88, "stop_loss": "0.115", "target": "0.143"},
        {"symbol": "SOL", "type": "BUY", "confidence": 80, "stop_loss": "156.2", "target": "178"},
        {"symbol": "PEPE", "type": "SELL", "confidence": 60, "stop_loss": "0.00000114", "target": "0.00000103"},
    ]
    # Sort by confidence descending
    signals = sorted(signals, key=lambda x: x["confidence"], reverse=True)
    # Return only the top signal
    return [signals[0]]
