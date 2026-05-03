import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="AI 투자 전략 및 국면 분석", layout="wide")
st.title("📈 2026 AI 투자 성과 및 포트폴리오 전략")

# 2. 데이터 로드 (2025년부터 현재까지)
@st.cache_data
def get_market_data():
    symbols = {
        "삼성전자": "005930.KS",
        "비트코인(USD)": "BTC-USD",
        "나스닥100(QQQ)": "QQQ",
        "S&P500(IVV)": "IVV",
        "엔비디아(NVDA)": "NVDA"
    }
    data = {}
    for name, ticker in symbols.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start="2025-01-01")
            if not hist.empty:
                data[name] = hist
        except:
            continue
    return data

market_data = get_market_data()

# 3. [신규] 현 국면 변화 및 시장 영향 분석
st.sidebar.header("🌐 현 시장 국면 분석")
market_phase = "실적 장세 (AI 슈퍼사이클)"
st.sidebar.subheader(f"현재 국면: {market_phase}")
st.sidebar.info("""
**핵심 변화 및 영향:**
1. **금리 정상화**: 3%대 금리 안착으로 유동성보다 기업 '이익'이 주가 결정.
2. **반도체 독주**: 삼성전자 등 AI 메모리 수요 폭증으로 국내 증시 재평가.
3. **K자 양극화**: 실적 있는 빅테크만 오르는 차별화 장세 심화.
""")

# 4. 투자 성과 요약 섹션
st.header("🔍 2025년 이후 자산별 성과")
cols = st.columns(len(market_data))

for i, (name, df) in enumerate(market_data.items()):
    start_price = df.iloc[0]['Close']
    current_price = df.iloc[-1]['Close']
    return_pct = ((current_price - start_price) / start_price) * 100
    
    with cols[i]:
        st.metric(name, f"{current_price:,.2f}", f"{return_pct:+.2f}%")
        st.line_chart(df['Close'], height=150)

# 5. [신규] 국면별 추천 포트폴리오 비중 조절
st.divider()
st.header("⚖️ 현 국면 맞춤형 포트폴리오 비중")

# 비중 조절 로직
portfolio_strategy = [
    {"자산군": "미국 지수 (QQQ/IVV)", "추천 비중": "45%", "전략": "코어(Core) 유지", "영향": "안정적 우상향"},
    {"자산군": "반도체/AI (삼성/NVDA)", "추천 비중": "30%", "전략": "비중 확대 (▲)", "영향": "실적 모멘텀 극대화"},
    {"자산군": "현금 및 안전자산", "추천 비중": "15%", "전략": "비중 축소 (▼)", "영향": "기회비용 최소화"},
    {"자산군": "가상자산/기타", "추천 비중": "10%", "전략": "관망/일부 실현", "영향": "변동성 리스크 관리"}
]
st.table(pd.DataFrame(portfolio_strategy))

# 6. 종목별 상세 매매 가이드 (매수/목표/손절)
st.header("🎯 종목별 실시간 매매 전략")

def calculate_strategy(name, price):
    if any(x in name for x in ["QQQ", "IVV"]):
        tp_rate, sl_rate = 1.15, 0.93  # 지수: 익절 +15%, 손절 -7%
    elif any(x in name for x in ["삼성", "엔비디아"]):
        tp_rate, sl_rate = 1.25, 0.90  # 우량주: 익절 +25%, 손절 -10%
    else:
        tp_rate, sl_rate = 1.50, 0.85  # 코인/기타: 익절 +50%, 손절 -15%
        
    return {
        "현재가": f"{price:,.2f}",
        "목표가(익절)": f"{price * tp_rate:,.2f}",
        "손절가(Stop-Loss)": f"{price * sl_rate:,.2f}",
        "대응전략": "보유/추가매수" if price > (price * sl_rate * 1.05) else "손절 준비"
    }

strategy_list = []
for name, df in market_data.items():
    current_price = df.iloc[-1]['Close']
    strat = calculate_strategy(name, current_price)
    strategy_list.append({"자산명": name, **strat})

st.table(pd.DataFrame(strategy_list))

st.caption(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 현 시장 국면 분석 데이터 포함")
