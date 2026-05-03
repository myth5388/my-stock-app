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
    [data-testid="stMetricValue"] { font-size: 2.3rem !important; font-weight: bold; }
    .reason-box { background-color: #f8f9fa; padding: 18px; border-radius: 10px; border-left: 6px solid #1E3A8A; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 AI 전략적 자산 배분 & 실시간 시장 분석")
st.markdown("<p style='text-align: center;'>미국 나스닥 선물 및 주요주 등락 기반 통합 대시보드</p>", unsafe_allow_html=True)

# 2. 데이터 로드 함수 (매크로 지표 + 미국 주요주)
@st.cache_data(ttl=300) # 5분마다 갱신 (선물 데이터 반영)
def get_integrated_market_data():
    tickers = {
        "금리": "^TNX", "환율": "KRW=X", "VIX": "^VIX", "나스닥선물": "NQ=F",
        "유가": "CL=F", "금시세": "GC=F", "채권": "TLT",
        "AAPL": "AAPL", "NVDA": "NVDA", "TSLA": "TSLA", "MSFT": "MSFT"
    }
    data = {}
    for name, symbol in tickers.items():
        t_obj = yf.Ticker(symbol)
        hist = t_obj.history(period="5d")
        if not hist.empty and len(hist) >= 2:
            data[name] = hist['Close'].iloc[-1]
            data[f"{name}_prev"] = hist['Close'].iloc[-2]
    return data

with st.spinner('실시간 글로벌 시장 데이터를 동기화 중...'):
    market_data = get_integrated_market_data()

# 3. 가중치 및 변동률 기반 점수 산정
def calculate_comprehensive_score(d):
    score = 100
    reasons = []
    
    # 지표별 변동률 및 가중치 패널티
    # 1. 나스닥 선물 (실시간 심리, 가중치 1.2)
    nq_chg = ((d.get('나스닥선물',0) - d.get('나스닥선물_prev',0)) / d.get('나스닥선물_prev',1)) * 100
    if nq_chg < -1.0:
        score -= (20 * 1.2); reasons.append(f"📉 **나스닥 선물 급락({nq_chg:.2f}%):** 실시간 투자 심리 악화")
        
    # 2. 환율 (수급 지표, 가중치 1.5)
    krw_chg = ((d.get('환율',0) - d.get('환율_prev',0)) / d.get('환율_prev',1)) * 100
    if krw_chg > 0.5:
        score -= (30 * 1.5); reasons.append(f"💵 **환율 급변({krw_chg:.1f}%):** 외국인 자금 이탈 경보")
        
    # 3. 금리 (가중치 1.2)
    tnx_chg = d.get('금리',0) - d.get('금리_prev',0)
    if tnx_chg > 0.05:
        score -= (20 * 1.2); reasons.append(f"🇺🇸 **금리 상승({tnx_chg:.2f}%p):** 성장주 밸류에이션 부담")

    return max(0, score), reasons

curr_score, curr_reasons = calculate_comprehensive_score(market_data)
# 비중 결정 로직
if curr_score >= 80: status, color, weights = "✅ 적극 매수", "green", {"주식": 70, "채권": 15, "금": 5, "현금": 10}
elif curr_score >= 50: status, color, weights = "⚠️ 비중 중립", "orange", {"주식": 45, "채권": 25, "금": 10, "현금": 20}
else: status, color, weights = "🚨 위험 관리", "red", {"주식": 20, "채권": 40, "금": 20, "현금": 20}

# 4. 상단 지표 (나스닥 선물 포함)
st.subheader("📍 실시간 핵심 지표 현황")
m_cols = st.columns(5)
m_list = [("📊 나스닥 선물", '나스닥선물', "{:,.1f}"), ("💵 환율", '환율', "{:,.1f}원"), ("🇺🇸 금리", '금리', "{:.2f}%"), ("📉 VIX", 'VIX', "{:.2f}"), ("🛢️ 유가", '유가', "${:.1f}")]
for i, (label, key, fmt) in enumerate(m_list):
    v, p = market_data.get(key, 0), market_data.get(f"{key}_prev", 0)
    m_cols[i].metric(label, fmt.format(v), fmt.format(v-p))

st.divider()

# 5. 미국 주요주 분석 & 4대 자산 비중
col_left, col_right = st.columns([1, 1.3])

with col_left:
    st.subheader("🎯 통합 투자 스코어 리포트")
    st.metric("종합 점수", f"{curr_score:.0f}점", delta_color="normal")
    st.markdown(f"### 상태: :{color}[{status}]")
    st.progress(curr_score / 100)
    
    st.markdown("#### 📊 추천 자산 비중 (증감 반영)")
    w_cols = st.columns(4)
    for i, (label, key) in enumerate([("📈 주식", "주식"), ("🏦 채권", "채권"), ("✨ 금", "금"), ("💵 현금", "현금")]):
        w_cols[i].metric(label, f"{weights[key]}%")

with col_right:
    st.subheader("📈 멀티 타임프레임 차트")
    c1, c2 = st.columns(2)
    with c1: target = st.selectbox("지표 선택", ["나스닥선물", "금리", "환율", "유가", "금시세"])
    with c2: timeframe = st.radio("주기", ["5분봉", "일봉"], horizontal=True)
    
    ticker_map = {"나스닥선물": "NQ=F", "금리": "^TNX", "환율": "KRW=X", "유가": "CL=F", "금시세": "GC=F"}
    if timeframe == "5분봉":
        chart_data = yf.Ticker(ticker_map[target]).history(period="1d", interval="5m")['Close']
    else:
        chart_data = yf.Ticker(ticker_map[target]).history(period="1mo", interval="1d")['Close']
    st.line_chart(chart_data, color="#1E3A8A")

# 6. 미국 주요주 급변동 및 사유
st.divider()
st.subheader("🇺🇸 미 주요주 등락 및 비중 변경 사유")
u_cols = st.columns(4)
us_stocks = {"NVDA": "엔비디아", "TSLA": "테슬라", "AAPL": "애플", "MSFT": "마이크로소프트"}
for i, (ticker, name) in enumerate(us_stocks.items()):
    change = ((market_data[ticker] - market_data[f"{ticker}_prev"]) / market_data[f"{ticker}_prev"]) * 100
    with u_cols[i]:
        st.metric(name, f"${market_data[ticker]:,.1f}", f"{change:.2f}%")
        if abs(change) >= 2.0:
            with st.expander("🔍 국내 영향"):
                if ticker == "NVDA": st.write("⚙️ **반도체:** 하이닉스, 한미반도체 강세")
                elif ticker == "TSLA": st.write("🔋 **2차전지:** 에코프로 등 배터리 섹터 영향")
                else: st.write("💻 **IT/AI:** 국내 관련주 심리 동조화")

if curr_reasons:
    for r in curr_reasons: st.markdown(f"<div class='reason-box'>{r}</div>", unsafe_allow_html=True)

# 7. AI 리포트
st.divider()
if st.button("🤖 AI 전문가 통합 전략 리포트 생성", use_container_width=True):
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        prompt = f"자산운용가로서 리포트 작성. 점수:{curr_score}, 이유:{curr_reasons}. 미 나스닥 선물 실시간 흐름과 매크로 지표가 오늘 한국 시장에 줄 영향을 요약해줘."
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        st.info(res.choices.message.content)
    except: st.error("AI 기능 활성화를 위해 Secrets에 API Key를 등록하세요.")
