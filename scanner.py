#!/usr/bin/env python
"""
NeonAlpha: Real-time Stock Screener (All Stocks Scan)
Scans all KOSPI/KOSDAQ stocks for DipSniper candidates.
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import requests

# 1. Get All Ticker List (Simplified)
# In production, use a library like 'finance-datareader' to get full KRX list
# For this demo, we use a static list of top 100 stocks
# You can expand this list dynamically
TICKERS = [
    "005930.KS", "000660.KS", "373220.KS", "207940.KS", "005380.KS", "000270.KS", 
    "068270.KS", "005490.KS", "035420.KS", "006400.KS", "051910.KS", "035720.KS",
    "105560.KS", "028260.KS", "012330.KS", "055550.KS", "003550.KS", "032830.KS",
    "086790.KS", "015760.KS", "018260.KS", "009150.KS", "003670.KS", "010130.KS",
    "034730.KS", "017670.KS", "096770.KS", "011200.KS", "051900.KS", "000810.KS",
    # Add more...
]

def scan_market():
    print("="*60)
    print(f"🔍 NeonAlpha: Scanning {len(TICKERS)} Stocks for Opportunities...")
    print("="*60)
    
    candidates = []
    
    # Batch download for speed (yfinance supports multi-ticker)
    data = yf.download(TICKERS, period="60d", progress=True, group_by='ticker')
    
    scored_candidates = []

    for ticker in TICKERS:
        try:
            df = data[ticker].copy()
            if df.empty or len(df) < 60: continue
            
            # Lowercase columns
            df.columns = [c.lower() for c in df.columns]
            
            # Indicators
            ma20 = df['close'].rolling(20).mean().iloc[-1]
            ma60 = df['close'].rolling(60).mean().iloc[-1]
            vol_ma5 = df['volume'].rolling(5).mean().iloc[-1]
            
            current_close = df['close'].iloc[-1]
            current_vol = df['volume'].iloc[-1]
            
            # Strategy: Advanced Dip
            # 1. Uptrend (20 > 60)
            if ma20 <= ma60: continue
            
            # 2. Dip (Price near MA20 ±3%)
            dist = abs(current_close - ma20) / ma20
            if dist > 0.03: continue
            
            # 3. Volume Dry-up (Vol < 70% of MA5)
            if current_vol >= (vol_ma5 * 0.7): continue
            
            # Calculate Dip Score (Higher is better)
            # - Volume Drop: More drop is better
            # - Trend Strength: Higher slope is better (approx by recent gain)
            # - Recent Gain: momentum
            
            recent_gain = (current_close - df['close'].iloc[-20]) / df['close'].iloc[-20]
            vol_ratio = current_vol / (vol_ma5 + 1)
            
            # Score formula: (Trend Gain * 50) + ((1 - Vol Ratio) * 30)
            score = (recent_gain * 50) + ((1 - vol_ratio) * 30)
            
            print(f"🎯 Candidate: {ticker} (Score: {score:.1f})")
            scored_candidates.append({'ticker': ticker, 'score': score})
            
        except Exception as e:
            continue
    
    # Sort by Score and pick Top 5
    scored_candidates.sort(key=lambda x: x['score'], reverse=True)
    top_5 = [c['ticker'] for c in scored_candidates[:5]]

    print("-" * 60)
    print(f"✅ Scan Complete. Top 5 Candidates: {top_5}")
    
    # Save to file for main.py to use
    if top_5:
        with open("/Volumes/SSD/DEV_SSD/MY/DipSniper/config/candidates.json", "w") as f:
            import json
            json.dump(top_5, f)
        print("💾 Saved top 5 candidates to config/candidates.json")
    else:
        print("❌ No suitable candidates found today.")

if __name__ == "__main__":
    scan_market()
