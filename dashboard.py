from flask import FastAPI, render_template_string, Request, Form
from fastapi.responses import HTMLResponse
import pandas as pd
import subprocess
import signal
import os
import json
from backtest import Backtester

app = FastAPI()

# Global Config
config = {
    "initial_cash": 10000000,
    "ma_period": 20,
    "stop_loss": 0.03,
    "take_profit": 0.05,
    "strategy": "basic"
}

last_result = []
main_process = None

# Mock Data for Backtest
data = {
    'date': pd.date_range(start='2024-01-01', periods=100),
    'close': [100 + i + (i%5)*(-2) for i in range(100)],
    'volume': [1000 if i%5!=0 else 200 for i in range(100)]
}

html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>🔫 DipSniper Dashboard</title>
    <style>
        body { font-family: sans-serif; background: #1a1a1a; color: #eee; padding: 20px; max-width: 800px; margin: auto; }
        .card { background: #2d2d2d; padding: 20px; margin-bottom: 20px; border-radius: 10px; }
        h1 { color: #4ec9b0; border-bottom: 1px solid #444; padding-bottom: 10px; }
        h2 { color: #dcb67a; margin-top: 0; }
        input, select { background: #333; border: 1px solid #555; color: #fff; padding: 5px; width: 100px; }
        button { background: #0e639c; color: #fff; border: none; padding: 8px 15px; cursor: pointer; border-radius: 4px; font-weight: bold; }
        button:hover { background: #1177bb; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #444; }
        .buy { color: #4ec9b0; font-weight: bold; } .sell { color: #f44336; font-weight: bold; }
        .form-group { margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        
        .status-box { padding: 15px; border-radius: 5px; margin-bottom: 20px; color: #fff; font-weight: bold; text-align: center; }
        .status-running { background: #2e7d32; border: 1px solid #4caf50; }
        .status-stopped { background: #c62828; border: 1px solid #ef5350; }
        .log-box { background: #000; color: #0f0; padding: 10px; font-family: monospace; height: 200px; overflow-y: scroll; border: 1px solid #333; margin-top: 10px; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>🔫 DipSniper Control Center</h1>

    <!-- Live Bot Control -->
    <div class="card">
        <h2>🤖 Live Trading Bot</h2>
        {% if is_running %}
        <div class="status-box status-running">🟢 Bot is RUNNING with current strategy</div>
        <form action="/stop_bot" method="post" style="text-align: center;">
            <button type="submit" style="background: #d32f2f;">⏹ Stop Bot</button>
        </form>
        {% else %}
        <div class="status-box status-stopped">🔴 Bot is STOPPED</div>
        <form action="/start_bot" method="post" style="text-align: center;">
            <button type="submit" style="background: #388e3c;">▶️ Start Live Bot</button>
        </form>
        {% endif %}
        
        <div class="log-box" id="log-viewer">
            Waiting for logs...
        </div>
    </div>

    <!-- Configuration -->
    <div class="card">
        <h2>⚙️ Strategy Settings</h2>
        <form action="/run_backtest" method="post">
            <div class="form-group">
                <label>Strategy Type</label>
                <select name="strategy">
                    <option value="basic" {% if config.strategy == 'basic' %}selected{% endif %}>Basic (Simple Dip)</option>
                    <option value="advanced" {% if config.strategy == 'advanced' %}selected{% endif %}>Advanced (MA20 + RSI)</option>
                </select>
            </div>
            <div class="form-group">
                <label>Initial Cash (₩)</label>
                <input type="number" name="initial_cash" value="{{ config.initial_cash }}">
            </div>
            <div class="form-group">
                <label>Stop Loss (%)</label>
                <input type="number" step="0.01" name="stop_loss" value="{{ config.stop_loss }}">
            </div>
            <div class="form-group">
                <label>Take Profit (%)</label>
                <input type="number" step="0.01" name="take_profit" value="{{ config.take_profit }}">
            </div>
            <div style="text-align: right;">
                <button type="submit">🚀 Run Backtest & Apply</button>
            </div>
        </form>
    </div>

    <!-- Results -->
    <div class="card">
        <h2>📊 Backtest Results</h2>
        {% if result %}
        <p><strong>Total Trades:</strong> {{ result|length }}</p>
        <table>
            <tr><th>Date</th><th>Type</th><th>Price</th><th>Note</th></tr>
            {% for trade in result %}
            <tr>
                <td>{{ trade.date.strftime('%Y-%m-%d') }}</td>
                <td class="{{ 'buy' if trade.type == 'BUY' else 'sell' }}">{{ trade.type }}</td>
                <td>{{ trade.price }}</td>
                <td>{{ 'Profit: ' + trade.profit|round(2)|string + '%' if trade.profit else '' }}</td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p style="color: #888;">No backtest run yet.</p>
        {% endif %}
    </div>

    <script>
        setInterval(async () => {
            const res = await fetch('/logs');
            const text = await res.text();
            const viewer = document.getElementById('log-viewer');
            if (text && text !== viewer.innerText) {
                viewer.innerText = text;
                viewer.scrollTop = viewer.scrollHeight;
            }
        }, 2000);
    </script>
</body>
</html>
"""

try:
    from jinja2 import Template
except ImportError:
    print("Please install jinja2: pip install jinja2")

@app.get("/", response_class=HTMLResponse)
def home():
    t = Template(html_template)
    is_running = main_process is not None and main_process.poll() is None
    return t.render(config=config, result=last_result, is_running=is_running)

@app.post("/run_backtest", response_class=HTMLResponse)
async def run_backtest(
    initial_cash: int = Form(...),
    stop_loss: float = Form(...),
    take_profit: float = Form(...),
    strategy: str = Form(...)
):
    global config, last_result
    
    config.update({
        "initial_cash": initial_cash,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "strategy": strategy
    })
    
    # Save Config for Live Bot
    os.makedirs("config", exist_ok=True)
    with open("config/live_strategy.json", "w") as f:
        json.dump(config, f)
    
    # Run Backtest
    df = pd.DataFrame(data)
    bt = Backtester(df, initial_cash, strategy_name=strategy) 
    last_result, _ = bt.run(config)
    
    t = Template(html_template)
    is_running = main_process is not None and main_process.poll() is None
    return t.render(config=config, result=last_result, is_running=is_running)

@app.post("/start_bot", response_class=HTMLResponse)
async def start_bot():
    global main_process
    if main_process is None or main_process.poll() is not None:
        os.makedirs("logs", exist_ok=True)
        main_process = subprocess.Popen(
            ["python3", "-u", "main.py"], 
            stdout=open("logs/bot.log", "w"), 
            stderr=subprocess.STDOUT
        )
    return home()

@app.post("/stop_bot", response_class=HTMLResponse)
async def stop_bot():
    global main_process
    if main_process:
        main_process.terminate()
        try:
            main_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            main_process.kill()
        main_process = None
    return home()

@app.get("/logs")
def get_logs():
    log_path = "logs/bot.log"
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            lines = f.readlines()
            return "".join(lines[-20:]) # Last 20 lines
    return "Waiting for logs..."

if __name__ == "__main__":
    import uvicorn
    print("🚀 Dashboard running at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
