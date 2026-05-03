import streamlit as st
import yfinance as yf
import pandas as pd
from openai import OpenAI

# 1. 앱 설정 및 가독성 개선 (글자 크기 확대)
st.set_page_config(page_title="공격적 투자 전략 대시보드", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="st-"] { font-size: 1.1rem; }
    h1 { font-size: 2.5rem !important; }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; }
    .stTable { font-size: 1.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 오늘의 경제지표 & AI 포트폴리오 전략")
st.markdown("---")

# 2. 데이터 로드 함수
@st.cache_data(ttl=3600)
def get_market_all_data():
    tickers = {"금리": "^TNX", "환율": "KRW=X", "VIX": "^VIX", "비트코인": "BTC-USD", "나스닥": "^IXIC"}
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

# 3. 마켓 스코어 및 비중 산출 로직 (함수화)
def get_weights_by_score(score):
    if score >= 80:
        return {"주식": 75, "가상자산": 20, "현금": 5}, "✅ 적극 매수", "green"
    elif score >= 50:
        return {"주식": 50, "가상자산": 10, "현금": 40}, "⚠️ 비중 중립", "orange"
    else:
        return {"주식": 20, "가상자산": 5, "현금": 75}, "🚨 위험 관리", "red"

def calculate_score(tnx, krw, vix):
    score = 100
    if tnx > 4.5: score -= 30
    elif tnx > 4.0: score -= 15
    if krw > 1450: score -= 40
    elif krw > 1350: score -= 20
    if vix > 30: score -= 30
    elif vix > 20: score -= 10
    return max(0, score)

# 점수 및 전일 대비 변동폭 계산
current_score = calculate_score(data['금리'], data['환율'], data['VIX'])
prev_score = calculate_score(data['금리_prev'], data['환율_prev'], data['VIX_prev'])
score_delta = current_score - prev_score

# 비중 및 비중 변동폭 계산
current_w, status, color = get_weights_by_score(current_score)
prev_w, _, _ = get_weights_by_score(prev_score)
w_delta = {k: current_w[k] - prev_w[k] for k in current_w}

# 4. 상단 지표 레이아웃
st.subheader("📍 핵심 매크로 지표")
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("🇺🇸 미 10년물 금리", f"{data['금리']:.2f}%", f"{data['금리']-data['금리_prev']:.2f}%")
with m2: st.metric("💵 원/달러 환율", f"{data['환율']:,.1f}원", f"{data['환율']-data['환율_prev']:,.1f}원")
with m3: st.metric("📉 VIX 공포지수", f"{data['VIX']:.2f}", f"{data['VIX']-data['VIX_prev']:.2f}")
with m4: st.metric("🪙 비트코인", f"${data['비트코인']:,.0f}", f"${data['비트코인']-data['비트코인_prev']:,.0f}")

st.divider()

# 5. 메인 분석 화면
left, right = st.columns([1, 1.2])

with left:
    st.subheader("🎯 마켓 스코어 리포트")
    st.metric(label="현재 투자 점수", value=f"{current_score}점", delta=f"{score_delta}점 (전일 대비)")
    st.markdown(f"### 상태: :{color}[{status}]")
    st.progress(current_score / 100)
    
    st.markdown("#### 📊 추천 포트폴리오 비중 (변동폭)")
    w_col1, w_col2, w_col3 = st.columns(3)
    w_col1.metric("📈 주식", f"{current_w['주식']}%", f"{w_delta['주식']}%")
    w_col2.metric("🪙 가상자산", f"{current_w['가상자산']}%", f"{w_delta['가상자산']}%")
    w_col3.metric("💵 현금", f"{current_w['현금']}%", f"{w_delta['현금']}%")

    st.markdown("#### 💡 상세 전략 제안")
    if current_score >= 80:
        st.write("· **추천 섹터:** AI 반도체, 나스닥 레버리지, 성장주")
        st.write("· **주요 종목:** NVDA, TQQQ, BTC")
    elif current_score >= 50:
        st.write("· **추천 섹터:** 배당주, 대형 우량주, 리밸런싱")
        st.write("· **주요 종목:** SCHD, AAPL, BTC")
    else:
        st.write("· **추천 섹터:** 초단기 채권, 금(Gold), 현금")
        st.write("· **주요 종목:** SHV, IAU, 파킹통장")

with right:
    st.subheader("📈 시장 흐름 시각화")
    target = st.radio("보고 싶은 그래프", ["나스닥", "금리", "비트코인", "환율"], horizontal=True)
    st.line_chart(history[target], color="#29b5e8")

# 6. AI 리포트
st.divider()
if st.button("🤖 AI 전문가 정밀 분석 리포트 생성", use_container_width=True):
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        prompt = f"투자자산운용가로서 리포트 작성. 점수:{current_score}(변동:{score_delta}). 비중변동: 주식({w_delta['주식']}%), 가상자산({w_delta['가상자산']}%), 현금({w_delta['현금']}%). 지표 변화가 왜 이런 비중 조절을 만들었는지 3~4문장으로 단호하게 설명해줘."
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        st.success(response.choices.message.content)
    except:
        st.error("AI 분석 기능을 사용하려면 Secrets에 API Key를 등록해 주세요.")

st.caption("※ 본 정보는 투자 참고용이며 최종 책임은 본인에게 있습니다.")
