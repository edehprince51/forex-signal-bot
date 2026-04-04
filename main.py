"""
IQ TRADING BOT - STABLE VERSION
REAL-TIME SIGNALS | NIGERIA TIME
"""

import os
import time
import requests
import asyncio
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, CommandHandler

load_dotenv()

print("""
╔════════════════════════════════════════════════════════════════╗
║   IQ TRADING BOT - STABLE EDITION                              ║
║   REAL-TIME SIGNALS | NIGERIA TIME                             ║
╚════════════════════════════════════════════════════════════════╝
""")

# Get credentials
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not found!")
    exit(1)

if not CHAT_ID:
    print("❌ TELEGRAM_CHAT_ID not found!")
    exit(1)

print("✅ Credentials loaded!")

# Nigeria Time Zone (UTC+1)
def get_nigeria_time():
    return datetime.utcnow() + timedelta(hours=1)

def format_time(dt=None):
    if dt is None:
        dt = get_nigeria_time()
    return dt.strftime("%I:%M %p")

# Create bot
bot = Bot(token=TELEGRAM_TOKEN)
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Settings
settings = {
    "total_signals": 0,
    "last_signal_time": {}
}

# ============================================
# SIMPLIFIED PAIRS (from your images)
# ============================================

# Priority pairs that definitely work
PRIORITY_PAIRS = [
    {"name": "EUR/USD", "symbol": "EURUSD=X", "flag": "🇪🇺🇺🇸"},
    {"name": "GBP/USD", "symbol": "GBPUSD=X", "flag": "🇬🇧🇺🇸"},
    {"name": "USD/JPY", "symbol": "JPY=X", "flag": "🇺🇸🇯🇵"},
    {"name": "Gold", "symbol": "GC=F", "flag": "🥇"},
    {"name": "Bitcoin", "symbol": "BTC-USD", "flag": "₿"},
    {"name": "Ethereum", "symbol": "ETH-USD", "flag": "⟠"},
    {"name": "US100", "symbol": "^IXIC", "flag": "📊"},
    {"name": "Apple", "symbol": "AAPL", "flag": "🍎"},
    {"name": "Tesla", "symbol": "TSLA", "flag": "🚗"},
]

# ============================================
# PRICE & RSI FUNCTIONS
# ============================================

def get_price(symbol):
    """Get real price from Yahoo Finance"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('chart', {}).get('result', [])
            if result:
                price = result[0].get('meta', {}).get('regularMarketPrice')
                if price:
                    return round(price, 5 if price < 100 else 2)
        return None
    except Exception as e:
        print(f"Price error: {e}")
        return None

def calculate_rsi(prices):
    """Calculate RSI from price list"""
    if len(prices) < 15:
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
    
    avg_gain = sum(gains[-14:]) / 14 if gains else 0
    avg_loss = sum(losses[-14:]) / 14 if losses else 0
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 1)

def get_rsi(symbol):
    """Get RSI for a symbol"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=5m"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('chart', {}).get('result', [])
            if result:
                closes = result[0].get('indicators', {}).get('quote', [{}])[0].get('close', [])
                closes = [c for c in closes if c is not None]
                if len(closes) > 14:
                    return calculate_rsi(closes)
        return 50
    except Exception as e:
        print(f"RSI error for {symbol}: {e}")
        return 50

def format_signal(pair_name, flag, direction, confidence, price, rsi, reason, is_otc=False):
    """Format signal message with 3-minute head start and martingale"""
    entry_time = get_nigeria_time() + timedelta(minutes=3)
    otc_tag = " (OTC)" if is_otc else ""
    
    martingale_lines = []
    for i in range(1, 4):
        level_time = entry_time + timedelta(minutes=i * 3)
        martingale_lines.append(f" Level {i} → {level_time.strftime('%I:%M %p')}")
    
    emoji = "🟢🟢" if confidence >= 75 and direction == "BUY" else "🟢" if direction == "BUY" else "🔴🔴" if confidence >= 75 else "🔴"
    
    tp_mult = 1.005 if direction == "BUY" else 0.995
    sl_mult = 0.995 if direction == "BUY" else 1.005
    
    return f"""
🔔 <b>NEW SIGNAL!</b>

🎫 Trade: {flag} {pair_name}{otc_tag}
⏳ Timer: 3 minutes
➡️ Entry: {entry_time.strftime('%I:%M %p')}
📈 Direction: {direction} {emoji}

💪 <b>Confidence:</b> {confidence}%

📊 <b>Technical Analysis:</b>
• RSI: {rsi}
• {reason}

↪️ <b>Martingale Levels:</b>
{chr(10).join(martingale_lines)}

💰 <b>Entry Price:</b> ${price:.5f}
🎯 <b>Take Profit:</b> ${(price * tp_mult):.5f}
🛑 <b>Stop Loss:</b> ${(price * sl_mult):.5f}

⏰ {format_time()} (Nigeria Time)
"""

# ============================================
# MONITOR FUNCTION (Runs every minute)
# ============================================

