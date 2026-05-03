import streamlit as st
import yfinance as yf
import pandas as pd
from openai import OpenAI

# 1. 앱 설정 및 가독성 개선 (글자 크기 확대 CSS)
st.set_page_config(page_title="AI 전략적 자산배분 시스템", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="st-"] { font-size: 1.15rem; }
    h1 { font-size: 2.6rem !important; color: #1E3A8A; text-align: center; }
    [data-testid="stMetricValue"] { font-size: 2.4rem !important; font-weight: bold; }
    .reason-box { background-color: #f8f9fa; padding: 18px; border-radius: 10px; border-left: 6px solid #1E3A8A; margin-bottom: 15px; }
    .stTable { font-size: 1.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 AI 전략적 자산 배분 & 미국 종목 분석")
st.markdown("<p style='text-align: center;'>미국 주요주 등락 및 거시지표 가중치 분석 시스템</p>", unsafe_allow_html=True)
st.markdown("---")

# 2. 데이터 로드 함수 (매크로 지표 + 미국 주요주)
@st.cache_data(ttl=3600)
def get_final_market_data():
    tickers = {
        "금리": "^TNX", "환율": "KRW=X", "VIX": "^VIX", 
        "나스닥": "^IXIC", "유가": "CL=F", "금시세": "GC=F",
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
            if name in ["금리", "환율", "유가", "금시세", "나스닥"]:
                history_data[name] = t_obj.history(period="1mo")['Close']
    return current_data, history_data

with st.spinner('글로벌 시장 및 종목 데이터를 정밀 분석 중...'):
    data, history = get_final_market_data()

# 3. 전략적 자산 배분 로직
def get_asset_strategy(score):
    if score >= 80:
        return {"주식": 70, "채권": 15, "금": 5, "현금": 10}, "✅ 적극 매수", "green"
    elif score >= 50:
        return {"주식": 45, "채권": 25, "금": 10, "현금": 20}, "⚠️ 비중 중립", "orange"
    else:
        return {"주식": 20, "채권": 40, "금": 20, "현금": 20}, "🚨 위험 관리", "red"

# 4. 변동률 및 가중치 기반 점수 산정
def calculate_advanced_score(d):
    score = 100
    reasons = []
    # 환율(1.5x)
    krw_chg = ((d.get('환율',0) - d.get('환율_prev',0)) / d.get('환율_prev',1)) * 100
    if krw_chg > 0.5:
        score -= (30 * 1.5); reasons.append(f"💵 **환율 급변({krw_chg:.1f}%):** 외인 수급 악화 우려")
    # 금리(1.2x)
    tnx_chg = d.get('금리',0) - d.get('금리_prev',0)
    if tnx_chg > 0.05:
        score -= (20 * 1.2); reasons.append(f"🇺🇸 **금리 상승({tnx_chg:.2f}%p):** 기술주 평가 가치 하락")
    # 유가(1.1x)
    oil_chg = ((d.get('유가',0) - d.get('유가_prev',0)) / d.get('유가_prev',1)) * 100
    if oil_chg > 2.0:
        score -= (15 * 1.1); reasons.append(f"🛢️ **유가 급등({oil_chg:.1f}%):** 인플레이션 및 비용 부담 증가")
    return max(0, score), reasons

curr_score, curr_reasons = calculate_advanced_score(data)
prev_score = 100
score_delta = curr_score - prev_score
curr_w, status, color = get_asset_strategy(curr_score)
prev_w, _, _ = get_asset_strategy(prev_score)

# 5. 상단 매크로 지표 현황
st.subheader("📍 핵심 매크로 지표")
m_cols = st.columns(5)
m_list = [("🇺🇸 금리", '금리', "{:.2f}%"), ("💵 환율", '환율', "{:,.1f}원"), ("📉 VIX", 'VIX', "{:.2f}"), ("🛢️ 유가", '유가', "${:.1f}"), ("✨ 금시세", '금시세', "${:,.1f}")]
for i, (label, key, fmt) in enumerate(m_list):
    with m_cols[i]:
        v, p = data.get(key, 0), data.get(f"{key}_prev", 0)
        st.metric(label, fmt.format(v), fmt.format(v-p))

st.divider()

# 6. 미국 주요종목 등락 및 국장 영향
st.subheader("🇺🇸 전일 미 주요주 등락 및 국장 영향")
us_stocks = {"AAPL": "애플", "NVDA": "엔비디아", "TSLA": "테슬라", "MSFT": "마이크로소프트"}
u_cols = st.columns(len(us_stocks))
for i, (ticker, name) in enumerate(us_stocks.items()):
    if ticker in data:
        change = ((data[ticker] - data[f"{ticker}_prev"]) / data[f"{ticker}_prev"]) * 100
        with u_cols[i]:
            st.metric(name, f"${data[ticker]:,.1f}", f"{change:.2f}%")
            if abs(change) >= 2.0:
                with st.expander("🔍 국내 영향"):
                    if ticker == "NVDA": st.write("⚙️ **반도체:** 하이닉스, 한미반도체 강세 예상")
                    elif ticker == "TSLA": st.write("🔋 **2차전지:** LG엔솔, 에코프로 수급 영향")
                    elif ticker == "AAPL": st.write("📱 **IT부품:** LG이노텍, 비에이치 동조화")
                    else: st.write("💻 **소프트웨어/AI:** 관련주 심리 영향")

st.divider()

# 7. 전략적 자산 배분 (좌: 점수/비중, 우: 그래프)
left, right = st.columns([1, 1.2])
with left:
    st.subheader("🎯 통합 투자 스코어")
    st.metric("종합 점수", f"{curr_score:.0f}점", f"{score_delta:.0f}점")
    st.markdown(f"### 상태: :{color}[{status}]")
    st.progress(curr_score / 100)
    st.markdown("#### 📊 추천 자산 비중 (전일비 증감)")
    w_cols = st.columns(4)
    for i, (label, key) in enumerate([("📈 주식", "주식"), ("🏦 채권", "채권"), ("✨ 금", "금"), ("💵 현금", "현금")]):
        diff = curr_w[key] - prev_w[key]
        w_cols[i].metric(label, f"{curr_w[key]}%", f"{diff:+} %p")

with right:
    st.subheader("📈 시장 흐름 시각화")
    chart_target = st.radio("분석 그래프", ["나스닥", "금리", "환율", "유가", "금시세"], horizontal=True)
    st.line_chart(history[chart_target], color="#1E3A8A")

# 8. 사유 및 AI 리포트
st.divider()
st.subheader("🧐 비중 변경 핵심 사유")
if curr_reasons:
    for reason in curr_reasons: st.markdown(f"<div class='reason-box'>{reason}</div>", unsafe_allow_html=True)
else: st.success("지표가 안정적입니다. 기존 전략을 유지하십시오.")

if st.button("🤖 AI 전문가 정밀 전략 리포트 생성", use_container_width=True):
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        prompt = f"자산운용가 리포트. 점수:{curr_score}, 사유:{curr_reasons}. 미 주요주 등락과 매크로 지표가 오늘 한국 시장에 줄 영향을 3문장 요약해줘."
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        st.info(res.choices.message.content)
    except: st.error("AI 기능을 위해 Secrets에 OPENAI_API_KEY를 등록하세요.")
