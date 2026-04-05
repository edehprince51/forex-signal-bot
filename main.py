"""
IQ TRADING BOT - PROFESSIONAL EDITION
TradingView Webhook + IQ Option API Integration
Real-time signals | Auto-trade capable | Nigeria Time
"""

import os
import json
import hmac
import requests
import asyncio
import threading
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, CommandHandler

# Load environment variables
load_dotenv()

print("""
╔════════════════════════════════════════════════════════════════╗
║   IQ TRADING BOT - PROFESSIONAL EDITION                        ║
║   TradingView Webhook + IQ Option API | Nigeria Time           ║
╚════════════════════════════════════════════════════════════════╝
""")

# ============================================
# CREDENTIALS
# ============================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your_secret_key_here")

# IQ Option Credentials
IQ_EMAIL = os.getenv("IQ_OPTION_EMAIL")
IQ_PASSWORD = os.getenv("IQ_OPTION_PASSWORD")
IQ_SSID = os.getenv("IQ_OPTION_SSID")

if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not found!")
    exit(1)

print("✅ Credentials loaded!")

# ============================================
# NIGERIA TIME ZONE
# ============================================

def get_nigeria_time():
    return datetime.utcnow() + timedelta(hours=1)

def format_time(dt=None):
    if dt is None:
        dt = get_nigeria_time()
    return dt.strftime("%I:%M %p")

# ============================================
# TELEGRAM BOT SETUP
# ============================================

bot = Bot(token=TELEGRAM_TOKEN)
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

# Settings
settings = {
    "total_signals": 0,
    "auto_trade_enabled": False,
    "iq_connected": False,
    "iq_api": None
}

# ============================================
# IQ OPTION CONNECTION
# ============================================

def connect_iq_option():
    """Connect to IQ Option API"""
    if not IQ_EMAIL or not IQ_PASSWORD:
        print("⚠️ IQ Option credentials not provided")
        return False
    
    try:
        from iqoptionapi.stable_api import IQ_Option
        
        print(f"🔌 Connecting to IQ Option as {IQ_EMAIL}...")
        api = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        
        # Try SSID first if provided, otherwise use email/password
        if IQ_SSID:
            check, reason = api.connect(ssid=IQ_SSID)
        else:
            check, reason = api.connect()
        
        if check:
            settings["iq_api"] = api
            settings["iq_connected"] = True
            
            # Set to practice mode by default (safe)
            api.change_balance("PRACTICE")
            balance = api.get_balance()
            print(f"✅ IQ Option connected! Balance: ${balance}")
            return True
        else:
            print(f"❌ IQ Option connection failed: {reason}")
            return False
            
    except Exception as e:
        print(f"❌ IQ Option error: {e}")
        return False

# ============================================
# SIGNAL FORMATTER
# ============================================

def format_signal(name, flag, direction, confidence, price, rsi, reason, is_manual=False):
    """Format signal with 3-minute head start and martingale levels"""
    entry_time = get_nigeria_time() + timedelta(minutes=3)
    
    martingale_lines = []
    for i in range(1, 4):
        level_time = entry_time + timedelta(minutes=i * 3)
        martingale_lines.append(f"Level {i} → {level_time.strftime('%I:%M %p')}")
    
    tp = price * 1.005 if direction == "BUY" else price * 0.995
    sl = price * 0.995 if direction == "BUY" else price * 1.005
    
    signal_type = "🔔 MANUAL SIGNAL" if is_manual else "🔔 TRADINGVIEW SIGNAL"
    
    return f"""
{signal_type}

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

# ============================================
# TRADINGVIEW WEBHOOK HANDLER
# ============================================

# Flask app for webhooks
flask_app = Flask(__name__)

@flask_app.route('/webhook', methods=['POST'])
def webhook():
    """Receive TradingView alerts and forward to Telegram"""
    
    # Verify secret
    secret = request.headers.get('X-Webhook-Token')
    if secret != WEBHOOK_SECRET:
        return jsonify({"error": "Invalid secret"}), 401
    
    # Get the alert data
    if request.is_json:
        data = request.json
        message = data.get('message', data.get('text', ''))
        side = data.get('side', data.get('direction', ''))
        symbol = data.get('symbol', data.get('ticker', ''))
        price = data.get('price', 0)
    else:
        message = request.data.decode('utf-8')
        # Try to parse the message
        parts = message.upper().split()
        side = "BUY" if "BUY" in message or "LONG" in message else "SELL" if "SELL" in message or "SHORT" in message else ""
        symbol = next((p for p in parts if "/" in p or any(x in p for x in ["EUR", "GBP", "USD", "BTC", "ETH", "GOLD"])), "UNKNOWN")
        price = 0
    
    if not side:
        return jsonify({"error": "No direction found"}), 400
    
    # Format and send signal
    signal_msg = f"""
🔔 TRADINGVIEW ALERT

🎫 Trade: {symbol}
📈 Direction: {side}
💰 Price: ${price if price > 0 else 'Market'}
⏰ Time: {format_time()}

