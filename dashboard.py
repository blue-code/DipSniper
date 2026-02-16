from flask import FastAPI, render_template_string
import pandas as pd
import threading

app = FastAPI()

# HTML Template (Simple Dashboard)
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>🔫 DipSniper Dashboard</title>
    <style>
        body { font-family: sans-serif; background: #1a1a1a; color: #eee; padding: 20px; }
        .card { background: #2d2d2d; padding: 20px; margin: 10px; border-radius: 10px; }
        h1 { color: #4ec9b0; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #444; }
        .buy { color: #4ec9b0; } .sell { color: #f44336; }
    </style>
</head>
<body>
    <h1>🔫 DipSniper Monitoring</h1>
    <div class="card">
        <h2>📊 Status</h2>
        <p>Running: ✅ Active</p>
        <p>Total Asset: ₩12,500,000</p>
        <p>Current Target: SAMSUNG ELEC (005930)</p>
    </div>
    <div class="card">
        <h2>📜 Trade Log</h2>
        <table>
            <tr><th>Time</th><th>Type</th><th>Price</th><th>Note</th></tr>
            <tr><td>2026-02-16 09:30</td><td class="buy">BUY</td><td>74,000</td><td>Dip detected</td></tr>
            <tr><td>2026-02-15 14:20</td><td class="sell">SELL</td><td>78,500</td><td>Profit +5.2%</td></tr>
        </table>
    </div>
</body>
</html>
"""

@app.get("/")
def home():
    return render_template_string(html_template)

if __name__ == "__main__":
    import uvicorn
    # Run server: uvicorn dashboard:app --reload
    print("🚀 Dashboard running at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
