import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="AI 동적 투자 전략 앱", layout="wide")
st.title("🛡️ 국면별 동적 자산 배분 및 성과 분석")

# 2. 시장 국면 선택 (사용자 판단 또는 시장 지표 기반)
st.sidebar.header("🕹️ 시장 국면 설정")
market_state = st.sidebar.selectbox(
    "현재 시장의 추세를 선택하세요",
    ["추세 상승기 (Bull)", "추세 하락기 (Bear)", "박스권/횡보분출기 (Sideways)"]
)

# 국면별 로직 설정 (손실 감당 및 비중)
def get_market_logic(state):
    if "상승기" in state:
        return {"stock_ratio": 0.8, "sl_rate": 0.88, "tp_rate": 1.30, "desc": "공격적 추세 향유", "color": "blue"}
    elif "하락기" in state:
        return {"stock_ratio": 0.2, "sl_rate": 0.96, "tp_rate": 1.05, "desc": "보수적 원금 방어", "color": "red"}
    else:
        return {"stock_ratio": 0.5, "sl_rate": 0.92, "tp_rate": 1.15, "desc": "중립적 리밸런싱", "color": "green"}

logic = get_market_logic(market_state)

st.sidebar.markdown(f"""
---
**[{market_state} 대응 전략]**
- **권장 주식 비중**: {logic['stock_ratio']*100:.0f}%
- **손절 감당 비율**: {(1-logic['sl_rate'])*100:.0f}% (타이트함)
- **목표 수익 비율**: {(logic['tp_rate']-1)*100:.0f}%
- **운용 기조**: {logic['desc']}
""")

# 3. 데이터 로드 (2024년 초부터 현재까지)
@st.cache_data
def get_data():
    symbols = {
        "나스닥100(QQQ)": "QQQ",
        "S&P500(IVV)": "IVV",
        "삼성전자": "005930.KS",
        "비트코인(BTC)": "BTC-USD"
    }
    data = {}
    for name, ticker in symbols.items():
        try:
            df = yf.Ticker(ticker).history(start="2024-01-01")
            if not df.empty: data[name] = df
        except: continue
    return data

market_data = get_data()

# 4. 성과 및 추세 시각화
st.header(f"📊 2024-2026 자산 성과 ({market_state})")
cols = st.columns(len(market_data))

for i, (name, df) in enumerate(market_data.items()):
    start_p = df.iloc[0]['Close']
    curr_p = df.iloc[-1]['Close']
    ret = ((curr_p - start_p) / start_p) * 100
    
    with cols[i]:
        st.metric(name, f"{curr_p:,.0f}", f"{ret:+.2f}%")
        st.line_chart(df['Close'], height=150)

# 5. [핵심] 1,000만 원 투자 시뮬레이션 및 전략 테이블
st.divider()
st.header("🎯 1,000만 원 투자 전략 가이드")
total_budget = 10000000

strategy_list = []
for name, df in market_data.items():
    curr_p = df.iloc[-1]['Close']
    
    # 국면별 로직 적용 계산
    allocation = (total_budget * logic['stock_ratio']) / len(market_data)
    target_p = curr_p * logic['tp_rate']
    stop_p = curr_p * logic['sl_rate']
    
    strategy_list.append({
        "자산명": name,
        "할당 금액": f"{allocation:,.0f}원",
        "현재가": f"{curr_p:,.2f}",
        "목표가(익절)": f"{target_p:,.2f}",
        "손절가(감당선)": f"{stop_p:,.2f}",
        "상태": "보유" if curr_p > stop_p else "매도/관망"
    })

st.table(pd.DataFrame(strategy_list))

# 6. 리밸런싱 및 국면 대응 수칙
with st.expander("💡 2024년 이후 시뮬레이션 기반 투자 수칙"):
    st.write(f"""
    1. **하락기 방어**: 2024년 8월 같은 급락장에서는 사이드바에서 **'추세 하락기'**를 선택하세요. 손절선이 **-4%**로 타이트해지며 현금 비중이 80%로 늘어납니다.
    2. **상승기 추격**: 2025년 삼성전자 폭등기에는 **'추세 상승기'**를 선택하세요. 손절선을 **-12%**로 넓혀 잔파동에 털리지 않고 큰 수익을 끝까지 가져갑니다.
    3. **비중 조절**: 현재 자산 중 삼성전자의 비중이 너무 크다면, 위 표의 **'할당 금액'**에 맞춰 나스닥(QQQ)으로 자금을 옮기는 리밸런싱을 권장합니다.
    """)

st.caption(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 국면별 동적 손절 로직 적용")
