import streamlit as st
import yfinance as yf
import pandas as pd
from openai import OpenAI

# 1. 앱 페이지 설정
st.set_page_config(page_title="공격적 투자 전략 대시보드", layout="wide")
st.title("📊 오늘의 경제지표 & AI 포트폴리오 전략")
st.markdown("실시간 금리, 환율, VIX 및 비트코인을 분석하여 최적의 공격적 비중을 제안합니다.")

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

with st.spinner('시장 데이터를 불러오는 중...'):
    data, history = get_market_all_data()

# 3. 지표 상단 표시 및 영향도 설명
st.subheader("📍 핵심 지표 실시간 현황")
col1, col2, col3, col4 = st.columns(4)

with col1:
    d = data['금리'] - data['금리_prev']
    st.metric("🇺🇸 미 10년물 금리", f"{data['금리']:.2f}%", f"{d:.2f}%")
    with st.expander("영향도 보기"):
        st.write("**상승 시:** 기술주/성장주 하락 압력 증가 📉")
        st.write("**하락 시:** 유동성 공급으로 지수 상승 호재 📈")

with col2:
    d = data['환율'] - data['환율_prev']
    st.metric("💵 원/달러 환율", f"{data['환율']:,.1f}원", f"{d:,.1f}원")
    with st.expander("영향도 보기"):
        st.write("**상승 시:** 외국인 자금 이탈, 국장 하락 위험 🚨")
        st.write("**하락 시:** 외국인 매수 유입, 대형주 호재 ✅")

with col3:
    d = data['VIX'] - data['VIX_prev']
    st.metric("📉 VIX 공포지수", f"{data['VIX']:.2f}", f"{d:.2f}")
    with st.expander("영향도 보기"):
        st.write("**상승 시:** 시장 불안 증폭, 변동성 매매 유효 ⚡")
        st.write("**하락 시:** 시장 안정화, 추세 추종 유리 😊")

with col4:
    d = data['비트코인'] - data['비트코인_prev']
    st.metric("🪙 비트코인", f"${data['비트코인']:,.0f}", f"${d:,.0f}")
    with st.expander("영향도 보기"):
        st.write("**상승 시:** 위험자산 선호(Risk-on) 강화 🚀")
        st.write("**하락 시:** 유동성 위축 및 투심 악화 🧊")

st.divider()

# 4. 마켓 스코어 및 비중 산출 로직
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

# 비중 결정
if market_score >= 80:
    status, status_color = "✅ 적극 매수 구간", "green"
    weights = {"주식": 75, "가상자산": 20, "현금": 5}
    advice = "지표가 우호적입니다. 공격적으로 비중을 확대할 적기입니다!"
elif market_score >= 50:
    status, status_color = "⚠️ 비중 중립 구간", "orange"
    weights = {"주식": 50, "가상자산": 10, "현금": 40}
    advice = "일부 지표에 경고등이 켜졌습니다. 무리한 추격 매수보다는 관망이 필요합니다."
else:
    status, status_color = "🚨 위험 관리 구간", "red"
    weights = {"주식": 20, "가상자산": 5, "현금": 75}
    advice = "시장 환경이 매우 악화되었습니다. 현금 비중을 높여 자산을 방어하세요."

# 5. 분석 화면 레이아웃 (TypeError 해결: st.columns(2) 적용)
left, right = st.columns(2)

with left:
    st.subheader(f"🎯 마켓 스코어: :{status_color}[{market_score}점]")
    st.markdown(f"### **{status}**")
    st.info(advice)
    st.progress(market_score / 100)
    st.table(pd.DataFrame([weights], index=["추천 비중(%)"]))

with right:
    st.subheader("📈 지표 추이 및 흐름")
    chart_target = st.selectbox("그래프 선택", ["나스닥", "금리", "비트코인", "환율"])
    st.line_chart(history[chart_target])

# 6. AI 리포트 생성 섹션
st.divider()
st.subheader("🤖 AI 전문가의 한마디")

def get_ai_report(m_data, score, w):
    try:
        # Streamlit Secrets에서 API 키 가져오기
        api_key = st.secrets["OPENAI_API_KEY"]
        client = OpenAI(api_key=api_key)
        prompt = f"""
        당신은 공격적 투자자를 위한 자산운용가입니다. 
        미금리:{m_data['금리']:.2f}%, 환율:{m_data['환율']:.1f}원, VIX:{m_data['VIX']:.2f}, 점수:{score}
        추천비중: 주식 {w['주식']}%, 가상자산 {w['가상자산']}%, 현금 {w['현금']}%
        경제지표의 변화가 투자자의 자산에 미치는 구체적인 영향과 대응 전략을 3~4문장으로 요약해줘.
        """
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return response.choices.message.content
    except Exception as e:
        return f"AI 분석 서비스를 이용할 수 없습니다. (비밀 설정이나 API 키를 확인하세요)"

if st.button("AI 전략 리포트 생성하기"):
    with st.spinner("지표 간 상관관계를 분석 중입니다..."):
        report = get_ai_report(data, market_score, weights)
        st.success(report)

st.divider()
st.caption("※ 본 정보는 투자 참고용이며, 최종 투자 판단은 본인에게 있습니다.")
