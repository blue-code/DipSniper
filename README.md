# 🔫 DipSniper (딥스나이퍼)

**AI 기반 눌림목(Pullback) 자동매매 & 백테스팅 시스템**  
한국투자증권(KIS) API를 활용하여 상승 추세 중 일시적인 하락(Dip)을 포착해 매수하고, 설정된 익절/손절 비율에 따라 자동으로 매도합니다.

---

## ✨ 주요 기능 (Key Features)

### 1. 🤖 자동 매매 (Auto Trading)
- **전략:** 20일 이동평균선 위의 상승 추세 종목 중, 최근 3일 하락 + 거래량 급감 시 매수.
- **실시간 감시:** 장중 실시간으로 시세를 조회하여 매수/매도 신호 포착.
- **주문 실행:** 한국투자증권 API를 통해 시장가 매수/매도 주문 전송.

### 2. 📉 백테스팅 (Backtesting)
- **시뮬레이션:** 과거 데이터(OHLCV)를 기반으로 전략의 수익률 검증.
- **파라미터 튜닝:** 초기 자금, 이평선 기간, 손절/익절 비율을 조절하며 최적의 설정값 탐색.

### 3. 🖥️ 웹 대시보드 (Web Dashboard)
- **설정 변경:** 코드를 수정하지 않고 웹 UI에서 전략 파라미터 변경 가능.
- **결과 시각화:** 백테스트 결과를 깔끔한 표와 컬러링(Buy/Sell)으로 확인.
- **상태 모니터링:** 현재 자산 현황 및 보유 종목 확인 (추후 연동).

---

## 🛠️ 설치 및 실행 (Installation)

### 1. 환경 설정
Python 3.10 이상이 필요합니다.

```bash
# 1. 저장소 클론
git clone https://github.com/blue-code/DipSniper.git
cd DipSniper

# 2. 패키지 설치
pip install -r requirements.txt
# (또는)
pip install requests pandas matplotlib fastapi uvicorn jinja2 python-dotenv
```

### 2. API 설정 (실전 매매용)
`config/settings.env` 파일을 열어 본인의 한국투자증권 계좌 정보를 입력하세요.

```ini
APP_KEY="나의_앱키"
APP_SECRET="나의_시크릿키"
CANO="계좌번호_앞8자리"
ACNT_PRDT_CD="01"
```

### 3. 실행 방법

#### 📊 웹 대시보드 (백테스트)
```bash
python3 dashboard.py
```
- 브라우저에서 `http://localhost:8000` 접속.
- 설정을 입력하고 **[🚀 Run Backtest]** 버튼 클릭!

#### 🤖 자동매매 봇 (실전/모의)
```bash
python3 main.py
```
- 터미널에서 실시간으로 종목을 분석하고 매매 로그를 출력합니다.

---

## 📂 프로젝트 구조
```
DipSniper/
├── config/             # 설정 파일
│   └── settings.env    # API 키 및 계좌 정보
├── core/               # 핵심 모듈
│   └── kis_api.py      # 한국투자증권 API 래퍼
├── backtest.py         # 백테스트 엔진
├── dashboard.py        # 웹 대시보드 (FastAPI)
├── main.py             # 실전 매매 봇 엔트리포인트
└── README.md           # 설명서
```

---

## 📝 라이선스
MIT License - **Created for 병호오빠 💕 by Tiffany**
