import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="AI 동적 리밸런싱 전략", layout="wide")
st.title("⚖️ 시장 국면별 포트폴리오 리밸런싱")

# 2. 투자 원금 설정 및 시장 국면 선택
total_budget = 10000000  # 1,000만 원
st.sidebar.header("⚙️ 리밸런싱 설정")
market_state = st.sidebar.selectbox(
    "현재 시장 국면을 선택하세요",
    ["추세 상승기 (적극 투자)", "추세 하락기 (방어 중심)", "횡보/변동기 (리스크 관리)"]
)

# 3. 국면별 리밸런싱 및 손절 로직 (핵심)
def get_rebalancing_logic(state):
    if "상승기" in state:
        # 나스닥/삼성전자 비중 확대, 손절 폭 넉넉히
        return {
            "ratios": {"QQQ": 0.45, "IVV": 0.15, "005930.KS": 0.30, "BTC-USD": 0.10},
            "sl_rate": 0.88, "tp_rate": 1.30, "cash_ratio": 0.0, "desc": "수익 극대화 (Full Invest)"
        }
    elif "하락기" in state:
        # 안전 자산(IVV) 위주, 현금 비중 60% 확보, 손절 폭 매우 타이트
        return {
            "ratios": {"QQQ": 0.10, "IVV": 0.20, "005930.KS": 0.05, "BTC-USD": 0.05},
            "sl_rate": 0.97, "tp_rate": 1.05, "cash_ratio": 0.6, "desc": "현금 확보 및 원금 방어"
        }
    else:
        # 지수 중심 5:5 전략, 손절 폭 보통
        return {
            "ratios": {"QQQ": 0.25, "IVV": 0.25, "005930.KS": 0.10, "BTC-USD": 0.05},
            "sl_rate": 0.93, "tp_rate": 1.15, "cash_ratio": 0.35, "desc": "중립적 자산 배분"
        }

logic = get_rebalancing_logic(market_state)

# 4. 데이터 로드 (2024년 이후)
@st.cache_data
def load_data():
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
            if not df.empty: data[ticker] = {"df": df, "name": name}
        except: continue
    return data

assets = load_data()

# 5. 리밸런싱 결과 출력
st.header(f"📅 2024-2026 리밸런싱 가이드 ({market_state})")
st.info(f"💡 **운용 전략**: {logic['desc']} | **현금 보유 비중**: {logic['cash_ratio']*100:.0f}%")

col_cash, col_invest = st.columns(2)
col_cash.metric("확보 필요 현금", f"{total_budget * logic['cash_ratio']:,.0f}원")
col_invest.metric("총 투자 집행 금액", f"{total_budget * (1-logic['cash_ratio']):,.0f}원")

# 6. 종목별 상세 리밸런싱 테이블
strategy_data = []
for ticker, info in assets.items():
    df = info['df']
    curr_p = df.iloc[-1]['Close']
    target_ratio = logic['ratios'].get(ticker, 0)
    alloc_amt = total_budget * target_ratio
    
    strategy_data.append({
        "종목명": info['name'],
        "리밸런싱 비중": f"{target_ratio*100:.0f}%",
        "목표 편입 금액": f"{alloc_amt:,.0f}원",
        "현재가": f"{curr_p:,.2f}",
        "익절가(+{:.0f}%)".format((logic['tp_rate']-1)*100): f"{curr_p * logic['tp_rate']:,.2f}",
        "손절가(-{:.0f}%)".format((1-logic['sl_rate'])*100): f"{curr_p * logic['sl_rate']:,.2f}",
    })

st.table(pd.DataFrame(strategy_data))

# 7. 성과 차트
st.subheader("📈 자산별 추세 분석")
chart_cols = st.columns(len(assets))
for i, (ticker, info) in enumerate(assets.items()):
    with chart_cols[i]:
        st.write(info['name'])
        st.line_chart(info['df']['Close'], height=150)

# 8. 리밸런싱 실행 수칙
with st.expander("📝 1,000만원 리밸런싱 실행 가이드"):
    st.write(f"""
    1. **추세 상승기**: 삼성전자와 나스닥 비중을 **75%까지 확대**하여 수익을 극대화하세요. 2025년과 같은 급등장에서는 손절선을 **-12%**로 넓혀야 일시적 조정에 털리지 않습니다.
    2. **추세 하락기**: 시장이 꺾이면 즉시 삼성전자 비중을 5% 미만으로 줄이고 **현금 600만 원을 확보**하세요. 손절선을 **-3%**로 매우 짧게 잡아 원금을 지키는 것이 리밸런싱의 핵심입니다.
    3. **교체 매매**: 현재 삼성전자의 수익률이 높다면, 일부를 매도하여 **나스닥(QQQ)**이나 **S&P500(IVV)**으로 비중을 옮겨 포트폴리오의 안정성을 높이세요.
    """)

st.caption(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 동적 리밸런싱 엔진 가동 중")
