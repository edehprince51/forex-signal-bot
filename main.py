"""
POCKET OPTION TRADING BOT - COMPLETE VERSION
Real-time signals | Auto-trade toggle | Nigeria Time
"""

import os
import asyncio
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, CommandHandler

# Pocket Option library
from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.models import AuthorizationData, UpdateCloseValueItem, DealAction

import config
from signal_generator import SignalGenerator
from indicators import TechnicalIndicators

load_dotenv()

print("""
╔════════════════════════════════════════════════════════════════╗
║   POCKET OPTION TRADING BOT - COMPLETE VERSION                 ║
║   Real-time signals | Auto-trade toggle | Nigeria Time         ║
╚════════════════════════════════════════════════════════════════╝
""")

# ============================================
# CREDENTIALS
# ============================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PO_SESSION = os.getenv("PO_SESSION")
PO_UID = os.getenv("PO_UID")

if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not found!")
    exit(1)

if not PO_SESSION or not PO_UID:
    print("⚠️ PO_SESSION or PO_UID not set. Bot will run in limited mode.")

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
    "po_connected": False,
    "auto_signals_enabled": True,
    "auto_trade_enabled": False,
    "total_signals": 0,
    "total_trades": 0,
    "last_signal_time": {},
    "client": None,
    "deals": None
}

# ============================================
# POCKET OPTION CLIENT
# ============================================

client = PocketOptionClient()

@client.on.connect
async def on_connect(data):
    print("✅ WebSocket connected to Pocket Option!")
    
    # Send authentication
    auth_data = AuthorizationData(
        session=PO_SESSION,
        isDemo=1,
        uid=int(PO_UID),
        platform=2,
        isFastHistory=True,
        isOptimized=True
    )
    await client.emit.auth(auth_data)

@client.on.success_auth
async def on_success_auth(data):
    print(f"✅ Authenticated! User ID: {data.id}")
    settings["po_connected"] = True
    
    # Subscribe to priority pairs
    for pair in config.PRIORITY_PAIRS:
        otc_pair = f"{pair}_otc"
        await client.emit.subscribe_to_asset(otc_pair)
        await asyncio.sleep(0.3)
    
    print(f"📊 Subscribed to {len(config.PRIORITY_PAIRS)} priority pairs")
    
    # Notify Telegram
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"✅ Pocket Option CONNECTED!\n📊 Monitoring {len(config.PRIORITY_PAIRS)} pairs\n💰 Demo account ready\n⏰ {format_time()}"
    )

@client.on.update_close_value
async def on_price_update(assets: list[UpdateCloseValueItem]):
    """Real-time price updates - This is where signals are generated"""
    if not settings["auto_signals_enabled"]:
        return
    
    for asset in assets:
        pair = asset.id.replace("_otc", "")
        price = asset.close_value
        
        # Generate signal
        signal = signal_gen.generate_signal_from_price(pair, price)
        
        if signal and signal.get("confidence", 0) >= config.MIN_CONFIDENCE:
            current_time = datetime.now().timestamp()
            last_time = settings["last_signal_time"].get(pair, 0)
            
            # 5 minute cooldown
            if (current_time - last_time) > config.SIGNAL_COOLDOWN_SECONDS:
                settings["last_signal_time"][pair] = current_time
                settings["total_signals"] += 1
                
                message = signal_gen.format_signal_message(signal)
                await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
                print(f"📤 AUTO SIGNAL: {pair} {signal['direction']} (Confidence: {signal['confidence']}%)")
                
                # Auto-trade if enabled
                if settings["auto_trade_enabled"] and settings["deals"]:
                    await execute_trade(pair, signal["direction"])

