"""
POCKET OPTION TRADING BOT - WORKING VERSION
Uses BinaryOptionsToolsV2 (real WebSocket API)
"""

import os
import asyncio
import threading
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

# REAL Pocket Option library
from BinaryOptionsToolsV2.pocketoption import PocketOptionAsync

load_dotenv()

print("""
╔════════════════════════════════════════════════════════════════╗
║   POCKET OPTION TRADING BOT - WORKING VERSION                  ║
║   Using BinaryOptionsToolsV2 (WebSocket API)                   ║
╚════════════════════════════════════════════════════════════════╝
""")

# ============================================
# CREDENTIALS
# ============================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your_secret_key_here")

# Pocket Option Session ID (from browser cookies)
PO_SSID = os.getenv("PO_SSID")  # Get this from browser DevTools

if not TELEGRAM_TOKEN or not CHAT_ID:
    print("❌ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not found!")
    exit(1)

if not PO_SSID:
    print("⚠️ PO_SSID not found! Get it from Pocket Option browser cookies.")
    print("   DevTools → Application → Cookies → ssid")
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
# BOT STATE
# ============================================

settings = {
    "po_connected": False,
    "auto_trade": False,
    "total_signals": 0,
    "client": None,
    "balance": 0.0
}

# ============================================
# POCKET OPTION CLIENT (REAL)
# ============================================

async def connect_pocket_option():
    """Connect to Pocket Option using WebSocket API"""
    try:
        print("🔌 Connecting to Pocket Option...")
        
        # Initialize client with SSID
        client = PocketOptionAsync(ssid=PO_SSID)
        settings["client"] = client
        
        # Get balance to verify connection
        balance = await client.balance()
        settings["balance"] = balance
        settings["po_connected"] = True
        
        print(f"✅ Connected! Balance: ${balance}")
        
        # Notify Telegram
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"✅ Pocket Option CONNECTED!\n"
                 f"💰 Balance: ${balance}\n"
                 f"⏰ {format_time()}"
        )
        
        return True
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        settings["po_connected"] = False
        return False

async def place_trade(symbol, direction, amount=1.0, duration=60):
    """Place a trade on Pocket Option"""
    if not settings["po_connected"] or not settings["client"]:
        return None, "Not connected"
    
    try:
        client = settings["client"]
        
        # Convert direction to buy/sell
        is_buy = direction.upper() == "BUY"
        
        # Place trade
        if is_buy:
            trade_id, deal = await client.buy(symbol, amount, duration)
        else:
            trade_id, deal = await client.sell(symbol, amount, duration)
        
        print(f"✅ Trade placed: {trade_id} - {deal}")
        return trade_id, deal
        
    except Exception as e:
        print(f"❌ Trade error: {e}")
        return None, str(e)

async def check_trade_result(trade_id):
    """Check if trade won or lost"""
    if not settings["client"]:
        return None
    
    try:
        result = await settings["client"].check_win(trade_id)
        return result  # 'win', 'draw', or 'loss'
    except Exception as e:
        print(f"❌ Check win error: {e}")
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
    if not data:
        return jsonify({"error": "No JSON data"}), 400
        
    symbol = data.get('symbol', 'EURUSD_otc')
    side = data.get('side', 'BUY')
    amount = data.get('amount', 1.0)
    duration = data.get('duration', 60)  # seconds
    
    settings["total_signals"] += 1
    
    # Calculate times
    entry_time = get_nigeria_time() + timedelta(minutes=3)
    
    # Auto-trade if enabled
    trade_result = None
    if settings["auto_trade"] and settings["po_connected"]:
        # Run async trade in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        trade_id, deal = loop.run_until_complete(
            place_trade(symbol, side, amount, duration)
        )
        trade_result = f"Trade ID: {trade_id}" if trade_id else f"Failed: {deal}"
    
    # Build message
    msg = f"""🔔 TRADINGVIEW SIGNAL #{settings['total_signals']}

🎫 Trade: {symbol}
📈 Direction: {side}
⏳ Duration: {duration}s
💰 Amount: ${amount}
➡️ Entry: {entry_time.strftime('%I:%M %p')}"""

    if trade_result:
        msg += f"\n🤖 Auto-trade: {trade_result}"
    
    msg += f"\n\n⏰ {format_time()} (Nigeria Time)"
    
    # Send to Telegram
    try:
        asyncio.run(bot.send_message(chat_id=CHAT_ID, text=msg))
        return jsonify({
            "status": "sent", 
            "signal_id": settings["total_signals"],
            "auto_traded": settings["auto_trade"] and settings["po_connected"]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@flask_app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "po_connected": settings["po_connected"],
        "balance": settings["balance"],
        "signals_received": settings["total_signals"],
        "time": format_time()
    }), 200

# ============================================
# TELEGRAM COMMANDS
# ============================================

