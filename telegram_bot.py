"""
Telegram Bot Handler with Commands
Manages all communication with Telegram and handles user commands
"""

import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError
import os
from dotenv import load_dotenv

load_dotenv()

class TelegramBot:
    """
    Handles sending messages and commands to Telegram
    """
    
    def __init__(self, token, chat_id):
        """
        Initialize the Telegram bot
        
        Args:
            token (str): Your bot's token from @BotFather
            chat_id (str): Your Telegram chat ID
        """
        self.token = token
        self.chat_id = chat_id
        self.application = None
        self.bot = Bot(token=token)
        self.signal_generator = None  # Will be set later
        self.config = None  # Will be set later
        self.bot_instance = None  # Will be set later
        
        print("📱 Telegram bot handler initialized")
    
    def set_bot_reference(self, bot_instance):
        """Set reference to main bot for commands"""
        self.bot_instance = bot_instance
    
    def set_signal_generator(self, signal_generator):
        """Set signal generator reference"""
        self.signal_generator = signal_generator
    
    def set_config(self, config):
        """Set config reference"""
        self.config = config
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🤖 <b>Welcome to Forex Signal Bot!</b>

I'm your automated trading assistant that scans the markets 24/7 and provides high-quality trading signals.

<b>📊 Features:</b>
• 70+ Currency Pairs
• Multiple Timeframes (1m, 5m, 15m, 30m)
• Advanced Indicators (RSI, MACD, Bollinger Bands)
• Martingale Levels with Timers
• Real-time Signal Alerts

<b>📋 Available Commands:</b>
Use /help to see all commands
        """
        await update.message.reply_text(welcome_message, parse_mode='HTML')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
📋 <b>COMPLETE COMMAND LIST</b>

<b>📊 SIGNAL COMMANDS:</b>
/status - Check bot status and current settings
/settings - View current configuration
/pairs - List all monitored currency pairs
/signal [pair] - Get signal for specific pair (e.g., /signal EURUSD)

<b>⚙️ CONFIGURATION COMMANDS:</b>
/confidence [value] - Set minimum confidence (40-90)
/timeframe [value] - Change timeframe (1m,5m,15m,30m)
/martingale [on/off] - Enable/disable Martingale levels
/strength [level] - Set signal strength filter (weak/medium/strong)

<b>📈 STATISTICS COMMANDS:</b>
/stats - Show trading statistics
/history - Last 10 signals
/performance - Win rate and performance metrics

<b>🔧 SYSTEM COMMANDS:</b>
/scan - Force immediate market scan
/pause - Pause auto-scanning
/resume - Resume auto-scanning
/restart - Restart the bot

<b>📚 INFO COMMANDS:</b>
/help - Show this help menu
/about - About this bot
/support - Support contact
/version - Bot version

<b>💡 Examples:</b>
/signal EURUSD - Get EURUSD signal
/confidence 60 - Set minimum confidence to 60%
        """
        await update.message.reply_text(help_message, parse_mode='HTML')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        if not self.bot_instance:
            await update.message.reply_text("❌ Bot not ready. Please try again.")
            return
        
        status = self.bot_instance.get_status()
        await update.message.reply_text(status, parse_mode='HTML')
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command"""
        if not self.config:
            await update.message.reply_text("❌ Configuration not loaded.")
            return
        
        settings = f"""
⚙️ <b>CURRENT SETTINGS</b>

📊 <b>Scan Settings:</b>
• Pairs monitored: {len(self.config.FOREX_PAIRS)}
• Timeframes: {', '.join(self.config.TIMEFRAMES.keys())}
• Scan interval: {self.config.SCAN_INTERVAL_MINUTES} minutes

🎯 <b>Signal Settings:</b>
• Min confidence: {self.config.MIN_CONFIDENCE}%
• Signal strength: {self.config.SIGNAL_STRENGTH}

📈 <b>Indicators:</b>
• RSI Period: {self.config.RSI_PERIOD}
• MACD: {self.config.MACD_FAST}/{self.config.MACD_SLOW}/{self.config.MACD_SIGNAL}
• Bollinger: {self.config.BB_PERIOD} ({self.config.BB_STD} STD)

