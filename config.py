"""
POCKET OPTION TRADING BOT - CONFIGURATION
87 Pairs | Binance (Crypto) + Alpha Vantage (Forex/Stocks)
"""

# ============================================
# CRYPTO PAIRS (Binance - 40 pairs)
# ============================================

CRYPTO_PAIRS = [
    # Major
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT",
    # Altcoins
    "MATICUSDT", "DOTUSDT", "AVAXUSDT", "LINKUSDT", "LTCUSDT", "NEARUSDT",
    "ATOMUSDT", "APTUSDT", "SUIUSDT", "ARBUSDT", "OPUSDT",
    # Meme Coins
    "SHIBUSDT", "PEPEUSDT", "FLOKIUSDT", "WIFUSDT", "BONKUSDT",
    # DeFi
    "AAVEUSDT", "UNIUSDT", "CAKEUSDT", "CRVUSDT", "MKRUSDT", "COMPUSDT",
    # Gaming
    "SANDUSDT", "MANAUSDT", "GALAUSDT", "AXSUSDT", "IMXUSDT",
    # Storage
    "FILUSDT", "ARUSDT", "STORJUSDT",
    # Oracle & Exchange
    "API3USDT", "BANDUSDT", "CROUSDT", "OKBUSDT",
]

# ============================================
# FOREX MAJORS (7 pairs)
# ============================================

FOREX_MAJORS = {
    "EURUSD": "EURUSD",
    "GBPUSD": "GBPUSD",
    "USDJPY": "USDJPY",
    "AUDUSD": "AUDUSD",
    "USDCAD": "USDCAD",
    "NZDUSD": "NZDUSD",
    "USDCHF": "USDCHF",
}

# ============================================
# FOREX MINORS (15 pairs)
# ============================================

FOREX_MINORS = {
    "EURGBP": "EURGBP",
    "EURJPY": "EURJPY",
    "EURCHF": "EURCHF",
    "EURCAD": "EURCAD",
    "GBPAUD": "GBPAUD",
    "GBPCAD": "GBPCAD",
    "GBPCHF": "GBPCHF",
    "AUDJPY": "AUDJPY",
    "AUDCAD": "AUDCAD",
    "AUDCHF": "AUDCHF",
    "CADJPY": "CADJPY",
    "NZDJPY": "NZDJPY",
    "CHFJPY": "CHFJPY",
    "EURAUD": "EURAUD",
    "EURTRY": "EURTRY",
}

# ============================================
# INDICES (10 pairs)
# ============================================

INDICES = {
    "US100": "^IXIC",
    "US30": "^DJI",
    "US500": "^GSPC",
    "GER30": "^GDAXI",
    "UK100": "^FTSE",
    "FRA40": "^FCHI",
    "ESP35": "^IBEX",
    "AUS200": "^AXJO",
    "JPN225": "^N225",
    "HK50": "^HSI",
}

# ============================================
# COMMODITIES (5 pairs)
# ============================================

COMMODITIES = {
    "Gold": "GC=F",
    "Silver": "SI=F",
    "BrentOil": "BZ=F",
    "WTICrudeOil": "CL=F",
    "NaturalGas": "NG=F",
}

# ============================================
# STOCKS (10 pairs)
# ============================================

STOCKS = {
    "Apple": "AAPL",
    "Tesla": "TSLA",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Google": "GOOGL",
    "Meta": "META",
    "NVIDIA": "NVDA",
    "AMD": "AMD",
    "Netflix": "NFLX",
    "Alibaba": "BABA",
}

# ============================================
# FLAG EMOJIS FOR DISPLAY
# ============================================

