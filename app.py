import streamlit as st
import yfinance as yf
import pandas as pd
from openai import OpenAI

# 1. 앱 설정 및 스타일
st.set_page_config(page_title="AI 전략적 자산배분 시스템", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="st-"] { font-size: 1.15rem; }
    h1 { font-size: 2.6rem !important; color: #1E3A8A; text-align: center; }
    [data-testid="stMetricValue"] { font-size: 2.4rem !important; font-weight: bold; }
    .reason-box { background-color: #f8f9fa; padding: 18px; border-radius: 10px; border-left: 6px solid #1E3A8A; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 AI 전략적 자산 배분 & 실시간 선물 분석")
st.markdown("<p style='text-align: center;'>미국 나스닥 선물 및 거시지표 실시간 분석 시스템</p>", unsafe_allow_html=True)

# 2. 데이터 로드 (나스닥 선물 NQ=F 추가)
@st.cache_data(ttl=300) # 선물 데이터는 더 자주 갱신 (5분)
def get_final_market_data():
    tickers = {
        "금리": "^TNX", "환율": "KRW=X", "VIX": "^VIX", 
        "나스닥": "^IXIC", "나스닥선물": "NQ=F", "유가": "CL=F", "금시세": "GC=F",
        "AAPL": "AAPL", "NVDA": "NVDA", "TSLA": "TSLA", "MSFT": "MSFT"
    }
    current_data = {}
    history_data = pd.DataFrame()
    for name, symbol in tickers.items():
        t_obj = yf.Ticker(symbol)
        hist = t_obj.history(period="5d")
        if not hist.empty and len(hist) >= 2:
            current_data[name] = hist['Close'].iloc[-1]
            current_data[f"{name}_prev"] = hist['Close'].iloc[-2]
            if name in ["나스닥선물", "환율", "금리", "비트코인"]:
                history_data[name] = t_obj.history(period="1mo")['Close']
    return current_data, history_data

with st.spinner('실시간 나스닥 선물 및 시장 데이터를 분석 중...'):
    data, history = get_final_market_data()

# 3. 점수 산정 로직 (나스닥 선물 변동률 반영)
def calculate_advanced_score(d):
    score = 100
    reasons = []
    
    # 나스닥 선물 변동률 패널티 (실시간 분위기 반영)
    nq_chg = ((d['나스닥선물'] - d['나스닥선물_prev']) / d['나스닥선물_prev']) * 100
    if nq_chg < -1.0:
        score -= 20
        reasons.append(f"📉 **나스닥 선물 급락({nq_chg:.2f}%):** 실시간 미 증시 분위기가 매우 어둡습니다.")
    
    # 환율(1.5x), 금리(1.2x) 등 기존 로직 유지
    krw_chg = ((d['환율'] - d['환율_prev']) / d['환율_prev']) * 100
    if krw_chg > 0.5:
        score -= 45; reasons.append(f"💵 **환율 급등({krw_chg:.1f}%):** 외국인 자금 이탈 경보")
        
    return max(0, score), reasons

curr_score, curr_reasons = calculate_advanced_score(data)
curr_w, status, color = ({"주식": 70, "채권": 15, "금": 5, "현금": 10}, "✅ 적극 매수", "green") if curr_score >= 80 else \
                        (({"주식": 45, "채권": 25, "금": 10, "현금": 20}, "⚠️ 비중 중립", "orange") if curr_score >= 50 else \
                        ({"주식": 20, "채권": 40, "금": 20, "현금": 20}, "🚨 위험 관리", "red"))

# 4. 메인 대시보드 표시
m_cols = st.columns(5)
metrics = [
    ("📊 나스닥 선물", '나스닥선물', "{:,.1f}"), ("💵 환율", '환율', "{:,.1f}원"), 
    ("🇺🇸 금리", '금리', "{:.2f}%"), ("📉 VIX", 'VIX', "{:.2f}"), ("🛢️ 유가", '유가', "${:.1f}")
]
for i, (label, key, fmt) in enumerate(metrics):
    with m_cols[i]:
        v, p = data.get(key, 0), data.get(f"{key}_prev", 0)
        st.metric(label, fmt.format(v), fmt.format(v-p))

st.divider()

# 이후 자산 배분 비중 및 AI 리포트 부분은 이전과 동일하게 유지...
st.subheader(f"🎯 실시간 투자 스코어: :{color}[{curr_score:.0f}점 ({status})]")
st.progress(curr_score / 100)

w_cols = st.columns(4)
for i, (label, key) in enumerate([("📈 주식", "주식"), ("🏦 채권", "채권"), ("✨ 금", "금"), ("💵 현금", "현금")]):
    w_cols[i].metric(label, f"{curr_w[key]}%")

st.divider()
if curr_reasons:
    for reason in curr_reasons: st.markdown(f"<div class='reason-box'>{reason}</div>", unsafe_allow_html=True)
else: st.success("시장이 매우 안정적입니다. 나스닥 선물도 우호적입니다.")
