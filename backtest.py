import pandas as pd
import numpy as np

# Mock Data for Backtest (Enhanced with OHLC for pattern recognition)
dates = pd.date_range(start='2024-01-01', periods=100)
close = []
open_p = []
high = []
low = []
volume = []

for i in range(100):
    base_price = 100 + i * 2
    if 30 <= i <= 32: # Dip
        base_price -= 10
        vol = 200
        # Hammer Pattern at the bottom (i=32)
        if i == 32:
            o, c, h, l = base_price, base_price + 2, base_price + 2, base_price - 5
        else:
            o, c, h, l = base_price + 2, base_price, base_price + 2, base_price - 2
    else:
        vol = 1000
        o, c, h, l = base_price - 1, base_price + 1, base_price + 2, base_price - 2
        
    close.append(c)
    open_p.append(o)
    high.append(h)
    low.append(l)
    volume.append(vol)

data = {
    'date': dates,
    'open': open_p,
    'high': high,
    'low': low,
    'close': close,
    'volume': volume
}

# TA-Lib Import Check
try:
    import talib
except ImportError:
    talib = None

class StrategyInterface:
    def execute(self, df, config, i):
        raise NotImplementedError

class BasicDipStrategy(StrategyInterface):
    def execute(self, df, config, i):
        today = df.iloc[i]
        yesterday = df.iloc[i-1]
        
        is_uptrend = today['close'] > today['ma20']
        is_dip = today['close'] < yesterday['close']
        vol_drop = today['volume'] < (yesterday['volume'] * 0.7)
        
        if is_uptrend and is_dip and vol_drop:
            return 'BUY'
        return None

class AdvancedDipStrategy(StrategyInterface):
    def execute(self, df, config, i):
        today = df.iloc[i]
        
        # 1. 정배열 (20 > 60)
        if pd.isna(today['ma60']): return None
        is_aligned = today['ma20'] > today['ma60']
        
        # 2. 눌림목 위치 (20일선 근처 ±5%)
        dist = abs(today['close'] - today['ma20']) / today['ma20']
        is_near_ma20 = dist <= 0.05
        
        # 3. 거래량 감소
        is_vol_dry = today['volume'] <= (today['vol_ma5'] * 0.7)
        
        # 4. 캔들 패턴 (TA-Lib 사용)
        is_pattern_bullish = False
        if talib:
            # TA-Lib functions expect numpy arrays of type float
            opens = df['open'].values.astype(float)
            highs = df['high'].values.astype(float)
            lows = df['low'].values.astype(float)
            closes = df['close'].values.astype(float)
            
            # Detect Patterns: Hammer, Inverted Hammer, Engulfing
            hammer = talib.CDLHAMMER(opens, highs, lows, closes)
            inverted = talib.CDLINVERTEDHAMMER(opens, highs, lows, closes)
            engulfing = talib.CDLENGULFING(opens, highs, lows, closes)
            
            # Check if any bullish pattern triggered today
            if hammer[i] > 0 or inverted[i] > 0 or engulfing[i] > 0:
                is_pattern_bullish = True
        else:
            # Fallback: Simple Rebound Logic (Close > Open AND Close > Prev Close)
            is_pattern_bullish = (today['close'] > today['open']) and (today['close'] > df.iloc[i-1]['close'])
        
        if is_aligned and is_near_ma20 and is_vol_dry and is_pattern_bullish:
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
        self.df['ma20'] = self.df['close'].rolling(window=20).mean()
        self.df['ma60'] = self.df['close'].rolling(window=60).mean()
        self.df['vol_ma5'] = self.df['volume'].rolling(window=5).mean()
        
        # RSI
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        self.df['rsi'] = 100 - (100 / (1 + rs))
        
        for i in range(60, len(self.df)):
            today = self.df.iloc[i]
            
            # Sell Logic
            if self.shares > 0:
                buy_price = self.history[-1]['price']
                pct = (today['close'] - buy_price) / buy_price
                
                if pct > config['take_profit'] or pct < -config['stop_loss']:
                    self.cash += self.shares * today['close']
                    self.shares = 0
                    self.history.append({'date': today['date'], 'type': 'SELL', 'price': today['close'], 'profit': pct*100})
                    continue

            # Buy Logic
            if self.shares == 0:
                signal = self.strategy.execute(self.df, config, i)
                if signal == 'BUY':
                    self.shares = self.cash // today['close']
                    self.cash -= self.shares * today['close']
                    self.history.append({'date': today['date'], 'type': 'BUY', 'price': today['close']})

        if self.shares > 0:
            total_value = self.cash + (self.shares * self.df.iloc[-1]['close'])
        else:
            total_value = self.cash
            
        return self.history, total_value

if __name__ == "__main__":
    df = pd.DataFrame(data)
    
    if not talib:
        print("⚠️ TA-Lib not installed. Using fallback logic.")
        print("   To install: brew install ta-lib && pip install ta-lib")

    print("\n----- [Advanced Strategy Test] -----")
    bt = Backtester(df.copy(), strategy_name='advanced')
    log, val = bt.run({'stop_loss':0.03, 'take_profit':0.05})
    print(f"💰 Final Value: {val:,.0f}")
    for t in log: print(f"  {t['date'].date()} {t['type']} @ {t['price']}")