↪️ <b>Martingale:</b>
• Levels: {self.config.MARTINGALE_LEVELS}
• Multiplier: {self.config.MARTINGALE_MULTIPLIER}x
• Interval: {self.config.MARTINGALE_INTERVAL_MINUTES} min
        """
        await update.message.reply_text(settings, parse_mode='HTML')
    
    async def pairs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pairs command"""
        if not self.config:
            await update.message.reply_text("❌ Configuration not loaded.")
            return
        
        pairs_list = "\n".join([f"• {pair}" for pair in self.config.FOREX_PAIRS[:20]])
        
        message = f"""
📊 <b>MONITORED PAIRS</b>

<b>Total:</b> {len(self.config.FOREX_PAIRS)} pairs

<b>Active Pairs:</b>
{pairs_list}

{'• ... and more' if len(self.config.FOREX_PAIRS) > 20 else ''}

Use /scan to analyze all pairs now
        """
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def signal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signal [pair] command"""
        if not context.args:
            await update.message.reply_text("⚠️ Please specify a pair.\nExample: /signal EURUSD")
            return
        
        pair = context.args[0].upper()
        
        if not self.bot_instance:
            await update.message.reply_text("❌ Bot not ready.")
            return
        
        await update.message.reply_text(f"🔍 Analyzing {pair}... Please wait.")
        
        # Get signal for specific pair
        signal = await self.bot_instance.get_signal_for_pair(pair)
        
        if signal:
            message = self.signal_generator.format_professional_signal(signal)
            await update.message.reply_text(message, parse_mode='HTML')
        else:
            await update.message.reply_text(f"❌ No signal found for {pair} right now. Try again later.")
    
    async def confidence_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /confidence command"""
        if not context.args:
            await update.message.reply_text(f"⚠️ Current minimum confidence: {self.config.MIN_CONFIDENCE}%\nTo change: /confidence 60")
            return
        
        try:
            new_confidence = int(context.args[0])
            if 40 <= new_confidence <= 90:
                self.config.MIN_CONFIDENCE = new_confidence
                await update.message.reply_text(f"✅ Minimum confidence set to {new_confidence}%")
            else:
                await update.message.reply_text("❌ Please enter a value between 40 and 90")
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number")
    
    async def timeframe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /timeframe command"""
        if not context.args:
            await update.message.reply_text(f"⚠️ Current timeframes: {', '.join(self.config.TIMEFRAMES.keys())}\nTo change: /timeframe 5min")
            return
        
        new_timeframe = context.args[0]
        if new_timeframe in self.config.TIMEFRAMES:
            # Temporarily set to single timeframe
            self.config.TIMEFRAMES = {new_timeframe: self.config.TIMEFRAMES[new_timeframe]}
            await update.message.reply_text(f"✅ Timeframe set to {new_timeframe}")
        else:
            await update.message.reply_text(f"❌ Invalid timeframe. Choose from: {', '.join(self.config.TIMEFRAMES.keys())}")
    
    async def scan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /scan command"""
        if not self.bot_instance:
            await update.message.reply_text("❌ Bot not ready.")
            return
        
        await update.message.reply_text("🔍 Starting immediate market scan...")
        signals = self.bot_instance.scan_all_pairs()
        
        if signals > 0:
            await update.message.reply_text(f"✅ Scan complete! Found {signals} signals.")
        else:
            await update.message.reply_text("✅ Scan complete! No signals found this time.")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        if not self.bot_instance:
            await update.message.reply_text("❌ Bot not ready.")
            return
        
        stats = self.bot_instance.get_stats()
        await update.message.reply_text(stats, parse_mode='HTML')
    
    async def version_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /version command"""
        version_message = """
🤖 <b>Forex Signal Bot v2.0</b>

<b>Features:</b>
✅ 70+ Currency Pairs
✅ Multiple Timeframes
✅ Advanced Technical Indicators
✅ Martingale Levels with Timers
✅ Real-time Telegram Alerts
✅ Interactive Commands

<b>Developer:</b> Trading Bot System
<b>Last Update:</b> March 2024
        """
        await update.message.reply_text(version_message, parse_mode='HTML')
    
    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /about command"""
        about_message = """
📈 <b>About Forex Signal Bot</b>

This bot uses advanced technical analysis to identify high-probability trading opportunities in the forex market.

<b>Strategies Used:</b>
• RSI Divergence
• MACD Crossovers
• Bollinger Band Squeeze
• Moving Average Crossovers
• Fibonacci Retracement
• Candlestick Patterns

<b>Data Source:</b> Alpha Vantage
<b>Update Frequency:</b> Every 5 minutes

Use /help for available commands
        """
        await update.message.reply_text(about_message, parse_mode='HTML')
    
    async def send_message_async(self, message):
        """
        Send a message to Telegram (asynchronous version)
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            print(f"✅ Message sent successfully")
            return True
        except TelegramError as e:
            print(f"❌ Telegram error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error sending message: {e}")
            return False
    
    def send_message(self, message):
        """
        Send a message to Telegram (synchronous wrapper)
        """
        asyncio.run(self.send_message_async(message))
    
    async def test_connection(self):
        """
        Test if the bot can connect to Telegram
        """
        try:
            bot_info = await self.bot.get_me()
            print(f"✅ Connected to Telegram as @{bot_info.username}")
            return bot_info
        except Exception as e:
            print(f"❌ Failed to connect to Telegram: {e}")
            return None
    
    def start_command_handler(self, bot_instance=None, signal_generator=None, config=None):
        """
        Start the command handler to listen for user commands
        """
        if bot_instance:
            self.set_bot_reference(bot_instance)
        if signal_generator:
            self.set_signal_generator(signal_generator)
        if config:
            self.set_config(config)
        
        # Create application
        self.application = Application.builder().token(self.token).build()
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("settings", self.settings_command))
        self.application.add_handler(CommandHandler("pairs", self.pairs_command))
        self.application.add_handler(CommandHandler("signal", self.signal_command))
        self.application.add_handler(CommandHandler("confidence", self.confidence_command))
        self.application.add_handler(CommandHandler("timeframe", self.timeframe_command))
        self.application.add_handler(CommandHandler("scan", self.scan_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("version", self.version_command))
        self.application.add_handler(CommandHandler("about", self.about_command))
        
        # Start polling
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        print("📱 Telegram command handler started")

if __name__ == "__main__":
    print("Testing Telegram bot connection...")
    
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or token == "your_telegram_bot_token_here":
        print("❌ Please set your TELEGRAM_BOT_TOKEN in the .env file")
    else:
        bot = TelegramBot(token, chat_id)
        asyncio.run(bot.test_connection())