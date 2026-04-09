"""
POCKET OPTION TRADING BOT - WORKING VERSION
Using pocket-option library (officially supports Pocket Option)
"""

import os
import asyncio
import threading
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, CommandHandler

# Pocket Option library
from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.models import AuthorizationData, Asset

load_dotenv()

print("""
╔════════════════════════════════════════════════════════════════╗
║   POCKET OPTION TRADING BOT - WORKING VERSION                  ║
║   Using official pocket-option library                         ║
╚════════════════════════════════════════════════════════════════╝
""")

# ============================================
# CREDENTIALS
# ============================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your_secret_key_here")

# Your Pocket Option credentials
PO_SESSION = os.getenv("PO_SESSION", "0d3ef4dafc05966efc12800ba7963e78")
PO_UID = os.getenv("PO_UID", "29984823")

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
# TELEGRAM BOT
# ============================================

bot = Bot(token=TELEGRAM_TOKEN)
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

settings = {
    "po_connected": False,
    "auto_trade": False,
    "total_signals": 0,
    "client": None
}

# ============================================
# POCKET OPTION CLIENT (WORKING)
# ============================================

po_client = PocketOptionClient()

@po_client.on.connect
async def on_connect(data):
    print("✅ WebSocket connected to Pocket Option!")
    settings["po_connected"] = True
    
    # Send authentication
    await po_client.emit.auth(
        AuthorizationData(
            session=PO_SESSION,
            isDemo=1,
            uid=int(PO_UID),
            platform=2,
            isFastHistory=True,
            isOptimized=True
        )
    )
    print("🔐 Auth message sent")

@po_client.on.success_auth
async def on_success_auth(data):
    print(f"✅ Successfully authenticated! User ID: {data.id}")
    settings["po_connected"] = True
    
    # Notify Telegram
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"✅ Pocket Option CONNECTED!\n💰 Demo account ready\n⏰ {format_time()}"
    )
    
    # Subscribe to some assets for testing
    await po_client.emit.subscribe_to_asset(Asset.EURUSD_otc)
    print("📊 Subscribed to EURUSD_otc")

@po_client.on.update_close_value
async def on_price_update(assets):
    """Called when price updates - this is your real-time data!"""
    for asset in assets:
        print(f"💰 {asset.id}: {asset.close_value}")
        # You can add signal logic here

@po_client.on.disconnect
async def on_disconnect():
    print("🔌 Disconnected from Pocket Option")
    settings["po_connected"] = False

async def connect_pocket_option():
    """Start Pocket Option connection"""
    try:
        print("🔌 Connecting to Pocket Option...")
        await po_client.connect(Regions.DEMO)
        print("🚀 Pocket Option client started")
        return True
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

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
    symbol = data.get('symbol', 'EURUSD')
    side = data.get('side', 'BUY')
    
    # Send to Telegram
    entry_time = get_nigeria_time() + timedelta(minutes=3)
    msg = f"""
🔔 TRADINGVIEW SIGNAL

🎫 Trade: {symbol}
📈 Direction: {side}
⏳ Timer: 3 minutes
➡️ Entry: {entry_time.strftime('%I:%M %p')}

↪️ Martingale Levels:
 Level 1 → {(entry_time + timedelta(minutes=3)).strftime('%I:%M %p')}
 Level 2 → {(entry_time + timedelta(minutes=6)).strftime('%I:%M %p')}
 Level 3 → {(entry_time + timedelta(minutes=9)).strftime('%I:%M %p')}

⏰ {format_time()} (Nigeria Time)
"""
    
    asyncio.run(bot.send_message(chat_id=CHAT_ID, text=msg))
    return jsonify({"status": "sent"}), 200

# ============================================
# TELEGRAM COMMANDS
# ============================================

async def start_command(update, context):
    await update.message.reply_text(
        f"🤖 POCKET OPTION TRADING BOT\n\n"
        f"✅ Bot ONLINE\n"
        f"📡 Pocket Option: {'✅ CONNECTED' if settings['po_connected'] else '🔄 CONNECTING...'}\n"
        f"🔗 TradingView Webhook: ACTIVE\n\n"
        f"Commands:\n"
        f"/status - Check status\n"
        f"/webhook - Get webhook URL\n"
        f"/autotrade - Toggle auto trade\n\n"
        f"⏰ {format_time()} (Nigeria Time)"
    )

async def status_command(update, context):
    await update.message.reply_text(
        f"📊 BOT STATUS\n\n"
        f"✅ Status: ONLINE\n"
        f"📡 Pocket Option: {'✅ CONNECTED' if settings['po_connected'] else '❌ DISCONNECTED'}\n"
        f"🤖 Auto-trade: {'✅ ON' if settings['auto_trade'] else '❌ OFF'}\n"
        f"🔗 TradingView Webhook: ACTIVE\n"
        f"📊 Total signals: {settings['total_signals']}\n"
        f"⏰ {format_time()} (Nigeria Time)"
    )

async def webhook_command(update, context):
    railway_url = os.getenv('RAILWAY_PUBLIC_URL', 'https://your-app.railway.app')
    webhook_url = f"{railway_url}/webhook"
    
    await update.message.reply_text(
        f"🔗 WEBHOOK URL\n\n"
        f"<code>{webhook_url}</code>\n\n"
        f"Headers:\n"
        f"X-Webhook-Token: {WEBHOOK_SECRET}\n\n"
        f"Example JSON:\n"
        f"<code>{{'symbol': 'EURUSD', 'side': 'BUY'}}</code>",
        parse_mode='HTML'
    )

async def autotrade_command(update, context):
    if not settings["po_connected"]:
        await update.message.reply_text("❌ Pocket Option not connected! Cannot enable auto-trade.")
        return
    
    settings["auto_trade"] = not settings["auto_trade"]
    status = "ON" if settings["auto_trade"] else "OFF"
    await update.message.reply_text(f"🤖 Auto-trade turned {status}\n\n⚠️ Currently in DEMO mode only!")

# Add handlers
telegram_app.add_handler(CommandHandler("start", start_command))
telegram_app.add_handler(CommandHandler("status", status_command))
telegram_app.add_handler(CommandHandler("webhook", webhook_command))
telegram_app.add_handler(CommandHandler("autotrade", autotrade_command))

# ============================================
# STARTUP
# ============================================

async def send_startup():
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"🤖 POCKET OPTION BOT\n\n✅ Bot ONLINE\n🔄 Connecting to Pocket Option...\n⏰ {format_time()}"
    )

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))

async def main():
    # Send startup message
    await send_startup()
    
    # Start Pocket Option connection in background
    asyncio.create_task(connect_pocket_option())
    
    # Start Flask thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🚀 Webhook server started")
    
    # Start Telegram bot
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()
    print("🚀 Telegram bot started")
    print(f"📍 {format_time()}")
    
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
