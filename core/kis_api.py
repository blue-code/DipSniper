import requests
import json
import os
import time
from dotenv import load_dotenv

# Load Config
load_dotenv("/Volumes/SSD/DEV_SSD/MY/KIS_AutoTrade/config/settings.env")

APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")
URL_BASE = os.getenv("URL_BASE")
CANO = os.getenv("CANO")
ACNT_PRDT_CD = os.getenv("ACNT_PRDT_CD")

class KISApi:
    def __init__(self):
        self.access_token = None
        self.token_expiry = 0
        self.headers = {"content-type": "application/json"}
        self._get_access_token()

    def _get_access_token(self):
        """토큰 발급 및 갱신"""
        if time.time() < self.token_expiry:
            return

        path = "oauth2/tokenP"
        url = f"{URL_BASE}/{path}"
        body = {
            "grant_type": "client_credentials",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET
        }
        
        try:
            res = requests.post(url, headers=self.headers, data=json.dumps(body))
            data = res.json()
            if "access_token" in data:
                self.access_token = data["access_token"]
                self.token_expiry = time.time() + 86000 # 24시간
                self.headers["authorization"] = f"Bearer {self.access_token}"
                self.headers["appkey"] = APP_KEY
                self.headers["appsecret"] = APP_SECRET
                print("✅ Access Token Issued")
            else:
                print(f"❌ Token Error: {data}")
        except Exception as e:
            print(f"❌ Connection Error: {e}")

    def get_current_price(self, code):
        """현재가 조회"""
        path = "uapi/domestic-stock/v1/quotations/inquire-price"
        url = f"{URL_BASE}/{path}"
        headers = self.headers.copy()
        headers["tr_id"] = "FHKST01010100"
        
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": code
        }
        
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            data = res.json().get('output', {})
            return {
                "price": int(data.get("stck_prpr", 0)),
                "name": data.get("rprs_mrkt_kor_name", ""),
                "volume": int(data.get("acml_vol", 0))
            }
        return None

    def get_daily_chart(self, code, period="D"):
        """일봉 데이터 조회 (이평선 계산용)"""
        path = "uapi/domestic-stock/v1/quotations/inquire-daily-price"
        url = f"{URL_BASE}/{path}"
        headers = self.headers.copy()
        headers["tr_id"] = "FHKST01010400"
        
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": code,
            "fid_period_div_code": period,
            "fid_org_adj_prc": "1" # 수정주가
        }
        
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            return res.json().get('output', [])
        return []

    def buy_order(self, code, qty):
        """시장가 매수"""
        path = "uapi/domestic-stock/v1/trading/order-cash"
        url = f"{URL_BASE}/{path}"
        headers = self.headers.copy()
        headers["tr_id"] = "VTTC0802U" # 모의투자 매수 (실전: TTTC0802U)
        
        data = {
            "CANO": CANO,
            "ACNT_PRDT_CD": ACNT_PRDT_CD,
            "PDNO": code,
            "ORD_DVSN": "01", # 시장가
            "ORD_QTY": str(qty),
            "ORD_UNPR": "0",
        }
        
        res = requests.post(url, headers=headers, data=json.dumps(data))
        return res.json()

    def sell_order(self, code, qty):
        """시장가 매도"""
        path = "uapi/domestic-stock/v1/trading/order-cash"
        url = f"{URL_BASE}/{path}"
        headers = self.headers.copy()
        headers["tr_id"] = "VTTC0801U" # 모의투자 매도 (실전: TTTC0801U)
        
        data = {
            "CANO": CANO,
            "ACNT_PRDT_CD": ACNT_PRDT_CD,
            "PDNO": code,
            "ORD_DVSN": "01",
            "ORD_QTY": str(qty),
            "ORD_UNPR": "0",
        }
        
        res = requests.post(url, headers=headers, data=json.dumps(data))
        return res.json()
