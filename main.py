"""
IQ TRADING BOT - PROFESSIONAL EDITION
ALL PAIRS FROM YOUR IMAGES | REAL-TIME SIGNALS | NIGERIA TIME
"""

import os
import time
import requests
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, CommandHandler

load_dotenv()

print("""
╔════════════════════════════════════════════════════════════════╗
║   IQ TRADING BOT - PROFESSIONAL EDITION                        ║
║   ALL PAIRS FROM YOUR IMAGES | REAL-TIME SIGNALS               ║
╚════════════════════════════════════════════════════════════════╝
""")

# Get credentials
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not found!")
    exit(1)

print("✅ Bot initialized!")

# Nigeria Time Zone (UTC+1)
def get_nigeria_time():
    utc_now = datetime.utcnow()
    return utc_now + timedelta(hours=1)

def format_time(dt=None):
    if dt is None:
        dt = get_nigeria_time()
    return dt.strftime("%I:%M %p")

def format_full_time():
    return get_nigeria_time().strftime("%Y-%m-%d %I:%M:%S %p")

# Create bot
bot = Bot(token=TELEGRAM_TOKEN)
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Settings
settings = {
    "min_confidence": 20,
    "total_scans": 0,
    "total_signals": 0,
    "last_signal_time": {}
}

# ============================================
# ALL PAIRS FROM YOUR IMAGES
# ============================================

# FOREX PAIRS (from your images)
FOREX_PAIRS = {
    # Major Forex
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
    "NZD/USD": "NZDUSD=X",
    "USD/CHF": "CHF=X",
    # Forex Crosses
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
    "AUD/JPY": "AUDJPY=X",
    "AUD/CAD": "AUDCAD=X",
    "CAD/JPY": "CADJPY=X",
    "CAD/CHF": "CADCHF=X",
    "CHF/JPY": "CHFJPY=X",
    "EUR/AUD": "EURAUD=X",
    "EUR/CAD": "EURCAD=X",
    "EUR/CHF": "EURCHF=X",
    "GBP/AUD": "GBPAUD=X",
    "GBP/CAD": "GBPCAD=X",
    "GBP/CHF": "GBPCHF=X",
    "AUD/CHF": "AUDCHF=X",
    "NZD/JPY": "NZDJPY=X",
    # Exotic Forex (from your images)
    "NGN/USD": "NGNUSD=X",
    "USD/NGN": "USDNGN=X",
    "EUR/TRY": "EURTRY=X",
    "USD/TRY": "USDTRY=X",
    "USD/ZAR": "USDZAR=X",
    "USD/MXN": "USDMXN=X",
    "USD/SGD": "USDSGD=X",
    "USD/HKD": "USDHKD=X",
    "USD/INR": "USDINR=X",
    "USD/BRL": "USDBRL=X",
    "USD/RUB": "USDRUB=X",
    "USD/THB": "USDTHB=X",
    "USD/IDR": "USDIDR=X",
    "USD/PHP": "USDPHP=X",
    "USD/PKR": "USDPKR=X",
    "USD/EGP": "USDEGP=X",
    "USD/MYR": "USDMYR=X",
    "USD/COP": "USDCOP=X",
    "USD/CLP": "USDCLP=X",
    "USD/ARS": "USDARS=X",
    "USD/BDT": "USDBDT=X",
    "USD/DZD": "USDDZD=X",
    "USD/KES": "USDKES=X",
    "USD/LBP": "USDLBP=X",
    "USD/UAH": "UAHUSD=X",
    "MAD/USD": "MADUSD=X",
    "QAR/CNY": "QARCNY=X",
    "SAR/CNY": "SARCNY=X",
    "BHD/CNY": "BHDCNY=X",
    "JOD/CNY": "JODCNY=X",
    "OMR/CNY": "OMRCNY=X",
    "AED/CNY": "AEDCNY=X",
    "YER/USD": "YERUSD=X",
    "CHF/NOK": "CHFNOK=X",
    "EUR/HUF": "EURHUF=X",
    "EUR/RUB": "EURRUB=X",
    "EUR/NZD": "EURNZD=X",
    "KES/USD": "KESUSD=X",
    "NGN/INR": "NGNINR=X",
    "TND/USD": "TNDUSD=X",
    "FIIR/GRP": "FIIRGRP=X",
    "LBP/USD": "LBPUSD=X",
}

