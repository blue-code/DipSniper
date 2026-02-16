# ... (Keep Imports)
import numpy as np

# ... (Keep Mock Data)

class StrategyInterface:
    def execute(self, df, config, i):
        """Returns: 'BUY', 'SELL', or None"""
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
        yesterday = df.iloc[i-1]
        
        # 1. 정배열 (20 > 60)
        is_aligned = today['ma20'] > today['ma60']
        
        # 2. 눌림목 위치 (20일선 근처 ±3%)
        dist = abs(today['close'] - today['ma20']) / today['ma20']
        is_near_ma20 = dist <= 0.03
        
        # 3. 거래량 감소 (평균 대비 70%)
        is_vol_dry = today['volume'] <= (today['vol_ma5'] * 0.7)
        
        # 4. 반등 시도 (양봉 & 전일보다 높음) - 캔들 데이터 부족 시 종가 비교로 대체
        # For mock data simplicity: Close > Open (if avail) AND Close > Yesterday Close
        # Here we assume close > yesterday close as 'rebound'
        is_rebound = today['close'] > yesterday['close']
        
        # 5. RSI (30~50) - Optional check if RSI calculated
        # is_rsi_ok = 30 <= today['rsi'] <= 50
        
        if is_aligned and is_near_ma20 and is_vol_dry and is_rebound:
            return 'BUY'
        return None

class Backtester:
    def __init__(self, df, initial_cash=10000000, strategy_name='basic'):
        self.df = df
        self.cash = initial_cash
        self.shares = 0
        self.history = []
        
        # Select Strategy
        if strategy_name == 'advanced':
            self.strategy = AdvancedDipStrategy()
        else:
            self.strategy = BasicDipStrategy()
        
    def run(self, config):
        # Calculate Indicators Common to All
        self.df['ma20'] = self.df['close'].rolling(window=20).mean()
        self.df['ma60'] = self.df['close'].rolling(window=60).mean()
        self.df['vol_ma5'] = self.df['volume'].rolling(window=5).mean()
        
        # RSI Calculation (Simple)
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        self.df['rsi'] = 100 - (100 / (1 + rs))
        
        for i in range(60, len(self.df)):
            today = self.df.iloc[i]
            
            # Sell Logic (Common)
            if self.shares > 0:
                buy_price = self.history[-1]['price']
                pct = (today['close'] - buy_price) / buy_price
                
                # Dynamic Config
                if pct > config['take_profit'] or pct < -config['stop_loss']:
                    self.cash += self.shares * today['close']
                    self.shares = 0
                    self.history.append({'date': today['date'], 'type': 'SELL', 'price': today['close'], 'profit': pct*100})
                    continue

            # Buy Logic (Strategy Specific)
            if self.shares == 0:
                signal = self.strategy.execute(self.df, config, i)
                if signal == 'BUY':
                    self.shares = self.cash // today['close']
                    self.cash -= self.shares * today['close']
                    self.history.append({'date': today['date'], 'type': 'BUY', 'price': today['close']})

        # Final Value
        if self.shares > 0:
            total_value = self.cash + (self.shares * self.df.iloc[-1]['close'])
        else:
            total_value = self.cash
            
        return self.history, total_value

if __name__ == "__main__":
    # Test
    df = pd.DataFrame(data)
    bt = Backtester(df, strategy_name='advanced')
    log, val = bt.run({'stop_loss':0.03, 'take_profit':0.1})
    print(log)
