import pandas as pd
import matplotlib.pyplot as plt
import os

# Mock Data for Backtest (Replace with real OHLCV csv)
# Date, Open, High, Low, Close, Volume
data = {
    'date': pd.date_range(start='2024-01-01', periods=100),
    'close': [100 + i + (i%5)*(-2) for i in range(100)], # Uptrnd with dips
    'volume': [1000 if i%5!=0 else 200 for i in range(100)] # Vol drops on dips
}

class Backtester:
    def __init__(self, df, initial_cash=10000000):
        self.df = df
        self.cash = initial_cash
        self.shares = 0
        self.history = []
        
    def run(self):
        # Calculate Indicators
        self.df['ma20'] = self.df['close'].rolling(window=20).mean()
        
        for i in range(20, len(self.df)):
            today = self.df.iloc[i]
            yesterday = self.df.iloc[i-1]
            
            # Strategy Logic (DipSniper)
            is_uptrend = today['close'] > today['ma20']
            is_dip = today['close'] < yesterday['close']
            vol_drop = today['volume'] < (yesterday['volume'] * 0.7)
            
            # Buy Signal
            if self.shares == 0 and is_uptrend and is_dip and vol_drop:
                self.shares = self.cash // today['close']
                self.cash -= self.shares * today['close']
                self.history.append({'date': today['date'], 'type': 'BUY', 'price': today['close']})
                
            # Sell Signal (Profit 5% or StopLoss 3%)
            elif self.shares > 0:
                buy_price = self.history[-1]['price']
                pct = (today['close'] - buy_price) / buy_price
                
                if pct > 0.05 or pct < -0.03:
                    self.cash += self.shares * today['close']
                    self.shares = 0
                    self.history.append({'date': today['date'], 'type': 'SELL', 'price': today['close'], 'profit': pct*100})

        # Final Value
        total_value = self.cash + (self.shares * self.df.iloc[-1]['close'])
        print(f"💰 Initial: 10,000,000 -> Final: {total_value:,.0f}")
        return self.history

if __name__ == "__main__":
    df = pd.DataFrame(data)
    bt = Backtester(df)
    log = bt.run()
    print(log)