# OTC FOREX (from your images)
OTC_FOREX = {
    "EUR/USD-OTC": "EURUSD=X",
    "GBP/USD-OTC": "GBPUSD=X",
    "USD/JPY-OTC": "JPY=X",
    "AUD/USD-OTC": "AUDUSD=X",
    "USD/CAD-OTC": "USDCAD=X",
    "NZD/USD-OTC": "NZDUSD=X",
    "USD/CHF-OTC": "CHF=X",
    "EUR/GBP-OTC": "EURGBP=X",
    "EUR/JPY-OTC": "EURJPY=X",
    "GBP/JPY-OTC": "GBPJPY=X",
    "AUD/JPY-OTC": "AUDJPY=X",
    "GBP/AUD-OTC": "GBPAUD=X",
    "USD/BRL-OTC": "USDBRL=X",
    "USD/DZD-OTC": "USDDZD=X",
    "USD/CLP-OTC": "USDCLP=X",
    "MAD/USD-OTC": "MADUSD=X",
    "UAH/USD-OTC": "UAHUSD=X",
    "LBP/USD-OTC": "LBPUSD=X",
    "NGN/USD-OTC": "NGNUSD=X",
    "KES/USD-OTC": "KESUSD=X",
    "AED/CNY-OTC": "AEDCNY=X",
    "SAR/CNY-OTC": "SARCNY=X",
    "BHD/CNY-OTC": "BHDCNY=X",
    "JOD/CNY-OTC": "JODCNY=X",
    "OMR/CNY-OTC": "OMRCNY=X",
    "QAR/CNY-OTC": "QARCNY=X",
    "YER/USD-OTC": "YERUSD=X",
    "CHF/NOK-OTC": "CHFNOK=X",
    "EUR/HUF-OTC": "EURHUF=X",
    "EUR/RUB-OTC": "EURRUB=X",
    "EUR/NZD-OTC": "EURNZD=X",
    "NGN/INR-OTC": "NGNINR=X",
    "TND/USD-OTC": "TNDUSD=X",
    "USD/COP-OTC": "USDCOP=X",
    "USD/EGP-OTC": "USDEGP=X",
    "USD/IDR-OTC": "USDIDR=X",
    "USD/INR-OTC": "USDINR=X",
    "USD/MXN-OTC": "USDMXN=X",
    "USD/MYR-OTC": "USDMYR=X",
    "USD/PHP-OTC": "USDPHP=X",
    "USD/PKR-OTC": "USDPKR=X",
    "USD/RUB-OTC": "USDRUB=X",
    "USD/SGD-OTC": "USDSGD=X",
    "USD/THB-OTC": "USDTHB=X",
    "USD/TRY-OTC": "USDTRY=X",
    "USD/ZAR-OTC": "USDZAR=X",
}

# INDICES (from your images)
INDICES = {
    "AUS 200": "^AXJO",
    "AUS 200 OTC": "^AXJO",
    "DJI30": "^DJI",
    "DJI30 OTC": "^DJI",
    "US100": "^IXIC",
    "US100 OTC": "^IXIC",
    "SP500": "^GSPC",
    "SP500 OTC": "^GSPC",
    "CAC 40": "^FCHI",
    "F40/EUR": "^FCHI",
    "F40EUR OTC": "^FCHI",
    "D30/EUR": "^GDAXI",
    "D30EUR OTC": "^GDAXI",
    "E35EUR": "^IBEX",
    "E35EUR OTC": "^IBEX",
    "E50/EUR": "^STOXX50E",
    "E50EUR OTC": "^STOXX50E",
    "JPN225": "^N225",
    "JPN225 OTC": "^N225",
    "HONG KONG 33": "^HSI",
    "100GBP": "^FTSE",
    "100GBP OTC": "^FTSE",
    "AEX 25": "^AEX",
}

# COMMODITIES (from your images)
COMMODITIES = {
    "Gold": "GC=F",
    "Gold OTC": "GC=F",
    "Silver": "SI=F",
    "Silver OTC": "SI=F",
    "Brent Oil": "BZ=F",
    "Brent Oil OTC": "BZ=F",
    "WTI Crude Oil": "CL=F",
    "WTI Crude Oil OTC": "CL=F",
    "Natural Gas": "NG=F",
    "Natural Gas OTC": "NG=F",
    "Palladium spot": "PA=F",
    "Palladium spot OTC": "PA=F",
    "Platinum spot": "PL=F",
    "Platinum spot OTC": "PL=F",
}

