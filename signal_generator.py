"""
Signal Generator - RSI Calculation and Signal Formatting
"""

from datetime import datetime, timedelta
import config

class SignalGenerator:
    def __init__(self):
        self.price_history = {}
        self.min_confidence = config.MIN_CONFIDENCE
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI from price list"""
        if len(prices) < period + 1:
            return 50
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-period:]) / period if gains else 0
        avg_loss = sum(losses[-period:]) / period if losses else 0
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 1)
    
    def update_price(self, pair, price):
        """Store price for RSI calculation"""
        if pair not in self.price_history:
            self.price_history[pair] = []
        
        self.price_history[pair].append(price)
        
        # Keep last 30 prices
        if len(self.price_history[pair]) > 30:
            self.price_history[pair] = self.price_history[pair][-30:]
    
    def generate_signal(self, pair, price, data_source="Alpha Vantage"):
        """Generate signal based on current price"""
        self.update_price(pair, price)
        
        history = self.price_history.get(pair, [])
        
        if len(history) < 15:
            return None
        
        rsi = self.calculate_rsi(history)
        
        if rsi <= config.RSI_OVERSOLD:
            direction = "BUY"
            confidence = min(95, int(75 - rsi + 20))
            signal_type = "STRONG_BUY"
            entry_emoji = "🐂 ⬆️"
            rsi_label = "OVERSOLD"
        elif rsi >= config.RSI_OVERBOUGHT:
            direction = "SELL"
            confidence = min(95, int(rsi - 70 + 20))
            signal_type = "STRONG_SELL"
            entry_emoji = "🐻 ⬇️"
            rsi_label = "OVERBOUGHT"
        else:
            return None
        
        if confidence < self.min_confidence:
            return None
        
        return {
            'pair': pair,
            'flag': config.get_flag(pair),
            'price': price,
            'rsi': rsi,
            'direction': direction,
            'entry_emoji': entry_emoji,
            'confidence': confidence,
            'signal_type': signal_type,
            'rsi_label': rsi_label,
            'data_source': data_source,
            'timestamp': datetime.now().strftime("%I:%M %p")
        }
    
    def format_signal_message(self, signal):
        """Format signal for Telegram display"""
        entry_time = datetime.now() + timedelta(minutes=config.SIGNAL_TIMER_MINUTES)
        expiry_time = entry_time + timedelta(minutes=config.SIGNAL_TIMER_MINUTES)
        
        martingale = []
        for i in range(1, config.MARTINGALE_LEVELS + 1):
            level_time = entry_time + timedelta(minutes=i * config.MARTINGALE_INTERVAL)
            martingale.append(f" Level {i} → {level_time.strftime('%I:%M %p')}")
        
        tp = signal['price'] * 1.005 if signal['direction'] == "BUY" else signal['price'] * 0.995
        sl = signal['price'] * 0.995 if signal['direction'] == "BUY" else signal['price'] * 1.005
        
        message = f"""
⚡ SIGNAL ALERT

{signal['flag']} {signal['pair']}
{signal['entry_emoji']} {signal['direction']} at ${signal['price']:.5f}

Entry: {entry_time.strftime('%I:%M %p')} (Nigeria Time)
Timer: {config.SIGNAL_TIMER_MINUTES} minutes
Expires: {expiry_time.strftime('%I:%M %p')}

━━━━━━━━━━━━━━━━━━━━━━━━━━

RSI: {signal['rsi']} ({signal['rsi_label']})
Confidence: {signal['confidence']}%

━━━━━━━━━━━━━━━━━━━━━━━━━━

Martingale Levels:
{chr(10).join(martingale)}

━━━━━━━━━━━━━━━━━━━━━━━━━━

Entry: ${signal['price']:.5f}
Take Profit: ${tp:.5f}
Stop Loss: ${sl:.5f}

━━━━━━━━━━━━━━━━━━━━━━━━━━

Data: {signal['data_source']}
{signal['timestamp']} (Nigeria Time)
"""
        return message