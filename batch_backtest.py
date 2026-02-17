import pandas as pd
import yfinance as yf
from backtest import Backtester
import time
import sys

# 1. KOSPI Top 20 (Blue Chip)
KOSPI_TOP = [
    "005930.KS", "000660.KS", "373220.KS", "207940.KS", "005380.KS", 
    "000270.KS", "068270.KS", "005490.KS", "035420.KS", "006400.KS", 
    "051910.KS", "035720.KS", "105560.KS", "028260.KS", "012330.KS", 
    "055550.KS", "003550.KS", "032830.KS", "086790.KS", "015760.KS"
]

# 2. US Tech Top 20 (Global Leader)
US_TECH_TOP = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", 
    "META", "TSLA", "AVGO", "TSM", "LLY",
    "JPM", "V", "UNH", "WMT", "MA",
    "XOM", "JNJ", "PG", "HD", "COST"
]

# 3. KOSDAQ Volatility (High Risk High Return)
KOSDAQ_VOL = [
    "247540.KQ", # Ecopro BM
    "086520.KQ", # Ecopro
    "196170.KQ", # Alteogen
    "028300.KQ", # HLB
    "403870.KQ", # HPSP
    "278280.KQ", # Chunbo
    "035900.KQ", # JYP Ent
    "293490.KQ", # Kakao Games
    "091990.KQ", # Celltrion Pharm
    "066970.KQ", # L&F
]

# 4. US Leverage ETF (Beast Mode)
US_LEVERAGE = [
    "TQQQ", "SQQQ", # Nasdaq 3x
    "SOXL", "SOXS", # Semi 3x
    "TSLL", "TSLS", # Tesla 2x
    "NVDL",         # Nvidia 2x
    "FNGU", "FNGD", # FAANG 3x
    "LABU", "LABD", # Bio 3x
]

# 5. Crypto (24/7 Market)
CRYPTO = [
    "BTC-USD", "ETH-USD", "XRP-USD", "SOL-USD", "DOGE-USD",
    "ADA-USD", "AVAX-USD", "SHIB-USD", "DOT-USD", "TRX-USD"
]

SCENARIOS = {
    "1": ("🇰🇷 KOSPI Top 20", KOSPI_TOP),
    "2": ("🇺🇸 US Tech Top 20", US_TECH_TOP),
    "3": ("🎢 KOSDAQ Volatility", KOSDAQ_VOL),
    "4": ("🦁 US Leverage ETF", US_LEVERAGE),
    "5": ("🪙 Crypto Currency", CRYPTO)
}

def run_batch_backtest():
    print("="*60)
    print("🚀 DipSniper Batch Backtest System")
    print("="*60)
    print("Select a Scenario:")
    for k, v in SCENARIOS.items():
        print(f" [{k}] {v[0]}")
    print("="*60)
    
    choice = input("Enter number (default 1): ").strip() or "1"
    
    if choice not in SCENARIOS:
        print("❌ Invalid choice.")
        return

    name, tickers = SCENARIOS[choice]
    print(f"\n🚀 Starting Backtest: {name} (5 Years)\n")
    
    results = []
    
    # Common Config
    config = {'stop_loss': 0.03, 'take_profit': 0.05}
    initial_cash = 10000000
    
    for ticker in tickers:
        print(f"🔄 Processing {ticker}...", end=" ")
        try:
            # Fetch Data (5y)
            df = yf.download(ticker, period="5y", progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.columns = [c.lower() for c in df.columns]
            df.reset_index(inplace=True)
            df.rename(columns={'Date': 'date', 'index': 'date'}, inplace=True)
            
            if len(df) < 200:
                print("⚠️ Not enough data")
                continue
                
            # Run Basic
            bt_basic = Backtester(df.copy(), initial_cash, 'basic')
            _, val_basic = bt_basic.run(config)
            ret_basic = (val_basic - initial_cash) / initial_cash * 100
            
            # Run Advanced
            bt_adv = Backtester(df.copy(), initial_cash, 'advanced')
            _, val_adv = bt_adv.run(config)
            ret_adv = (val_adv - initial_cash) / initial_cash * 100
            
            print(f"Basic: {ret_basic:>6.1f}% | Adv: {ret_adv:>6.1f}%")
            
            results.append({
                'Ticker': ticker,
                'Basic': ret_basic,
                'Advanced': ret_adv
            })
            
        except Exception as e:
            print(f"❌ Error: {e}")
            
    # Summary
    print("-" * 60)
    res_df = pd.DataFrame(results)
    print(res_df)
    
    if not res_df.empty:
        avg_basic = res_df['Basic'].mean()
        avg_adv = res_df['Advanced'].mean()
        
        print("-" * 60)
        print(f"🏆 Average Return (Basic):    {avg_basic:.2f}%")
        print(f"🏆 Average Return (Advanced): {avg_adv:.2f}%")
        
        winner = "Advanced" if avg_adv > avg_basic else "Basic"
        print(f"🎉 Winner Strategy: {winner}")

if __name__ == "__main__":
    run_batch_backtest()
