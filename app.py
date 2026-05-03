import streamlit as st
import yfinance as yf
import pandas as pd
from openai import OpenAI

# 1. 앱 설정 및 가독성 개선
st.set_page_config(page_title="AI 마켓 가중치 분석기", layout="wide")
st.markdown("<style>html, body, [class*='st-'] { font-size: 1.1rem; } [data-testid='stMetricValue'] { font-size: 2.2rem !important; font-weight: bold; }</style>", unsafe_allow_html=True)

st.title("🚀 AI 경제지표 가중치 분석 & 포트폴리오")
st.markdown("---")

# 2. 데이터 로드 함수 (유가, 금 추가)
@st.cache_data(ttl=3600)
def get_total_market_data():
    tickers = {
        "금리": "^TNX", "환율": "KRW=X", "VIX": "^VIX", "비트코인": "BTC-USD", 
        "나스닥": "^IXIC", "유가": "CL=F", "금시세": "GC=F"
    }
    current_data = {}
    history_data = pd.DataFrame()
    for name, symbol in tickers.items():
        t_obj = yf.Ticker(symbol)
        hist = t_obj.history(period="5d")
        if not hist.empty and len(hist) >= 2:
            current_data[name] = hist['Close'].iloc[-1]
            current_data[f"{name}_prev"] = hist['Close'].iloc[-2]
            if name in ["금리", "환율", "유가", "금시세"]:
                history_data[name] = t_obj.history(period="1mo")['Close']
    return current_data, history_data

with st.spinner('전 세계 시장 데이터를 정밀 분석 중...'):
    data, history = get_total_market_data()

# 3. 가중치 및 변동률 기반 점수 산정 로직
def calculate_weighted_score(d):
    score = 100
    impacts = {}
    
    # 지표별 변동률 및 가중치 설정
    # (변동률 * 가중치 만큼 점수 차감)
    def get_penalty(curr, prev, base_penalty, weight):
        change_pct = ((curr - prev) / prev) * 100
        return (base_penalty * weight) if change_pct > 1.0 else 0, abs(change_pct * weight)

    p_krw, i_krw = get_penalty(d['환율'], d['환율_prev'], 30, 1.5) # 환율 가중치 1.5
    p_oil, i_oil = get_penalty(d['유가'], d['유가_prev'], 20, 1.3) # 유가 가중치 1.3
    p_tnx, i_tnx = (20 * 1.2 if (d['금리']-d['금리_prev']) > 0.05 else 0), abs((d['금리']-d['금리_prev'])*100*1.2)
    p_gold, i_gold = get_penalty(d['금시세'], d['금시세_prev'], 10, 0.7) # 금 가중치 0.7

    score -= (p_krw + p_oil + p_tnx + p_gold)
    
    impacts = {"환율": i_krw, "유가": i_oil, "금리": i_tnx, "금시세": i_gold}
    top_indicator = max(impacts, key=impacts.get)
    
    return max(0, score), top_indicator

m_score, top_issue = calculate_weighted_score(data)

# 4. 상단 지표 레이아웃 (유가, 금 추가)
st.subheader(f"📍 현재 시장 지배 지표: :red[{top_issue}]")
m1, m2, m3, m4, m5, m6 = st.columns(6)
metrics = [
    ("🇺🇸 금리", '금리', "{:.2f}%"), ("💵 환율", '환율', "{:,.1f}원"), 
    ("📉 VIX", 'VIX', "{:.2f}"), ("🪙 비트코인", '비트코인', "${:,.0f}"),
    ("🛢️ 유가", '유가', "${:.1f}"), ("✨ 금시세", '금시세', "${:,.1f}")
]
cols = [m1, m2, m3, m4, m5, m6]
for i, (label, key, fmt) in enumerate(metrics):
    with cols[i]:
        v, p = data.get(key, 0), data.get(f"{key}_prev", 0)
        st.metric(label, fmt.format(v), fmt.format(v-p))

st.divider()

# 5. 메인 분석 및 포트폴리오
left, right = st.columns([1, 1.2])

if m_score >= 80: status, color, s_w, c_w, h_w = "✅ 적극 매수", "green", 75, 20, 5
elif m_score >= 50: status, color, s_w, c_w, h_w = "⚠️ 비중 중립", "orange", 50, 10, 40
else: status, color, s_w, c_w, h_w = "🚨 위험 관리", "red", 20, 5, 75

with left:
    st.subheader("🎯 가중치 적용 투자 스코어")
    st.metric("종합 점수", f"{m_score}점")
    st.markdown(f"### 상태: :{color}[{status}]")
    st.progress(m_score / 100)
    
    st.markdown("#### 📊 추천 자산 비중")
    c1, c2, c3 = st.columns(3)
    c1.metric("주식", f"{s_w}%")
    c2.metric("가상자산", f"{c_w}%")
    c3.metric("현금", f"{h_w}%")

with right:
    st.subheader("📈 시장 흐름 시각화")
    target = st.radio("그래프 선택", ["금리", "환율", "유가", "금시세"], horizontal=True)
    st.line_chart(history[target], color="#1E3A8A")

# 6. AI 리포트
st.divider()
if st.button("🤖 AI 전문가 가중치 분석 리포트 생성", use_container_width=True):
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        prompt = f"자산운용가로서 리포트 작성. 점수:{m_score}, 가장 큰 영향 지표:{top_issue}. 유가(${data['유가']:.1f})와 금시세(${data['금시세']:.1f})의 변동을 포함하여 공격적 투자자가 주의해야 할 점을 3문장으로 요약해줘."
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        st.success(res.choices.message.content)
    except:
        st.error("AI 기능을 위해 Secrets에 OPENAI_API_KEY를 등록하세요.")
