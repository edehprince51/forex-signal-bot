"""
POCKET OPTION TRADING BOT - BINANCE + ALPHA VANTAGE
Real-time crypto | 10-12 min auto signals | Nigeria Time
"""

import os
import asyncio
import aiohttp
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, CommandHandler
from binance import AsyncClient, BinanceSocketManager

import config
from signal_generator import SignalGenerator

load_dotenv()

print("""
╔════════════════════════════════════════════════════════════════╗
║   POCKET OPTION TRADING BOT - BINANCE + ALPHA VANTAGE          ║
║   Real-time crypto | 10-12 min auto signals | Nigeria Time     ║
╚════════════════════════════════════════════════════════════════╝
""")

# ============================================
# CREDENTIALS
# ============================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY", "ZBJN7KGNDPHVVCCW")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

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
    "auto_signals_enabled": True,
    "total_signals": 0,
    "last_signal_time": {},
    "crypto_prices": {},
    "forex_prices": {}
}

# ============================================
# ALPHA VANTAGE API (Forex, Indices, Stocks)
# ============================================

async def get_alpha_vantage_price(symbol, function="CURRENCY_EXCHANGE_RATE"):
    """Get price from Alpha Vantage API"""
    try:
        if function == "CURRENCY_EXCHANGE_RATE":
            # For forex: from_currency and to_currency
            from_currency = symbol[:3]
            to_currency = symbol[3:]
            url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={from_currency}&to_currency={to_currency}&apikey={ALPHA_VANTAGE_KEY}"
        else:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                data = await response.json()
                
                if function == "CURRENCY_EXCHANGE_RATE":
                    rate = data.get("Realtime Currency Exchange Rate", {}).get("5. Exchange Rate")
                    return float(rate) if rate else None
                else:
                    price = data.get("Global Quote", {}).get("05. price")
                    return float(price) if price else None
    except Exception as e:
        print(f"Alpha Vantage error for {symbol}: {e}")
        return None

async def scan_forex_pairs():
    """Scan all forex and stock pairs using Alpha Vantage"""
    prices = {}
    
    # Scan forex majors
    for pair, symbol in config.FOREX_MAJORS.items():
        price = await get_alpha_vantage_price(symbol)
        if price:
            prices[pair] = price
            signal_gen.update_price(pair, price)
        await asyncio.sleep(12)  # Respect rate limit (5 calls per minute)
    
    # Scan forex minors
    for pair, symbol in config.FOREX_MINORS.items():
        price = await get_alpha_vantage_price(symbol)
        if price:
            prices[pair] = price
            signal_gen.update_price(pair, price)
        await asyncio.sleep(12)
    
    # Scan indices
    for pair, symbol in config.INDICES.items():
        price = await get_alpha_vantage_price(symbol, "GLOBAL_QUOTE")
        if price:
            prices[pair] = price
            signal_gen.update_price(pair, price)
        await asyncio.sleep(12)
    
    # Scan commodities
    for pair, symbol in config.COMMODITIES.items():
        price = await get_alpha_vantage_price(symbol, "GLOBAL_QUOTE")
        if price:
            prices[pair] = price
            signal_gen.update_price(pair, price)
        await asyncio.sleep(12)
    
    # Scan stocks
    for pair, symbol in config.STOCKS.items():
        price = await get_alpha_vantage_price(symbol, "GLOBAL_QUOTE")
        if price:
            prices[pair] = price
            signal_gen.update_price(pair, price)
        await asyncio.sleep(12)
    
    settings["forex_prices"] = prices
    return prices

# ============================================
# BINANCE WEBSOCKET (Crypto - Real-time)
# ============================================