FLAGS = {
    # Forex
    "EURUSD": "🇪🇺🇺🇸", "GBPUSD": "🇬🇧🇺🇸", "USDJPY": "🇺🇸🇯🇵",
    "AUDUSD": "🇦🇺🇺🇸", "USDCAD": "🇺🇸🇨🇦", "NZDUSD": "🇳🇿🇺🇸", "USDCHF": "🇺🇸🇨🇭",
    "EURGBP": "🇪🇺🇬🇧", "EURJPY": "🇪🇺🇯🇵", "EURCHF": "🇪🇺🇨🇭", "EURCAD": "🇪🇺🇨🇦",
    "GBPAUD": "🇬🇧🇦🇺", "GBPCAD": "🇬🇧🇨🇦", "GBPCHF": "🇬🇧🇨🇭",
    "AUDJPY": "🇦🇺🇯🇵", "AUDCAD": "🇦🇺🇨🇦", "AUDCHF": "🇦🇺🇨🇭",
    "CADJPY": "🇨🇦🇯🇵", "NZDJPY": "🇳🇿🇯🇵", "CHFJPY": "🇨🇭🇯🇵",
    "EURAUD": "🇪🇺🇦🇺", "EURTRY": "🇪🇺🇹🇷",
    # Indices
    "US100": "📊", "US30": "📈", "US500": "📊", "GER30": "📊🇩🇪",
    "UK100": "📊🇬🇧", "FRA40": "📊🇫🇷", "ESP35": "📊🇪🇸",
    "AUS200": "📊🇦🇺", "JPN225": "📊🇯🇵", "HK50": "📊🇭🇰",
    # Commodities
    "Gold": "🥇", "Silver": "🥈", "BrentOil": "🛢️", "WTICrudeOil": "🛢️", "NaturalGas": "🔥",
    # Stocks
    "Apple": "🍎", "Tesla": "🚗", "Microsoft": "💻", "Amazon": "📦",
    "Google": "🔍", "Meta": "📘", "NVIDIA": "🎮", "AMD": "💻",
    "Netflix": "🎬", "Alibaba": "🛒",
    # Crypto
    "BTCUSDT": "₿", "ETHUSDT": "⟠", "BNBUSDT": "🟡", "SOLUSDT": "⚡",
    "XRPUSDT": "✖️", "ADAUSDT": "🟣", "DOGEUSDT": "🐕", "MATICUSDT": "🟣",
    "SHIBUSDT": "🐕", "PEPEUSDT": "🐸",
}

def get_flag(pair):
    """Get flag emoji for a pair"""
    return FLAGS.get(pair, "🌍")

# ============================================
# COMBINED PAIRS LIST
# ============================================

ALL_PAIRS = {
    "crypto": CRYPTO_PAIRS,
    "forex_majors": list(FOREX_MAJORS.keys()),
    "forex_minors": list(FOREX_MINORS.keys()),
    "indices": list(INDICES.keys()),
    "commodities": list(COMMODITIES.keys()),
    "stocks": list(STOCKS.keys()),
}

# Priority pairs for quick scanning
PRIORITY_PAIRS = (
    CRYPTO_PAIRS[:15] +
    list(FOREX_MAJORS.keys()) +
    ["Gold", "Bitcoin"] +
    ["Apple", "Tesla", "Microsoft"]
)

# ============================================
# TECHNICAL SETTINGS
# ============================================

RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
SIGNAL_TIMER_MINUTES = 3
MARTINGALE_LEVELS = 3
MARTINGALE_INTERVAL = 3
SIGNAL_COOLDOWN_SECONDS = 600  # 10 minutes between same pair
MIN_CONFIDENCE = 25
SCAN_INTERVAL_SECONDS = 660  # 11 minutes (between 10-12)

print(f"✅ Loaded {len(CRYPTO_PAIRS) + len(FOREX_MAJORS) + len(FOREX_MINORS) + len(INDICES) + len(COMMODITIES) + len(STOCKS)} total instruments")
print(f"   Crypto: {len(CRYPTO_PAIRS)}")
print(f"   Forex Majors: {len(FOREX_MAJORS)}")
print(f"   Forex Minors: {len(FOREX_MINORS)}")
print(f"   Indices: {len(INDICES)}")
print(f"   Commodities: {len(COMMODITIES)}")
print(f"   Stocks: {len(STOCKS)}")