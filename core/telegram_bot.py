import os
import requests
import asyncio
import threading
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Load Env
env_path = "/Volumes/SSD/DEV_SSD/MY/DipSniper/config/settings.env"
load_dotenv(env_path)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Simple Message Sender (No Async) ---
def send_message(text):
    """단방향 메시지 전송 (알림용)"""
    if not TOKEN or not CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=5)
    except Exception as e:
        print(f"❌ Telegram Send Error: {e}")

def send_report(result, final_value, initial_cash):
    """백테스트 결과 리포트 전송"""
    profit = final_value - initial_cash
    profit_pct = (profit / initial_cash) * 100
    emoji = "🚀" if profit > 0 else "📉"
    
    msg = f"""
*🔫 DipSniper Backtest Report*
--------------------------------
{emoji} *Profit:* {profit_pct:.2f}%
💰 *Final:* ₩{final_value:,.0f}
📊 *Trades:* {len(result)}
"""
    send_message(msg)

# --- Interactive Bot Logic (Async) ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔫 **DipSniper Bot Online!**\n명령어를 선택하세요:\n/status - 상태 확인\n/stop - 봇 정지")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # In a real app, check global state or IPC
    await update.message.reply_text("✅ **System Status:**\n- Dashboard: Running\n- Tunnel: Active")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛑 **Stopping Bot...**\n(Not implemented in this demo)")

def run_telegram_bot():
    """텔레그램 봇 리스너 실행 (별도 스레드)"""
    if not TOKEN:
        print("⚠️ No Telegram Token. Bot listener skipped.")
        return

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("stop", stop_command))

    print("🤖 Telegram Bot Listening...")
    application.run_polling()

def start_bot_thread():
    t = threading.Thread(target=run_telegram_bot, daemon=True)
    t.start()

def set_bot_commands():
    # Only setting commands via API for UI hints
    if not TOKEN: return
    url = f"https://api.telegram.org/bot{TOKEN}/setMyCommands"
    commands = [
        {"command": "start", "description": "봇 시작"},
        {"command": "status", "description": "상태 확인"},
        {"command": "stop", "description": "긴급 정지"}
    ]
    try:
        requests.post(url, json={"commands": commands}, timeout=5)
    except: pass
