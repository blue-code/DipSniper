import os
import requests
import asyncio
import threading
import pandas as pd
import yfinance as yf
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
from backtest import Backtester

# Load Env
env_path = "/Volumes/SSD/DEV_SSD/MY/DipSniper/config/settings.env"
load_dotenv(env_path)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Simple Message Sender (No Async) ---
def send_message(text):
    if not TOKEN or not CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=5)
    except Exception as e:
        print(f"❌ Telegram Send Error: {e}")

def send_report(result, final_value, initial_cash):
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
    await update.message.reply_text(
        "🔫 **DipSniper Bot Online!**\n\n"
        "👇 명령어를 선택하세요:\n"
        "/backtest [종목] [전략] [기간] - 백테스트 실행\n"
        "/price [종목] - 현재가 조회\n"
        "/recommend - AI 추천 종목\n"
        "/status - 상태 확인\n"
        "/stop - 봇 정지\n\n"
        "예시: `/backtest AAPL advanced 1y`"
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ **System Status:**\n- Dashboard: Running\n- Tunnel: Active")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛑 **Stopping Bot...**\n(Not implemented in this demo)")

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """현재가 조회: /price TSLA"""
    if not context.args:
        await update.message.reply_text("⚠️ 종목 코드를 입력해주세요. (예: /price TSLA)")
        return
        
    ticker = context.args[0]
    try:
        data = yf.Ticker(ticker).history(period="1d")
        if data.empty:
            await update.message.reply_text("❌ 종목을 찾을 수 없습니다.")
            return
            
        price = data['Close'].iloc[-1]
        await update.message.reply_text(f"💰 *{ticker}* 현재가: *{price:,.2f}*")
    except Exception as e:
        await update.message.reply_text(f"❌ 에러: {e}")

async def recommend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """뉴스 감성 기반 추천 종목"""
    sentiment_path = "/Volumes/SSD/DEV_SSD/MY/neon_alpha/data/real_sentiment_factors.csv"
    
    if not os.path.exists(sentiment_path):
        await update.message.reply_text("⚠️ 분석된 뉴스 데이터가 없습니다.")
        return
        
    try:
        df = pd.read_csv(sentiment_path)
        # Get latest date
        latest_date = df['date'].max()
        latest = df[df['date'] == latest_date]
        
        # Sort by score
        top = latest.sort_values('sentiment_score', ascending=False).head(5)
        
        msg = f"📰 *오늘의 AI 추천 ({latest_date})*\n------------------\n"
        for _, row in top.iterrows():
            icon = "🔥" if row['sentiment_score'] > 0.2 else "😐"
            msg += f"{icon} *{row['symbol']}*: {row['sentiment_score']:.2f}\n"
            
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ 데이터 읽기 실패: {e}")

async def backtest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    ticker = "005930.KS"
    strategy = "advanced"
    period = "1y" # Default period
    
    if args:
        if len(args) >= 1: ticker = args[0]
        if len(args) >= 2: strategy = args[1]
        if len(args) >= 3: period = args[2]
    
    await update.message.reply_text(f"⏳ **백테스트 시작...**\n- 종목: {ticker}\n- 전략: {strategy}\n- 기간: {period}\n잠시만 기다려주세요!")
    
    try:
        # Fetch Data
        df = yf.download(ticker, period=period, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [c.lower() for c in df.columns]
        df.reset_index(inplace=True)
        df.rename(columns={'Date': 'date', 'index': 'date'}, inplace=True)
        
        if len(df) < 60:
            await update.message.reply_text(f"❌ 데이터가 부족합니다. (60일 미만)")
            return

        # Run Backtest
        config = {'stop_loss': 0.03, 'take_profit': 0.05}
        
        bt = Backtester(df, initial_cash=10000000, strategy_name=strategy)
        log, val = bt.run(config)
        
        # Format Report
        profit = val - 10000000
        profit_pct = (profit / 10000000) * 100
        emoji = "🚀" if profit > 0 else "📉"
        
        msg = f"""
*📊 백테스트 결과 ({ticker})*
전략: {strategy} ({period})
-------------------
{emoji} 수익률: *{profit_pct:.2f}%*
💰 최종금액: ₩{val:,.0f}
📜 거래횟수: {len(log)}회
"""
        await update.message.reply_text(msg, parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"❌ 오류 발생: {str(e)}")

def run_telegram_bot():
    """텔레그램 봇 리스너 실행 (별도 스레드)"""
    if not TOKEN:
        print("⚠️ No Telegram Token. Bot listener skipped.")
        return

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("backtest", backtest_command))
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("recommend", recommend_command))

    print("🤖 Telegram Bot Listening...")
    application.run_polling()

def start_bot_thread():
    t = threading.Thread(target=run_telegram_bot, daemon=True)
    t.start()

def set_bot_commands():
    if not TOKEN: return
    url = f"https://api.telegram.org/bot{TOKEN}/setMyCommands"
    commands = [
        {"command": "start", "description": "봇 시작"},
        {"command": "backtest", "description": "백테스트 (종목 전략 기간)"},
        {"command": "price", "description": "현재가 조회"},
        {"command": "recommend", "description": "AI 추천 종목"},
        {"command": "status", "description": "상태 확인"},
        {"command": "stop", "description": "긴급 정지"}
    ]
    try:
        requests.post(url, json={"commands": commands}, timeout=5)
    except: pass