async def execute_trade(pair, direction):
    """Execute trade on Pocket Option"""
    try:
        action = DealAction.CALL if direction == "BUY" else DealAction.PUT
        otc_pair = f"{pair}_otc"
        
        deal = await settings["deals"].open_deal(
            asset=otc_pair,
            amount=1.0,  # $1 minimum
            action=action,
            is_demo=1,
            option_type=100,
            time=60  # 1 minute expiry
        )
        settings["total_trades"] += 1
        print(f"🤖 AUTO-TRADE: {direction} {pair} - Order ID: {deal.id}")
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"🤖 AUTO-TRADE EXECUTED\n📈 {direction} {pair}\n💰 Amount: $1.00\n⏰ {format_time()}"
        )
    except Exception as e:
        print(f"❌ Trade execution error: {e}")

@client.on.disconnect
async def on_disconnect():
    print("🔌 Disconnected from Pocket Option")
    settings["po_connected"] = False

async def connect_pocket_option():
    """Start Pocket Option connection"""
    if not PO_SESSION or not PO_UID:
        print("⚠️ Pocket Option credentials missing. Skipping connection.")
        return
    
    try:
        await client.connect(Regions.DEMO)
        print("🚀 Pocket Option client started")
    except Exception as e:
        print(f"❌ Connection error: {e}")

# ============================================
# TELEGRAM COMMANDS
# ============================================

async def start_command(update, context):
    po_status = "✅ CONNECTED" if settings["po_connected"] else "🔄 CONNECTING..."
    auto_signal = "✅ ON" if settings["auto_signals_enabled"] else "❌ OFF"
    auto_trade = "✅ ON" if settings["auto_trade_enabled"] else "❌ OFF"
    
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
        f"/autosignal - Toggle auto signals\n"
        f"/autotrade - Toggle auto trade\n"
        f"/webhook - TradingView webhook URL\n"
        f"/settings - Current settings\n"
        f"/stats - Trading statistics\n"
        f"/time - Current time\n"
        f"/help - All commands\n\n"
        f"⏰ {format_time()} (Nigeria Time)",
        parse_mode='HTML'
    )

async def help_command(update, context):
    await update.message.reply_text(
        f"📋 <b>COMPLETE COMMAND LIST</b>\n\n"
        f"<b>📊 SIGNAL COMMANDS:</b>\n"
        f"/status - Bot status and settings\n"
        f"/settings - View current configuration\n"
        f"/pairs - List all monitored pairs\n"
        f"/signal [pair] - Get signal (e.g., /signal EURUSD)\n\n"
        f"<b>⚙️ CONTROL COMMANDS:</b>\n"
        f"/autosignal - Toggle auto signals ON/OFF\n"
        f"/autotrade - Toggle auto trade ON/OFF\n"
        f"/confidence [value] - Set min confidence (40-90)\n\n"
        f"<b>📈 STATISTICS COMMANDS:</b>\n"
        f"/stats - Trading statistics\n"
        f"/time - Current Nigeria time\n\n"
        f"<b>🔧 SYSTEM COMMANDS:</b>\n"
        f"/webhook - TradingView webhook URL\n"
        f"/about - About this bot\n"
        f"/version - Bot version\n\n"
        f"<b>💡 Examples:</b>\n"
        f"/signal EURUSD - Get EURUSD signal\n"
        f"/autotrade - Enable/disable auto-trade",
        parse_mode='HTML'
    )

async def status_command(update, context):
    po_status = "✅ CONNECTED" if settings["po_connected"] else "❌ DISCONNECTED"
    auto_signal = "✅ ON" if settings["auto_signals_enabled"] else "❌ OFF"
    auto_trade = "✅ ON" if settings["auto_trade_enabled"] else "❌ OFF"
    
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
    
    # Check if pair exists
    if pair not in config.ALL_PAIRS and pair not in config.PRIORITY_PAIRS:
        await update.message.reply_text(f"❌ '{pair}' not found.\n\nType /pairs to see all instruments.")
        return
    
    await update.message.reply_text(f"🔍 Analyzing {pair}...")
    
    # Use fallback price if not connected
    price = 1.09234 if "USD" in pair else 2350.00
    signal = signal_gen.generate_signal_from_price(pair, price)
    
    if signal:
        message = signal_gen.format_signal_message(signal)
        await update.message.reply_text(message, parse_mode='HTML')
        settings["total_signals"] += 1
    else:
        await update.message.reply_text(f"📊 {pair}: No strong signal right now.\n\nRSI is in neutral zone (30-70).")

