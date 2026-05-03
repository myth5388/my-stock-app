import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="AI 동적 리밸런싱 대시보드", layout="wide")
st.title("⚖️ 2024-2026 동적 리밸런싱 및 자산 관리")

# 2. 투자 설정 및 국면 선택
total_budget = 10000000  # 1,000만 원 기준
st.sidebar.header("⚙️ 투자 환경 설정")
market_state = st.sidebar.selectbox(
    "현재 시장 국면을 선택하세요",
    ["추세 상승기 (Bull)", "추세 하락기 (Bear)", "박스권/횡보분출기 (Sideways)"]
)

# 3. 국면별 리밸런싱 및 손절 로직
def get_rebalancing_logic(state):
    if "상승기" in state:
        return {"ratios": {"QQQ": 0.45, "IVV": 0.15, "005930.KS": 0.30, "BTC-USD": 0.10},
                "sl_rate": 0.88, "tp_rate": 1.30, "cash_ratio": 0.0, "desc": "공격적 수익 극대화"}
    elif "하락기" in state:
        return {"ratios": {"QQQ": 0.10, "IVV": 0.20, "005930.KS": 0.05, "BTC-USD": 0.05},
                "sl_rate": 0.96, "tp_rate": 1.05, "cash_ratio": 0.6, "desc": "현금 확보 및 원금 보호"}
    else:
        return {"ratios": {"QQQ": 0.25, "IVV": 0.25, "005930.KS": 0.10, "BTC-USD": 0.05},
                "sl_rate": 0.92, "tp_rate": 1.15, "cash_ratio": 0.35, "desc": "중립적 자산 배분"}

logic = get_rebalancing_logic(market_state)

# 4. 데이터 로드 (2024년 이후)
@st.cache_data
def load_data():
    symbols = {"나스닥100(QQQ)": "QQQ", "S&P500(IVV)": "IVV", "삼성전자": "005930.KS", "비트코인(BTC)": "BTC-USD"}
    data = {}
    for name, ticker in symbols.items():
        try:
            df = yf.Ticker(ticker).history(start="2024-01-01")
            if not df.empty: data[ticker] = {"df": df, "name": name}
        except: continue
    return data

assets = load_data()

# 5. [신규 추가] 리밸런싱 실행 가이드 섹션
st.header(f"🔄 리밸런싱 항목 (현 국면: {market_state})")
st.info(f"**전략 기조**: {logic['desc']} | **목표 현금 비중**: {logic['cash_ratio']*100:.0f}%")

rebalancing_table = []
for ticker, info in assets.items():
    curr_p = info['df'].iloc[-1]['Close']
    target_ratio = logic['ratios'].get(ticker, 0)
    target_amt = total_budget * target_ratio
    
    # 리밸런싱 행동 판단
    action = "유지"
    if target_ratio > 0.3: action = "적극 매수"
    elif target_ratio < 0.1: action = "부분 매도"

    rebalancing_table.append({
        "자산명": info['name'],
        "현재가": f"{curr_p:,.2f}",
        "목표 비중": f"{target_ratio*100:.0f}%",
        "목표 보유 금액": f"{target_amt:,.0f}원",
        "리밸런싱 액션": action,
        "손절 기준가": f"{curr_p * logic['sl_rate']:,.2f}",
        "익절 기준가": f"{curr_p * logic['tp_rate']:,.2f}"
    })

st.table(pd.DataFrame(rebalancing_table))

# 6. 성과 분석 차트
st.divider()
st.header("📈 2024-2026 자산별 추세")
chart_cols = st.columns(len(assets))
for i, (ticker, info) in enumerate(assets.items()):
    with chart_cols[i]:
        st.write(f"**{info['name']}**")
        st.line_chart(info['df']['Close'], height=150)

# 7. 투자 수칙 요약
with st.expander("📝 리밸런싱 실행 시 주의사항"):
    st.write(f"""
    - **슬리피지 고려**: 대량 매도/매수 시 발생하는 거래 비용을 고려하여 분할로 처리하세요.
    - **세금 관리**: 수익이 크게 난 종목(삼성전자 등)은 연간 비과세 한도를 체크하며 리밸런싱하세요.
    - **현금의 역할**: 하락기 모드에서 확보된 **{total_budget * logic['cash_ratio']:,.0f}원**의 현금은 추후 상승 반전 시 강력한 무기가 됩니다.
    """)

st.caption(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 동적 리밸런싱 로직 적용")
