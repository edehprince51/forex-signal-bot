"""
Main Forex Signal Bot - Professional Edition
With Command Handling, Multi-Pair Scanning, and Advanced Signals
"""

import os
import time
import schedule
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

import config
from telegram_bot import TelegramBot
from data_fetcher import AlphaVantageFetcher
from signal_generator import SignalGenerator
from advanced_indicators import AdvancedIndicators

load_dotenv()

class ForexSignalBot:
    def __init__(self):
        print("""
        ╔══════════════════════════════════════════════════════════╗
        ║     FOREX SIGNAL BOT - PROFESSIONAL EDITION v2.0         ║
        ║     Advanced Trading Signals | Multi-Pair Scanner        ║
        ╚══════════════════════════════════════════════════════════╝
        """)
        
        # Load credentials
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        # Validate credentials
        self._validate_credentials()
        
        # Initialize components
        print("\n📱 Initializing Telegram bot...")
        self.telegram = TelegramBot(self.telegram_token, self.telegram_chat_id)
        
        print("\n📊 Initializing data fetcher...")
        self.data_fetcher = AlphaVantageFetcher(self.alpha_vantage_key)
        
        print("\n🎯 Initializing signal generator...")
        self.signal_generator = SignalGenerator()
        
        print("\n📈 Initializing advanced indicators...")
        self.indicators = AdvancedIndicators()
        
        # Connect bot components
        self.telegram.set_bot_reference(self)
        self.telegram.set_signal_generator(self.signal_generator)
        self.telegram.set_config(config)
        
        print("\n✅ Bot initialization complete!")
        
        # Tracking variables
        self.total_scans = 0
        self.total_signals = 0
        self.auto_scan_enabled = True
        self.scan_history = {}  # Track recent scans to avoid duplicates
        self.signal_history = []  # Store last 50 signals
        
        # Start command handler in background
        self.start_command_handler()
        
        print(f"\n📊 Configuration Summary:")
        print(f"   • Pairs monitored: {len(config.FOREX_PAIRS)}")
        print(f"   • Timeframes: {', '.join(config.TIMEFRAMES.keys())}")
        print(f"   • Scan interval: {config.SCAN_INTERVAL_MINUTES} minutes")
        print(f"   • Min confidence: {config.MIN_CONFIDENCE}%")
        print(f"   • Martingale levels: {config.MARTINGALE_LEVELS}")
    
    def start_command_handler(self):
        """Start the Telegram command handler in a separate thread"""
        import threading
        command_thread = threading.Thread(
            target=self.telegram.start_command_handler,
            args=(self, self.signal_generator, config),
            daemon=True
        )
        command_thread.start()
        print("📱 Command handler started in background")
    
    def _validate_credentials(self):
        """Check all required credentials"""
        missing = []
        
        if not self.telegram_token or self.telegram_token == "your_telegram_bot_token_here":
            missing.append("TELEGRAM_BOT_TOKEN")
        
        if not self.alpha_vantage_key or self.alpha_vantage_key == "your_alpha_vantage_api_key_here":
            missing.append("ALPHA_VANTAGE_API_KEY")
        
        if not self.telegram_chat_id or self.telegram_chat_id == "your_chat_id_here":
            missing.append("TELEGRAM_CHAT_ID")
        
        if missing:
            print("❌ Missing credentials in .env file:")
            for item in missing:
                print(f"   - {item}")
            print("\nPlease update your .env file with the correct values.")
            exit(1)
        
        print("✅ All credentials found")
    
    def _should_skip_pair(self, pair, timeframe):
        """Skip pairs scanned recently to save API calls"""
        key = f"{pair}_{timeframe}"
        last_scan = self.scan_history.get(key)
        
        if last_scan:
            time_since = (datetime.now() - last_scan).seconds
            if time_since < 120:  # Skip if scanned in last 2 minutes
                return True
        
        self.scan_history[key] = datetime.now()
        return False
    
    def scan_all_pairs(self):
        """Scan all configured pairs across all timeframes"""
        if not self.auto_scan_enabled:
            print("⏸️ Auto-scan is paused. Use /resume to start.")
            return 0
        
        self.total_scans += 1
        scan_start = datetime.now()
        
        print(f"\n{'='*70}")
        print(f"🔍 SCAN #{self.total_scans} started at {scan_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Total pairs: {len(config.FOREX_PAIRS)} | Timeframes: {len(config.TIMEFRAMES)}")
        print(f"{'='*70}")
        
        signals_found = 0
        total_checks = 0
        
        # Send scan started notification
        self.telegram.send_message(f"🔍 Scan #{self.total_scans} started - analyzing {len(config.FOREX_PAIRS)} pairs...")
        
        for timeframe_name, interval in config.TIMEFRAMES.items():
            print(f"\n⏰ Scanning {timeframe_name.upper()} timeframe...")
            
            for i, pair in enumerate(config.FOREX_PAIRS):
                total_checks += 1
                
                # Show progress every 10 pairs
                if (i + 1) % 10 == 0:
                    print(f"   Progress: {i+1}/{len(config.FOREX_PAIRS)} pairs scanned")
                
                # Skip if scanned recently
                if self._should_skip_pair(pair, timeframe_name):
                    continue
                
                # Fetch data
                df = self.data_fetcher.fetch_forex_data(pair, interval)
                
                if df is not None:
                    # Generate signal
                    signal = self.signal_generator.analyze_pair(df, pair, timeframe_name)
                    
                    if signal:
                        signals_found += 1
                        self.total_signals += 1
                        
                        # Store in history
                        self.signal_history.insert(0, signal)
                        if len(self.signal_history) > 50:
                            self.signal_history.pop()
                        
                        # Format and send professional signal
                        message = self.signal_generator.format_professional_signal(signal)
                        self.telegram.send_message(message)
                        
                        # Small delay between signals
                        time.sleep(1)
                
                # Rate limiting
                time.sleep(0.5)
        
        # Scan complete
        scan_end = datetime.now()
        scan_duration = (scan_end - scan_start).total_seconds()
        
        # Send summary
        summary = f"""
✅ <b>SCAN #{self.total_scans} COMPLETE</b>

📊 <b>Statistics:</b>
• Pairs analyzed: {len(config.FOREX_PAIRS)}
• Timeframes: {len(config.TIMEFRAMES)}
• Total checks: {total_checks}
• Signals found: {signals_found}

⏱️ <b>Duration:</b> {scan_duration:.1f} seconds
📈 <b>Total signals to date:</b> {self.total_signals}

⚙️ <b>Current Settings:</b>
• Min confidence: {config.MIN_CONFIDENCE}%
• Auto-scan: {"ON" if self.auto_scan_enabled else "OFF"}
        """
        
        print(f"\n📊 Scan summary: {signals_found} signals found in {scan_duration:.1f}s")
        self.telegram.send_message(summary)
        
        return signals_found
    
    async def get_signal_for_pair(self, pair):
        """Get signal for a specific pair (for /signal command)"""
        print(f"🔍 Analyzing {pair} on demand...")
        
        # Try different timeframes
        for timeframe_name, interval in config.TIMEFRAMES.items():
            df = self.data_fetcher.fetch_forex_data(pair, interval)
            if df is not None:
                signal = self.signal_generator.analyze_pair(df, pair, timeframe_name)
                if signal:
                    return signal
        
        return None
    
    def get_status(self):
        """Get bot status for /status command"""
        status = f"""
🤖 <b>FOREX SIGNAL BOT STATUS</b>

✅ <b>System Status:</b> ONLINE
📊 <b>Pairs monitored:</b> {len(config.FOREX_PAIRS)}
⏰ <b>Timeframes:</b> {', '.join(config.TIMEFRAMES.keys())}

📈 <b>Performance:</b>
• Total scans: {self.total_scans}
• Total signals: {self.total_signals}
• Signals per scan: {self.total_signals / max(self.total_scans, 1):.1f}

⚙️ <b>Settings:</b>
• Min confidence: {config.MIN_CONFIDENCE}%
• Scan interval: {config.SCAN_INTERVAL_MINUTES} min
• Auto-scan: {"ON" if self.auto_scan_enabled else "OFF"}

↪️ <b>Martingale:</b>
• Levels: {config.MARTINGALE_LEVELS}
• Multiplier: {config.MARTINGALE_MULTIPLIER}x
• Interval: {config.MARTINGALE_INTERVAL_MINUTES} min

📱 <b>Last activity:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        return status
    
    def get_stats(self):
        """Get trading statistics for /stats command"""
        # Calculate recent signal stats
        last_10_signals = self.signal_history[:10]
        buy_signals = sum(1 for s in last_10_signals if s.get('direction') == 'BUY')
        sell_signals = sum(1 for s in last_10_signals if s.get('direction') == 'SELL')
        
        stats = f"""
