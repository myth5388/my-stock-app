import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# 1. 앱 설정 및 제목
st.set_page_config(page_title="공격적 투자 지표 대시보드", layout="wide")
st.title("📊 공격적 투자자를 위한 경제지표 & 포트폴리오 분석")
st.markdown("실시간 금리, 환율, VIX를 분석하여 최적의 자산 비중을 제안합니다.")

# 2. 데이터 가져오기 함수 (yfinance 사용)
@st.cache_data(ttl=3600) # 1시간마다 데이터 갱신
def get_market_data():
    # 주요 티커: 금리(^TNX), 환율(KRW=X), VIX(^VIX), 비트코인(BTC-USD), 나스닥(^IXIC)
    tickers = {
        "금리": "^TNX",
        "환율": "KRW=X",
        "VIX": "^VIX",
        "비트코인": "BTC-USD",
        "나스닥": "^IXIC"
    }
    
    current_data = {}
    history_data = pd.DataFrame()

    for name, symbol in tickers.items():
        ticker_obj = yf.Ticker(symbol)
        # 실시간 값 (최근 2일치 가져와서 전일 대비 계산용으로 활용)
        hist = ticker_obj.history(period="5d")
        if not hist.empty:
            current_data[name] = hist['Close'].iloc[-1]
            current_data[f"{name}_prev"] = hist['Close'].iloc[-2]
            # 차트용 1개월 데이터
            history_data[name] = yf.Ticker(symbol).history(period="1mo")['Close']
            
    return current_data, history_data

# 데이터 로드
with st.spinner('실시간 시장 데이터를 가져오는 중...'):
    data, history = get_market_data()

# 3. 마켓 스코어 알고리즘 (유동적 패널티 방식)
def calculate_market_score(tnx, krw, vix):
    score = 100
    # 금리 패널티 (임계치 4.5%)
    if tnx > 4.5: score -= 30
    elif tnx > 4.0: score -= 15
    
    # 환율 패널티 (임계치 1400원)
    if krw > 1450: score -= 40
    elif krw > 1350: score -= 20
    
    # VIX 패널티 (심리적 위축)
    if vix > 30: score -= 30
    elif vix > 20: score -= 10
    
    return max(0, score)

market_score = calculate_market_score(data['금리'], data['환율'], data['VIX'])

# 4. 상단 지표 레이아웃 (Metrics)
col1, col2, col3, col4 = st.columns(4)
with col1:
    delta = data['금리'] - data['금리_prev']
    st.metric("🇺🇸 미 10년물 금리", f"{data['금리']:.2f}%", f"{delta:.2f}%")
with col2:
    delta = data['환율'] - data['환율_prev']
    st.metric("💵 원/달러 환율", f"{data['환율']:,.1f}원", f"{delta:,.1f}원")
with col3:
    delta = data['VIX'] - data['VIX_prev']
    st.metric("📉 VIX 지수", f"{data['VIX']:.2f}", f"{delta:.2f}")
with col4:
    delta = data['비트코인'] - data['비트코인_prev']
    st.metric("🪙 비트코인", f"${data['비트코인']:,.0f}", f"${delta:,.0f}")

st.divider()

# 5. 분석 결과 섹션
left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("🎯 마켓 익스포저 점수")
    st.write(f"현재 당신의 공격적 투자 점수는 **{market_score}점**입니다.")
    st.progress(market_score / 100)
    
    # 점수별 비중 로직
    if market_score >= 80:
        st.success("✅ **공격적 매수 구간**: 적극적인 비중 확대를 추천합니다.")
        weights = {"주식": 75, "가상자산": 20, "현금": 5}
    elif market_score >= 50:
        st.warning("⚠️ **중립 구간**: 변동성에 대비하며 우량주 위주로 보유하세요.")
        weights = {"주식": 50, "가상자산": 10, "현금": 40}
    else:
        st.error("🚨 **위험 관리 구간**: 현금 비중을 높이고 관망해야 합니다.")
        weights = {"주식": 20, "가상자산": 5, "현금": 75}

    # 비중 시각화 (간이 표)
    st.table(pd.DataFrame([weights], index=["추천 비중(%)"]))

with right_col:
    st.subheader("📈 주요 지표 추이 (1개월)")
    selected_chart = st.selectbox("보고 싶은 지표를 선택하세요", ["나스닥", "금리", "비트코인", "환율"])
    st.line_chart(history[selected_chart])

# 6. 하단 안내 (면책 조항)
st.divider()
st.caption("※ 본 앱의 분석 결과는 투자 참고용이며, 모든 투자의 책임은 투자자 본인에게 있습니다.")