async def binance_worker():
    """Listen to real-time crypto prices from Binance WebSocket"""
    if not BINANCE_API_KEY or not BINANCE_SECRET_KEY:
        print("⚠️ Binance API keys not set. Crypto will use fallback.")
        return
    
    try:
        client = await AsyncClient.create(api_key=BINANCE_API_KEY, api_secret=BINANCE_SECRET_KEY)
        bm = BinanceSocketManager(client)
        
        # Subscribe to all crypto pairs
        socket = bm.multiplex_socket([f"{pair.lower()}@ticker" for pair in config.CRYPTO_PAIRS])
        
        async with socket as stream:
            async for msg in stream:
                if msg.get('data'):
                    symbol = msg['data']['s'].upper()
                    price = float(msg['data']['c'])
                    settings["crypto_prices"][symbol] = price
                    signal_gen.update_price(symbol, price)
    except Exception as e:
        print(f"Binance WebSocket error: {e}")

# ============================================
# AUTO SIGNAL SCANNER (Every 10-12 minutes)
# ============================================

async def auto_signal_scanner():
    """Scan all pairs and send signals automatically every 10-12 minutes"""
    while True:
        if not settings["auto_signals_enabled"]:
            await asyncio.sleep(30)
            continue
        
        print(f"🔍 Auto scan started at {format_time()}")
        
        # Scan crypto (from stored WebSocket prices)
        for pair in config.CRYPTO_PAIRS:
            price = settings["crypto_prices"].get(pair)
            if price:
                signal = signal_gen.generate_signal(pair, price, "Binance")
                await send_signal_if_valid(signal, pair)
        
        # Scan forex/stocks (via Alpha Vantage)
        await scan_forex_pairs()
        
        for pair, price in settings["forex_prices"].items():
            signal = signal_gen.generate_signal(pair, price, "Alpha Vantage")
            await send_signal_if_valid(signal, pair)
        
        print(f"✅ Auto scan completed at {format_time()}")
        
        # Wait 10-12 minutes before next scan
        await asyncio.sleep(config.SCAN_INTERVAL_SECONDS)

async def send_signal_if_valid(signal, pair):
    """Send signal if valid and not on cooldown"""
    if not signal:
        return
    
    current_time = datetime.now().timestamp()
    last_time = settings["last_signal_time"].get(pair, 0)
    
    if (current_time - last_time) > config.SIGNAL_COOLDOWN_SECONDS:
        settings["last_signal_time"][pair] = current_time
        settings["total_signals"] += 1
        
        message = signal_gen.format_signal_message(signal)
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
        print(f"📤 SIGNAL: {pair} {signal['direction']} (Confidence: {signal['confidence']}%)")

# ============================================
# TELEGRAM COMMANDS
# ============================================

async def start_command(update, context):
    auto_status = "✅ ON" if settings["auto_signals_enabled"] else "❌ OFF"
    await update.message.reply_text(
        f"🤖 <b>POCKET OPTION TRADING BOT</b>\n\n"
        f"✅ Bot ONLINE\n"
        f"🤖 Auto Signals: {auto_status}\n"
        f"📊 Total Signals: {settings['total_signals']}\n"
        f"📈 Crypto Pairs: {len(config.CRYPTO_PAIRS)}\n"
        f"📈 Forex/Stocks: {len(config.FOREX_MAJORS) + len(config.FOREX_MINORS) + len(config.INDICES) + len(config.COMMODITIES) + len(config.STOCKS)}\n\n"
        f"📋 <b>Commands:</b>\n"
        f"/status - Bot status\n"
        f"/signal [pair] - Manual signal\n"
        f"/pairs - List all pairs\n"
        f"/scan - Force manual scan\n"
        f"/autosignal - Toggle auto signals\n"
        f"/stats - Trading statistics\n"
        f"/time - Current time\n\n"
        f"⏰ {format_time()} (Nigeria Time)",
        parse_mode='HTML'
    )