📊 <b>TRADING STATISTICS</b>

<b>Overall Performance:</b>
• Total scans: {self.total_scans}
• Total signals: {self.total_signals}
• Signals/scan: {self.total_signals / max(self.total_scans, 1):.1f}

<b>Last 10 Signals:</b>
• BUY signals: {buy_signals}
• SELL signals: {sell_signals}
• Avg confidence: {sum(s.get('confidence', 0) for s in last_10_signals) / max(len(last_10_signals), 1):.0f}%

<b>Active Strategies:</b>
• RSI Divergence
• MACD Crossover
• Bollinger Squeeze
• Moving Average Crossovers
• Fibonacci Retracement
• Candlestick Patterns

<b>Market Coverage:</b>
• Major Pairs: 7
• Minor Pairs: 20
• Exotic Pairs: 15
• Commodities: 5
        """
        return stats
    
    def send_startup_message(self):
        """Send startup message to Telegram"""
        message = f"""
🤖 <b>FOREX SIGNAL BOT - PROFESSIONAL EDITION</b>

✅ <b>Bot is now ONLINE!</b>

📊 <b>Monitoring:</b>
• {len(config.FOREX_PAIRS)} Currency Pairs
• {len(config.TIMEFRAMES)} Timeframes
• 70+ Trading Instruments

