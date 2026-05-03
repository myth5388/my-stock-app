import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="AI 투자 전략 대시보드", layout="wide")
st.title("📈 2025-2026 투자 성과 및 매매 전략")

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

# 3. 투자 성과 요약 섹션
st.header("🔍 2025년 이후 자산별 성과")
cols = st.columns(len(market_data))

for i, (name, df) in enumerate(market_data.items()):
    start_price = df.iloc[0]['Close']
    current_price = df.iloc[-1]['Close']
    return_pct = ((current_price - start_price) / start_price) * 100
    
    with cols[i]:
        st.metric(name, f"{current_price:,.2f}", f"{return_pct:+.2f}%")
        st.line_chart(df['Close'], height=150)

# 4. [신규 추가] 오늘의 추천 전략 및 리스크 관리 (매수/매도/손절)
st.divider()
st.header("🎯 자산별 매매 전략 가이드 (비중 및 손절선)")

def calculate_strategy(name, price):
    """자산 성격에 따른 매매 비율 계산 알고리즘"""
    if "QQQ" in name or "IVV" in name:  # 지수 ETF (안정 지향)
        buy_ratio = 35   # 추천 비중 35%
        tp_rate = 1.15   # 목표가 +15%
        sl_rate = 0.93   # 손절가 -7%
    elif "삼성" in name or "엔비디아" in name:  # 개별 우량주 (수익 지향)
        buy_ratio = 20   # 추천 비중 20%
        tp_rate = 1.25   # 목표가 +25%
        sl_rate = 0.90   # 손절가 -10%
    else:  # 가상자산 등 (고위험 고수익)
        buy_ratio = 10   # 추천 비중 10%
        tp_rate = 1.50   # 목표가 +50%
        sl_rate = 0.85   # 손절가 -15%
        
    return {
        "추천 비중": f"{buy_ratio}%",
        "현재가(매수기준)": f"{price:,.2f}",
        "목표가(익절)": f"{price * tp_rate:,.2f}",
        "손절가(Stop-Loss)": f"{price * sl_rate:,.2f}",
        "리스크 등급": "낮음" if buy_ratio > 30 else ("보통" if buy_ratio > 15 else "높음")
    }

strategy_list = []
for name, df in market_data.items():
    current_price = df.iloc[-1]['Close']
    strat = calculate_strategy(name, current_price)
    strategy_list.append({"자산명": name, **strat})

# 전략 테이블 출력
strat_df = pd.DataFrame(strategy_list)
st.table(strat_df)

# 5. 투자 수칙 가이드라인
with st.expander("💡 필독: 자산 관리 및 손절 수칙"):
    st.write("""
    - **분할 매수**: 추천 비중 내에서도 3회 이상 나누어 진입하는 것을 권장합니다.
    - **손절매(Stop-Loss) 준수**: 위 표의 '손절가'를 종가 기준으로 이탈할 경우 미련 없이 비중을 축소하세요.
    - **수익 확정**: 목표가 도달 시 보유 물량의 50%를 매도하여 수익을 확정 짓는 '트레일링 스탑' 전략이 유리합니다.
    - **ETF 우선주의**: 초보 투자자일수록 추천 비중이 높은 **QQQ**나 **IVV** 같은 지수형 ETF 비중을 먼저 채우시기 바랍니다.
    """)

st.caption(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d')} | 본 정보는 투자 참고용이며 최종 책임은 투자자에게 있습니다.")
