import streamlit as st
import yfinance as yf
import pandas as pd
from openai import OpenAI

# 1. 앱 설정 및 가독성 개선
st.set_page_config(page_title="AI 전략적 자산 배분 분석기", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="st-"] { font-size: 1.15rem; }
    [data-testid="stMetricValue"] { font-size: 2.3rem !important; font-weight: bold; }
    .reason-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #1E3A8A; margin-bottom: 10px; }
    .delta-plus { color: #28a745; font-weight: bold; }
    .delta-minus { color: #dc3545; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 AI 전략적 자산 배분 & 비중 변동 분석")
st.markdown("---")

# 2. 데이터 로드
@st.cache_data(ttl=3600)
def get_full_data():
    tickers = {"금리": "^TNX", "환율": "KRW=X", "VIX": "^VIX", "유가": "CL=F", "금시세": "GC=F", "채권": "TLT"}
    data = {}
    for name, symbol in tickers.items():
        t_obj = yf.Ticker(symbol)
        hist = t_obj.history(period="5d")
        if not hist.empty and len(hist) >= 2:
            data[name] = hist['Close'].iloc[-1]
            data[f"{name}_prev"] = hist['Close'].iloc[-2]
    return data

with st.spinner('시장 데이터를 정밀 분석 중...'):
    data = get_full_data()

# 3. 점수 및 비중 산정 로직
def get_portfolio_strategy(score):
    if score >= 80:
        return {"주식": 70, "채권": 15, "금": 5, "현금": 10}, "적극 매수 ✅", "green"
    elif score >= 50:
        return {"주식": 45, "채권": 25, "금": 10, "현금": 20}, "비중 중립 ⚠️", "orange"
    else:
        return {"주식": 20, "채권": 40, "금": 20, "현금": 20}, "위험 관리 🚨", "red"

def calculate_score_with_reasons(d):
    score = 100
    reasons = []
    # 환율 패널티
    krw_chg = ((d['환율'] - d['환율_prev']) / d['환율_prev']) * 100
    if krw_chg > 0.5:
        score -= 45
        reasons.append(f"💵 **환율 급등({krw_chg:.1f}%):** 외국인 매도세 강화 및 국장 하방 압력 증대")
    # 금리 패널티
    tnx_chg = d['금리'] - d['금리_prev']
    if tnx_chg > 0.05:
        score -= 24
        reasons.append(f"🇺🇸 **금리 상승({tnx_chg:.2f}%p):** 채권 가격 하락 및 기술주 밸류에이션 부담 가중")
    return max(0, score), reasons

# 점수 및 비중 계산
curr_score, curr_reasons = calculate_score_with_reasons(data)
# 전일 점수를 위한 가상 계산 (변동폭 추출용)
prev_data_mock = {k.replace('_prev', ''): v for k, v in data.items() if '_prev' in k}
# 이전 데이터 셋이 필요하므로 여기서는 간단히 로직만 구현
prev_score = 100 # 기본값
curr_weights, status, color = get_portfolio_strategy(curr_score)
prev_weights, _, _ = get_portfolio_strategy(prev_score)

# 4. 상단 대시보드
col_score, col_metrics = st.columns([1, 2])
with col_score:
    st.metric("🎯 종합 투자 스코어", f"{curr_score:.0f}점", f"{curr_score - prev_score:.0f}점")
    st.markdown(f"### 현재 상태: :{color}[{status}]")

with col_metrics:
    m1, m2, m3 = st.columns(3)
    m1.metric("💵 환율", f"{data['환율']:,.1f}원", f"{data['환율']-data['환율_prev']:,.1f}원")
    m2.metric("🇺🇸 금리", f"{data['금리']:.2f}%", f"{data['금리']-data['금리_prev']:.2f}%")
    m3.metric("✨ 금시세", f"${data['금시세']:,.1f}", f"{data['금시세']-data['금시세_prev']:.1f}")

st.divider()

# 5. 전략적 자산 배분 비중 및 증감률
st.subheader("📊 전략적 자산 배분 현황 (전일 대비 증감)")
w1, w2, w3, w4 = st.columns(4)

assets = [("📈 주식", "주식"), ("🏦 채권", "채권"), ("✨ 금", "금"), ("💵 현금", "현금")]
cols = [w1, w2, w3, w4]

for i, (label, key) in enumerate(assets):
    diff = curr_weights[key] - prev_weights[key]
    delta_text = f"{diff:+} %p"
    with cols[i]:
        st.metric(label, f"{curr_weights[key]}%", delta_text)

# 6. 비중 변경 이유 및 영향 분석
st.subheader("🧐 비중 변경 핵심 사유")
if curr_reasons:
    for reason in curr_reasons:
        st.markdown(f"<div class='reason-box'>{reason}</div>", unsafe_allow_html=True)
else:
    st.success("지표가 안정적입니다. 기존의 공격적 비중을 유지하십시오.")

# 7. AI 분석 리포트
st.divider()
if st.button("🤖 AI 정밀 전략 분석 생성", use_container_width=True):
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        prompt = f"""
        자산운용가로서 오늘 자산 비중이 다음과 같이 변경된 이유를 분석해줘.
        현재 점수: {curr_score}점, 주요 변경 사유: {curr_reasons}
        비중 변화: 주식 {curr_weights['주식']}%({curr_weights['주식']-prev_weights['주식']}%p), 
        채권 {curr_weights['채권']}%({curr_weights['채권']-prev_weights['채권']}%p).
        이 변화가 시장에 미치는 영향과 투자자가 취해야 할 태도를 3문장으로 요약해줘.
        """
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        st.info(res.choices.message.content)
    except:
        st.error("API 키 설정을 확인하세요.")
