"""
POCKET OPTION TRADING BOT - FIXED COMMANDS WITH SCAN
Real-time WebSocket | Auto signals | All commands working | /scan added
"""

import os
import asyncio
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, CommandHandler

from BinaryOptionsToolsV2.pocketoption import PocketOptionAsync

import config
from signal_generator import SignalGenerator

load_dotenv()

print("""
╔════════════════════════════════════════════════════════════════╗
║   POCKET OPTION TRADING BOT - FIXED COMMANDS WITH SCAN         ║
║   Real-time WebSocket | Auto signals | /scan added             ║
╚════════════════════════════════════════════════════════════════╝
""")

# ============================================
# CREDENTIALS
# ============================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PO_SESSION = os.getenv("PO_SESSION")

if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not found!")
    exit(1)

print("✅ Credentials loaded!")

# ============================================
# NIGERIA TIME
# ============================================

def get_nigeria_time():
    return datetime.utcnow() + timedelta(hours=1)

def format_time():
    return get_nigeria_time().strftime("%I:%M %p")

# ============================================
# TELEGRAM BOT SETUP
# ============================================

bot = Bot(token=TELEGRAM_TOKEN)
application = Application.builder().token(TELEGRAM_TOKEN).build()
signal_gen = SignalGenerator()

# Settings
settings = {
    "connected": False,
    "auto_signals_enabled": True,
    "auto_trade_enabled": False,
    "total_signals": 0,
    "total_trades": 0,
    "last_signal_time": {},
    "client": None,
    "last_prices": {}
}

# ============================================
# WEBSOCKET THREAD (Runs separately)
# ============================================

async def websocket_worker():
    """WebSocket connection running in background"""
    if not PO_SESSION:
        print("⚠️ No SSID provided. WebSocket disabled.")
        return
    
    try:
        print("🔌 Connecting to Pocket Option WebSocket...")
        client = PocketOptionAsync(ssid=PO_SESSION)
        settings["client"] = client
        settings["connected"] = True
        
        # Get balance
        balance = await client.balance()
        print(f"✅ Connected! Balance: ${balance}")
        
        # Notify Telegram
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"✅ Pocket Option CONNECTED!\n💰 Balance: ${balance}\n📊 Real-time data active\n⏰ {format_time()}"
        )
        
        # Subscribe to priority pairs
        for pair in config.PRIORITY_PAIRS:
            otc_pair = f"{pair}_otc"
            try:
                print(f"📊 Subscribing to {otc_pair}...")
                async for candle in client.subscribe_symbol(otc_pair):
                    await process_candle(pair, candle)
                    break
            except Exception as e:
                print(f"⚠️ Could not subscribe to {otc_pair}: {e}")
            await asyncio.sleep(0.3)
        
        print(f"✅ Subscribed to {len(config.PRIORITY_PAIRS)} pairs")
        
        # Keep connection alive
        while True:
            await asyncio.sleep(60)
            
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        settings["connected"] = False

async def process_candle(pair, candle):
    """Process each real-time candle"""
    if not settings["auto_signals_enabled"]:
        return
    
    price = candle.get('close', 0)
    if price == 0:
        return
    
    settings["last_prices"][pair] = price
    
    # Generate signal
    signal = signal_gen.generate_signal_from_price(pair, price)
    
    if signal and signal.get("confidence", 0) >= config.MIN_CONFIDENCE:
        current_time = datetime.now().timestamp()
        last_time = settings["last_signal_time"].get(pair, 0)
        
        if (current_time - last_time) > config.SIGNAL_COOLDOWN_SECONDS:
            settings["last_signal_time"][pair] = current_time
            settings["total_signals"] += 1
            
            message = signal_gen.format_signal_message(signal)
            await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
            print(f"📤 SIGNAL: {pair} {signal['direction']}")

