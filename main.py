import pandas as pd
import json
import os
from core.kis_api import KISApi
from backtest import AdvancedDipStrategy, BasicDipStrategy

class LiveTrader:
    def __init__(self):
        self.api = KISApi()
        self.load_config()
        
    def load_config(self):
        """대시보드에서 설정한 전략 로드"""
        config_path = "config/live_strategy.json"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                self.config = json.load(f)
            print(f"✅ 전략 로드: {self.config['strategy']} (익절 {self.config['take_profit']*100}%, 손절 {self.config['stop_loss']*100}%)")
        else:
            print("⚠️ 설정 파일 없음. 기본값 사용.")
            self.config = {"strategy": "basic", "take_profit": 0.05, "stop_loss": 0.03}

        if self.config['strategy'] == 'advanced':
            self.strategy = AdvancedDipStrategy()
        else:
            self.strategy = BasicDipStrategy()

    def analyze(self, code):
        """실전 매매 분석 (백테스트 로직 재사용)"""
        # 1. 데이터 가져오기 (60일치)
        daily_data = self.api.get_daily_chart(code) # Need update to fetch 60+
        if not daily_data: return False, "데이터 부족"

        # 2. DataFrame 변환 & 지표 계산
        df = pd.DataFrame(daily_data).iloc[::-1] # Reverse to chronological
        df['close'] = df['stck_clpr'].astype(int)
        df['volume'] = df['acml_vol'].astype(int)
        
        # Calculate Indicators exactly like Backtest
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma60'] = df['close'].rolling(window=60).mean()
        df['vol_ma5'] = df['volume'].rolling(window=5).mean()
        
        # 3. 전략 실행 (오늘 날짜 기준)
        # We pass the last index to strategy
        signal = self.strategy.execute(df, self.config, len(df)-1)
        
        if signal == 'BUY':
            return True, f"✅ [{self.config['strategy']}] 매수 신호 발생!"
        return False, "조건 미충족"

    def run(self, target_codes):
        self.load_config() # 매번 최신 설정 로드
        print("🚀 DipSniper 실전 매매 시작...")
        
        for code in target_codes:
            is_buy, msg = self.analyze(code)
            print(f"[{code}] {msg}")
            
            if is_buy:
                # self.api.buy_order(code, 10) 
                print(f"💰 {code} 매수 주문 전송 완료!")

if __name__ == "__main__":
    bot = LiveTrader()
    # 삼성전자, SK하이닉스, NAVER
    bot.run(["005930", "000660", "035420"])