🎯 <b>Advanced Strategies:</b>
• RSI Divergence Detection
• MACD Crossovers
• Bollinger Band Squeeze
• Golden/Death Cross
• Stochastic RSI
• Fibonacci Levels
• Candlestick Patterns

↪️ <b>Features:</b>
• Martingale Levels with Timers
• Real-time Signal Alerts
• Interactive Commands
• Performance Statistics

⚙️ <b>Current Settings:</b>
• Min confidence: {config.MIN_CONFIDENCE}%
• Scan interval: {config.SCAN_INTERVAL_MINUTES} minutes
• Martingale levels: {config.MARTINGALE_LEVELS}

📱 <b>Commands:</b>
Type /help to see all available commands

<i>Ready to scan the markets!</i>
        """
        self.telegram.send_message(message)
        print("📨 Startup message sent to Telegram")
    
    def pause_scanning(self):
        """Pause auto-scanning"""
        self.auto_scan_enabled = False
        self.telegram.send_message("⏸️ Auto-scanning paused. Use /resume to start again.")
        print("⏸️ Auto-scanning paused")
    
    def resume_scanning(self):
        """Resume auto-scanning"""
        self.auto_scan_enabled = True
        self.telegram.send_message("▶️ Auto-scanning resumed.")
        print("▶️ Auto-scanning resumed")
    
    def run(self):
        """Main execution loop"""
        print(f"\n{'='*70}")
        print(f"🚀 Starting bot with scan interval: {config.SCAN_INTERVAL_MINUTES} minutes")
        print(f"📊 Monitoring {len(config.FOREX_PAIRS)} currency pairs")
        print(f"⏰ Timeframes: {', '.join(config.TIMEFRAMES.keys())}")
        print(f"{'='*70}\n")
        
        # Send startup notification
        self.send_startup_message()
        
        # Perform initial scan immediately
        print("🔍 Performing initial scan...")
        self.scan_all_pairs()
        
        # Schedule regular scans
        schedule.every(config.SCAN_INTERVAL_MINUTES).minutes.do(self.scan_all_pairs)
        
        print(f"\n✅ Bot is now running 24/7. Press Ctrl+C to stop.")
        print(f"⏰ Next scan in {config.SCAN_INTERVAL_MINUTES} minutes...")
        print(f"📱 Send /help in Telegram to see available commands\n")
        
        try:
            # Keep running until interrupted
            while True:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\n\n🛑 Bot stopped by user")
            self.telegram.send_message("🛑 Bot stopped by user")
        except Exception as e:
            # Handle unexpected errors
            print(f"\n❌ Unexpected error: {e}")
            self.telegram.send_message(f"❌ Bot crashed: {str(e)[:100]}")
        finally:
            print("👋 Goodbye!")

# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     FOREX SIGNAL BOT - PROFESSIONAL EDITION v2.0         ║
    ║                                                          ║
    ║     • 70+ Currency Pairs                                 ║
    ║     • 9 Advanced Strategies                              ║
    ║     • Martingale Levels with Timers                      ║
    ║     • Real-time Telegram Alerts                          ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Create and run the bot
    bot = ForexSignalBot()
    bot.run()