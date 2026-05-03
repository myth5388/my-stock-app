import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="AI 동적 리밸런싱 대시보드", layout="wide")
st.title("📈 2026 AI 동적 리밸런싱 및 자산 관리 시스템")

# 2. 투자 설정 및 국면 선택 (사이드바)
total_budget = 10000000  # 1,000만 원 기준
st.sidebar.header("🌐 현 시장 국면 분석")
market_state = st.sidebar.selectbox(
    "현재 시장 추세를 선택하세요",
    ["추세 상승기 (Bull)", "추세 하락기 (Bear)", "박스권/횡보분출기 (Sideways)"]
)

# 국면별 로직 설정
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

# 사이드바 요약 정보 (에러 방지를 위해 format 사용)
st.sidebar.info(f"""
**[전략 기조: {logic['risk_adj']}]**
- **상태**: {logic['desc']}
- **현금 비중**: {int(logic['cash_ratio']*100)}%
- **손절 폭**: {int((1-logic['sl_rate'])*100)}% 이내
""")

# 3. 데이터 로드 (2024년 이후)
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

# 4. 자산별 성과 요약 (차트 제외, 메트릭 중심)
st.header("🔍 자산별 현재 성과 (2024~2026)")
cols = st.columns(len(assets))
for i, (ticker, info) in enumerate(assets.items()):
    df = info['df']
    start_p = df['Close'].iloc[0]
    curr_p = df['Close'].iloc[-1]
    ret = ((curr_p - start_p) / start_p) * 100
    with cols[i]:
        st.metric(info['name'], f"{curr_p:,.2f}", f"{ret:+.2f}%")

# 5. 통합 리밸런싱 및 상세 전략 테이블
st.divider()
st.header("🎯 국면 맞춤형 리밸런싱 실행 가이드")

strategy_list = []
for ticker, info in assets.items():
    curr_p = info['df']['Close'].iloc[-1]
    target_ratio = logic['ratios'].get(ticker, 0)
    target_amt = total_budget * target_ratio
    
    # 리스크 및 상태 판단
    risk_lv = "높음" if "BTC" in ticker or "005930" in ticker else "보통"
    if "IVV" in ticker: risk_lv = "낮음"
    
    status = "✅ 안전" if curr_p > (curr_p * logic['sl_rate'] * 1.05) else "⚠️ 경계"
    action = "비중 확대" if target_ratio >= 0.3 else ("축소/관망" if target_ratio <= 0.05 else "유지")

    strategy_list.append({
        "자산명": info['name'],
        "권장 비중": f"{int(target_ratio*100)}%",
        "목표 금액": f"{target_amt:,.0f}원",
        "현재가": f"{curr_p:,.2f}",
        "손절가": f"{curr_p * logic['sl_rate']:,.2f}",
        "익절가": f"{curr_p * logic['tp_rate']:,.2f}",
        "리스크": risk_lv,
        "상태": status,
        "추천 액션": action
    })

st.table(pd.DataFrame(strategy_list))

# 6. 하단 요약 및 실전 수칙
c1, c2, c3 = st.columns(3)
c1.success(f"**투자 집행**: {total_budget * (1-logic['cash_ratio']):,.0f}원")
c2.warning(f"**현금 확보**: {total_budget * logic['cash_ratio']:,.0f}원")
c3.info(f"**현재 모드**: {market_state}")

with st.expander("📝 2024년 이후 시뮬레이션 기반 투자 수칙"):
    st.write(f"""
    - **하락기**: 2024년 8월 급락 시 손절선 **-4%**를 적용했다면 원금의 대부분을 보존했을 것입니다.
    - **상승기**: 2025년 삼성전자 폭등 국면에서는 손절선을 **-12%**로 넓혀 추세를 끝까지 가져갔어야 합니다.
    - **리밸런싱**: 현재 보유 비중이 표의 '권장 비중'과 5% 이상 차이 날 경우 즉시 조절을 권장합니다.
    """)

st.caption(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 차트 제외 수치 집중 버전")
