import streamlit as st
import yfinance as yf
import pandas as pd
from openai import OpenAI

# 1. 앱 페이지 설정 및 글자 크기 커스텀 (CSS)
st.set_page_config(page_title="공격적 투자 전략 대시보드", layout="wide")

st.markdown("""
    <style>
    /* 전체 기본 글자 크기 확대 */
    html, body, [class*="st-"] {
        font-size: 1.1rem;
    }
    /* 제목 및 강조 글자 크기 조정 */
    h1 { font-size: 2.5rem !important; }
    h2 { font-size: 2rem !important; }
    h3 { font-size: 1.7rem !important; }
    /* 메트릭(숫자) 글자 크기 확대 */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
    }
    /* 테이블 글자 크기 확대 */
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

with st.spinner('실시간 시장 분석 중...'):
    data, history = get_market_all_data()

# 3. 마켓 스코어 계산 로직
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

# 4. 상단 지표 레이아웃
st.subheader("📍 핵심 매크로 지표")
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("🇺🇸 미 10년물 금리", f"{data['금리']:.2f}%", f"{data['금리']-data['금리_prev']:.2f}%")
with m2: st.metric("💵 원/달러 환율", f"{data['환율']:,.1f}원", f"{data['환율']-data['환율_prev']:,.1f}원")
with m3: st.metric("📉 VIX 공포지수", f"{data['VIX']:.2f}", f"{data['VIX']-data['VIX_prev']:.2f}")
with m4: st.metric("🪙 비트코인", f"${data['비트코인']:,.0f}", f"${data['비트코인']-data['비트코인_prev']:,.0f}")

st.markdown("---")

# 5. 점수별 상세 포트폴리오 추천 로직
if current_score >= 80:
    status, color = "✅ 적극 매수 (Bullish)", "green"
    weights = {"주식": 75, "가상자산": 20, "현금": 5}
    portfolio = {
        "추천 섹터": "AI 반도체, 나스닥 레버리지, 성장주",
        "주요 종목 예시": "NVDA(엔비디아), TQQQ, 비트코인 알트코인 혼합",
        "운용 전략": "공격적 추세 추종 및 수익 극대화 전략"
    }
elif current_score >= 50:
    status, color = "⚠️ 비중 중립 (Neutral)", "orange"
    weights = {"주식": 50, "가상자산": 10, "현금": 40}
    portfolio = {
        "추천 섹터": "배당주, 대형 우량주, 방어주",
        "주요 종목 예시": "SCHD(배당ETF), AAPL(애플), 비트코인(BTC) 단일",
        "운용 전략": "변동성 대비를 위한 리밸런싱 및 관망"
    }
else:
    status, color = "🚨 위험 관리 (Bearish)", "red"
    weights = {"주식": 20, "가상자산": 5, "현금": 75}
    portfolio = {
        "추천 섹터": "초단기 채권, 금(Gold), 현금",
        "주요 종목 예시": "SHV(단기채), IAU(금), 파킹통장",
        "운용 전략": "자산 방어 및 저점 매수 기회 대기"
    }

# 6. 메인 분석 화면
left, right = st.columns([1, 1.2])

with left:
    st.subheader("🎯 마켓 스코어 리포트")
    st.metric(label="현재 투자 점수", value=f"{current_score}점", delta=f"{score_delta}점 (전일 대비)")
    st.markdown(f"### 상태: :{color}[{status}]")
    st.progress(current_score / 100)
    
    st.markdown("#### 🛠 추천 자산 비중")
    st.table(pd.DataFrame([weights], index=["비중(%)"]))
    
    st.markdown("#### 💡 AI 맞춤 포트폴리오 추천")
    for key, value in portfolio.items():
        st.write(f"**· {key}:** {value}")

with right:
    st.subheader("📈 시장 흐름 시각화")
    target = st.radio("보고 싶은 그래프", ["나스닥", "금리", "비트코인", "환율"], horizontal=True)
    st.line_chart(history[target], color="#29b5e8")

# 7. AI 리포트
st.markdown("---")
if st.button("🤖 AI 전문가 정밀 분석 리포트 생성", use_container_width=True):
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        prompt = f"""공격적 투자자 자산운용가로서 리포트 작성. 점수:{current_score}(변동:{score_delta}), 금리:{data['금리']:.2f}%, 환율:{data['환율']:.1f}원. 추천섹터:{portfolio['추천 섹터']}. 위 지표들이 왜 이런 포트폴리오를 만드는지 전문적이고 단호하게 3~4문장으로 설명해줘."""
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        st.success(response.choices.message.content)
    except:
        st.error("AI 분석 기능을 사용하려면 Secrets에 API Key를 등록해 주세요.")

st.caption("※ 본 정보는 투자 참고용이며 최종 책임은 본인에게 있습니다.")