async def status_command(update, context):
    auto_status = "✅ ON" if settings["auto_signals_enabled"] else "❌ OFF"
    await update.message.reply_text(
        f"📊 <b>BOT STATUS</b>\n\n"
        f"✅ Status: ONLINE\n"
        f"🤖 Auto Signals: {auto_status}\n"
        f"📊 Total Signals: {settings['total_signals']}\n"
        f"🎯 Min Confidence: {config.MIN_CONFIDENCE}%\n"
        f"⏱️ Scan Interval: {config.SCAN_INTERVAL_SECONDS // 60} minutes\n"
        f"📈 Crypto: {len(config.CRYPTO_PAIRS)} pairs\n"
        f"📈 Forex Majors: {len(config.FOREX_MAJORS)}\n"
        f"📈 Forex Minors: {len(config.FOREX_MINORS)}\n"
        f"📈 Indices: {len(config.INDICES)}\n"
        f"📈 Commodities: {len(config.COMMODITIES)}\n"
        f"📈 Stocks: {len(config.STOCKS)}\n\n"
        f"⏰ {format_time()} (Nigeria Time)",
        parse_mode='HTML'
    )

async def signal_command(update, context):
    if not context.args:
        await update.message.reply_text(
            f"⚠️ Usage: /signal [pair]\n\n"
            f"Examples: /signal BTCUSDT\n"
            f"          /signal EURUSD\n"
            f"          /signal Gold\n\n"
            f"Type /pairs to see all instruments"
        )
        return
    
    pair = context.args[0].upper()
    await update.message.reply_text(f"🔍 Analyzing {pair}...")
    
    price = None
    data_source = None
    
    # Check crypto first
    if pair in config.CRYPTO_PAIRS:
        price = settings["crypto_prices"].get(pair)
        data_source = "Binance"
    
    # Check forex
    if not price and pair in config.FOREX_MAJORS:
        price = await get_alpha_vantage_price(config.FOREX_MAJORS[pair])
        data_source = "Alpha Vantage"
    
    if not price and pair in config.FOREX_MINORS:
        price = await get_alpha_vantage_price(config.FOREX_MINORS[pair])
        data_source = "Alpha Vantage"
    
    if not price:
        await update.message.reply_text(f"❌ Could not fetch price for {pair}.")
        return
    
    signal = signal_gen.generate_signal(pair, price, data_source)
    
    if signal:
        message = signal_gen.format_signal_message(signal)
        await update.message.reply_text(message, parse_mode='HTML')
    else:
        history = signal_gen.price_history.get(pair, [])
        rsi = signal_gen.calculate_rsi(history) if len(history) >= 15 else 50
        await update.message.reply_text(
            f"📊 {pair} Analysis\n\n"
            f"💰 Price: ${price:.5f}\n"
            f"📈 RSI: {rsi}\n\n"
            f"❌ No strong signal right now.\n"
            f"RSI is in neutral zone (30-70)."
        )

async def pairs_command(update, context):
    await update.message.reply_text(
        f"📊 <b>AVAILABLE INSTRUMENTS</b>\n\n"
        f"<b>Crypto ({len(config.CRYPTO_PAIRS)})</b>\n"
        f"{', '.join(config.CRYPTO_PAIRS[:15])}...\n\n"
        f"<b>Forex Majors ({len(config.FOREX_MAJORS)})</b>\n"
        f"{', '.join(config.FOREX_MAJORS.keys())}\n\n"
        f"<b>Forex Minors ({len(config.FOREX_MINORS)})</b>\n"
        f"{', '.join(list(config.FOREX_MINORS.keys())[:10])}...\n\n"
        f"<b>Indices ({len(config.INDICES)})</b>\n"
        f"{', '.join(config.INDICES.keys())}\n\n"
        f"<b>Commodities ({len(config.COMMODITIES)})</b>\n"
        f"{', '.join(config.COMMODITIES.keys())}\n\n"
        f"<b>Stocks ({len(config.STOCKS)})</b>\n"
        f"{', '.join(config.STOCKS.keys())}\n\n"
        f"<b>TOTAL: {len(config.CRYPTO_PAIRS) + len(config.FOREX_MAJORS) + len(config.FOREX_MINORS) + len(config.INDICES) + len(config.COMMODITIES) + len(config.STOCKS)} instruments</b>\n\n"
        f"Use /signal [pair] for any instrument",
        parse_mode='HTML'
    )