⚠️ This is a TradingView alert. Verify before trading!
"""
    
    # Send to Telegram
    try:
        asyncio.run(bot.send_message(chat_id=CHAT_ID, text=signal_msg))
        print(f"📤 TradingView alert forwarded: {side} {symbol}")
        
        # Auto-trade if enabled
        if settings["auto_trade_enabled"] and settings["iq_connected"]:
            trade_result = execute_iq_option_trade(symbol, side, 1.0)  # $1 trade
            asyncio.run(bot.send_message(chat_id=CHAT_ID, text=f"🤖 Auto-trade executed: {trade_result}"))
        
        return jsonify({"status": "sent"}), 200
    except Exception as e:
        print(f"Error sending: {e}")
        return jsonify({"error": str(e)}), 500

def execute_iq_option_trade(symbol, direction, amount):
    """Execute trade on IQ Option"""
    if not settings["iq_connected"]:
        return "IQ Option not connected"
    
    try:
        api = settings["iq_api"]
        # Convert direction to call/put
        action = "call" if direction.upper() == "BUY" else "put"
        
        success, order_id = api.buy(amount, symbol, action, 1)  # 1 minute expiry
        if success:
            return f"✅ {direction} {symbol} ${amount} - Order ID: {order_id}"
        else:
            return f"❌ Trade failed: {order_id}"
    except Exception as e:
        return f"❌ Error: {e}"

# ============================================
# TELEGRAM COMMANDS
# ============================================

async def start_command(update, context):
    await update.message.reply_text(
        f"🤖 IQ TRADING BOT - PROFESSIONAL EDITION\n\n"
        f"✅ Bot is ONLINE!\n\n"
        f"⚡ <b>Integrations:</b>\n"
        f"   • TradingView Webhook - ACTIVE\n"
        f"   • IQ Option API - {'CONNECTED' if settings['iq_connected'] else 'DISCONNECTED'}\n\n"
        f"📋 <b>Commands:</b>\n"
        f"   /status - Bot status\n"
        f"   /autotrade - Toggle auto-trading\n"
        f"   /webhook - Show webhook URL\n\n"
        f"⏰ Nigeria Time: {format_time()}",
        parse_mode='HTML'
    )

async def status_command(update, context):
    auto_status = "🟢 ENABLED" if settings["auto_trade_enabled"] else "🔴 DISABLED"
    iq_status = "🟢 CONNECTED" if settings["iq_connected"] else "🔴 DISCONNECTED"
    
    await update.message.reply_text(
        f"📊 BOT STATUS\n\n"
        f"✅ Status: ONLINE\n"
        f"🎯 Total signals: {settings['total_signals']}\n"
        f"🤖 Auto-trade: {auto_status}\n"
        f"📡 IQ Option: {iq_status}\n"
        f"🔗 TradingView Webhook: ACTIVE\n"
        f"⏰ Nigeria Time: {format_time()}\n\n"
        f"📋 Commands:\n"
        f"   /autotrade - Toggle auto-trading\n"
        f"   /webhook - Show webhook URL",
        parse_mode='HTML'
    )

async def autotrade_command(update, context):
    settings["auto_trade_enabled"] = not settings["auto_trade_enabled"]
    status = "ENABLED" if settings["auto_trade_enabled"] else "DISABLED"
    await update.message.reply_text(f"🤖 Auto-trading {status}!\n\n⚠️ Make sure IQ Option is connected and in PRACTICE mode first!")

async def webhook_command(update, context):
    railway_url = os.getenv('RAILWAY_PUBLIC_URL', 'https://your-app.railway.app')
    webhook_url = f"{railway_url}/webhook"
    
    await update.message.reply_text(
        f"🔗 <b>Webhook URL for TradingView</b>\n\n"
        f"<code>{webhook_url}</code>\n\n"
        f"<b>Headers:</b>\n"
        f"X-Webhook-Token: {WEBHOOK_SECRET}\n\n"
        f"<b>JSON Format Example:</b>\n"
        f"<code>{{'symbol': 'EURUSD', 'side': 'BUY', 'price': 1.09234}}</code>\n\n"
        f"<b>Text Format Example:</b>\n"
        f"BUY EURUSD at 1.09234",
        parse_mode='HTML'
    )

# Add handlers
telegram_app.add_handler(CommandHandler("start", start_command))
telegram_app.add_handler(CommandHandler("status", status_command))
telegram_app.add_handler(CommandHandler("autotrade", autotrade_command))
telegram_app.add_handler(CommandHandler("webhook", webhook_command))

# ============================================
# STARTUP MESSAGE
# ============================================

async def send_startup():
    iq_status = "CONNECTED" if settings["iq_connected"] else "DISCONNECTED"
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"🤖 IQ TRADING BOT - PROFESSIONAL EDITION\n\n✅ Bot is ONLINE!\n📡 IQ Option: {iq_status}\n🔗 TradingView Webhook: ACTIVE\n\n📋 Commands: /status, /autotrade, /webhook\n\n⏰ Nigeria Time: {format_time()}"
    )

# ============================================
# FLASK WEBHOOK SERVER
# ============================================

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))

# ============================================
# MAIN
# ============================================

async def main():
    # Connect to IQ Option
    connect_iq_option()
    
    # Send startup message
    await send_startup()
    
    # Start Flask in separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🚀 Webhook server started on port 5000")
    
    # Start Telegram bot
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()
    print("🚀 Telegram bot started")
    print(f"📋 Commands: /status, /autotrade, /webhook")
    print(f"📍 Nigeria Time: {format_time()}")
    
    # Keep running
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