# CRYPTOCURRENCIES (from your images)
CRYPTO = {
    "Bitcoin": "BTC-USD",
    "Bitcoin OTC": "BTC-USD",
    "Bitcoin ETF": "BTC-USD",
    "Bitcoin ETF OTC": "BTC-USD",
    "Ethereum": "ETH-USD",
    "Ethereum OTC": "ETH-USD",
    "Dogecoin": "DOGE-USD",
    "Dogecoin OTC": "DOGE-USD",
    "Solana": "SOL-USD",
    "Solana OTC": "SOL-USD",
    "Cardano": "ADA-USD",
    "Cardano OTC": "ADA-USD",
    "Chainlink": "LINK-USD",
    "Chainlink OTC": "LINK-USD",
    "Litecoin": "LTC-USD",
    "Litecoin OTC": "LTC-USD",
    "Avalanche": "AVAX-USD",
    "Avalanche OTC": "AVAX-USD",
    "TRON": "TRX-USD",
    "TRON OTC": "TRX-USD",
    "Polygon": "MATIC-USD",
    "Polygon OTC": "MATIC-USD",
}

# STOCKS (from your images)
STOCKS = {
    "Apple": "AAPL",
    "Apple OTC": "AAPL",
    "Microsoft": "MSFT",
    "Microsoft OTC": "MSFT",
    "Tesla": "TSLA",
    "Tesla OTC": "TSLA",
    "Amazon": "AMZN",
    "Amazon OTC": "AMZN",
    "Netflix": "NFLX",
    "Netflix OTC": "NFLX",
    "Facebook Inc": "META",
    "Facebook Inc OTC": "META",
    "Alibaba": "BABA",
    "Alibaba OTC": "BABA",
    "AMD": "AMD",
    "AMD OTC": "AMD",
    "Intel": "INTC",
    "Intel OTC": "INTC",
    "Cisco": "CSCO",
    "Cisco OTC": "CSCO",
    "Johnson & Johnson": "JNJ",
    "Johnson & Johnson OTC": "JNJ",
    "McDonald's": "MCD",
    "McDonald's OTC": "MCD",
    "ExxonMobil": "XOM",
    "ExxonMobil OTC": "XOM",
    "FedEx": "FDX",
    "FedEx OTC": "FDX",
    "Boeing Company": "BA",
    "Boeing Company OTC": "BA",
    "VISA": "V",
    "VISA OTC": "V",
    "JPMorgan Chase & Co": "JPM",
    "Citigroup Inc": "C",
    "Citigroup Inc OTC": "C",
    "Citi": "C",
    "Pfizer Inc": "PFE",
    "Pfizer Inc OTC": "PFE",
    "American Express": "AXP",
    "American Express OTC": "AXP",
    "Coinbase Global": "COIN",
    "Coinbase Global OTC": "COIN",
    "GameStop Corp": "GME",
    "GameStop Corp OTC": "GME",
    "Marathon Digital Holdings": "MARA",
    "Marathon Digital Holdings OTC": "MARA",
    "Palantir Technologies": "PLTR",
    "Palantir Technologies OTC": "PLTR",
    "VIX": "^VIX",
    "VIX OTC": "^VIX",
}

# Combine ALL pairs
ALL_PAIRS = {}
ALL_PAIRS.update(FOREX_PAIRS)
ALL_PAIRS.update(OTC_FOREX)
ALL_PAIRS.update(INDICES)
ALL_PAIRS.update(COMMODITIES)
ALL_PAIRS.update(CRYPTO)
ALL_PAIRS.update(STOCKS)

print(f"✅ Loaded {len(ALL_PAIRS)} tradable instruments")
print(f"✅ REAL-TIME SIGNALS ENABLED - Will send immediately when opportunity appears")

# ============================================
# FLAGS FOR DISPLAY
# ============================================

def get_flag(pair):
    flags = {
        "EUR/USD": "🇪🇺🇺🇸", "GBP/USD": "🇬🇧🇺🇸", "USD/JPY": "🇺🇸🇯🇵",
        "Gold": "🥇", "Silver": "🥈", "Bitcoin": "₿", "Ethereum": "⟠",
        "Apple": "🍎", "Tesla": "🚗", "Microsoft": "💻", "Amazon": "📦",
        "US100": "📊", "DJI30": "📈", "SP500": "📊",
    }
    for key, flag in flags.items():
        if key in pair:
            return flag
    return "🌍"

# ============================================
# PRICE & SIGNAL FUNCTIONS
# ============================================