bot = Bot(token=TELEGRAM_TOKEN)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🤖 POCKET OPTION TRADING BOT\n\n"
        f"✅ Bot ONLINE\n"
        f"📡 Pocket Option: {'✅ CONNECTED' if settings['po_connected'] else '❌ DISCONNECTED'}\n"
        f"💰 Balance: ${settings['balance']:.2f}\n"
        f"🔗 TradingView Webhook: ACTIVE\n\n"
        f"Commands:\n"
        f"/status - Check status\n"
        f"/balance - Check balance\n"
        f"/webhook - Get webhook URL\n"
        f"/autotrade - Toggle auto trade\n"
        f"/trade - Manual trade (e.g., /trade EURUSD_otc BUY 1.0)\n\n"
        f"⏰ {format_time()} (Nigeria Time)"
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_text = (
        f"📊 BOT STATUS\n\n"
        f"✅ Status: ONLINE\n"
        f"📡 Pocket Option: {'✅ CONNECTED' if settings['po_connected'] else '❌ DISCONNECTED'}\n"
        f"💰 Balance: ${settings['balance']:.2f}\n"
        f"🤖 Auto-trade: {'✅ ON' if settings['auto_trade'] else '❌ OFF'}\n"
        f"🔗 TradingView Webhook: ACTIVE\n"
        f"📊 Total signals: {settings['total_signals']}\n"
        f"⏰ {format_time()} (Nigeria Time)"
    )
    await update.message.reply_text(status_text)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if settings["po_connected"] and settings["client"]:
        try:
            bal = await settings["client"].balance()
            settings["balance"] = bal
            await update.message.reply_text(f"💰 Current Balance: ${bal:.2f}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error checking balance: {e}")
    else:
        await update.message.reply_text("❌ Not connected to Pocket Option")

async def webhook_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    railway_url = os.getenv('RAILWAY_PUBLIC_URL', 'https://your-app.railway.app')
    webhook_url = f"{railway_url}/webhook"
    
    await update.message.reply_text(
        f"🔗 WEBHOOK URL\n\n"
        f"<code>{webhook_url}</code>\n\n"
        f"Headers:\n"
        f"X-Webhook-Token: <code>{WEBHOOK_SECRET}</code>\n\n"
        f"Example JSON:\n"
        f'<code>{{"symbol": "EURUSD_otc", "side": "BUY", "amount": 1.0, "duration": 60}}</code>',
        parse_mode='HTML'
    )

async def autotrade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not settings["po_connected"]:
        await update.message.reply_text("❌ Pocket Option not connected! Cannot enable auto-trade.")
        return
    
    settings["auto_trade"] = not settings["auto_trade"]
    status = "ON ✅" if settings["auto_trade"] else "OFF ❌"
    await update.message.reply_text(f"🤖 Auto-trade turned {status}")

async def trade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual trade: /trade EURUSD_otc BUY 1.0 60"""
    if not settings["po_connected"]:
        await update.message.reply_text("❌ Not connected to Pocket Option")
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: /trade <symbol> <BUY/SELL> [amount] [duration_seconds]\n"
            "Example: /trade EURUSD_otc BUY 1.0 60"
        )
        return
    
    symbol = args[0]
    direction = args[1].upper()
    amount = float(args[2]) if len(args) > 2 else 1.0
    duration = int(args[3]) if len(args) > 3 else 60
    
    await update.message.reply_text(f"⏳ Placing trade: {symbol} {direction} ${amount}...")
    
    trade_id, result = await place_trade(symbol, direction, amount, duration)
    
    if trade_id:
        await update.message.reply_text(f"✅ Trade placed!\nID: {trade_id}\nDetails: {result}")
        
        # Wait for result
        await asyncio.sleep(duration + 2)
        outcome = await check_trade_result(trade_id)
        await update.message.reply_text(f"🏁 Trade result: {outcome.upper()}")
    else:
        await update.message.reply_text(f"❌ Trade failed: {result}")

# ============================================
# STARTUP
# ============================================

async def send_startup():
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"🤖 POCKET OPTION BOT STARTED\n\n"
             f"✅ Bot ONLINE\n"
             f"🔄 Connecting to Pocket Option...\n"
             f"⏰ {format_time()}"
    )

def run_flask():
    port = int(os.getenv('PORT', 5000))
    flask_app.run(host='0.0.0.0', port=port, debug=False)

async def main():
    # Send startup message
    await send_startup()
    
    # Connect to Pocket Option
    connected = await connect_pocket_option()
    if not connected:
        await bot.send_message(
            chat_id=CHAT_ID,
            text="⚠️ Failed to connect to Pocket Option. Check your SSID."
        )
    
    # Build Telegram app
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("webhook", webhook_command))
    application.add_handler(CommandHandler("autotrade", autotrade_command))
    application.add_handler(CommandHandler("trade", trade_command))
    
    # Start Flask in background
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print(f"🚀 Webhook server started on port {os.getenv('PORT', 5000)}")
    
    # Start Telegram bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("🚀 Telegram bot started")
    print(f"📍 {format_time()}")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        if settings["client"]:
            await settings["client"].shutdown()
        await application.stop()

if __name__ == "__main__":
    asyncio.run(main())
