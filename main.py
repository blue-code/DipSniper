import pandas as pd
from core.kis_api import KISApi

class PullbackStrategy:
    def __init__(self):
        self.api = KISApi()
        
    def analyze(self, code):
        """
        눌림목 조건 분석
        1. 20일 이평선 위에 있는가? (상승 추세)
        2. 최근 3일 이내 하락했는가? (눌림목)
        3. 거래량이 급감했는가? (매도세 진정)
        """
        daily_data = self.api.get_daily_chart(code)
        if not daily_data:
            return False, "데이터 부족"

        df = pd.DataFrame(daily_data[:30]) # 최근 30일
        df['stck_clpr'] = df['stck_clpr'].astype(int) # 종가
        df['acml_vol'] = df['acml_vol'].astype(int)   # 거래량
        
        # 20일 이동평균선
        ma20 = df['stck_clpr'].rolling(window=20).mean().iloc[0]
        current_price = df['stck_clpr'].iloc[0]
        
        # 1. 상승 추세 확인
        if current_price < ma20:
            return False, f"하락 추세 (현:{current_price} < 20이평:{ma20})"
            
        # 2. 눌림목 확인 (오늘/어제 하락)
        price_change = current_price - df['stck_clpr'].iloc[1]
        if price_change > 0:
            return False, "상승 중 (눌림목 아님)"
            
        # 3. 거래량 급감 확인 (전일 대비 70% 이하)
        vol_today = df['acml_vol'].iloc[0]
        vol_yesterday = df['acml_vol'].iloc[1]
        
        if vol_today > (vol_yesterday * 0.7):
            return False, "거래량 많음 (매도세 지속)"
            
        return True, "✅ 눌림목 매수 신호!"

    def run(self, target_codes):
        print("🚀 눌림목 자동매매 시작...")
        for code in target_codes:
            is_buy, msg = self.analyze(code)
            print(f"[{code}] {msg}")
            
            if is_buy:
                print(f"💰 {code} 매수 주문 실행!")
                # self.api.buy_order(code, 10) # 10주 매수 (테스트)
