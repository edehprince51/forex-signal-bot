"""
IQ TRADING BOT - POCKET OPTION DIRECT
Direct WebSocket connection to Pocket Option
"""

import os
import json
import asyncio
import websocket
import threading
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, CommandHandler

load_dotenv()

print("""
╔════════════════════════════════════════════════════════════════╗
║   IQ TRADING BOT - POCKET OPTION DIRECT                        ║
║   Direct WebSocket Connection                                  ║
╚════════════════════════════════════════════════════════════════╝
""")

# ============================================
# CREDENTIALS
# ============================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your_secret_key_here")

# Pocket Option credentials from your browser
SSID = os.getenv("IQ_OPTION_SSID", "0d3ef4dafc05966efc12800ba7963e78")
UID = os.getenv("IQ_OPTION_UID", "29984823")

if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not found!")
    exit(1)

print("✅ Credentials loaded!")
print(f"📡 SSID: {SSID[:20]}...")
print(f"👤 UID: {UID}")

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

settings = {
    "total_signals": 0,
    "auto_trade_enabled": False,
    "ws_connected": False,
    "ws": None
}

# ============================================
# POCKET OPTION WEBSOCKET CONNECTION
# ============================================

def on_message(ws, message):
    """Handle incoming WebSocket messages"""
    try:
        print(f"📨 Raw message: {message[:100]}...")
        
        # Parse message
        if message.startswith("42"):
            # This is a socket.io message
            data = json.loads(message[2:])
            print(f"📊 Parsed: {data}")
            
            # Check for price updates or signals
            if isinstance(data, list) and len(data) > 1:
                event = data[0]
                payload = data[1]
                print(f"🎯 Event: {event}")
                
                if event == "candle":
                    # Real-time candle data
                    print(f"💰 Candle: {payload}")
                    
    except Exception as e:
        print(f"Error parsing message: {e}")

def on_error(ws, error):
    print(f"❌ WebSocket error: {error}")
    settings["ws_connected"] = False

def on_close(ws, close_status_code, close_msg):
    print("🔌 WebSocket closed")
    settings["ws_connected"] = False

def on_open(ws):
    print("✅ WebSocket connected to Pocket Option!")
    settings["ws_connected"] = True
    settings["ws"] = ws
    
    # Send authentication message
    auth_message = f'42["auth",{{"session":"{SSID}","isDemo":1,"uid":{UID},"platform":1}}]'
    ws.send(auth_message)
    print(f"🔐 Auth message sent")
    
    # Subscribe to candles for EURUSD
    subscribe_msg = '42["subscribe",{"name":"candle-1-EURUSD"}]'
    ws.send(subscribe_msg)
    print(f"📊 Subscribed to EURUSD")

def connect_websocket():
    """Connect to Pocket Option WebSocket"""
    try:
        # Pocket Option WebSocket URL
        ws_url = "wss://api.pocketoption.com/socket.io/?EIO=4&transport=websocket"
        
        print(f"🔌 Connecting to {ws_url}...")
        
        ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # Run WebSocket in separate thread
        wst = threading.Thread(target=ws.run_forever, daemon=True)
        wst.start()
        
        return ws
    except Exception as e:
        print(f"❌ WebSocket connection error: {e}")
        return None

# ============================================
# FLASK WEBHOOK SERVER
# ============================================

flask_app = Flask(__name__)

@flask_app.route('/webhook', methods=['POST'])
def webhook():
    secret = request.headers.get('X-Webhook-Token')
    if secret != WEBHOOK_SECRET:
        return jsonify({"error": "Invalid secret"}), 401
    
    data = request.json
    message = data.get('message', '')
    side = data.get('side', '')
    symbol = data.get('symbol', '')
    
    signal_msg = f"""
🔔 TRADINGVIEW ALERT

🎫 Trade: {symbol}
📈 Direction: {side}
⏰ Time: {format_time()}
"""
    
    try:
        asyncio.run(bot.send_message(chat_id=CHAT_ID, text=signal_msg))
        return jsonify({"status": "sent"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# TELEGRAM COMMANDS
# ============================================

async def start_command(update, context):
    await update.message.reply_text(
        f"🤖 IQ TRADING BOT - POCKET OPTION DIRECT\n\n"
        f"✅ Bot is ONLINE!\n\n"
        f"📡 Pocket Option WS: {'✅ CONNECTED' if settings['ws_connected'] else '❌ DISCONNECTED'}\n"
        f"🔗 TradingView Webhook: ACTIVE\n\n"
        f"📋 Commands:\n"
        f"   /status - Bot status\n"
        f"   /webhook - Show webhook URL\n\n"
        f"⏰ Nigeria Time: {format_time()}",
        parse_mode='HTML'
    )

async def status_command(update, context):
    ws_status = "🟢 CONNECTED" if settings["ws_connected"] else "🔴 DISCONNECTED"
    auto_status = "🟢 ENABLED" if settings["auto_trade_enabled"] else "🔴 DISABLED"
    
    await update.message.reply_text(
        f"📊 BOT STATUS\n\n"
        f"✅ Status: ONLINE\n"
        f"📡 Pocket Option WS: {ws_status}\n"
        f"🤖 Auto-trade: {auto_status}\n"
        f"🔗 TradingView Webhook: ACTIVE\n"
        f"🎯 Total signals: {settings['total_signals']}\n"
        f"⏰ Nigeria Time: {format_time()}",
        parse_mode='HTML'
    )

async def webhook_command(update, context):
    railway_url = os.getenv('RAILWAY_PUBLIC_URL', 'https://your-app.railway.app')
    webhook_url = f"{railway_url}/webhook"
    
    await update.message.reply_text(
        f"🔗 Webhook URL for TradingView\n\n"
        f"<code>{webhook_url}</code>\n\n"
        f"Headers: X-Webhook-Token: {WEBHOOK_SECRET}\n\n"
        f"JSON Format:\n"
        f"<code>{{'symbol': 'EURUSD', 'side': 'BUY'}}</code>",
        parse_mode='HTML'
    )

async def autotrade_command(update, context):
    if not settings["ws_connected"]:
        await update.message.reply_text("❌ Cannot enable: Pocket Option not connected!")
        return
    
    settings["auto_trade_enabled"] = not settings["auto_trade_enabled"]
    status = "ENABLED" if settings["auto_trade_enabled"] else "DISABLED"
    await update.message.reply_text(f"🤖 Auto-trading {status} (Practice Mode)")

# Add handlers
telegram_app.add_handler(CommandHandler("start", start_command))
telegram_app.add_handler(CommandHandler("status", status_command))
telegram_app.add_handler(CommandHandler("webhook", webhook_command))
telegram_app.add_handler(CommandHandler("autotrade", autotrade_command))

# ============================================
# STARTUP
# ============================================

async def send_startup():
    ws_status = "CONNECTED" if settings["ws_connected"] else "DISCONNECTED"
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"🤖 IQ TRADING BOT - POCKET OPTION DIRECT\n\n✅ Bot ONLINE!\n📡 WebSocket: {ws_status}\n🔗 TradingView Webhook: ACTIVE\n\n⏰ Nigeria Time: {format_time()}"
    )

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))

async def main():
    # Start WebSocket connection
    connect_websocket()
    
    # Send startup message
    await send_startup()
    
    # Start Flask thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🚀 Webhook server started")
    
    # Start Telegram bot
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()
    print("🚀 Telegram bot started")
    print(f"📍 Nigeria Time: {format_time()}")
    
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
