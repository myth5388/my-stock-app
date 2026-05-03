import streamlit as st
import yfinance as yf
import pandas as pd
from openai import OpenAI

# 1. 앱 설정 및 가독성 개선 (글자 크기 확대)
st.set_page_config(page_title="AI 투자 전략 대시보드", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="st-"] { font-size: 1.15rem; }
    h1 { font-size: 2.6rem !important; color: #1E3A8A; text-align: center; }
    [data-testid="stMetricValue"] { font-size: 2.3rem !important; font-weight: bold; }
    .stTable { font-size: 1.25rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 AI 경제지표 분석 & 포트폴리오 전략")
st.markdown("<p style='text-align: center;'>실시간 데이터 기반 공격적 자산 배분 가이드</p>", unsafe_allow_html=True)
st.markdown("---")

# 2. 데이터 로드 함수 (미국 주요주 티커 포함)
@st.cache_data(ttl=3600)
def get_market_full_data():
    tickers = {
        "금리": "^TNX", "환율": "KRW=X", "VIX": "^VIX", "비트코인": "BTC-USD", "나스닥": "^IXIC",
        "AAPL": "AAPL", "NVDA": "NVDA", "TSLA": "TSLA", "MSFT": "MSFT"
    }
    current_data = {}
    history_data = pd.DataFrame()
    
    for name, symbol in tickers.items():
        ticker_obj = yf.Ticker(symbol)
        hist = ticker_obj.history(period="5d")
        if not hist.empty and len(hist) >= 2:
            current_data[name] = hist['Close'].iloc[-1]
            current_data[f"{name}_prev"] = hist['Close'].iloc[-2]
            if name in ["금리", "나스닥", "비트코인", "환율"]:
                history_data[name] = ticker_obj.history(period="1mo")['Close']
    return current_data, history_data

with st.spinner('실시간 시장 데이터를 분석 중입니다...'):
    data, history = get_market_full_data()

# 3. 마켓 스코어 산출 로직
def calculate_score(tnx, krw, vix):
    score = 100
    if tnx > 4.5: score -= 30
    elif tnx > 4.0: score -= 15
    if krw > 1450: score -= 40
    elif krw > 1350: score -= 20
    if vix > 25: score -= 25
    elif vix > 20: score -= 10
    return max(0, score)

current_score = calculate_score(data.get('금리', 0), data.get('환율', 0), data.get('VIX', 0))
prev_score = calculate_score(data.get('금리_prev', 0), data.get('환율_prev', 0), data.get('VIX_prev', 0))
score_delta = current_score - prev_score

# 4. 상단 매크로 지표 레이아웃 (안전한 포맷팅 적용)
st.subheader("📍 핵심 매크로 지표")
m1, m2, m3, m4 = st.columns(4)

with m1:
    v, p = data.get('금리', 0), data.get('금리_prev', 0)
    st.metric("🇺🇸 미 10년물 금리", f"{v:.2f}%", f"{v-p:.2f}%")
with m2:
    v, p = data.get('환율', 0), data.get('환율_prev', 0)
    st.metric("💵 원/달러 환율", f"{v:,.1f}원", f"{v-p:,.1f}원")
with m3:
    v, p = data.get('VIX', 0), data.get('VIX_prev', 0)
    st.metric("📉 VIX 공포지수", f"{v:.2f}", f"{v-p:.2f}")
with m4:
    v, p = data.get('비트코인', 0), data.get('비트코인_prev', 0)
    st.metric("🪙 비트코인", f"${v:,.0f}", f"${v-p:,.0f}")

st.divider()

# 5. 미국 대장주 분석 및 국장 영향
st.subheader("🇺🇸 전일 미 주요주 변동 및 국장 영향")
us_stocks = {"AAPL": "애플", "NVDA": "엔비디아", "TSLA": "테슬라", "MSFT": "마이크로소프트"}
movers_cols = st.columns(len(us_stocks))

for i, (ticker, name) in enumerate(us_stocks.items()):
    if ticker in data and f"{ticker}_prev" in data:
        curr, prev = data[ticker], data[f"{ticker}_prev"]
        change = ((curr - prev) / prev) * 100
        with movers_cols[i]:
            st.metric(name, f"${curr:,.1f}", f"{change:.2f}%")
            if abs(change) >= 2.0:
                with st.expander("🔍 국내 영향"):
                    if ticker == "AAPL": st.write("📱 **LG이노텍, 비에이치** 등 수혜")
                    elif ticker == "NVDA": st.write("⚙️ **SK하이닉스, 한미반도체** 등 강세")
                    elif ticker == "TSLA": st.write("🔋 **2차전지 섹터** 심리적 영향")
                    elif ticker == "MSFT": st.write("☁️ **AI 소프트웨어** 수급 영향")

st.divider()

# 6. 메인 분석 및 포트폴리오
left, right = st.columns([1, 1.2])

if current_score >= 80:
    status, color, s_w, c_w, h_w = "✅ 적극 매수", "green", 75, 20, 5
    advice = "AI 반도체 및 나스닥 레버리지 전략이 유효합니다."
elif current_score >= 50:
    status, color, s_w, c_w, h_w = "⚠️ 비중 중립", "orange", 50, 10, 40
    advice = "배당주 및 대형 우량주로 리밸런싱을 추천합니다."
else:
    status, color, s_w, c_w, h_w = "🚨 위험 관리", "red", 20, 5, 75
    advice = "단기 채권 및 금(Gold) 비중을 늘려 자산을 보호하세요."

with left:
    st.subheader("🎯 투자 스코어 리포트")
    st.metric("현재 점수", f"{current_score}점", f"{score_delta}점")
    st.markdown(f"### 상태: :{color}[{status}]")
    st.progress(current_score / 100)
    st.info(f"**전략:** {advice}")
    
    st.markdown("#### 📊 추천 자산 비중")
    c1, c2, c3 = st.columns(3)
    c1.metric("주식", f"{s_w}%")
    c2.metric("가상자산", f"{c_w}%")
    c3.metric("현금", f"{h_w}%")

with right:
    st.subheader("📈 시장 흐름 시각화")
    target = st.radio("그래프 선택", ["나스닥", "금리", "비트코인", "환율"], horizontal=True)
    if target in history:
        st.line_chart(history[target], color="#1E3A8A")

# 7. AI 리포트
st.divider()
if st.button("🤖 AI 전문가 정밀 분석 리포트 생성", use_container_width=True):
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        prompt = f"투자운용가로서 리포트 작성. 점수:{current_score}, 환율:{data.get('환율', 0):.1f}원. 미국 대장주 흐름과 매크로 지표가 오늘 한국 시장에 줄 영향을 3~4문장으로 단호하게 요약해줘."
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        st.success(res.choices.message.content)
    except:
        st.error("Secrets에 OPENAI_API_KEY를 등록해 주세요.")

st.caption("※ 본 정보는 참고용이며 최종 투자 책임은 본인에게 있습니다.")
