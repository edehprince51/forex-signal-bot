"""
IQ TRADING BOT - COMPLETE EDITION
ALL PAIRS FROM YOUR IMAGES | MANUAL + AUTO SIGNALS
"""

import os
import requests
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, CommandHandler

load_dotenv()

print("""
╔════════════════════════════════════════════════════════════════╗
║   IQ TRADING BOT - COMPLETE EDITION                            ║
║   ALL PAIRS | MANUAL + AUTO SIGNALS | NIGERIA TIME             ║
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
# ALL PAIRS FROM YOUR IMAGES
# ============================================

ALL_PAIRS = {
    # Forex Majors
    "EUR/USD": {"symbol": "EURUSD=X", "flag": "🇪🇺🇺🇸", "type": "Forex"},
    "GBP/USD": {"symbol": "GBPUSD=X", "flag": "🇬🇧🇺🇸", "type": "Forex"},
    "USD/JPY": {"symbol": "JPY=X", "flag": "🇺🇸🇯🇵", "type": "Forex"},
    "AUD/USD": {"symbol": "AUDUSD=X", "flag": "🇦🇺🇺🇸", "type": "Forex"},
    "USD/CAD": {"symbol": "USDCAD=X", "flag": "🇺🇸🇨🇦", "type": "Forex"},
    "NZD/USD": {"symbol": "NZDUSD=X", "flag": "🇳🇿🇺🇸", "type": "Forex"},
    "USD/CHF": {"symbol": "CHF=X", "flag": "🇺🇸🇨🇭", "type": "Forex"},
    # Forex Crosses
    "EUR/GBP": {"symbol": "EURGBP=X", "flag": "🇪🇺🇬🇧", "type": "Forex"},
    "EUR/JPY": {"symbol": "EURJPY=X", "flag": "🇪🇺🇯🇵", "type": "Forex"},
    "GBP/JPY": {"symbol": "GBPJPY=X", "flag": "🇬🇧🇯🇵", "type": "Forex"},
    "AUD/JPY": {"symbol": "AUDJPY=X", "flag": "🇦🇺🇯🇵", "type": "Forex"},
    "AUD/CAD": {"symbol": "AUDCAD=X", "flag": "🇦🇺🇨🇦", "type": "Forex"},
    "CAD/JPY": {"symbol": "CADJPY=X", "flag": "🇨🇦🇯🇵", "type": "Forex"},
    "CAD/CHF": {"symbol": "CADCHF=X", "flag": "🇨🇦🇨🇭", "type": "Forex"},
    "CHF/JPY": {"symbol": "CHFJPY=X", "flag": "🇨🇭🇯🇵", "type": "Forex"},
    "EUR/AUD": {"symbol": "EURAUD=X", "flag": "🇪🇺🇦🇺", "type": "Forex"},
    "EUR/CAD": {"symbol": "EURCAD=X", "flag": "🇪🇺🇨🇦", "type": "Forex"},
    "EUR/CHF": {"symbol": "EURCHF=X", "flag": "🇪🇺🇨🇭", "type": "Forex"},
    "GBP/AUD": {"symbol": "GBPAUD=X", "flag": "🇬🇧🇦🇺", "type": "Forex"},
    "GBP/CAD": {"symbol": "GBPCAD=X", "flag": "🇬🇧🇨🇦", "type": "Forex"},
    "GBP/CHF": {"symbol": "GBPCHF=X", "flag": "🇬🇧🇨🇭", "type": "Forex"},
    "AUD/CHF": {"symbol": "AUDCHF=X", "flag": "🇦🇺🇨🇭", "type": "Forex"},
    "NZD/JPY": {"symbol": "NZDJPY=X", "flag": "🇳🇿🇯🇵", "type": "Forex"},
    # Exotic Forex
    "USD/TRY": {"symbol": "USDTRY=X", "flag": "🇺🇸🇹🇷", "type": "Forex"},
    "USD/ZAR": {"symbol": "USDZAR=X", "flag": "🇺🇸🇿🇦", "type": "Forex"},
    "USD/MXN": {"symbol": "USDMXN=X", "flag": "🇺🇸🇲🇽", "type": "Forex"},
    "USD/SGD": {"symbol": "USDSGD=X", "flag": "🇺🇸🇸🇬", "type": "Forex"},
    "USD/INR": {"symbol": "USDINR=X", "flag": "🇺🇸🇮🇳", "type": "Forex"},
    "USD/BRL": {"symbol": "USDBRL=X", "flag": "🇺🇸🇧🇷", "type": "Forex"},
    "USD/RUB": {"symbol": "USDRUB=X", "flag": "🇺🇸🇷🇺", "type": "Forex"},
    "USD/THB": {"symbol": "USDTHB=X", "flag": "🇺🇸🇹🇭", "type": "Forex"},
    # Indices
    "US100": {"symbol": "^IXIC", "flag": "📊", "type": "Index"},
    "US30": {"symbol": "^DJI", "flag": "📈", "type": "Index"},
    "US500": {"symbol": "^GSPC", "flag": "📊", "type": "Index"},
    "GER30": {"symbol": "^GDAXI", "flag": "📊🇩🇪", "type": "Index"},
    "UK100": {"symbol": "^FTSE", "flag": "📊🇬🇧", "type": "Index"},
    "FRA40": {"symbol": "^FCHI", "flag": "📊🇫🇷", "type": "Index"},
    "ESP35": {"symbol": "^IBEX", "flag": "📊🇪🇸", "type": "Index"},
    "AUS200": {"symbol": "^AXJO", "flag": "📊🇦🇺", "type": "Index"},
    "JPN225": {"symbol": "^N225", "flag": "📊🇯🇵", "type": "Index"},
    "HK50": {"symbol": "^HSI", "flag": "📊🇭🇰", "type": "Index"},
    # Commodities
    "Gold": {"symbol": "GC=F", "flag": "🥇", "type": "Commodity"},
    "Silver": {"symbol": "SI=F", "flag": "🥈", "type": "Commodity"},
    "Brent Oil": {"symbol": "BZ=F", "flag": "🛢️", "type": "Commodity"},
    "WTI Oil": {"symbol": "CL=F", "flag": "🛢️", "type": "Commodity"},
    "Natural Gas": {"symbol": "NG=F", "flag": "🔥", "type": "Commodity"},
    "Platinum": {"symbol": "PL=F", "flag": "🔘", "type": "Commodity"},
    "Palladium": {"symbol": "PA=F", "flag": "🔘", "type": "Commodity"},
    # Cryptocurrencies
    "Bitcoin": {"symbol": "BTC-USD", "flag": "₿", "type": "Crypto"},
    "Ethereum": {"symbol": "ETH-USD", "flag": "⟠", "type": "Crypto"},
    "Solana": {"symbol": "SOL-USD", "flag": "⚡", "type": "Crypto"},
    "Cardano": {"symbol": "ADA-USD", "flag": "🟣", "type": "Crypto"},
    "Dogecoin": {"symbol": "DOGE-USD", "flag": "🐕", "type": "Crypto"},
    "Ripple": {"symbol": "XRP-USD", "flag": "✖️", "type": "Crypto"},
    "Litecoin": {"symbol": "LTC-USD", "flag": "Ł", "type": "Crypto"},
    "Chainlink": {"symbol": "LINK-USD", "flag": "🔗", "type": "Crypto"},
    "Avalanche": {"symbol": "AVAX-USD", "flag": "🔺", "type": "Crypto"},
    "Polygon": {"symbol": "MATIC-USD", "flag": "🟣", "type": "Crypto"},
    # Stocks
    "Apple": {"symbol": "AAPL", "flag": "🍎", "type": "Stock"},
    "Tesla": {"symbol": "TSLA", "flag": "🚗", "type": "Stock"},
    "Microsoft": {"symbol": "MSFT", "flag": "💻", "type": "Stock"},
    "Amazon": {"symbol": "AMZN", "flag": "📦", "type": "Stock"},
    "Netflix": {"symbol": "NFLX", "flag": "🎬", "type": "Stock"},
    "Google": {"symbol": "GOOGL", "flag": "🔍", "type": "Stock"},
    "Meta": {"symbol": "META", "flag": "📘", "type": "Stock"},
    "NVIDIA": {"symbol": "NVDA", "flag": "🎮", "type": "Stock"},
    "AMD": {"symbol": "AMD", "flag": "💻", "type": "Stock"},
    "Intel": {"symbol": "INTC", "flag": "💻", "type": "Stock"},
    "Cisco": {"symbol": "CSCO", "flag": "🌐", "type": "Stock"},
    "Johnson & Johnson": {"symbol": "JNJ", "flag": "💊", "type": "Stock"},
    "McDonald's": {"symbol": "MCD", "flag": "🍔", "type": "Stock"},
    "ExxonMobil": {"symbol": "XOM", "flag": "⛽", "type": "Stock"},
    "FedEx": {"symbol": "FDX", "flag": "📦", "type": "Stock"},
    "Boeing": {"symbol": "BA", "flag": "✈️", "type": "Stock"},
    "Visa": {"symbol": "V", "flag": "💳", "type": "Stock"},
    "JPMorgan": {"symbol": "JPM", "flag": "🏦", "type": "Stock"},
    "Citigroup": {"symbol": "C", "flag": "🏦", "type": "Stock"},
    "Pfizer": {"symbol": "PFE", "flag": "💊", "type": "Stock"},
    "Alibaba": {"symbol": "BABA", "flag": "🛒", "type": "Stock"},
    "Coinbase": {"symbol": "COIN", "flag": "₿", "type": "Stock"},
    "GameStop": {"symbol": "GME", "flag": "🎮", "type": "Stock"},
    "Marathon Digital": {"symbol": "MARA", "flag": "₿", "type": "Stock"},
    "Palantir": {"symbol": "PLTR", "flag": "🔍", "type": "Stock"},
}

print(f"✅ Loaded {len(ALL_PAIRS)} tradable instruments")

# Priority pairs for auto-scan (most liquid)
AUTO_PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "Gold", "Bitcoin", 
    "US100", "Apple", "Tesla", "Ethereum", "Silver"
]

# ============================================
# PRICE & RSI FUNCTIONS
# ============================================

def get_price(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('chart', {}).get('result', [])
            if result:
                price = result[0].get('meta', {}).get('regularMarketPrice')
                if price:
                    return round(price, 5 if price < 100 else 2)
        return None
    except:
        return None

def calculate_rsi(prices):
    if len(prices) < 15:
        return 50
    gains, losses = [], []
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
    return round(100 - (100 / (1 + rs)), 1)

def get_rsi(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=5m"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            result = data.get('chart', {}).get('result', [])
            if result:
                closes = result[0].get('indicators', {}).get('quote', [{}])[0].get('close', [])
                closes = [c for c in closes if c is not None]
                if len(closes) > 14:
                    return calculate_rsi(closes)
        return 50
    except:
        return 50

def format_signal(name, flag, direction, confidence, price, rsi, reason, is_manual=False):
    entry_time = get_nigeria_time() + timedelta(minutes=3)
    
    martingale_lines = []
    for i in range(1, 4):
        level_time = entry_time + timedelta(minutes=i * 3)
        martingale_lines.append(f"Level {i} -> {level_time.strftime('%I:%M %p')}")
    
    tp = price * 1.005 if direction == "BUY" else price * 0.995
    sl = price * 0.995 if direction == "BUY" else price * 1.005
    
    signal_type = "MANUAL SIGNAL" if is_manual else "NEW SIGNAL"
    
    return f"""
🔔 {signal_type}!

🎫 Trade: {flag} {name}
⏳ Timer: 3 minutes
➡️ Entry: {entry_time.strftime('%I:%M %p')}
📈 Direction: {direction}

💪 Confidence: {confidence}%

📊 Technical Analysis:
• RSI: {rsi}
• {reason}

↪️ Martingale Levels:
{chr(10).join(martingale_lines)}

💰 Entry Price: ${price:.5f}
🎯 Take Profit: ${tp:.5f}
🛑 Stop Loss: ${sl:.5f}

⏰ {format_time()} (Nigeria Time)
"""

def get_signal_data(name, symbol, flag):
    price = get_price(symbol)
    if not price:
        return None
    
    rsi = get_rsi(symbol)
    
    if rsi <= 30:
        direction = "BUY"
        confidence = min(95, int(75 - rsi + 20))
        reason = f"RSI Oversold ({rsi}) - Price may reverse UP"
        return {"name": name, "flag": flag, "direction": direction, "confidence": confidence, "price": price, "rsi": rsi, "reason": reason}
    elif rsi >= 70:
        direction = "SELL"
        confidence = min(95, int(rsi - 70 + 20))
        reason = f"RSI Overbought ({rsi}) - Price may reverse DOWN"
        return {"name": name, "flag": flag, "direction": direction, "confidence": confidence, "price": price, "rsi": rsi, "reason": reason}
    return None

# ============================================
# AUTO MONITOR
# ============================================

async def monitor_pairs():
    print("🔄 Auto monitor started - checking every 30 seconds")
    
    while True:
        try:
            for name in AUTO_PAIRS:
                if name not in ALL_PAIRS:
                    continue
                    
                pair = ALL_PAIRS[name]
                symbol = pair["symbol"]
                flag = pair["flag"]
                
                signal_data = get_signal_data(name, symbol, flag)
                
                if signal_data:
                    current_time = datetime.now().timestamp()
                    last_time = settings["last_signal_time"].get(name, 0)
                    
                    if (current_time - last_time) > 300:
                        settings["last_signal_time"][name] = current_time
                        settings["total_signals"] += 1
                        
                        message = format_signal(
                            signal_data["name"], signal_data["flag"],
                            signal_data["direction"], signal_data["confidence"],
                            signal_data["price"], signal_data["rsi"],
                            signal_data["reason"], is_manual=False
                        )
                        await bot.send_message(chat_id=CHAT_ID, text=message)
                        print(f"📤 AUTO SIGNAL: {name} {signal_data['direction']} (RSI: {signal_data['rsi']})")
                
                await asyncio.sleep(2)
            
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"Monitor error: {e}")
            await asyncio.sleep(30)

# ============================================
# COMMAND HANDLERS
# ============================================

async def start_command(update, context):
    await update.message.reply_text(
        f"🤖 IQ TRADING BOT - COMPLETE EDITION\n\n"
        f"✅ Bot is ONLINE!\n\n"
        f"📈 Total instruments: {len(ALL_PAIRS)}\n"
        f"   • Forex: 30+ pairs\n"
        f"   • Indices: 10\n"
        f"   • Commodities: 7\n"
        f"   • Crypto: 10\n"
        f"   • Stocks: 25+\n\n"
        f"⚡ Signal Mode: REAL-TIME\n"
        f"🎯 Trigger: RSI < 30 = BUY | RSI > 70 = SELL\n\n"
        f"📋 Commands:\n"
        f"   /signal [pair] - Manual signal (e.g., /signal Gold)\n"
        f"   /pairs - List all available pairs\n"
        f"   /status - Bot status\n\n"
        f"⏰ Nigeria Time: {format_time()}"
    )

async def signal_command(update, context):
    if not context.args:
        # Show available pairs if no argument
        sample = list(ALL_PAIRS.keys())[:20]
        await update.message.reply_text(
            f"⚠️ Usage: /signal [pair name]\n\n"
            f"Examples: /signal Gold\n"
            f"          /signal EUR/USD\n"
            f"          /signal Bitcoin\n\n"
            f"Available pairs: {', '.join(sample)}...\n"
            f"Total: {len(ALL_PAIRS)} instruments"
        )
        return
    
    # Join multiple words (e.g., "Brent Oil" -> "Brent Oil")
    name = " ".join(context.args)
    
    # Try exact match first
    if name not in ALL_PAIRS:
        # Try case-insensitive match
        found = None
        for key in ALL_PAIRS.keys():
            if key.lower() == name.lower():
                found = key
                break
        if found:
            name = found
        else:
            await update.message.reply_text(f"❌ '{name}' not found.\n\nType /pairs to see all available instruments.")
            return
    
    pair = ALL_PAIRS[name]
    symbol = pair["symbol"]
    flag = pair["flag"]
    
    await update.message.reply_text(f"🔍 Analyzing {name}...")
    
    signal_data = get_signal_data(name, symbol, flag)
    
    if signal_data:
        message = format_signal(
            signal_data["name"], signal_data["flag"],
            signal_data["direction"], signal_data["confidence"],
            signal_data["price"], signal_data["rsi"],
            signal_data["reason"], is_manual=True
        )
        await update.message.reply_text(message)
        settings["total_signals"] += 1
    else:
        rsi = get_rsi(symbol)
        price = get_price(symbol) or 0
        await update.message.reply_text(
            f"📊 {name} Analysis\n\n"
            f"💰 Price: ${price:.5f}\n"
            f"📈 RSI: {rsi}\n\n"
            f"❌ No strong signal right now.\n"
            f"RSI is in neutral zone ({rsi}).\n\n"
            f"Signals are sent when RSI < 30 (BUY) or RSI > 70 (SELL)"
        )

async def pairs_command(update, context):
    # Group by type
    forex = [p for p, info in ALL_PAIRS.items() if info["type"] == "Forex"]
    indices = [p for p, info in ALL_PAIRS.items() if info["type"] == "Index"]
    commodities = [p for p, info in ALL_PAIRS.items() if info["type"] == "Commodity"]
    crypto = [p for p, info in ALL_PAIRS.items() if info["type"] == "Crypto"]
    stocks = [p for p, info in ALL_PAIRS.items() if info["type"] == "Stock"]
    
    await update.message.reply_text(
        f"📊 AVAILABLE INSTRUMENTS\n\n"
        f"Forex ({len(forex)}): {', '.join(forex[:15])}{'...' if len(forex) > 15 else ''}\n\n"
        f"Indices ({len(indices)}): {', '.join(indices)}\n\n"
        f"Commodities ({len(commodities)}): {', '.join(commodities)}\n\n"
        f"Crypto ({len(crypto)}): {', '.join(crypto)}\n\n"
        f"Stocks ({len(stocks)}): {', '.join(stocks[:15])}{'...' if len(stocks) > 15 else ''}\n\n"
        f"Total: {len(ALL_PAIRS)} instruments\n\n"
        f"Type /signal [name] for any instrument"
    )

async def status_command(update, context):
    await update.message.reply_text(
        f"📊 BOT STATUS\n\n"
        f"✅ Status: ONLINE\n"
        f"📈 Total instruments: {len(ALL_PAIRS)}\n"
        f"🎯 Total signals sent: {settings['total_signals']}\n"
        f"⚡ Auto-scan: {len(AUTO_PAIRS)} priority pairs\n"
        f"🎯 Signal trigger: RSI < 30 = BUY | RSI > 70 = SELL\n"
        f"⏰ Time Zone: Nigeria (WAT)\n"
        f"🕐 Current Time: {format_time()}\n\n"
        f"📋 Commands:\n"
        f"   /signal [pair] - Manual signal\n"
        f"   /pairs - List all pairs\n"
        f"   /status - This menu"
    )

# Add handlers
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("signal", signal_command))
application.add_handler(CommandHandler("pairs", pairs_command))
application.add_handler(CommandHandler("status", status_command))

async def send_startup():
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"🤖 IQ TRADING BOT - COMPLETE EDITION\n\n✅ Bot is ONLINE!\n📈 Total instruments: {len(ALL_PAIRS)}\n⚡ Auto-signals active for priority pairs\n🎯 Type /signal [pair] for manual analysis\n\n⏰ Nigeria Time: {format_time()}"
    )

async def main():
    await send_startup()
    print(f"🚀 Bot is running!")
    print(f"📈 Total instruments: {len(ALL_PAIRS)}")
    print(f"🔄 Auto-monitoring {len(AUTO_PAIRS)} priority pairs")
    print(f"📋 Commands: /signal [pair], /pairs, /status")
    
    asyncio.create_task(monitor_pairs())
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