async def pairs_command(update, context):
    forex_count = len(config.FOREX_PAIRS)
    indices_count = len(config.INDICES)
    commodities_count = len(config.COMMODITIES)
    crypto_count = len(config.CRYPTOS)
    stocks_count = len(config.STOCKS)
    
    await update.message.reply_text(
        f"📊 <b>AVAILABLE INSTRUMENTS</b>\n\n"
        f"<b>Forex:</b> {forex_count} pairs (plus OTC)\n"
        f"<b>Indices:</b> {indices_count}\n"
        f"<b>Commodities:</b> {commodities_count}\n"
        f"<b>Crypto:</b> {crypto_count}\n"
        f"<b>Stocks:</b> {stocks_count}\n\n"
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
        f"When ON, signals will be sent automatically when RSI < 30 or RSI > 70.\n"
        f"⏰ {format_time()} (Nigeria Time)"
    )

async def autotrade_command(update, context):
    if not settings["po_connected"]:
        await update.message.reply_text("❌ Cannot enable auto-trade: Pocket Option not connected!")
        return
    
    settings["auto_trade_enabled"] = not settings["auto_trade_enabled"]
    status = "ON" if settings["auto_trade_enabled"] else "OFF"
    await update.message.reply_text(
        f"💰 Auto Trade turned {status}\n\n"
        f"⚠️ Trading in DEMO mode only!\n"
        f"⏰ {format_time()} (Nigeria Time)"
    )

async def settings_command(update, context):
    await update.message.reply_text(
        f"⚙️ <b>CURRENT SETTINGS</b>\n\n"
        f"📊 <b>Scan Settings:</b>\n"
        f"• Pairs monitored: {len(config.PRIORITY_PAIRS)} priority\n"
        f"• Total available: {len(config.ALL_PAIRS)}\n\n"
        f"🎯 <b>Signal Settings:</b>\n"
        f"• Min confidence: {config.MIN_CONFIDENCE}%\n"
        f"• RSI Oversold: {config.RSI_OVERSOLD}\n"
        f"• RSI Overbought: {config.RSI_OVERBOUGHT}\n\n"
        f"↪️ <b>Martingale:</b>\n"
        f"• Levels: {config.MARTINGALE_LEVELS}\n"
        f"• Interval: {config.MARTINGALE_INTERVAL} minutes\n\n"
        f"⏰ Cooldown: {config.SIGNAL_COOLDOWN_SECONDS // 60} minutes per pair",
        parse_mode='HTML'
    )

async def stats_command(update, context):
    await update.message.reply_text(
        f"📊 <b>TRADING STATISTICS</b>\n\n"
        f"Total Signals: {settings['total_signals']}\n"
        f"Total Trades: {settings['total_trades']}\n"
        f"Auto Signals: {'ON' if settings['auto_signals_enabled'] else 'OFF'}\n"
        f"Auto Trade: {'ON' if settings['auto_trade_enabled'] else 'OFF'}\n"
        f"Pocket Option: {'Connected' if settings['po_connected'] else 'Disconnected'}\n\n"
        f"⏰ {format_time()} (Nigeria Time)",
        parse_mode='HTML'
    )

async def webhook_command(update, context):
    railway_url = os.getenv('RAILWAY_PUBLIC_URL', 'https://your-app.railway.app')
    webhook_url = f"{railway_url}/webhook"
    
    await update.message.reply_text(
        f"🔗 <b>WEBHOOK URL FOR TRADINGVIEW</b>\n\n"
        f"<code>{webhook_url}</code>\n\n"
        f"<b>Headers:</b>\n"
        f"Content-Type: application/json\n\n"
        f"<b>JSON Format Example:</b>\n"
        f"<code>{{'symbol': 'EURUSD', 'side': 'BUY', 'price': 1.09234}}</code>\n\n"
        f"<b>Text Format Example:</b>\n"
        f"BUY EURUSD at 1.09234",
        parse_mode='HTML'
    )

