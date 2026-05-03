import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="AI 통합 투자 전략 대시보드", layout="wide")
st.title("📈 2026 AI 동적 리밸런싱 및 통합 전략")

# 2. 투자 설정 및 국면 선택 (사이드바 복구)
total_budget = 10000000  # 1,000만 원 기준
st.sidebar.header("🌐 현 시장 국면 분석")
market_state = st.sidebar.selectbox(
    "현재 시장의 추세를 선택하세요",
    ["추세 상승기 (Bull)", "추세 하락기 (Bear)", "박스권/횡보분출기 (Sideways)"]
)

# 국면별 로직 설정 (비중 및 리스크 관리)
def get_market_logic(state):
    if "상승기" in state:
        return {"ratios": {"QQQ": 0.45, "IVV": 0.15, "005930.KS": 0.30, "BTC-USD": 0.10},
                "sl_rate": 0.88, "tp_rate": 1.30, "cash_ratio": 0.0, "desc": "실적 장세 / AI 슈퍼사이클", "risk_adj": "공격적"}
    elif "하락기" in state:
        return {"ratios": {"QQQ": 0.10, "IVV": 0.20, "005930.KS": 0.05, "BTC-USD": 0.05},
                "sl_rate": 0.96, "tp_rate": 1.05, "cash_ratio": 0.6, "desc": "금리/매크로 불확실성", "risk_adj": "보수적"}
    else:
        return {"ratios": {"QQQ": 0.25, "IVV": 0.25, "005930.KS": 0.10, "BTC-USD": 0.05},
                "sl_rate": 0.92, "tp_rate": 1.15, "cash_ratio": 0.35, "desc": "고점 부담 / 순환매 장세", "risk_adj": "중립적"}

logic = get_market_logic(market_state)

st.sidebar.info(f"""
**[전략 기조: {logic['risk_adj']}]**
- {logic['desc']}
- **현금 비중**: {logic['cash_ratio']*100:.0f}% 확보
- **손절 대응**: {((1-logic['sl_rate'])*100):.0f}% 이내
""")

# 3. 데이터 로드 (2024년 초부터)
@st.cache_data
def load_full_data():
    symbols = {"나스닥100(QQQ)": "QQQ", "S&P500(IVV)": "IVV", "삼성전자": "005930.KS", "비트코인(BTC)": "BTC-USD"}
    data = {}
    for name, ticker in symbols.items():
        try:
            df = yf.Ticker(ticker).history(start="2024-01-01")
            if not df.empty: data[ticker] = {"df": df, "name": name}
        except: continue
    return data

assets = load_full_data()

# 4. 성과 요약 메트릭
st.header("🔍 자산별 성과 요약")
cols = st.columns(len(assets))
for i, (ticker, info) in enumerate(assets.items()):
    df = info['df']
    start_p = df.iloc['Close']
    curr_p = df.iloc[-1]['Close']
    ret = ((curr_p - start_p) / start_p) * 100
    with cols[i]:
        st.metric(info['name'], f"{curr_p:,.2f}", f"{ret:+.2f}%")
        st.line_chart(df['Close'], height=120)

# 5. [복구 완료] 통합 리밸런싱 및 상세 매매 전략 테이블
st.divider()
st.header("🎯 통합 리밸런싱 및 상세 전략")

strategy_list = []
for ticker, info in assets.items():
    curr_p = info['df'].iloc[-1]['Close']
    target_ratio = logic['ratios'].get(ticker, 0)
    target_amt = total_budget * target_ratio
    
    # 사라졌던 항목들 복구
    risk_lv = "높음" if "BTC" in ticker or "005930" in ticker else "보통"
    if "IVV" in ticker: risk_lv = "낮음"
    
    action = "매수 확대" if target_ratio >= 0.3 else ("축소/대기" if target_ratio <= 0.05 else "비중 유지")
    status = "안전" if curr_p > (curr_p * logic['sl_rate'] * 1.05) else "경계"

    strategy_list.append({
        "자산명": info['name'],
        "권장 비중": f"{target_ratio*100:.0f}%",
        "목표 금액": f"{target_amt:,.0f}원",
        "현재가": f"{curr_p:,.2f}",
        "손절가": f"{curr_p * logic['sl_rate']:,.2f}",
        "목표가": f"{curr_p * logic['tp_rate']:,.2f}",
        "리스크": risk_lv,
        "상태": status,
        "액션": action
    })

st.table(pd.DataFrame(strategy_list))

# 6. 리밸런싱 실행 가이드
col1, col2 = st.columns(2)
with col1:
    st.success(f"✅ **현재 투자 집행 금액**: {total_budget * (1-logic['cash_ratio']):,.0f}원")
with col2:
    st.warning(f"💰 **미체결/현금 확보 자산**: {total_budget * logic['cash_ratio']:,.0f}원")

with st.expander("💡 2024년~현재 분석 기반 실전 수칙"):
    st.write(f"""
    - **하락장 대응**: 2024년 8월 같은 급락 시 '추세 하락기'로 전환하여 현금 **{logic['cash_ratio']*100:.0f}%**를 즉시 확보하세요.
    - **수익 향유**: 삼성전자와 같은 주도주는 '추세 상승기' 설정 시 손절선을 넓게 가져가 추세를 끝까지 추종합니다.
    - **리밸런싱 주기**: 최소 월 1회 또는 시장 국면이 바뀔 때 위 표의 '목표 금액'에 맞춰 보유 수량을 조절하세요.
    """)

st.caption(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 모든 전략 항목 복구 완료")
