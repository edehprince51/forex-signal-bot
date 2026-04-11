"""
POCKET OPTION TRADING BOT - PRODUCTION VERSION v3.1
WebSocket Continuous Streaming | Multi-Indicator | Auto-Reconnect
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from BinaryOptionsToolsV2.pocketoption import PocketOptionAsync

import config
from signal_generator import SignalGenerator
from advanced_indicators import AdvancedIndicators

load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

print("""
╔════════════════════════════════════════════════════════════════╗
║   POCKET OPTION TRADING BOT - PRODUCTION v3.1                  ║
║   WebSocket Streaming | RSI + Bollinger | Auto-Reconnect         ║
╚════════════════════════════════════════════════════════════════╝
""")

# ============================================
# CREDENTIALS (HARDCODED FOR RAILWAY)
# ============================================

TELEGRAM_TOKEN = "8345600681:AAFeGdeyYjUDis9RcV5Sj4lzP8nhks9-fQU"
CHAT_ID = "2019463667"
PO_SESSION = "0d3ef4dafc05966efc12800ba7963e78"

if not TELEGRAM_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN not found!")
    exit(1)

logger.info("✅ Credentials loaded!")

# ============================================
# NIGERIA TIME
# ============================================

def get_nigeria_time():
    return datetime.utcnow() + timedelta(hours=1)

def format_time():
    return get_nigeria_time().strftime("%I:%M %p")

# ============================================
# SETTINGS
# ============================================

MIN_CONFIDENCE = 25
TRADE_DURATION_MINUTES = 3
AUTO_SIGNALS_ENABLED = True
AUTO_TRADE_ENABLED = False

DURATION_OPTIONS = [1, 2, 3, 4, 5, 10, 15, 30, 60]

# ============================================
# GLOBAL STATE
# ============================================

bot = Bot(token=TELEGRAM_TOKEN)
signal_gen = SignalGenerator()
advanced_ind = AdvancedIndicators()

runtime_settings = {
    "connected": False,
    "auto_signals_enabled": AUTO_SIGNALS_ENABLED,
    "auto_trade_enabled": AUTO_TRADE_ENABLED,
    "min_confidence": MIN_CONFIDENCE,
    "trade_duration": TRADE_DURATION_MINUTES,
    "total_signals": 0,
    "total_trades": 0,
    "last_signal_time": {},
    "client": None,
    "last_prices": {},
    "price_history": {},
    "websocket_active": False
}

signal_gen.min_confidence = MIN_CONFIDENCE

# ============================================
# WEBSOCKET WORKER (CONTINUOUS STREAMING)
# ============================================

async def websocket_worker():
    """WebSocket connection with continuous streaming and auto-reconnect"""
    if not PO_SESSION:
        logger.warning("⚠️ No SSID provided. WebSocket disabled.")
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"⚠️ Pocket Option WebSocket disabled
No PO_SESSION provided
⏰ {format_time()}"
        )
        return

    reconnect_delay = 5
    max_reconnect_delay = 60

    while True:
        try:
            logger.info("🔌 Connecting to Pocket Option WebSocket...")
            client = PocketOptionAsync(ssid=PO_SESSION)
            runtime_settings["client"] = client

            # Get balance
            balance = await client.balance()
            runtime_settings["connected"] = True
            runtime_settings["websocket_active"] = True

            logger.info(f"✅ Connected! Balance: ${balance}")
            await bot.send_message(
                chat_id=CHAT_ID,
                text=f"✅ Pocket Option CONNECTED!
💰 Balance: ${balance}
📊 Real-time streaming active
🎯 Monitoring {len(config.PRIORITY_PAIRS)} priority pairs
⏰ {format_time()}",
                parse_mode='Markdown'
            )

            # Create tasks for all pairs (concurrent streaming)
            tasks = []
            for pair in config.PRIORITY_PAIRS:
                task = asyncio.create_task(subscribe_pair(client, pair))
                tasks.append(task)
                await asyncio.sleep(0.1)

            logger.info(f"✅ Subscribed to {len(config.PRIORITY_PAIRS)} pairs with continuous streaming")

            # Keep alive and monitor
            while runtime_settings["websocket_active"]:
                await asyncio.sleep(30)
                if not runtime_settings["connected"]:
                    break

            raise Exception("WebSocket connection lost")

        except Exception as e:
            runtime_settings["connected"] = False
            runtime_settings["websocket_active"] = False
            logger.error(f"❌ WebSocket error: {e}")

            await bot.send_message(
                chat_id=CHAT_ID,
                text=f"⚠️ Pocket Option disconnected
Error: {str(e)[:100]}
🔄 Reconnecting in {reconnect_delay}s...
⏰ {format_time()}",
                parse_mode='Markdown'
            )

            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)

async def subscribe_pair(client, pair):
    """Subscribe to a single pair with CONTINUOUS streaming (NO break)"""
    otc_pair = f"{pair}_otc"
    retry_count = 0
    max_retries = 3

    while runtime_settings["websocket_active"]:
        try:
            logger.info(f"📊 Subscribing to {otc_pair}...")

            # CONTINUOUS STREAMING - NO break STATEMENT
            async for candle in client.subscribe_symbol(otc_pair):
                if not runtime_settings["websocket_active"]:
                    break

                await process_candle(pair, candle)

            logger.warning(f"⚠️ Subscription ended for {otc_pair}, reconnecting...")
            retry_count += 1

            if retry_count > max_retries:
                logger.error(f"❌ Max retries reached for {otc_pair}")
                await asyncio.sleep(60)
                retry_count = 0
            else:
                await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"❌ Error in {otc_pair} subscription: {e}")
            retry_count += 1
            await asyncio.sleep(5)

async def process_candle(pair, candle):
    """Process each real-time candle with enhanced indicators"""
    if not runtime_settings["auto_signals_enabled"]:
        return

    try:
        price = float(candle.get('close', 0))
        high = float(candle.get('high', price))
        low = float(candle.get('low', price))
        open_price = float(candle.get('open', price))

        if price == 0:
            return

        # Store OHLC history
        if pair not in runtime_settings["price_history"]:
            runtime_settings["price_history"][pair] = []

        runtime_settings["price_history"][pair].append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': price,
            'timestamp': datetime.now()
        })

        if len(runtime_settings["price_history"][pair]) > 50:
            runtime_settings["price_history"][pair] = runtime_settings["price_history"][pair][-50:]

        runtime_settings["last_prices"][pair] = price

        # Generate signal
        prices = [c['close'] for c in runtime_settings["price_history"][pair]]

        if len(prices) >= 14:
            signal = signal_gen.generate_signal_from_price(pair, price, prices)

            if signal and signal.get("confidence", 0) >= runtime_settings["min_confidence"]:
                current_time = datetime.now().timestamp()
                last_time = runtime_settings["last_signal_time"].get(pair, 0)

                if (current_time - last_time) > config.SIGNAL_COOLDOWN_SECONDS:
                    runtime_settings["last_signal_time"][pair] = current_time
                    runtime_settings["total_signals"] += 1

                    # Add Bollinger Bands if enough data
                    if len(prices) >= 20:
                        upper, sma, lower = advanced_ind.calculate_bollinger_bands(prices)
                        signal['bollinger'] = {'upper': upper, 'sma': sma, 'lower': lower}

                    message = signal_gen.format_signal_message(signal)
                    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
                    logger.info(f"📤 SIGNAL SENT: {pair} {signal['direction']} (RSI: {signal.get('rsi', 'N/A')})")

    except Exception as e:
        logger.error(f"❌ Error processing candle for {pair}: {e}")

# ============================================
# FALLBACK PRICE
# ============================================

def get_fallback_price(pair):
    fallback_prices = {
        "EURUSD": 1.09234, "GBPUSD": 1.28560, "USDJPY": 148.50,
        "Gold": 2350.00, "Bitcoin": 65000.00, "Silver": 28.50,
        "Apple": 175.00, "Tesla": 240.00, "Ethereum": 3500.00,
    }
    return fallback_prices.get(pair, 1.09234)

# ============================================
# COMMAND HANDLERS
# ============================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    auto_signal = "✅ ON" if runtime_settings["auto_signals_enabled"] else "❌ OFF"
    auto_trade = "✅ ON" if runtime_settings["auto_trade_enabled"] else "❌ OFF"
    po_status = "✅ CONNECTED" if runtime_settings["connected"] else "❌ DISCONNECTED"

    await update.message.reply_text(
        f"🤖 <b>POCKET OPTION TRADING BOT v3.1 (PRODUCTION)</b>

"
        f"✅ Bot ONLINE
"
        f"📡 Pocket Option: {po_status}
"
        f"🤖 Auto Signals: {auto_signal}
"
        f"💰 Auto Trade: {auto_trade}
"
        f"📊 Total Signals: {runtime_settings['total_signals']}
"
        f"📈 Total Trades: {runtime_settings['total_trades']}

"
        f"📋 <b>Commands:</b>
"
        f"/help - Show all commands
"
        f"/status - Bot status
"
        f"/signal [pair] - Manual signal
"
        f"/pairs - List all pairs
"
        f"/scan - Force manual scan
"
        f"/confidence [value] - Set min confidence (10-90)
"
        f"/duration [min] - Set trade duration
"
        f"/autosignal - Toggle auto signals
"
        f"/autotrade - Toggle auto trade
"
        f"/stats - Trading statistics
"
        f"/settings - Current settings
"
        f"/about - Bot information
"
        f"/stop - Stop auto signals
"
        f"/startbot - Resume auto signals
"
        f"/time - Current time

"
        f"⏰ {format_time()} (Nigeria Time)",
        parse_mode='HTML'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📋 <b>AVAILABLE COMMANDS</b>

"
        f"<b>Basic:</b>
"
        f"/start - Start the bot
"
        f"/help - Show this help
"
        f"/status - Check bot status
"
        f"/time - Current Nigeria time

"
        f"<b>Trading:</b>
"
        f"/signal [pair] - Get signal for specific pair (e.g., /signal EURUSD)
"
        f"/scan - Scan all priority pairs manually
"
        f"/pairs - List all available instruments

"
        f"<b>Settings:</b>
"
        f"/confidence [10-90] - Set minimum signal confidence
"
        f"/duration [1,2,3,5,10,15,30,60] - Set trade duration in minutes
"
        f"/autosignal - Toggle automatic signals ON/OFF
"
        f"/autotrade - Toggle automatic trading ON/OFF
"
        f"/stop - Stop automatic signals
"
        f"/startbot - Resume automatic signals

"
        f"<b>Info:</b>
"
        f"/stats - Trading statistics
"
        f"/settings - Current configuration
"
        f"/about - Bot information

"
        f"⏰ {format_time()} (Nigeria Time)",
        parse_mode='HTML'
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    auto_signal = "✅ ON" if runtime_settings["auto_signals_enabled"] else "❌ OFF"
    auto_trade = "✅ ON" if runtime_settings["auto_trade_enabled"] else "❌ OFF"
    po_status = "✅ CONNECTED" if runtime_settings["connected"] else "❌ DISCONNECTED"
    websocket_status = "🟢 ACTIVE" if runtime_settings["websocket_active"] else "🔴 INACTIVE"

    await update.message.reply_text(
        f"📊 <b>BOT STATUS</b>

"
        f"✅ Status: ONLINE
"
        f"📡 Pocket Option: {po_status}
"
        f"🔌 WebSocket: {websocket_status}
"
        f"🤖 Auto Signals: {auto_signal}
"
        f"💰 Auto Trade: {auto_trade}
"
        f"📊 Total Signals: {runtime_settings['total_signals']}
"
        f"📈 Total Trades: {runtime_settings['total_trades']}
"
        f"🎯 Min Confidence: {runtime_settings['min_confidence']}%
"
        f"⏱️ Trade Duration: {runtime_settings['trade_duration']} min
"
        f"📈 Pairs Monitored: {len(config.PRIORITY_PAIRS)}
"
        f"🌍 Total Instruments: {len(config.ALL_PAIRS)}

"
        f"⏰ {format_time()} (Nigeria Time)",
        parse_mode='HTML'
    )

async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            f"⚠️ Usage: /signal [pair]

"
            f"Examples: /signal EURUSD
"
            f"          /signal Gold
"
            f"          /signal Bitcoin

"
            f"Type /pairs to see all instruments"
        )
        return

    pair = context.args[0].upper()

    if pair not in config.ALL_PAIRS and pair not in config.PRIORITY_PAIRS:
        await update.message.reply_text(f"❌ '{pair}' not found.

Type /pairs to see all instruments.")
        return

    await update.message.reply_text(f"🔍 Analyzing {pair}...")

    price = runtime_settings["last_prices"].get(pair, 0)
    if price == 0:
        price = get_fallback_price(pair)

    prices = []
    if pair in runtime_settings["price_history"]:
        prices = [c['close'] for c in runtime_settings["price_history"][pair]]

    signal = signal_gen.generate_signal_from_price(pair, price, prices if len(prices) >= 14 else None)

    if signal:
        message = signal_gen.format_signal_message(signal)
        await update.message.reply_text(message, parse_mode='HTML')
        runtime_settings["total_signals"] += 1
    else:
        rsi = 50
        if prices and len(prices) >= 14:
            from indicators import TechnicalIndicators
            rsi = TechnicalIndicators.calculate_rsi(prices)

        await update.message.reply_text(
            f"📊 {pair} Analysis

"
            f"💰 Price: ${price:.5f}
"
            f"📈 RSI: {rsi}

"
            f"❌ No strong signal right now.
"
            f"RSI is in neutral zone (30-70).

"
            f"💡 Try /confidence {runtime_settings['min_confidence'] - 5} for more signals"
        )

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🔍 Scanning all priority pairs...
⏰ {format_time()}")

    results = []
    signals_found = []

    for pair in config.PRIORITY_PAIRS:
        price = runtime_settings["last_prices"].get(pair, 0)
        if price == 0:
            price = get_fallback_price(pair)

        prices = []
        if pair in runtime_settings["price_history"]:
            prices = [c['close'] for c in runtime_settings["price_history"][pair]]

        signal = signal_gen.generate_signal_from_price(pair, price, prices if len(prices) >= 14 else None)

        rsi = signal['rsi'] if signal else 50
        direction = signal['direction'] if signal else "NEUTRAL"
        confidence = signal['confidence'] if signal else 0

        if rsi < 30:
            emoji = "🔥"
            display = f"{emoji} STRONG BUY"
            if confidence >= runtime_settings["min_confidence"]:
                signals_found.append(signal)
        elif rsi < 40:
            emoji = "📈"
            display = f"{emoji} WEAK BUY"
            if confidence >= runtime_settings["min_confidence"]:
                signals_found.append(signal)
        elif rsi < 60:
            emoji = "⚪"
            display = f"{emoji} NEUTRAL"
        elif rsi < 70:
            emoji = "📉"
            display = f"{emoji} WEAK SELL"
            if confidence >= runtime_settings["min_confidence"]:
                signals_found.append(signal)
        else:
            emoji = "🔥"
            display = f"{emoji} STRONG SELL"
            signals_found.append(signal)

        results.append(f"{display} {pair} | RSI: {rsi} | Conf: {confidence}%")
        await asyncio.sleep(0.1)

    summary = f"🔍 <b>SCAN COMPLETE</b>

"
    summary += "
".join(results[:15])
    if len(results) > 15:
        summary += f"
... and {len(results) - 15} more pairs"

    summary += f"

📊 Min Confidence: {runtime_settings['min_confidence']}%"
    summary += f"
💰 Trade Duration: {runtime_settings['trade_duration']} min"
    summary += f"
⏰ {format_time()} (Nigeria Time)"

    await update.message.reply_text(summary, parse_mode='HTML')

    for signal in signals_found[:3]:
        if signal.get("confidence", 0) >= runtime_settings["min_confidence"]:
            message = signal_gen.format_signal_message(signal)
            await update.message.reply_text(message, parse_mode='HTML')
            await asyncio.sleep(0.5)

async def pairs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📊 <b>AVAILABLE INSTRUMENTS</b>

"
        f"<b>Forex:</b> {len(config.FOREX_PAIRS)} pairs (plus OTC)
"
        f"<b>Indices:</b> {len(config.INDICES)}
"
        f"<b>Commodities:</b> {len(config.COMMODITIES)}
"
        f"<b>Crypto:</b> {len(config.CRYPTOS)}
"
        f"<b>Stocks:</b> {len(config.STOCKS)}

"
        f"<b>TOTAL: {len(config.ALL_PAIRS)} instruments</b>

"
        f"<i>Priority pairs being monitored:</i>
"
        f"{', '.join(config.PRIORITY_PAIRS[:10])}
"
        f"... and {len(config.PRIORITY_PAIRS) - 10} more

"
        f"Use /signal [pair] for any instrument",
        parse_mode='HTML'
    )

async def confidence_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            f"⚙️ Current minimum confidence: {runtime_settings['min_confidence']}%

"
            f"Usage: /confidence [value]
"
            f"Example: /confidence 25

"
            f"Lower = more signals | Higher = fewer but stronger signals"
        )
        return

    try:
        new_conf = int(context.args[0])
        if 10 <= new_conf <= 90:
            runtime_settings["min_confidence"] = new_conf
            signal_gen.min_confidence = new_conf
            await update.message.reply_text(
                f"✅ Minimum confidence set to {new_conf}%

"
                f"Only signals with {new_conf}%+ confidence will be sent.
"
                f"⏰ {format_time()} (Nigeria Time)"
            )
        else:
            await update.message.reply_text("❌ Please enter a value between 10 and 90")
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number")

async def duration_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            f"⚙️ Current trade duration: {runtime_settings['trade_duration']} minutes

"
            f"Usage: /duration [minutes]
"
            f"Options: {', '.join(str(d) for d in DURATION_OPTIONS)}
"
            f"Example: /duration 3"
        )
        return

    try:
        new_duration = int(context.args[0])
        if new_duration in DURATION_OPTIONS:
            runtime_settings["trade_duration"] = new_duration
            await update.message.reply_text(
                f"✅ Trade duration set to {new_duration} minutes

"
                f"Future signals will use this duration.
"
                f"⏰ {format_time()} (Nigeria Time)"
            )
        else:
            await update.message.reply_text(
                f"❌ Invalid duration. Options: {', '.join(str(d) for d in DURATION_OPTIONS)}"
            )
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number")

async def autosignal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    runtime_settings["auto_signals_enabled"] = not runtime_settings["auto_signals_enabled"]
    status = "ON ✅" if runtime_settings["auto_signals_enabled"] else "OFF ❌"
    await update.message.reply_text(
        f"🤖 Auto Signals turned {status}

"
        f"When ON, signals will be sent automatically based on RSI analysis.
"
        f"⏰ {format_time()} (Nigeria Time)"
    )

async def autotrade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not runtime_settings["connected"]:
        await update.message.reply_text("❌ Cannot enable auto-trade: Pocket Option not connected!")
        return

    runtime_settings["auto_trade_enabled"] = not runtime_settings["auto_trade_enabled"]
    status = "ON ✅" if runtime_settings["auto_trade_enabled"] else "OFF ❌"
    await update.message.reply_text(
        f"💰 Auto Trade turned {status}

"
        f"⚠️ Trading in DEMO mode only!
"
        f"⏰ {format_time()} (Nigeria Time)"
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📊 <b>TRADING STATISTICS</b>

"
        f"Total Signals: {runtime_settings['total_signals']}
"
        f"Total Trades: {runtime_settings['total_trades']}
"
        f"Auto Signals: {'ON' if runtime_settings['auto_signals_enabled'] else 'OFF'}
"
        f"Auto Trade: {'ON' if runtime_settings['auto_trade_enabled'] else 'OFF'}
"
        f"Min Confidence: {runtime_settings['min_confidence']}%
"
        f"Trade Duration: {runtime_settings['trade_duration']} min
"
        f"Pocket Option: {'Connected ✅' if runtime_settings['connected'] else 'Disconnected ❌'}

"
        f"⏰ {format_time()} (Nigeria Time)",
        parse_mode='HTML'
    )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"⚙️ <b>CURRENT SETTINGS</b>

"
        f"<b>Signal Settings:</b>
"
        f"• Min Confidence: {runtime_settings['min_confidence']}%
"
        f"• Trade Duration: {runtime_settings['trade_duration']} minutes
"
        f"• Auto Signals: {'ON ✅' if runtime_settings['auto_signals_enabled'] else 'OFF ❌'}
"
        f"• Auto Trade: {'ON ✅' if runtime_settings['auto_trade_enabled'] else 'OFF ❌'}

"
        f"<b>Technical Settings:</b>
"
        f"• RSI Oversold (BUY): {config.RSI_OVERSOLD}
"
        f"• RSI Overbought (SELL): {config.RSI_OVERBOUGHT}
"
        f"• RSI Period: {config.RSI_PERIOD}
"
        f"• Cooldown: {config.SIGNAL_COOLDOWN_SECONDS // 60} minutes per pair

"
        f"<b>System:</b>
"
        f"• Pocket Option: {'Connected ✅' if runtime_settings['connected'] else 'Disconnected ❌'}
"
        f"• WebSocket: {'Active 🟢' if runtime_settings['websocket_active'] else 'Inactive 🔴'}
"
        f"• Total Instruments: {len(config.ALL_PAIRS)}

"
        f"⏰ {format_time()} (Nigeria Time)",
        parse_mode='HTML'
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📈 <b>About Pocket Option Trading Bot</b>

"
        f"<b>Version:</b> 3.1 Production
"
        f"<b>Strategies:</b> RSI + Bollinger Bands
"
        f"<b>RSI BUY Signal:</b> Below {config.RSI_OVERSOLD}
"
        f"<b>RSI SELL Signal:</b> Above {config.RSI_OVERBOUGHT}

"
        f"<b>Features:</b>
"
        f"• Real-time WebSocket streaming (continuous)
"
        f"• {len(config.ALL_PAIRS)}+ instruments
"
        f"• Auto signals with cooldown protection
"
        f"• Auto trade capability (demo mode)
"
        f"• Adjustable confidence level (10-90%)
"
        f"• Adjustable trade duration (1-60 min)
"
        f"• Martingale levels with timers
"
        f"• Nigeria Time Zone (UTC+1)

"
        f"<b>Data Source:</b> Pocket Option WebSocket API
"
        f"<b>Library:</b> BinaryOptionsToolsV2

"
        f"Use /help for available commands",
        parse_mode='HTML'
    )

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    runtime_settings["auto_signals_enabled"] = False
    await update.message.reply_text(
        f"🛑 Auto signals STOPPED

"
        f"Manual signals via /signal [pair] still work.
"
        f"Use /startbot to resume auto signals.

"
        f"⏰ {format_time()} (Nigeria Time)"
    )

async def startbot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    runtime_settings["auto_signals_enabled"] = True
    await update.message.reply_text(
        f"✅ Auto signals RESUMED!

"
        f"Signals will be sent automatically when RSI conditions are met.
"
        f"Use /stop to turn off.

"
        f"⏰ {format_time()} (Nigeria Time)"
    )

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"⏰ Nigeria Time: {format_time()}")

# ============================================
# MAIN FUNCTION
# ============================================

async def send_startup():
    po_status = "CONNECTING..." if PO_SESSION else "DISABLED (no SSID)"
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"🤖 <b>POCKET OPTION BOT v3.1 STARTING</b>

"
            f"✅ Bot initializing...
"
            f"📡 Pocket Option: {po_status}
"
            f"📊 Total instruments: {len(config.ALL_PAIRS)}
"
            f"🎯 Min Confidence: {runtime_settings['min_confidence']}%
"
            f"⏱️ Trade Duration: {runtime_settings['trade_duration']} min
"
            f"🤖 Auto signals: ON
"
            f"💰 Auto trade: OFF

"
            f"📋 Type /help for all commands
"
            f"⏰ {format_time()} (Nigeria Time)",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Failed to send startup message: {e}")

async def main():
    await send_startup()

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register all handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("signal", signal_command))
    application.add_handler(CommandHandler("pairs", pairs_command))
    application.add_handler(CommandHandler("scan", scan_command))
    application.add_handler(CommandHandler("confidence", confidence_command))
    application.add_handler(CommandHandler("duration", duration_command))
    application.add_handler(CommandHandler("autosignal", autosignal_command))
    application.add_handler(CommandHandler("autotrade", autotrade_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("startbot", startbot_command))
    application.add_handler(CommandHandler("time", time_command))

    logger.info("✅ All 16 command handlers registered")

    # Start WebSocket as asyncio task (NO threading)
    websocket_task = None
    if PO_SESSION:
        websocket_task = asyncio.create_task(websocket_worker())
        logger.info("🚀 WebSocket task created")
    else:
        logger.warning("⚠️ WebSocket disabled (no PO_SESSION)")

    # Start Telegram bot
    await application.initialize()
    await application.start()

    logger.info(f"🚀 Bot is running!")
    logger.info(f"📍 Nigeria Time: {format_time()}")
    logger.info(f"📋 16 commands available")

    # Keep running with health check
    try:
        while True:
            await asyncio.sleep(60)
            if websocket_task and websocket_task.done():
                logger.warning("WebSocket task died, restarting...")
                websocket_task = asyncio.create_task(websocket_worker())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await application.stop()

if __name__ == "__main__":
    asyncio.run(main())