async def scan_command(update, context):
    await update.message.reply_text(f"🔍 Manual scan started...\n⏰ {format_time()}")
    
    signals_found = 0
    
    # Check crypto
    for pair in config.CRYPTO_PAIRS[:15]:  # Limit to 15 for speed
        price = settings["crypto_prices"].get(pair)
        if price:
            signal = signal_gen.generate_signal(pair, price, "Binance")
            if signal:
                signals_found += 1
                message = signal_gen.format_signal_message(signal)
                await update.message.reply_text(message, parse_mode='HTML')
        await asyncio.sleep(0.5)
    
    await update.message.reply_text(
        f"🔍 <b>SCAN COMPLETE!</b>\n\n"
        f"✅ Found {signals_found} signal(s)\n"
        f"⏰ {format_time()} (Nigeria Time)",
        parse_mode='HTML'
    )

async def autosignal_command(update, context):
    settings["auto_signals_enabled"] = not settings["auto_signals_enabled"]
    status = "ON" if settings["auto_signals_enabled"] else "OFF"
    await update.message.reply_text(
        f"🤖 Auto Signals turned {status}\n\n"
        f"When ON, signals will be sent automatically every {config.SCAN_INTERVAL_SECONDS // 60} minutes.\n"
        f"⏰ {format_time()} (Nigeria Time)"
    )

async def stats_command(update, context):
    await update.message.reply_text(
        f"📊 <b>TRADING STATISTICS</b>\n\n"
        f"Total Signals: {settings['total_signals']}\n"
        f"Auto Signals: {'ON' if settings['auto_signals_enabled'] else 'OFF'}\n"
        f"Min Confidence: {config.MIN_CONFIDENCE}%\n"
        f"Scan Interval: {config.SCAN_INTERVAL_SECONDS // 60} minutes\n\n"
        f"⏰ {format_time()} (Nigeria Time)",
        parse_mode='HTML'
    )

async def time_command(update, context):
    await update.message.reply_text(f"⏰ Nigeria Time: {format_time()}")

# Register all commands
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("status", status_command))
application.add_handler(CommandHandler("signal", signal_command))
application.add_handler(CommandHandler("pairs", pairs_command))
application.add_handler(CommandHandler("scan", scan_command))
application.add_handler(CommandHandler("autosignal", autosignal_command))
application.add_handler(CommandHandler("stats", stats_command))
application.add_handler(CommandHandler("time", time_command))

print("✅ All command handlers registered")

# ============================================
# STARTUP
# ============================================

async def send_startup():
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"🤖 <b>POCKET OPTION TRADING BOT</b>\n\n"
        f"✅ Bot ONLINE\n"
        f"📊 Crypto: {len(config.CRYPTO_PAIRS)} pairs (Binance WebSocket)\n"
        f"📊 Forex/Stocks: {len(config.FOREX_MAJORS) + len(config.FOREX_MINORS) + len(config.INDICES) + len(config.COMMODITIES) + len(config.STOCKS)} pairs (Alpha Vantage)\n"
        f"🤖 Auto signals: ON (every {config.SCAN_INTERVAL_SECONDS // 60} minutes)\n"
        f"🎯 Min Confidence: {config.MIN_CONFIDENCE}%\n\n"
        f"⏰ {format_time()} (Nigeria Time)\n\n"
        f"Type /help for commands",
        parse_mode='HTML'
    )

async def main():
    await send_startup()
    
    # Start Binance WebSocket in background
    asyncio.create_task(binance_worker())
    
    # Start auto signal scanner
    asyncio.create_task(auto_signal_scanner())
    
    # Start Telegram bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    print(f"🚀 Bot is running!")
    print(f"📍 Nigeria Time: {format_time()}")
    print(f"📋 Commands: /start, /status, /signal, /pairs, /scan, /autosignal, /stats, /time")
    
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())