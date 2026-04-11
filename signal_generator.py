"""
Signal Generator - Enhanced with RSI + Bollinger Bands
Real-time technical analysis with multi-factor confidence scoring
"""

from datetime import datetime, timedelta
import config
from indicators import TechnicalIndicators
from advanced_indicators import AdvancedIndicators

class SignalGenerator:
    def __init__(self):
        self.last_prices = {}
        self.last_rsi = {}
        self.min_confidence = 25
        self.indicators = TechnicalIndicators()
        self.advanced = AdvancedIndicators()

    def calculate_rsi(self, prices, period=14):
        """Calculate RSI using TechnicalIndicators class"""
        return self.indicators.calculate_rsi(prices, period)

    def generate_signal_from_price(self, pair, price, price_history=None):
        """
        Generate trading signal using RSI + Bollinger Bands

        Args:
            pair: Trading pair (e.g., "EURUSD")
            price: Current price
            price_history: Optional list of historical closing prices

        Returns:
            dict: Signal data or None if no signal
        """
        # Store price history
        if pair not in self.last_prices:
            self.last_prices[pair] = []

        self.last_prices[pair].append(price)

        # Keep last 50 prices
        if len(self.last_prices[pair]) > 50:
            self.last_prices[pair] = self.last_prices[pair][-50:]

        # Use provided history if available and sufficient
        prices = price_history if price_history and len(price_history) >= 14 else self.last_prices[pair]

        if len(prices) < 14:
            return None

        # Calculate RSI
        rsi = self.calculate_rsi(prices)
        self.last_rsi[pair] = rsi

        # Calculate Bollinger Bands if enough data
        bb_upper, bb_sma, bb_lower = None, None, None
        if len(prices) >= 20:
            bb_upper, bb_sma, bb_lower = self.advanced.calculate_bollinger_bands(prices)

        # Multi-factor signal generation
        signal = None
        confidence = 0
        factors = []

        # RSI Analysis
        if rsi <= config.RSI_OVERSOLD:
            direction = "BUY"
            confidence += min(40, int(80 - rsi))
            factors.append(f"RSI Oversold ({rsi})")

            # Bollinger Band confirmation
            if bb_lower and price <= bb_lower * 1.001:
                confidence += 15
                factors.append("Price at lower BB")
            elif bb_lower and price <= bb_sma:
                confidence += 8
                factors.append("Price below mid BB")

        elif rsi >= config.RSI_OVERBOUGHT:
            direction = "SELL"
            confidence += min(40, int(rsi - 60))
            factors.append(f"RSI Overbought ({rsi})")

            # Bollinger Band confirmation
            if bb_upper and price >= bb_upper * 0.999:
                confidence += 15
                factors.append("Price at upper BB")
            elif bb_upper and price >= bb_sma:
                confidence += 8
                factors.append("Price above mid BB")
        else:
            return None

        # Check minimum confidence
        if confidence < self.min_confidence:
            return None

        confidence = min(95, confidence)

        # Emoji based on confidence
        if confidence >= 80:
            emoji = "🟢🟢" if direction == "BUY" else "🔴🔴"
        elif confidence >= 60:
            emoji = "🟢" if direction == "BUY" else "🔴"
        else:
            emoji = "⚪"

        reason = " | ".join(factors)

        return {
            'pair': pair,
            'flag': config.get_flag(pair),
            'price': price,
            'rsi': rsi,
            'direction': direction,
            'confidence': confidence,
            'emoji': emoji,
            'reason': reason,
            'timestamp': datetime.now().strftime("%I:%M %p"),
            'bollinger': {
                'upper': bb_upper,
                'sma': bb_sma,
                'lower': bb_lower
            } if bb_upper else None
        }

    def format_signal_message(self, signal):
        """Format signal message with entry time and martingale levels"""
        entry_time = datetime.now() + timedelta(minutes=config.SIGNAL_TIMER_MINUTES)

        # Build martingale levels
        martingale_lines = []
        for i in range(1, config.MARTINGALE_LEVELS + 1):
            level_time = entry_time + timedelta(minutes=i * config.MARTINGALE_INTERVAL)
            martingale_lines.append(f"  Level {i} → {level_time.strftime('%I:%M %p')}")

        # Calculate TP/SL
        tp_mult = 1.005 if signal['direction'] == "BUY" else 0.995
        sl_mult = 0.995 if signal['direction'] == "BUY" else 1.005

        tp = signal['price'] * tp_mult
        sl = signal['price'] * sl_mult

        # Bollinger Band info
        bb_info = ""
        if signal.get('bollinger') and signal['bollinger']['upper']:
            bb = signal['bollinger']
            bb_info = f"""
📊 <b>Bollinger Bands:</b>
• Upper: ${bb['upper']:.5f}
• SMA20: ${bb['sma']:.5f}
• Lower: ${bb['lower']:.5f}"""

        return f"""
🔔 <b>NEW SIGNAL!</b>

🎫 Trade: {signal['flag']} {signal['pair']} (OTC)
⏳ Timer: {config.SIGNAL_TIMER_MINUTES} minutes
➡️ Entry: {entry_time.strftime('%I:%M %p')}
📈 Direction: {signal['direction']} {signal['emoji']}

💪 <b>Confidence:</b> {signal['confidence']}%

📊 <b>Technical Analysis:</b>
• RSI: {signal['rsi']}
• {signal['reason']}{bb_info}

↪️ <b>Martingale Levels:</b>
{chr(10).join(martingale_lines)}

💰 <b>Entry Price:</b> ${signal['price']:.5f}
🎯 <b>Take Profit:</b> ${tp:.5f}
🛑 <b>Stop Loss:</b> ${sl:.5f}

⏰ {signal['timestamp']} (Nigeria Time)
"""
