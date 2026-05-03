import streamlit as st
import yfinance as yf
import pandas as pd
from openai import OpenAI

# 1. 앱 페이지 설정
st.set_page_config(page_title="공격적 투자 전략 대시보드", layout="wide")

# 스타일 커스텀: 가독성을 높이기 위한 CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 오늘의 경제지표 & AI 포트폴리오 전략")
st.markdown("---")

# 2. 데이터 로드 함수 (캐싱 적용)
@st.cache_data(ttl=3600)
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
        hist = ticker_obj.history(period="5d")
        if not hist.empty:
            current_data[name] = hist['Close'].iloc[-1]
            current_data[f"{name}_prev"] = hist['Close'].iloc[-2]
            history_data[name] = yf.Ticker(symbol).history(period="1mo")['Close']
    return current_data, history_data

with st.spinner('실시간 시장 데이터를 분석 중입니다...'):
    data, history = get_market_all_data()

# 3. 마켓 스코어 계산 로직 (전일 점수 포함)
def calculate_score(tnx, krw, vix):
    score = 100
    if tnx > 4.5: score -= 30
    elif tnx > 4.0: score -= 15
    if krw > 1450: score -= 40
    elif krw > 1350: score -= 20
    if vix > 30: score -= 30
    elif vix > 20: score -= 10
    return max(0, score)

current_score = calculate_score(data['금리'], data['환율'], data['VIX'])
prev_score = calculate_score(data['금리_prev'], data['환율_prev'], data['VIX_prev'])
score_delta = current_score - prev_score

# 4. 상단 지표 레이아웃 (4분할)
st.subheader("📍 핵심 매크로 지표")
m1, m2, m3, m4 = st.columns(4)

with m1:
    d_tnx = data['금리'] - data['금리_prev']
    st.metric("🇺🇸 미 10년물 금리", f"{data['금리']:.2f}%", f"{d_tnx:.2f}%")
with m2:
    d_krw = data['환율'] - data['환율_prev']
    st.metric("💵 원/달러 환율", f"{data['환율']:,.1f}원", f"{d_krw:,.1f}원")
with m3:
    d_vix = data['VIX'] - data['VIX_prev']
    st.metric("📉 VIX 공포지수", f"{data['VIX']:.2f}", f"{d_vix:.2f}")
with m4:
    d_btc = data['비트코인'] - data['비트코인_prev']
    st.metric("🪙 비트코인", f"${data['비트코인']:,.0f}", f"${d_btc:,.0f}")

# 각 지표 영향도 안내 (접이식)
with st.expander("💡 지표 변화가 내 자산에 미치는 영향 확인하기"):
    c1, c2, c3 = st.columns(3)
    c1.write("**금리/환율 상승:** 주식 비중 축소 신호 🚨")
    c2.write("**VIX 하락:** 안정적인 추세 매매 가능 ✅")
    c3.write("**비트코인 상승:** 위험자산 선호 심리 강화 🚀")

st.markdown("---")

# 5. 메인 분석 섹션 (좌: 스코어/비중, 우: 차트)
left, right = st.columns([1, 1.2]) # 비율 조절

# 비중 및 상태 결정
if current_score >= 80:
    status, color = "✅ 적극 매수", "green"
    weights = {"주식": 75, "가상자산": 20, "현금": 5}
    advice = "시장 환경이 매우 우호적입니다. 공격적으로 수익을 극대화하세요."
elif current_score >= 50:
    status, color = "⚠️ 비중 중립", "orange"
    weights = {"주식": 50, "가상자산": 10, "현금": 40}
    advice = "일부 지표에 경계 신호가 있습니다. 핵심 우량주 위주로 방어하세요."
else:
    status, color = "🚨 위험 관리", "red"
    weights = {"주식": 20, "가상자산": 5, "현금": 75}
    advice = "리스크가 매우 높습니다. 현금을 확보하고 소나기를 피하십시오."

with left:
    st.subheader("🎯 마켓 익스포저 스코어")
    # 점수 변동률 표시 (Delta 사용)
    st.metric(label="현재 투자 점수", value=f"{current_score}점", delta=f"{score_delta}점 (전일 대비)")
    st.markdown(f"### 상태: :{color}[{status}]")
    st.progress(current_score / 100)
    st.info(f"**전문가 조언:** {advice}")
    
    st.markdown("#### 🛠 추천 자산 비중")
    st.table(pd.DataFrame([weights], index=["비중(%)"]))

with right:
    st.subheader("📈 시장 흐름 시각화")
    target = st.radio("보고 싶은 그래프", ["나스닥", "금리", "비트코인", "환율"], horizontal=True)
    st.line_chart(history[target], color="#29b5e8")

# 6. AI 리포트 섹션
st.markdown("---")
st.subheader("🤖 AI 전문가 맞춤형 전략 리포트")

def get_ai_report(m_data, score, delta, w):
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        client = OpenAI(api_key=api_key)
        prompt = f"""
        당신은 공격적 투자자를 위한 자산운용가입니다.
        현재 점수: {score}점 (전일 대비 {delta}점 변동)
        주요지표: 금리 {m_data['금리']:.2f}%, 환율 {m_data['환율']:.1f}원, VIX {m_data['VIX']:.2f}
        추천비중: 주식 {w['주식']}%, 가상자산 {w['가상자산']}%, 현금 {w['현금']}%
        현재 지표의 변화 흐름과 점수 변동의 의미를 포함하여 공격적 투자 전략을 3~4문장으로 요약해줘.
        """
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return response.choices.message.content
    except:
        return "AI 분석을 불러올 수 없습니다. 시스템 설정(API Key)을 확인해 주세요."

if st.button("AI 정밀 분석 리포트 생성", use_container_width=True):
    with st.spinner("지표 간 상관관계를 정밀 분석 중..."):
        report = get_ai_report(data, current_score, score_delta, weights)
        st.success(report)

st.caption("※ 본 데이터는 실시간 시장 수치를 바탕으로 산출되며, 최종 투자 책임은 본인에게 있습니다.")
