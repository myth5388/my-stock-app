import streamlit as st
import yfinance as yf
import pandas as pd
from openai import OpenAI

# 1. 앱 페이지 설정
st.set_page_config(page_title="공격적 투자 전략 대시보드", layout="wide")
st.title("📊 오늘의 경제지표 & AI 포트폴리오 전략")
st.markdown("실시간 금리, 환율, VIX 및 비트코인을 분석하여 최적의 공격적 비중을 제안합니다.")

# 2. 실시간 및 과거 데이터 로드 함수
@st.cache_data(ttl=3600) # 1시간마다 데이터 갱신
def get_market_all_data():
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
        # 실시간 값 (최근 2일치 가져와서 전일 대비 계산용)
        hist = ticker_obj.history(period="5d")
        if not hist.empty:
            current_data[name] = hist['Close'].iloc[-1]
            current_data[f"{name}_prev"] = hist['Close'].iloc[-2]
            # 차트용 1개월 데이터
            history_data[name] = yf.Ticker(symbol).history(period="1mo")['Close']
            
    return current_data, history_data

# 데이터 가져오기
with st.spinner('시장 데이터를 불러오는 중...'):
    data, history = get_market_all_data()

# 3. 지표 상단 표시 (Metrics)
col1, col2, col3, col4 = st.columns(4)
with col1:
    d = data['금리'] - data['금리_prev']
    st.metric("🇺🇸 미 10년물 실제금리", f"{data['금리']:.2f}%", f"{d:.2f}%")
with col2:
    d = data['환율'] - data['환율_prev']
    st.metric("💵 원/달러 환율", f"{data['환율']:,.1f}원", f"{d:,.1f}원")
with col3:
    d = data['VIX'] - data['VIX_prev']
    st.metric("📉 VIX 공포지수", f"{data['VIX']:.2f}", f"{d:.2f}")
with col4:
    d = data['비트코인'] - data['비트코인_prev']
    st.metric("🪙 비트코인", f"${data['비트코인']:,.0f}", f"${d:,.0f}")

st.divider()

# 4. 마켓 스코어 및 비중 산출 (유동적 패널티 로직)
def calculate_score(tnx, krw, vix):
    score = 100
    if tnx > 4.5: score -= 30
    elif tnx > 4.0: score -= 15
    if krw > 1450: score -= 40
    elif krw > 1350: score -= 20
    if vix > 30: score -= 30
    elif vix > 20: score -= 10
    return max(0, score)

market_score = calculate_score(data['금리'], data['환율'], data['VIX'])

# 비중 결정 (NameError 방지를 위해 AI 호출 전에 선언)
if market_score >= 80:
    status = "✅ 적극 매수"
    weights = {"주식": 75, "가상자산": 20, "현금": 5}
elif market_score >= 50:
    status = "⚠️ 비중 중립"
    weights = {"주식": 50, "가상자산": 10, "현금": 40}
else:
    status = "🚨 위험 관리"
    weights = {"주식": 20, "가상자산": 5, "현금": 75}

# 5. 분석 화면 레이아웃
left, right = st.columns([1, 1])

with left:
    st.subheader(f"🎯 마켓 스코어: {market_score}점 ({status})")
    st.progress(market_score / 100)
    st.write("공격적 투자 성향을 위한 추천 비중입니다.")
    st.table(pd.DataFrame([weights], index=["추천 비중(%)"]))

with right:
    st.subheader("📈 주요 지표 추이 (1개월)")
    chart_target = st.selectbox("지표 선택", ["나스닥", "금리", "비트코인", "환율"])
    st.line_chart(history[chart_target])

# 6. AI 리포트 생성 섹션
st.divider()
st.subheader("🤖 AI 전문가 맞춤형 전략 리포트")

def get_ai_report(m_data, score, w):
    # Streamlit Secrets에서 API 키를 가져오도록 설정
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        client = OpenAI(api_key=api_key)
        
        prompt = f"""
        당신은 공격적 투자자를 위한 자산운용가입니다. 아래 지표를 분석하세요.
        미금리: {m_data['금리']:.2f}%, 환율: {m_data['환율']:.1f}원, VIX: {m_data['VIX']:.2f}, 점수: {score}
        추천비중: 주식 {w['주식']}%, 가상자산 {w['가상자산']}%, 현금 {w['현금']}%
        현재 시장 상황에 따른 공격적 투자 전략을 전문적인 말투로 3~4문장 요약해줘.
        """
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices.message.content
    except Exception as e:
        return f"AI 리포트 생성 실패: API 키를 설정하거나 코드를 확인하세요. ({e})"

if st.button("AI 전략 리포트 생성하기"):
    with st.spinner("AI 분석 중..."):
        report = get_ai_report(data, market_score, weights)
        st.info(report)

st.divider()
st.caption("※ 본 정보는 투자 참고용이며, 모든 투자 결정의 책임은 본인에게 있습니다.")
