"""
Telegram Bot - Command handlers and message formatting
"""

from datetime import datetime, timedelta

class TelegramBot:
    def __init__(self, settings, config):
        self.settings = settings
        self.config = config

    def get_status(self):
        """Get formatted bot status message"""
        po_status = "✅ CONNECTED" if self.settings.get("connected") else "❌ DISCONNECTED"
        auto_signal = "✅ ON" if self.settings.get("auto_signals_enabled") else "❌ OFF"
        auto_trade = "✅ ON" if self.settings.get("auto_trade_enabled") else "❌ OFF"

        return f"""
📊 <b>BOT STATUS</b>

✅ Status: ONLINE
📡 Pocket Option: {po_status}
🤖 Auto Signals: {auto_signal}
💰 Auto Trade: {auto_trade}
📊 Total Signals: {self.settings.get('total_signals', 0)}
📈 Pairs Monitored: {len(self.config.PRIORITY_PAIRS)}
🌍 Total Instruments: {len(self.config.ALL_PAIRS)}

⏰ {self.format_time()} (Nigeria Time)
"""

    def get_stats(self):
        """Get formatted trading statistics"""
        return f"""
📊 <b>TRADING STATISTICS</b>

Total Signals: {self.settings.get('total_signals', 0)}
Total Trades: {self.settings.get('total_trades', 0)}
Auto Signals: {'ON' if self.settings.get('auto_signals_enabled') else 'OFF'}
Auto Trade: {'ON' if self.settings.get('auto_trade_enabled') else 'OFF'}
Pocket Option: {'Connected' if self.settings.get('connected') else 'Disconnected'}

⏰ {self.format_time()} (Nigeria Time)
"""

    def format_time(self):
        """Format current Nigeria time"""
        return (datetime.utcnow() + timedelta(hours=1)).strftime("%I:%M %p")

    def format_signal_alert(self, signal):
        """Format a signal alert message"""
        entry_time = datetime.now() + timedelta(minutes=self.config.SIGNAL_TIMER_MINUTES)

        martingale_lines = []
        for i in range(1, self.config.MARTINGALE_LEVELS + 1):
            level_time = entry_time + timedelta(minutes=i * self.config.MARTINGALE_INTERVAL)
            martingale_lines.append(f"  Level {i} → {level_time.strftime('%I:%M %p')}")

        tp_mult = 1.005 if signal['direction'] == "BUY" else 0.995
        sl_mult = 0.995 if signal['direction'] == "BUY" else 1.005

        tp = signal['price'] * tp_mult
        sl = signal['price'] * sl_mult

        return f"""
🔔 <b>SIGNAL ALERT!</b>

🎫 Trade: {signal.get('flag', '🌍')} {signal['pair']} (OTC)
⏳ Timer: {self.config.SIGNAL_TIMER_MINUTES} minutes
➡️ Entry: {entry_time.strftime('%I:%M %p')}
📈 Direction: {signal['direction']} {signal.get('emoji', '⚪')}

💪 <b>Confidence:</b> {signal['confidence']}%

📊 <b>Analysis:</b>
• RSI: {signal.get('rsi', 'N/A')}
• {signal['reason']}

↪️ <b>Martingale Levels:</b>
{chr(10).join(martingale_lines)}

💰 <b>Entry:</b> ${signal['price']:.5f}
🎯 <b>TP:</b> ${tp:.5f}
🛑 <b>SL:</b> ${sl:.5f}

⏰ {signal.get('timestamp', self.format_time())} (Nigeria Time)
"""

    def format_help(self):
        """Format help message"""
        return """
📋 <b>AVAILABLE COMMANDS</b>

<b>Basic:</b>
/start - Start the bot
/help - Show this help
/status - Check bot status
/time - Current Nigeria time

<b>Trading:</b>
/signal [pair] - Get signal (e.g., /signal EURUSD)
/scan - Scan all priority pairs
/pairs - List all instruments

<b>Settings:</b>
/confidence [10-90] - Set minimum confidence
/duration [min] - Set trade duration
/autosignal - Toggle auto signals
/autotrade - Toggle auto trade
/stop - Stop auto signals
/startbot - Resume auto signals

<b>Info:</b>
/stats - Trading statistics
/settings - Current configuration
/about - Bot information

⏰ Nigeria Time (UTC+1)
"""
