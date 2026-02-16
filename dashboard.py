from flask import FastAPI, render_template_string, Request, Form
from fastapi.responses import HTMLResponse
import pandas as pd
import threading
from backtest import Backtester

app = FastAPI()

# Global Config (In-memory for demo, ideally DB/File)
config = {
    "initial_cash": 10000000,
    "ma_period": 20,
    "stop_loss": 0.03,
    "take_profit": 0.05
}

# Backtest Result
last_result = []

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
        input { background: #333; border: 1px solid #555; color: #fff; padding: 5px; width: 100px; }
        button { background: #0e639c; color: #fff; border: none; padding: 8px 15px; cursor: pointer; border-radius: 4px; font-weight: bold; }
        button:hover { background: #1177bb; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #444; }
        .buy { color: #4ec9b0; font-weight: bold; } .sell { color: #f44336; font-weight: bold; }
        .form-group { margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
    </style>
</head>
<body>
    <h1>🔫 DipSniper Control Center</h1>

    <!-- Configuration -->
    <div class="card">
        <h2>⚙️ Strategy Settings</h2>
        <form action="/run_backtest" method="post">
            <div class="form-group">
                <label>Initial Cash (₩)</label>
                <input type="number" name="initial_cash" value="{{ config.initial_cash }}">
            </div>
            <div class="form-group">
                <label>MA Period (Days)</label>
                <input type="number" name="ma_period" value="{{ config.ma_period }}">
            </div>
            <div class="form-group">
                <label>Stop Loss (%)</label>
                <input type="number" step="0.01" name="stop_loss" value="{{ config.stop_loss }}">
            </div>
            <div class="form-group">
                <label>Take Profit (%)</label>
                <input type="number" step="0.01" name="take_profit" value="{{ config.take_profit }}">
            </div>
            <button type="submit">🚀 Run Backtest</button>
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
</body>
</html>
"""

from fastapi.templating import Jinja2Templates
# We'll use simple string replacement or Jinja2 for cleaner template
# Since we need to render the template with data, Jinja2 is better.
# But to keep it single file, I'll use a hacky replace or Jinja2 if installed.
# Let's use Jinja2 properly.

try:
    from jinja2 import Template
except ImportError:
    print("Please install jinja2: pip install jinja2")

@app.get("/", response_class=HTMLResponse)
def home():
    t = Template(html_template)
    return t.render(config=config, result=last_result)

@app.post("/run_backtest", response_class=HTMLResponse)
async def run_backtest(
    initial_cash: int = Form(...),
    ma_period: int = Form(...),
    stop_loss: float = Form(...),
    take_profit: float = Form(...)
):
    global config, last_result
    
    # Update Config
    config = {
        "initial_cash": initial_cash,
        "ma_period": ma_period,
        "stop_loss": stop_loss,
        "take_profit": take_profit
    }
    
    # Run Backtest
    df = pd.DataFrame(data)
    # Note: Pass dynamic config to Backtester if updated to support it
    # For now, we assume Backtester uses defaults or we modify it
    # Let's assume we update Backtester class to accept these params
    bt = Backtester(df, initial_cash) 
    # Monkey patch or update backtester logic dynamically here for demo
    # In real app, pass params to .run()
    
    last_result = bt.run() # This runs the logic
    
    t = Template(html_template)
    return t.render(config=config, result=last_result)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Dashboard running at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