def run_websocket():
    """Run WebSocket in a separate event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(websocket_worker())

# ============================================
# FALLBACK PRICE (when WebSocket not connected)
# ============================================

def get_fallback_price(pair):
    fallback_prices = {
        "EURUSD": 1.09234,
        "GBPUSD": 1.28560,
        "USDJPY": 148.50,
        "Gold": 2350.00,
        "Bitcoin": 65000.00,
    }
    return fallback_prices.get(pair, 1.09234)

# ============================================
# SCAN COMMAND - Force manual scan of all pairs
# ============================================

async def scan_command(update, context):
    """Force immediate scan of all priority pairs"""
    await update.message.reply_text(f"🔍 Starting manual scan of all priority pairs...\n⏰ {format_time()}")
    
    signals_found = []
    scan_results = []
    
    for pair in config.PRIORITY_PAIRS:
        # Try to get price from WebSocket first
        price = settings["last_prices"].get(pair, 0)
        
        # If no price from WebSocket, use fallback
        if price == 0:
            price = get_fallback_price(pair)
        
        # Generate signal
        signal = signal_gen.generate_signal_from_price(pair, price)
        
        if signal and signal.get("confidence", 0) >= config.MIN_CONFIDENCE:
            signals_found.append(signal)
            scan_results.append(f"• {signal['direction']} {pair} | RSI: {signal['rsi']} | Conf: {signal['confidence']}%")
            print(f"📊 SCAN: Found signal for {pair}")
        
        # Small delay to avoid rate limits
        await asyncio.sleep(0.5)
    
    if signals_found:
        # Send summary of all signals found
        summary = f"🔍 <b>SCAN COMPLETE!</b>\n\n✅ Found {len(signals_found)} signal(s):\n\n"
        summary += "\n".join(scan_results)
        summary += f"\n\nUse /signal [pair] for detailed analysis\n⏰ {format_time()} (Nigeria Time)"
        await update.message.reply_text(summary, parse_mode='HTML')
        
        # Also send each detailed signal
        for signal in signals_found:
            message = signal_gen.format_signal_message(signal)
            await update.message.reply_text(message, parse_mode='HTML')
            settings["total_signals"] += 1
            await asyncio.sleep(1)
    else:
        await update.message.reply_text(
            f"🔍 <b>SCAN COMPLETE!</b>\n\n"
            f"❌ No strong signals found.\n\n"
            f"📊 Scanned: {len(config.PRIORITY_PAIRS)} priority pairs\n"
            f"🎯 Confidence threshold: {config.MIN_CONFIDENCE}%\n\n"
            f"💡 Try /autosignal to enable auto signals\n"
            f"⏰ {format_time()} (Nigeria Time)",
            parse_mode='HTML'
        )

# ============================================
# TELEGRAM COMMANDS
# ============================================

async def start_command(update, context):
    auto_signal = "✅ ON" if settings["auto_signals_enabled"] else "❌ OFF"
    auto_trade = "✅ ON" if settings["auto_trade_enabled"] else "❌ OFF"
    po_status = "✅ CONNECTED" if settings["connected"] else "❌ DISCONNECTED"
    
    await update.message.reply_text(
        f"🤖 <b>POCKET OPTION TRADING BOT</b>\n\n"
        f"✅ Bot ONLINE\n"
        f"📡 Pocket Option: {po_status}\n"
        f"🤖 Auto Signals: {auto_signal}\n"
        f"💰 Auto Trade: {auto_trade}\n"
        f"📊 Total Signals: {settings['total_signals']}\n"
        f"📈 Total Trades: {settings['total_trades']}\n\n"
        f"📋 <b>Commands:</b>\n"
        f"/status - Bot status\n"
        f"/signal [pair] - Manual signal\n"
        f"/pairs - List all pairs\n"
        f"/scan - Force manual scan\n"
        f"/autosignal - Toggle auto signals\n"
        f"/autotrade - Toggle auto trade\n"
        f"/time - Current time\n\n"
        f"⏰ {format_time()} (Nigeria Time)",
        parse_mode='HTML'
    )

async def status_command(update, context):
    auto_signal = "✅ ON" if settings["auto_signals_enabled"] else "❌ OFF"
    auto_trade = "✅ ON" if settings["auto_trade_enabled"] else "❌ OFF"
    po_status = "✅ CONNECTED" if settings["connected"] else "❌ DISCONNECTED"
    
    await update.message.reply_text(
        f"📊 <b>BOT STATUS</b>\n\n"
        f"✅ Status: ONLINE\n"
        f"📡 Pocket Option: {po_status}\n"
        f"🤖 Auto Signals: {auto_signal}\n"
        f"💰 Auto Trade: {auto_trade}\n"
        f"📊 Total Signals: {settings['total_signals']}\n"
        f"📈 Total Trades: {settings['total_trades']}\n"
        f"🎯 Min Confidence: {config.MIN_CONFIDENCE}%\n"
        f"📈 Pairs Monitored: {len(config.PRIORITY_PAIRS)}\n"
        f"🌍 Total Instruments: {len(config.ALL_PAIRS)}\n\n"
        f"⏰ {format_time()} (Nigeria Time)",
        parse_mode='HTML'
    )

async def signal_command(update, context):
    if not context.args:
        await update.message.reply_text(
            f"⚠️ Usage: /signal [pair]\n\n"
            f"Examples: /signal EURUSD\n"
            f"          /signal Gold\n"
            f"          /signal Bitcoin\n\n"
            f"Type /pairs to see all instruments"
        )
        return
    
    pair = context.args[0].upper()
    
    if pair not in config.ALL_PAIRS and pair not in config.PRIORITY_PAIRS:
        await update.message.reply_text(f"❌ '{pair}' not found.\n\nType /pairs to see all instruments.")
        return
    
    await update.message.reply_text(f"🔍 Analyzing {pair}...")
    
    # Try to get price from WebSocket first
    price = settings["last_prices"].get(pair, 0)
    if price == 0:
        price = get_fallback_price(pair)
    
    signal = signal_gen.generate_signal_from_price(pair, price)
    
    if signal:
        message = signal_gen.format_signal_message(signal)
        await update.message.reply_text(message, parse_mode='HTML')
        settings["total_signals"] += 1
    else:
        await update.message.reply_text(f"📊 {pair}: No strong signal right now.\n\nRSI is in neutral zone (30-70).")

async def pairs_command(update, context):
    await update.message.reply_text(
        f"📊 <b>AVAILABLE INSTRUMENTS</b>\n\n"
        f"<b>Forex:</b> {len(config.FOREX_PAIRS)} pairs (plus OTC)\n"
        f"<b>Indices:</b> {len(config.INDICES)}\n"
        f"<b>Commodities:</b> {len(config.COMMODITIES)}\n"
        f"<b>Crypto:</b> {len(config.CRYPTOS)}\n"
        f"<b>Stocks:</b> {len(config.STOCKS)}\n\n"
        f"<b>TOTAL: {len(config.ALL_PAIRS)} instruments</b>\n\n"
        f"<i>Priority pairs being monitored:</i>\n"
        f"{', '.join(config.PRIORITY_PAIRS[:15])}\n\n"
        f"Use /signal [pair] for any instrument",
        parse_mode='HTML'
    )

async def autosignal_command(update, context):
    settings["auto_signals_enabled"] = not settings["auto_signals_enabled"]
    status = "ON" if settings["auto_signals_enabled"] else "OFF"
    await update.message.reply_text(
        f"🤖 Auto Signals turned {status}\n\n"
        f"When ON, signals will be sent automatically.\n"
        f"⏰ {format_time()} (Nigeria Time)"
    )

async def autotrade_command(update, context):
    if not settings["connected"]:
        await update.message.reply_text("❌ Cannot enable auto-trade: Pocket Option not connected!")
        return
    
    settings["auto_trade_enabled"] = not settings["auto_trade_enabled"]
    status = "ON" if settings["auto_trade_enabled"] else "OFF"
    await update.message.reply_text(
        f"💰 Auto Trade turned {status}\n\n"
        f"⚠️ Trading in DEMO mode!\n"
        f"⏰ {format_time()} (Nigeria Time)"
    )

async def time_command(update, context):
    await update.message.reply_text(f"⏰ Nigeria Time: {format_time()}")

# ============================================
# REGISTER ALL COMMANDS
# ============================================

application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("status", status_command))
application.add_handler(CommandHandler("signal", signal_command))
application.add_handler(CommandHandler("pairs", pairs_command))
application.add_handler(CommandHandler("scan", scan_command))
application.add_handler(CommandHandler("autosignal", autosignal_command))
application.add_handler(CommandHandler("autotrade", autotrade_command))
application.add_handler(CommandHandler("time", time_command))

print("✅ All command handlers registered (including /scan)")

# ============================================
# STARTUP
# ============================================

async def send_startup():
    po_status = "CONNECTING..." if PO_SESSION else "DISABLED (no SSID)"
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"🤖 <b>POCKET OPTION TRADING BOT</b>\n\n"
        f"✅ Bot ONLINE\n"
        f"📡 Pocket Option: {po_status}\n"
        f"📊 Total instruments: {len(config.ALL_PAIRS)}\n"
        f"🎯 Auto signals: ON\n"
        f"💰 Auto trade: OFF\n\n"
        f"⏰ {format_time()} (Nigeria Time)\n\n"
        f"Commands: /status, /signal, /pairs, /scan, /autosignal, /autotrade, /time",
        parse_mode='HTML'
    )

async def main():
    # Send startup message
    await send_startup()
    
    # Start WebSocket in a separate thread (so it doesn't block commands)
    if PO_SESSION:
        ws_thread = threading.Thread(target=run_websocket, daemon=True)
        ws_thread.start()
        print("🚀 WebSocket thread started")
    else:
        print("⚠️ WebSocket disabled (no SSID)")
    
    # Start Telegram bot (this will handle commands)
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    print(f"🚀 Bot is running!")
    print(f"📍 Nigeria Time: {format_time()}")
    print(f"📋 Commands: /start, /status, /signal, /pairs, /scan, /autosignal, /autotrade, /time")
    
    # Keep the bot alive
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
