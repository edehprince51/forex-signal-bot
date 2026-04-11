"""
Signal Generator - Real-time RSI calculation and signal formatting
"""

from datetime import datetime, timedelta
import config

class SignalGenerator:
    def __init__(self):
        self.last_prices = {}
        self.last_rsi = {}
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI from price list"""
        if len(prices) < period:
            return 50
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(