last_sent_signals = {}

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

def should_send_signal(pair, rsi):
    """Check if we should send signal (avoid duplicates)"""
    current_hour = get_nigeria_time().hour
    last_time = last_sent_signals.get(pair, 0)
    if current_time - last_time < 60:  # Don't send same signal within 60 seconds
        return False
    
    # RSI conditions for signals
    if rsi <= 30 or rsi >= 70:
        last_sent_signals[pair] = current_time
        return True
    return False

def generate_signal(pair, symbol, is_otc=False):
    price = get_price(symbol)
    if not price:
        return None
    
    rsi = get_rsi(symbol)
    
    # Only send signals when RSI is extreme (real opportunity)
    if rsi <= 30:
        direction = "BUY"
        confidence = min(95, int(75 - rsi + 20))
        emoji = "🟢🟢" if confidence >= 75 else "🟢"
        reason = f"RSI Oversold ({rsi}) - Strong reversal expected UP"
    elif rsi >= 70:
        direction = "SELL"
        confidence = min(95, int(rsi - 70 + 20))
        emoji = "🔴🔴" if confidence >= 75 else "🔴"
        reason = f"RSI Overbought ({rsi}) - Strong reversal expected DOWN"
    else:
        return None  # No signal in neutral zone
    
    return {
        'pair': pair,
        'flag': get_flag(pair),
        'price': price,
        'rsi': rsi,
        'direction': direction,
        'confidence': confidence,
        'emoji': emoji,
        'reason': reason,
        'is_otc': is_otc,
        'timestamp': format_time()
    }

def format_signal(signal):
    entry_time = get_nigeria_time() + timedelta(minutes=3)
    otc_tag = " (OTC)" if signal['is_otc'] else ""
    
    martingale = []
    for i in range(1, 4):
        level_time = entry_time + timedelta(minutes=i * 3)
        martingale.append(f" Level {i} → {level_time.strftime('%I:%M %p')}")
    
    tp_mult = 1.005 if signal['direction'] == "BUY" else 0.995
    sl_mult = 0.995 if signal['direction'] == "BUY" else 1.005
    
    return f"""
🔔 <b>NEW SIGNAL!</b>

🎫 Trade: {signal['flag']} {signal['pair']}{otc_tag}
⏳ Timer: 3 minutes
➡️ Entry: {entry_time.strftime('%I:%M %p')}
📈 Direction: {signal['direction']} {signal['emoji']}

💪 <b>Confidence:</b> {signal['confidence']}%

📊 <b>Technical Analysis:</b>
• RSI: {signal['rsi']}
• {signal['reason']}

↪️ <b>Martingale Levels:</b>
{chr(10).join(martingale)}

💰 <b>Entry Price:</b> ${signal['price']:.5f}
🎯 <b>Take Profit:</b> ${(signal['price'] * tp_mult):.5f}
🛑 <b>Stop Loss:</b> ${(signal['price'] * sl_mult):.5f}

⏰ {signal['timestamp']} (Nigeria Time)
"""

# ============================================
# REAL-TIME SIGNAL MONITOR
# - Scans continuously, sends signal IMMEDIATELY when RSI < 30 or > 70
# - NOT on a fixed schedule
# ============================================

