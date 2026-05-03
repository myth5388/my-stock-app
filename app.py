import streamlit as st
import yfinance as yf
import pandas as pd
from openai import OpenAI

# 1. 앱 설정
st.set_page_config(page_title="AI 4대 자산(채권형) 전략 대시보드", layout="wide")
st.title("🚀 주식·채권·금·현금 4대 자산 포트폴리오")
st.markdown("---")

# 2. 데이터 로드 (가상자산 제외, 채권 지표 유지)
@st.cache_data(ttl=3600)
def get_bond_market_data():
    tickers = {
        "금리": "^TNX", "환율": "KRW=X", "VIX": "^VIX", 
        "나스닥": "^IXIC", "유가": "CL=F", "금시세": "GC=F",
        "채권ETF": "TLT"  # 미국 20년+ 국채 ETF를 채권 지표로 활용
    }
    data = {}
    history = pd.DataFrame()
    for name, symbol in tickers.items():
        t_obj = yf.Ticker(symbol)
        hist = t_obj.history(period="5d")
        if not hist.empty and len(hist) >= 2:
            data[name] = hist['Close'].iloc[-1]
            data[f"{name}_prev"] = hist['Close'].iloc[-2]
            if name in ["금리", "환율", "유가", "금시세", "채권ETF"]:
                history[name] = t_obj.history(period="1mo")['Close']
    return data, history

with st.spinner('글로벌 거시 지표 및 채권 데이터를 분석 중...'):
    data, history = get_bond_market_data()

# 3. 가중치 기반 점수 산정
def calculate_bond_strategy_score(d):
    score = 100
    # 환율(1.5), 금리(1.2), 유가(1.1) 가중치 적용
    if ((d['환율']-d['환율_prev'])/d['환율_prev'])*100 > 0.5: score -= 30 * 1.5
    if (d['금리']-d['금리_prev']) > 0.05: score -= 20 * 1.2
    if ((d['유가']-d['유가_prev'])/d['유가_prev'])*100 > 2.0: score -= 15 * 1.1
    return max(0, score)

m_score = calculate_bond_strategy_score(data)

# 4. 상단 지표 레이아웃
st.subheader("📍 실시간 매크로 & 채권 지표")
m1, m2, m3, m4, m5, m6 = st.columns(6)
metrics_info = [
    ("🇺🇸 10년물 금리", '금리', "{:.2f}%"), ("💵 환율", '환율', "{:,.1f}원"), 
    ("📉 VIX", 'VIX', "{:.2f}"), ("🏦 채권(TLT)", '채권ETF', "${:.1f}"),
    ("🛢️ 유가", '유가', "${:.1f}"), ("✨ 금시세", '금시세', "${:,.1f}")
]
cols = [m1, m2, m3, m4, m5, m6]
for i, (label, key, fmt) in enumerate(metrics_info):
    with cols[i]:
        v, p = data.get(key, 0), data.get(f"{key}_prev", 0)
        st.metric(label, fmt.format(v), fmt.format(v-p))

st.divider()

# 5. 비중 결정 및 시각화
if m_score >= 80:
    status, color = "✅ 적극 매수", "green"
    weights = {"주식": 70, "채권": 15, "금": 5, "현금": 10}
elif m_score >= 50:
    status, color = "⚠️ 비중 중립", "orange"
    weights = {"주식": 45, "채권": 25, "금": 10, "현금": 20}
else:
    status, color = "🚨 위험 관리", "red"
    weights = {"주식": 20, "채권": 40, "금": 20, "현금": 20}

left, right = st.columns([1, 1.2])

with left:
    st.subheader("🎯 전략 통합 스코어")
    st.metric("종합 점수", f"{m_score:.0f}점")
    st.markdown(f"### 상태: :{color}[{status}]")
    st.progress(m_score / 100)
    
    st.markdown("#### 📊 추천 4대 자산 비중")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("주식", f"{weights['주식']}%")
    c2.metric("채권", f"{weights['채권']}%")
    c3.metric("금", f"{weights['금']}%")
    c4.metric("현금", f"{weights['현금']}%")

with right:
    st.subheader("📈 자산 흐름 차트")
    target = st.radio("그래프 선택", ["금리", "환율", "채권ETF", "금시세"], horizontal=True)
    st.line_chart(history[target], color="#1E3A8A")

# 6. AI 리포트
st.divider()
if st.button("🤖 AI 채권형 자산 전략 리포트 생성", use_container_width=True):
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        prompt = f"자산운용가 리포트. 점수:{m_score:.0f}. 추천비중: 주식{weights['주식']}%, 채권{weights['채권']}%, 금{weights['금']}%, 현금{weights['현금']}%.\n금리 변동에 따라 채권(Bond) 비중을 조절한 이유와 금리 인하기/인상기별 채권 투자 전략을 3문장으로 설명해줘."
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        st.success(res.choices.message.content)
    except:
        st.error("OpenAI API 키를 등록하세요.")
