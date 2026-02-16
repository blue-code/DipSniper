import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

# Strategy Interface
class StrategyInterface:
    def execute(self, df, config, i):
        raise NotImplementedError

class BasicDipStrategy(StrategyInterface):
    def execute(self, df, config, i):
        today = df.iloc[i]
        yesterday = df.iloc[i-1]
        
        # 1. 상승 추세 (20일선 위)
        if pd.isna(today['ma20']): return None
        is_uptrend = today['close'] > today['ma20']
        
        # 2. 눌림목 (전일 하락)
        is_dip = today['close'] < yesterday['close']
        
        # 3. 거래량 감소
        if pd.isna(today['vol_ma5']): return None
        vol_drop = today['volume'] < (today['vol_ma5'] * 0.8) # 80% 이하
        
        if is_uptrend and is_dip and vol_drop:
            return 'BUY'
        return None

class AdvancedDipStrategy(StrategyInterface):
    def execute(self, df, config, i):
        today = df.iloc[i]
        yesterday = df.iloc[i-1]
        
        # 1. 정배열 (20 > 60)
        if pd.isna(today['ma60']): return None
        is_aligned = today['ma20'] > today['ma60']
        
        # 2. 눌림목 위치 (20일선 근처 ±5%)
        dist = abs(today['close'] - today['ma20']) / today['ma20']
        is_near_ma20 = dist <= 0.05
        
        # 3. 거래량 감소
        is_vol_dry = today['volume'] <= (today['vol_ma5'] * 0.7)
        
        # 4. 반등 시도 (양봉 or 전일보다 높음)
        is_rebound = (today['close'] > today['open']) or (today['close'] > yesterday['close'])
        
        # 5. RSI (30~55)
        is_rsi_good = False
        if not pd.isna(today['rsi']):
            is_rsi_good = 30 <= today['rsi'] <= 60 # Range relaxed
        
        if is_aligned and is_near_ma20 and is_vol_dry and is_rebound and is_rsi_good:
            return 'BUY'
        return None

class Backtester:
    def __init__(self, df, initial_cash=10000000, strategy_name='basic'):
        self.df = df
        self.cash = initial_cash
        self.shares = 0
        self.history = []
        
        if strategy_name == 'advanced':
            self.strategy = AdvancedDipStrategy()
        else:
            self.strategy = BasicDipStrategy()
        
    def run(self, config):
        # Calculate Indicators
        self.df['ma20'] = self.df['close'].rolling(window=20).mean()
        self.df['ma60'] = self.df['close'].rolling(window=60).mean()
        self.df['vol_ma5'] = self.df['volume'].rolling(window=5).mean()
        
        # RSI
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        self.df['rsi'] = 100 - (100 / (1 + rs))
        
        # Ensure we have enough data
        if len(self.df) < 60: return [], self.cash

        for i in range(60, len(self.df)):
            today = self.df.iloc[i]
            
            # Use 'Date' column if exists, otherwise use Index
            date_val = today.get('date') or today.name 
            
            # Sell Logic
            if self.shares > 0:
                buy_price = self.history[-1]['price']
                pct = (today['close'] - buy_price) / buy_price
                
                if pct > config['take_profit'] or pct < -config['stop_loss']:
                    self.cash += self.shares * today['close']
                    self.shares = 0
                    self.history.append({'date': date_val, 'type': 'SELL', 'price': today['close'], 'profit': pct*100})
                    continue

            # Buy Logic
            if self.shares == 0:
                signal = self.strategy.execute(self.df, config, i)
                if signal == 'BUY':
                    self.shares = self.cash // today['close']
                    self.cash -= self.shares * today['close']
                    self.history.append({'date': date_val, 'type': 'BUY', 'price': today['close']})

        # Final Value
        if self.shares > 0:
            total_value = self.cash + (self.shares * self.df.iloc[-1]['close'])
        else:
            total_value = self.cash
            
        return self.history, total_value

if __name__ == "__main__":
    from core.telegram_bot import send_report
    
    print("🔄 Fetching Data (Samsung Elec - 005930.KS)...")
    df = yf.download("005930.KS", period="1y")
    
    # Flatten MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df.columns = [c.lower() for c in df.columns]
    df.reset_index(inplace=True)
    df.rename(columns={'Date': 'date', 'index': 'date'}, inplace=True)
    
    print(f"✅ Data Loaded: {len(df)} rows")

    print("\n----- [Advanced Strategy Test] -----")
    bt = Backtester(df.copy(), strategy_name='advanced')
    initial = 10000000
    log, val = bt.run({'stop_loss':0.03, 'take_profit':0.05})
    
    print(f"💰 Final Value: {val:,.0f}")
    print(f"📜 Trade Log: {len(log)} trades")
    for t in log:
        d_str = t['date'].strftime('%Y-%m-%d') if hasattr(t['date'], 'strftime') else str(t['date'])
        print(f"  {d_str} {t['type']} @ {t['price']:.0f}")
        
    send_report(log, val, initial)
    print("🔔 Telegram report sent!")