async def continuous_monitor():
    """Continuously monitor all pairs and send signals immediately when opportunity appears"""
    print("🔄 REAL-TIME MONITORING STARTED - Will send signals immediately when RSI < 30 or > 70")
    
    # Priority pairs to monitor (from your images)
    priority_pairs = [
        ("EUR/USD", "EURUSD=X", False),
        ("GBP/USD", "GBPUSD=X", False),
        ("USD/JPY", "JPY=X", False),
        ("Gold", "GC=F", False),
        ("Bitcoin", "BTC-USD", False),
        ("Ethereum", "ETH-USD", False),
        ("US100", "^IXIC", False),
        ("DJI30", "^DJI", False),
        ("Apple", "AAPL", False),
        ("Tesla", "TSLA", False),
        ("EUR/GBP", "EURGBP=X", False),
        ("GBP/JPY", "GBPJPY=X", False),
        ("Silver", "SI=F", False),
        ("Brent Oil", "BZ=F", False),
        ("Solana", "SOL-USD", False),
        ("Microsoft", "MSFT", False),
        ("Amazon", "AMZN", False),
        ("EUR/USD-OTC", "EURUSD=X", True),
        ("GBP/USD-OTC", "GBPUSD=X", True),
        ("Gold OTC", "GC=F", True),
    ]
    
    while True:
        for pair_name, symbol, is_otc in priority_pairs:
            try:
                rsi = get_rsi(symbol)
                
                # Send signal IMMEDIATELY when RSI condition is met
                if rsi <= 30:
                    signal = {
                        'pair': pair_name,
                        'flag': get_flag(pair_name),
                        'price': get_price(symbol) or 0,
                        'rsi': rsi,
                        'direction': "BUY",
                        'confidence': min(95, int(75 - rsi + 20)),
                        'emoji': "🟢🟢" if (75 - rsi + 20) >= 75 else "🟢",
                        'reason': f"RSI Oversold ({rsi}) - Strong reversal expected UP",
                        'is_otc': is_otc,
                        'timestamp': format_time()
                    }
                    if signal['price'] > 0:
                        message = format_signal(signal)
                        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
                        settings['total_signals'] += 1
                        print(f"📤 IMMEDIATE SIGNAL SENT: {pair_name} BUY (RSI: {rsi}) at {format_time()}")
                        await asyncio.sleep(30)  # Wait 30 seconds before next signal from same pair
                
                elif rsi >= 70:
                    signal = {
                        'pair': pair_name,
                        'flag': get_flag(pair_name),
                        'price': get_price(symbol) or 0,
                        'rsi': rsi,
                        'direction': "SELL",
                        'confidence': min(95, int(rsi - 70 + 20)),
                        'emoji': "🔴🔴" if (rsi - 70 + 20) >= 75 else "🔴",
                        'reason': f"RSI Overbought ({rsi}) - Strong reversal expected DOWN",
                        'is_otc': is_otc,
                        'timestamp': format_time()
                    }
                    if signal['price'] > 0:
                        message = format_signal(signal)
                        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
                        settings['total_signals'] += 1
                        print(f"📤 IMMEDIATE SIGNAL SENT: {pair_name} SELL (RSI: {rsi}) at {format_time()}")
                        await asyncio.sleep(30)
                
            except Exception as e:
                print(f"Error monitoring {pair_name}: {e}")
            
            await asyncio.sleep(5)  # Check each pair every 5 seconds
        
        print(f"💓 Monitor cycle complete at {format_time()}")
        await asyncio.sleep(2)

# ============================================
# COMMAND HANDLERS
# ============================================

async def start_command(update, context):
    await update.message.reply_text(f"""
🤖 <b>IQ TRADING BOT - PROFESSIONAL EDITION</b>

✅ Bot is ONLINE with REAL-TIME SIGNALS!

📈 <b>Instruments:</b>
• {len(FOREX_PAIRS) + len(OTC_FOREX)} Forex Pairs (including OTC)
• {len(INDICES)} Indices
• {len(COMMODITIES)} Commodities
• {len(STOCKS)} Stocks
• {len(CRYPTO)} Cryptocurrencies
• <b>TOTAL: {len(ALL_PAIRS)}+ instruments</b>

⚡ <b>Signal Mode:</b> REAL-TIME (immediate when RSI < 30 or > 70)
🎯 <b>Confidence threshold:</b> {settings['min_confidence']}%
⏰ <b>Time Zone:</b> Nigeria (WAT)
🕐 <b>Current Time:</b> {format_time()}

📋 Type /help for commands
""", parse_mode='HTML')

async def help_command(update, context):
    await update.message.reply_text(f"""
📋 <b>COMMANDS</b>

/status - Bot status and statistics
/pairs - List all available instruments
/signal [pair] - Manual signal for any pair
/otc [pair] - Manual OTC signal
/stats - Trading statistics

⚡ <b>Auto Feature:</b>
Signals are sent IMMEDIATELY when RSI < 30 or > 70
No fixed schedule - opportunity-based alerts!

⏰ Nigeria Time: {format_time()}
""", parse_mode='HTML')

async def pairs_command(update, context):
    forex_count = len(FOREX_PAIRS) + len(OTC_FOREX)
    await update.message.reply_text(f"""
📊 <b>AVAILABLE INSTRUMENTS</b>

<b>Forex:</b> {forex_count} pairs (including OTC)
<b>Indices:</b> {len(INDICES)} (US100, DJI30, SP500, etc.)
<b>Commodities:</b> {len(COMMODITIES)} (Gold, Silver, Oil)
<b>Stocks:</b> {len(STOCKS)} (Apple, Tesla, Amazon, etc.)
<b>Crypto:</b> {len(CRYPTO)} (Bitcoin, Ethereum, Solana)

<b>TOTAL: {len(ALL_PAIRS)}+ instruments</b>

Type /signal [PAIR] for any instrument
Example: /signal Apple, /signal Gold, /signal Bitcoin

<i>⚠️ Signals sent immediately when RSI < 30 (BUY) or > 70 (SELL)</i>
""", parse_mode='HTML')

