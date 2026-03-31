"""
Signal Generator
"""

import pandas as pd
import numpy as np
from datetime import datetime
from indicators import TechnicalIndicators
import config

class SignalGenerator:
    def __init__(self):
        self.indicators = TechnicalIndicators()
        print("🎯 Signal generator initialized")
    
    def analyze_pair(self, df, pair, timeframe):
        if df is None or len(df) < 50:
            return None
        
        close_prices = df['close']
        high_prices = df['high']
        low_prices = df['low']
        
        # Calculate indicators
        rsi = self.indicators.calculate_rsi(close_prices, config.RSI_PERIOD)
        ema_fast = self.indicators.calculate_ema(close_prices, config.EMA_FAST)
        ema_slow = self.indicators.calculate_ema(close_prices, config.EMA_SLOW)
        macd_line, signal_line, macd_hist = self.indicators.calculate_macd(
            close_prices, config.MACD_FAST, config.MACD_SLOW, config.MACD_SIGNAL
        )
        resistance, support = self.indicators.calculate_support_resistance(high_prices, low_prices)
        
        # Get latest values
        current_price = close_prices.iloc[-1]
        current_rsi = rsi.iloc[-1]
        prev_rsi = rsi.iloc[-2] if len(rsi) > 1 else current_rsi
        current_ema_fast = ema_fast.iloc[-1]
        current_ema_slow = ema_slow.iloc[-1]
        current_macd_hist = macd_hist.iloc[-1]
        prev_macd_hist = macd_hist.iloc[-2] if len(macd_hist) > 1 else current_macd_hist
        current_resistance = resistance.iloc[-1]
        current_support = support.iloc[-1]
        
        # Calculate confidence
        confidence = 0
        signals_detected = []
        
        # RSI
        if current_rsi < config.RSI_OVERSOLD:
            confidence += config.WEIGHTS["RSI_EXTREME"]
            signals_detected.append(f"RSI Oversold ({current_rsi:.1f})")
        elif current_rsi > config.RSI_OVERBOUGHT:
            confidence -= config.WEIGHTS["RSI_EXTREME"]
            signals_detected.append(f"RSI Overbought ({current_rsi:.1f})")
        
        # EMA
        if current_ema_fast > current_ema_slow and current_price > current_ema_fast:
            confidence += config.WEIGHTS["EMA_ALIGNMENT"]
            signals_detected.append("EMA Bullish Alignment")
        elif current_ema_fast < current_ema_slow and current_price < current_ema_fast:
            confidence -= config.WEIGHTS["EMA_ALIGNMENT"]
            signals_detected.append("EMA Bearish Alignment")
        
        # MACD
        if current_macd_hist > 0 and prev_macd_hist <= 0:
            confidence += config.WEIGHTS["MACD_CROSSOVER"]
            signals_detected.append("MACD Bullish Crossover")
        elif current_macd_hist < 0 and prev_macd_hist >= 0:
            confidence -= config.WEIGHTS["MACD_CROSSOVER"]
            signals_detected.append("MACD Bearish Crossover")
        
        # Support/Resistance
        if current_price >= current_resistance * 0.99:
            confidence -= config.WEIGHTS["SUPPORT_RESISTANCE"]
            signals_detected.append(f"Near Resistance")
        elif current_price <= current_support * 1.01:
            confidence += config.WEIGHTS["SUPPORT_RESISTANCE"]
            signals_detected.append(f"Near Support")
        
        if abs(confidence) < config.MIN_CONFIDENCE:
            return None
        
        # Determine signal
        if confidence >= 50:
            signal_type = "STRONG_BUY"
        elif confidence >= 20:
            signal_type = "BUY"
        elif confidence <= -50:
            signal_type = "STRONG_SELL"
        elif confidence <= -20:
            signal_type = "SELL"
        else:
            signal_type = "NEUTRAL"
        
        emoji = config.SIGNAL_EMOJIS.get(signal_type, "⚪")
        
        return {
            'pair': pair,
            'timeframe': timeframe,
            'signal_type': signal_type,
            'confidence': abs(confidence),
            'direction': 'BUY' if confidence > 0 else 'SELL',
            'price': current_price,
            'rsi': round(current_rsi, 2),
            'signals': signals_detected,
            'emoji': emoji,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def format_signal_message(self, signal):
        header = f"{signal['emoji']} <b>{signal['direction']} {signal['pair']}</b> {signal['emoji']}"
        
        details = f"""
📊 <b>Timeframe:</b> {signal['timeframe']}
💰 <b>Price:</b> ${signal['price']:.5f}
🎯 <b>Confidence:</b> {signal['confidence']}%
📈 <b>RSI:</b> {signal['rsi']}"""
        
        indicators = "\n\n<b>Indicators:</b>\n• "
        indicators += "\n• ".join(signal['signals'])
        
        timestamp = f"\n\n⏰ {signal['timestamp']}"
        
        return header + details + indicators + timestamp
