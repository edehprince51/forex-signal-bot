"""
Advanced Technical Indicators
More indicators and strategies for better signals
"""

import pandas as pd
import numpy as np

class AdvancedIndicators:
    
    @staticmethod
    def calculate_rsi(prices, period=14):
        """Calculate RSI"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices, fast=12, slow=26, signal=9):
        """Calculate MACD with histogram"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(prices, period=20, std=2):
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        rolling_std = prices.rolling(window=period).std()
        upper_band = sma + (rolling_std * std)
        lower_band = sma - (rolling_std * std)
        return upper_band, sma, lower_band
    
    @staticmethod
    def calculate_moving_averages(prices, fast=9, medium=21, slow=50):
        """Calculate multiple moving averages"""
        ma_fast = prices.rolling(window=fast).mean()
        ma_medium = prices.rolling(window=medium).mean()
        ma_slow = prices.rolling(window=slow).mean()
        return ma_fast, ma_medium, ma_slow
    
    @staticmethod
    def calculate_stochastic_rsi(prices, period=14, k=3, d=3):
        """Calculate Stochastic RSI"""
        rsi = AdvancedIndicators.calculate_rsi(prices, period)
        stoch_rsi = (rsi - rsi.rolling(window=period).min()) / (rsi.rolling(window=period).max() - rsi.rolling(window=period).min())
        k_line = stoch_rsi.rolling(window=k).mean() * 100
        d_line = k_line.rolling(window=d).mean()
        return k_line, d_line
    
    @staticmethod
    def calculate_atr(high, low, close, period=14):
        """Calculate Average True Range"""
        high_low = high - low
        high_close = abs(high - close.shift())
        low_close = abs(low - close.shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    @staticmethod
    def find_fibonacci_levels(high, low):
        """Calculate Fibonacci retracement levels"""
        diff = high - low
        levels = {}
        for level in [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]:
            if level == 0:
                levels[level] = low
            elif level == 1:
                levels[level] = high
            else:
                levels[level] = low + (diff * level)
        return levels
    
    @staticmethod
    def identify_candlestick_patterns(df):
        """Identify important candlestick patterns"""
        patterns = []
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Bullish Engulfing
        if (prev['close'] < prev['open'] and 
            last['close'] > last['open'] and 
            last['open'] < prev['close'] and 
            last['close'] > prev['open']):
            patterns.append("Bullish Engulfing")
        
        # Bearish Engulfing
        if (prev['close'] > prev['open'] and 
            last['close'] < last['open'] and 
            last['open'] > prev['close'] and 
            last['close'] < prev['open']):
            patterns.append("Bearish Engulfing")
        
        # Doji
        body = abs(last['close'] - last['open'])
        total_range = last['high'] - last['low']
        if total_range > 0 and body / total_range < 0.1:
            patterns.append("Doji")
        
        # Hammer
        lower_wick = min(last['open'], last['close']) - last['low']
        body_size = abs(last['close'] - last['open'])
        if lower_wick > body_size * 2:
            patterns.append("Hammer")
        
        # Shooting Star
        upper_wick = last['high'] - max(last['open'], last['close'])
        if upper_wick > body_size * 2:
            patterns.append("Shooting Star")
        
        return patterns
    
    @staticmethod
    def rsi_divergence(prices, rsi):
        """Detect RSI divergence"""
        # Look for price making lower low but RSI making higher low (bullish)
        price_low = prices.iloc[-5:].min()
        rsi_low = rsi.iloc[-5:].min()
        
        if prices.iloc[-1] <= price_low and rsi.iloc[-1] > rsi_low:
            return "Bullish Divergence"
        
        # Look for price making higher high but RSI making lower high (bearish)
        price_high = prices.iloc[-5:].max()
        rsi_high = rsi.iloc[-5:].max()
        
        if prices.iloc[-1] >= price_high and rsi.iloc[-1] < rsi_high:
            return "Bearish Divergence"
        
        return None