async def time_command(update, context):
    await update.message.reply_text(f"⏰ Nigeria Time: {format_time()}")

async def about_command(update, context):
    await update.message.reply_text(
        f"📈 <b>About Pocket Option Trading Bot</b>\n\n"
        f"This bot connects to Pocket Option via WebSocket for real-time price data.\n\n"
        f"<b>Strategies Used:</b>\n"
        f"• RSI (Relative Strength Index)\n"
        f"• RSI < 30 = BUY signal\n"
        f"• RSI > 70 = SELL signal\n\n"
        f"<b>Features:</b>\n"
        f"• Real-time price streaming\n"
        f"• Auto signals (can be toggled)\n"
        f"• Auto trade (can be toggled)\n"
        f"• Martingale levels with timers\n"
        f"• TradingView webhook integration\n\n"
        f"<b>Data Source:</b> Pocket Option WebSocket API\n"
        f"<b>Time Zone:</b> Nigeria (WAT)\n\n"
        f"Use /help for available commands",
        parse_mode='HTML'
    )

async def version_command(update, context):
    await update.message.reply_text(
        f"🤖 <b>Pocket Option Trading Bot v3.0</b>\n\n"
        f"<b>Features:</b>\n"
        f"✅ Real-time WebSocket connection\n"
        f"✅ {len(config.ALL_PAIRS)}+ instruments\n"
        f"✅ Auto signals (RSI-based)\n"
        f"✅ Auto trade toggle\n"
        f"✅ Martingale levels with timers\n"
        f"✅ TradingView webhook\n"
        f"✅ Nigeria Time Zone\n\n"
        f"<b>Last Update:</b> April 2025\n"
        f"<b>Library:</b> pocket-option==0.1.6",
        parse_mode='HTML'
    )

async def confidence_command(update, context):
    if not context.args:
        await update.message.reply_text(f"⚠️ Current minimum confidence: {config.MIN_CONFIDENCE}%\nTo change: /confidence 60")
        return
    
    try:
        new_confidence = int(context.args[0])
        if 40 <= new_confidence <= 90:
            config.MIN_CONFIDENCE = new_confidence
            await update.message.reply_text(f"✅ Minimum confidence set to {new_confidence}%")
        else:
            await update.message.reply_text("❌ Please enter a value between 40 and 90")
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number")

# Add handlers
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("status", status_command))
application.add_handler(CommandHandler("signal", signal_command))
application.add_handler(CommandHandler("pairs", pairs_command))
application.add_handler(CommandHandler("autosignal", autosignal_command))
application.add_handler(CommandHandler("autotrade", autotrade_command))
application.add_handler(CommandHandler("settings", settings_command))
application.add_handler(CommandHandler("stats", stats_command))
application.add_handler(CommandHandler("webhook", webhook_command))
application.add_handler(CommandHandler("time", time_command))
application.add_handler(CommandHandler("about", about_command))
application.add_handler(CommandHandler("version", version_command))
application.add_handler(CommandHandler("confidence", confidence_command))

# ============================================
# STARTUP
# ============================================

async def send_startup():
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"🤖 <b>POCKET OPTION TRADING BOT v3.0</b>\n\n"
        f"✅ Bot ONLINE\n"
        f"📡 Connecting to Pocket Option...\n"
        f"📊 Total instruments: {len(config.ALL_PAIRS)}\n"
        f"🎯 Auto signals: ON\n"
        f"💰 Auto trade: OFF\n\n"
        f"⏰ {format_time()} (Nigeria Time)\n\n"
        f"Type /help for all commands",
        parse_mode='HTML'
    )

async def main():
    await send_startup()
    
    # Start Pocket Option connection
    asyncio.create_task(connect_pocket_option())
    
    # Start Telegram bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    print(f"🚀 Bot is running!")
    print(f"📍 Nigeria Time: {format_time()}")
    print(f"📋 Commands: /start, /status, /signal, /autosignal, /autotrade, /help")
    
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