async def monitor_pairs():
    """Monitor pairs and send signals when RSI < 30 or > 70"""
    print("🔄 Monitor started - checking every 60 seconds")
    
    while True:
        try:
            for pair in PRIORITY_PAIRS:
                try:
                    name = pair["name"]
                    symbol = pair["symbol"]
                    flag = pair["flag"]
                    
                    # Get RSI
                    rsi = get_rsi(symbol)
                    price = get_price(symbol)
                    
                    if price is None:
                        continue
                    
                    # Check if we should send signal (avoid duplicates within 5 minutes)
                    current_time = time.time()
                    last_time = settings["last_signal_time"].get(name, 0)
                    
                    # Send signal on RSI condition
                    if rsi <= 30 and (current_time - last_time) > 300:
                        settings["last_signal_time"][name] = current_time
                        settings["total_signals"] += 1
                        
                        confidence = min(95, int(75 - rsi + 20))
                        reason = f"RSI Oversold ({rsi}) - Price may reverse UP"
                        
                        message = format_signal(name, flag, "BUY", confidence, price, rsi, reason, False)
                        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
                        print(f"📤 SIGNAL SENT: {name} BUY (RSI: {rsi}) at {format_time()}")
                        
                    elif rsi >= 70 and (current_time - last_time) > 300:
                        settings["last_signal_time"][name] = current_time
                        settings["total_signals"] += 1
                        
                        confidence = min(95, int(rsi - 70 + 20))
                        reason = f"RSI Overbought ({rsi}) - Price may reverse DOWN"
                        
                        message = format_signal(name, flag, "SELL", confidence, price, rsi, reason, False)
                        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
                        print(f"📤 SIGNAL SENT: {name} SELL (RSI: {rsi}) at {format_time()}")
                    
                except Exception as e:
                    print(f"Error checking {pair.get('name')}: {e}")
                
                await asyncio.sleep(2)  # Small delay between pairs
            
            print(f"💓 Monitor cycle complete at {format_time()}")
            await asyncio.sleep(60)  # Wait 60 seconds before next full cycle
            
        except Exception as e:
            print(f"Monitor error: {e}")
            await asyncio.sleep(30)

# ============================================
# COMMAND HANDLERS
# ============================================

async def start_command(update, context):
    await update.message.reply_text(f"""
🤖 <b>IQ TRADING BOT - STABLE EDITION</b>

✅ Bot is ONLINE!

📈 <b>Monitoring:</b>
• EUR/USD, GBP/USD, USD/JPY
• Gold, Bitcoin, Ethereum
• US100, Apple, Tesla

⚡ <b>Signal Mode:</b> REAL-TIME
🎯 <b>Trigger:</b> RSI < 30 = BUY | RSI > 70 = SELL
⏰ <b>Nigeria Time:</b> {format_time()}

<i>Signals will appear here automatically when RSI conditions are met!</i>
""", parse_mode='HTML')

async def status_command(update, context):
    await update.message.reply_text(f"""
📊 <b>BOT STATUS</b>

✅ Status: ONLINE
🎯 Total signals sent: {settings['total_signals']}
⚡ Signal mode: REAL-TIME (RSI-based)
📱 Platform: Railway Cloud
⏰ Time Zone: Nigeria (WAT)
🕐 Current Time: {format_time()}

<b>Signal Trigger:</b>
• RSI < 30 → BUY signal
• RSI > 70 → SELL signal
""", parse_mode='HTML')

async def pairs_command(update, context):
    pairs_list = "\n".join([f"• {p['name']}" for p in PRIORITY_PAIRS])
    await update.message.reply_text(f"""
📊 <b>MONITORED INSTRUMENTS</b>

{pairs_list}

<i>Signals sent automatically when RSI < 30 (BUY) or RSI > 70 (SELL)</i>
""", parse_mode='HTML')

# Add handlers
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("status", status_command))
application.add_handler(CommandHandler("pairs", pairs_command))

# ============================================
# STARTUP
# ============================================

async def send_startup():
    await bot.send_message(chat_id=CHAT_ID, text=f"""
🤖 <b>IQ TRADING BOT - STABLE EDITION</b>

✅ Bot is ONLINE!
⚡ REAL-TIME SIGNALS ACTIVE

📈 <b>Monitoring:</b>
• EUR/USD, GBP/USD, USD/JPY
• Gold, Bitcoin, Ethereum
• US100, Apple, Tesla

🎯 <b>Signal Trigger:</b>
• RSI < 30 → BUY signal
• RSI > 70 → SELL signal

⏰ <b>Nigeria Time:</b> {format_time()}

<i>Signals will appear here immediately when opportunities arise!</i>
""", parse_mode='HTML')

# ============================================
# MAIN
# ============================================

async def main():
    # Send startup message
    await send_startup()
    
    # Start monitoring in background
    asyncio.create_task(monitor_pairs())
    
    # Start bot polling
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    print("""
🚀 BOT IS RUNNING!
📊 Monitoring 9 priority instruments
⚡ REAL-TIME SIGNALS: RSI < 30 (BUY) or RSI > 70 (SELL)
📍 Nigeria Time Zone
📍 Commands: /status, /pairs
    """)
    
    # Keep running
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
