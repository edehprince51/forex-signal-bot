"""
Technical Indicators Calculator
"""

import pandas as pd
import numpy as np

class TechnicalIndicators:
    @staticmethod
    def calculate_rsi(prices, period=14):
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_ema(prices, period):
        return prices.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_macd(prices, fast=12, slow=26, signal=9):
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_support_resistance(high_prices, low_prices, window=20):
        resistance = high_prices.rolling(window=window).max()
        support = low_prices.rolling(window=window).min()
        return resistance, support

if __name__ == "__main__":
    print("Testing technical indicators...")
    dates = pd.date_range(start='2024-01-01', periods=100, freq='H')
    prices = pd.Series(np.random.randn(100).cumsum() + 100, index=dates)
    
    rsi = TechnicalIndicators.calculate_rsi(prices)
    print(f"RSI - Latest: {rsi.iloc[-1]:.2f}")