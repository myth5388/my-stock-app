import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. 앱 설정 및 제목
st.set_page_config(page_title="주식 투자 전략 도우미", layout="wide")
st.title("📊 실시간 시장 국면 및 투자 전략 분석")

# 2. 데이터 가져오기 (나스닥, 금리, 환율, VIX)
@st.cache_data(ttl=600)
def load_market_data():
    tickers = {
        "^IXIC": "나스닥", 
        "^TNX": "미국10년금리", 
        "USDKRW=X": "환율", 
        "^VIX": "공포지수"
    }
    data = yf.download(list(tickers.keys()), period="6mo", interval="1d")['Close']
    return data.ffill().dropna()

try:
    df = load_market_data()
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    # --- [분석 1] 시장 국면 판단 (20일 이동평균선 기준) ---
    ma20 = df['^IXIC'].rolling(window=20).mean().iloc[-1]
    nasdaq_now = current['^IXIC']
    
    if nasdaq_now > ma20 * 1.03:
        regime, color, advice = "🚀 상승 국면", "#D4EDDA", "적극적인 매수 전략이 유효합니다."
    elif nasdaq_now < ma20 * 0.97:
        regime, color, advice = "📉 하락 국면", "#F8D7DA", "현금 비중을 높이고 리스크를 관리하세요."
    else:
        regime, color, advice = "⚖️ 횡보 국면", "#FFF3CD", "분할 매수로 신중하게 접근하세요."

    # 상단 요약 박스
    st.markdown(f"""
        <div style="background-color:{color}; padding:20px; border-radius:10px; text-align:center;">
            <h2 style="margin:0;">현재 시장은 【 {regime} 】 입니다</h2>
            <p style="font-size:1.2rem; margin-top:10px;">{advice}</p>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # --- [분석 2] 주요 지표 현황 ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        diff = current['^IXIC'] - prev['^IXIC']
        st.metric("나스닥 지수", f"{current['^IXIC']:,.2f}", f"{diff:+,.2f}")
        
    with col2:
        diff_tnx = current['^TNX'] - prev['^TNX']
        st.metric("미국 10년물 금리", f"{current['^TNX']:.2f}%", f"{diff_tnx:+.2f}%")
        
    with col3:
        diff_krw = current['USDKRW=X'] - prev['USDKRW=X']
        st.metric("원/달러 환율", f"{current['USDKRW=X']:,.1f}원", f"{diff_krw:+.1f}원")

    # --- [분석 3] 추세 그래프 ---
    st.subheader("📈 나스닥 최근 6개월 흐름")
    st.line_chart(df['^IXIC'])

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.info("잠시 후 다시 시도하거나 깃허브의 requirements.txt 파일을 확인해 주세요.")
