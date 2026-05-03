import streamlit as st
import yfinance as yf
import pandas as pd
from openai import OpenAI

# 1. 앱 페이지 설정 및 가독성 개선
st.set_page_config(page_title="공격적 투자 전략 대시보드", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="st-"] { font-size: 1.15rem; }
    h1 { font-size: 2.6rem !important; color: #1E3A8A; }
    [data-testid="stMetricValue"] { font-size: 2.3rem !important; font-weight: bold; }
    .stTable { font-size: 1.25rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 AI 경제지표 분석 & 포트폴리오 전략")
st.markdown("---")

# 2. 데이터 로드 함수 (미국 주요주 티커를 정확히 포함)
@st.cache_data(ttl=3600)
def get_market_full_data():
    # 모든 티커를 여기에 정의합니다 (KeyError 방지)
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
            # 차트용 데이터 (매크로 지표만)
            if name in ["금리", "나스닥", "비트코인", "환율"]:
                history_data[name] = ticker_obj.history(period="1mo")['Close']
    return current_data, history_data

with st.spinner('실시간 시장 데이터를 분석 중입니다...'):
    data, history = get_market_full_data()

# 3. 마켓 스코어 산출
def calculate_score(tnx, krw, vix):
    score = 100
    if tnx > 4.5: score -= 30
    if krw > 1450: score -= 40
    if vix > 25: score -= 25
    return max(0, score)

current_score = calculate_score(data.get('금리', 0), data.get('환율', 0), data.get('VIX', 0))
prev_score = calculate_score(data.get('금리_prev', 0), data.get('환율_prev', 0), data.get('VIX_prev', 0))
score_delta = current_score - prev_score

# 4. 상단 매크로 지표 레이아웃
st.subheader("📍 핵심 매크로 지표")
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("🇺🇸 미 10년물 금리", f"{data.get('금리', 0):.2f}%", f"{data.get('금리', 0)-data.get('금리_prev', 0):.2f}%")
with m2: st.metric("💵 원/달러 환율", f"{data.get('환율', 0):,1f}원", f"{data.get('환율', 0)-data.get('환율_prev', 0):,1f}원")
with m3: st.metric("📉 VIX 공포지수", f"{data.get('VIX', 0):.2f}", f"{data.get('VIX', 0)-data.get('VIX_prev', 0):.2f}")
with m4: st.metric("🪙 비트코인", f"${data.get('비트코인', 0):,.0f}", f"${data.get('비트코인', 0)-data.get('비트코인_prev', 0):,.0f}")

st.divider()

# 5. 미국 대장주 급변동 분석 (KeyError 방지 로직 적용)
st.subheader("🇺🇸 전일 미 주요주 급변동 및 국장 영향")
us_stocks = {"AAPL": "애플", "NVDA": "엔비디아", "TSLA": "테슬라", "MSFT": "마이크로소프트"}
movers_cols = st.columns(len(us_stocks))

for i, (ticker, name) in enumerate(us_stocks.items()):
    # 데이터 존재 여부 확인 후 계산
    if ticker in data and f"{ticker}_prev" in data:
        curr_val = data[ticker]
        prev_val = data[f"{ticker}_prev"]
        change = ((curr_val - prev_val) / prev_val) * 100
        
        with movers_cols[i]:
            st.metric(name, f"${curr_val:,.1f}", f"{change:.2f}%")
            if abs(change) >= 2.0:
                with st.expander("🔍 국내 영향 분석"):
                    if ticker == "AAPL": st.write("📱 **LG이노텍, 비에이치** 등 부품주 동조화 예상")
                    elif ticker == "NVDA": st.write("⚙️ **SK하이닉스, 한미반도체** 등 반도체주 강세 가능성")
                    elif ticker == "TSLA": st.write("🔋 **LG엔솔, 에코프로** 등 2차전지 심리적 영향")
                    elif ticker == "MSFT": st.write("☁️ **AI 소프트웨어 섹터** 수급 영향 예상")
    else:
        with movers_cols[i]:
            st.write(f"{name} 데이터 로드 실패")

st.divider()

# 6. 메인 포트폴리오 분석
left, right = st.columns([1, 1.2])

if current_score >= 80:
    status, color, s_w, c_w, h_w = "✅ 적극 매수", "green", 75, 20, 5
elif current_score >= 50:
    status, color, s_w, c_w, h_w = "⚠️ 비중 중립", "orange", 50, 10, 40
else:
    status, color, s_w, c_w, h_w = "🚨 위험 관리", "red", 20, 5, 75

with left:
    st.subheader("🎯 마켓 익스포저")
    st.metric("투자 점수", f"{current_score}점", f"{score_delta}점")
    st.markdown(f"### 상태: :{color}[{status}]")
    st.progress(current_score / 100)
    
    st.markdown("#### 📊 추천 비중 및 변동")
    c1, c2, c3 = st.columns(3)
    c1.metric("주식", f"{s_w}%")
    c2.metric("가상자산", f"{c_w}%")
    c3.metric("현금", f"{h_w}%")

with right:
    st.subheader("📈 주요 지표 추이")
    target = st.radio("그래프 선택", ["나스닥", "금리", "비트코인", "환율"], horizontal=True)
    if target in history:
        st.line_chart(history[target])

# 7. AI 리포트 생성
st.divider()
if st.button("🤖 AI 전문가 정밀 분석 리포트 생성", use_container_width=True):
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        prompt = f"투자자산운용가로서 분석. 점수:{current_score}, 환율:{data.get('환율', 0):.1f}원. 미국 대장주 흐름과 매크로 지표가 오늘 한국 시장에 줄 영향을 3~4문장으로 요약해줘."
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        st.success(res.choices.message.content)
    except:
        st.error("AI 기능을 위해 Secrets에 OPENAI_API_KEY를 등록하세요.")