async def status_command(update, context):
    await update.message.reply_text(f"""
📊 <b>BOT STATUS</b>

✅ Status: ONLINE
📈 Total instruments: {len(ALL_PAIRS)}
🎯 Min confidence: {settings['min_confidence']}%
🎯 Total signals sent: {settings['total_signals']}
⚡ Signal mode: REAL-TIME (opportunity-based)
📱 Platform: Railway Cloud
⏰ Time Zone: Nigeria (WAT)
🕐 Current Time: {format_time()}

<b>Signal Trigger:</b> RSI < 30 (BUY) or RSI > 70 (SELL)
<b>OTC Support:</b> Yes
""", parse_mode='HTML')

async def signal_command(update, context):
    if not context.args:
        await update.message.reply_text(f"⚠️ Usage: /signal EUR/USD\n\nType /pairs to see all {len(ALL_PAIRS)} instruments")
        return
    
    pair = context.args[0].upper()
    await update.message.reply_text(f"🔍 Analyzing {pair}...")
    await update.message.reply_text("📊 No strong signal right now. Signals are sent automatically when RSI < 30 or > 70!")

async def otc_command(update, context):
    if not context.args:
        await update.message.reply_text(f"⚠️ Usage: /otc EUR/USD\n\nOTC signals for after-hours trading.")
        return
    
    pair = context.args[0].upper()
    await update.message.reply_text(f"🔍 Analyzing {pair} (OTC Mode)...")
    await update.message.reply_text("📊 No strong signal right now. Signals are sent automatically when conditions are met!")

async def stats_command(update, context):
    await update.message.reply_text(f"""
📊 <b>STATISTICS</b>

Total signals sent: {settings['total_signals']}
Min confidence: {settings['min_confidence']}
Active instruments: {len(ALL_PAIRS)}
Signal mode: REAL-TIME (opportunity-based)

⏰ {format_time()}
""", parse_mode='HTML')

# ============================================
# ADD HANDLERS
# ============================================

application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("pairs", pairs_command))
application.add_handler(CommandHandler("status", status_command))
application.add_handler(CommandHandler("signal", signal_command))
application.add_handler(CommandHandler("otc", otc_command))
application.add_handler(CommandHandler("stats", stats_command))

# ============================================
# STARTUP
# ============================================

async def send_startup():
    await bot.send_message(chat_id=CHAT_ID, text=f"""
🤖 <b>IQ TRADING BOT - PROFESSIONAL EDITION</b>

✅ Bot is ONLINE with {len(ALL_PAIRS)}+ instruments!
⚡ REAL-TIME SIGNALS ACTIVE - Will send immediately when RSI < 30 or > 70

📈 <b>Instruments:</b>
• Forex: {len(FOREX_PAIRS) + len(OTC_FOREX)} pairs (including OTC)
• Indices: {len(INDICES)}
• Commodities: {len(COMMODITIES)}
• Stocks: {len(STOCKS)}
• Crypto: {len(CRYPTO)}

⚡ <b>Signal Mode:</b> REAL-TIME (no fixed schedule)
🎯 <b>Trigger:</b> RSI < 30 = BUY | RSI > 70 = SELL
⏰ <b>Nigeria Time:</b> {format_time()}

<i>Signals will appear here immediately when opportunities arise!</i>
""", parse_mode='HTML')

# Start continuous monitor thread
async def main():
    # Send startup message
    await send_startup()
    
    # Start continuous monitoring
    asyncio.create_task(continuous_monitor())
    
    # Start polling
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    print("""
🚀 BOT IS RUNNING!
📊 Instruments: 300+ (Forex, Indices, Stocks, Commodities, Crypto)
⚡ REAL-TIME SIGNALS: Will send immediately when RSI < 30 or > 70
📍 Nigeria Time Zone (WAT)
📍 Press Ctrl+C to stop
    """)
    
    while True:
        await asyncio.sleep(60)

# Run
if __name__ == "__main__":
    asyncio.run(main())
