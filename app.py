import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="AI 투자 전략 통합 대시보드", layout="wide")
st.title("📈 2026 AI 투자 성과 및 통합 매매 전략")

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

# 3. 사이드바: 현 국면 분석 (살려낸 부분)
st.sidebar.header("🌐 현 시장 국면 분석")
st.sidebar.subheader("현재: 실적 장세 (AI 슈퍼사이클)")
st.sidebar.info("""
- **금리**: 3%대 안착 (이익 중심 장세)
- **반도체**: 삼성전자 실적 모멘텀 강세
- **전략**: K자 양극화에 따른 우량주 집중
""")

# 4. 투자 성과 요약 (기존 유지)
st.header("🔍 2025년 이후 자산별 성과")
cols = st.columns(len(market_data))
for i, (name, df) in enumerate(market_data.items()):
    start_price = df.iloc[0]['Close']
    current_price = df.iloc[-1]['Close']
    return_pct = ((current_price - start_price) / start_price) * 100
    with cols[i]:
        st.metric(name, f"{current_price:,.2f}", f"{return_pct:+.2f}%")
        st.line_chart(df['Close'], height=150)

# 5. 포트폴리오 비중 조절 (현 국면 반영)
st.divider()
st.header("⚖️ 국면 맞춤형 포트폴리오 구성")
portfolio_strategy = [
    {"자산군": "미국 지수 (QQQ/IVV)", "추천 비중": "45%", "전략": "코어(Core) 유지", "영향": "안정적 우상향"},
    {"자산군": "반도체/AI (삼성/NVDA)", "추천 비중": "30%", "전략": "비중 확대 (▲)", "영향": "실적 모멘텀 극대화"},
    {"자산군": "현금 및 안전자산", "추천 비중": "15%", "전략": "비중 축소 (▼)", "영향": "기회비용 최소화"},
    {"자산군": "가상자산/기타", "추천 비중": "10%", "전략": "관망/일부 실현", "영향": "변동성 리스크 관리"}
]
st.table(pd.DataFrame(portfolio_strategy))

# 6. 상세 매매 가이드 (비중, 목표가, 손절가 모두 복구)
st.header("🎯 종목별 상세 실시간 전략")

def calculate_detailed_strategy(name, price):
    # 자산별 세부 파라미터 복구
    if any(x in name for x in ["QQQ", "IVV"]):
        buy_ratio, tp_rate, sl_rate, risk = "35%", 1.15, 0.93, "낮음"
    elif any(x in name for x in ["삼성", "엔비디아"]):
        buy_ratio, tp_rate, sl_rate, risk = "20%", 1.25, 0.90, "보통"
    else:
        buy_ratio, tp_rate, sl_rate, risk = "10%", 1.50, 0.85, "높음"
        
    return {
        "추천 비중": buy_ratio,
        "현재가": f"{price:,.2f}",
        "목표가(익절)": f"{price * tp_rate:,.2f}",
        "손절가(Stop-Loss)": f"{price * sl_rate:,.2f}",
        "리스크 등급": risk,
        "대응상태": "안전" if price > (price * sl_rate * 1.05) else "경계"
    }

strategy_list = []
for name, df in market_data.items():
    current_price = df.iloc[-1]['Close']
    strat = calculate_detailed_strategy(name, current_price)
    strategy_list.append({"자산명": name, **strat})

st.table(pd.DataFrame(strategy_list))

# 7. 투자 수칙 가이드라인 (복구)
with st.expander("💡 필독: 자산 관리 및 손절 수칙"):
    st.write("""
    - **분할 매수**: 추천 비중 내에서도 3회 이상 나누어 진입하여 평균 단가를 관리하세요.
    - **손절매 준수**: 손절가 이탈 시 기계적으로 비중을 축소하여 원금을 보존하는 것이 최우선입니다.
    - **수익 확정**: 목표가 도달 시 절반은 매도하여 수익을 챙기고, 나머지는 추세를 따라가세요.
    """)

st.caption(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 분석 데이터 포함")
