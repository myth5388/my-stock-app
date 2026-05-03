import streamlit as st
import yfinance as yf
import pandas as pd
from openai import OpenAI

# 1. 앱 설정 및 UI 스타일링
st.set_page_config(page_title="AI 4대 자산 전략 분석기", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="st-"] { font-size: 1.15rem; }
    [data-testid="stMetricValue"] { font-size: 2.3rem !important; font-weight: bold; }
    .stTable { font-size: 1.2rem !important; }
    .reason-box { background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #1E3A8A; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 AI 자산 점수 변동 분석 & 포트폴리오")
st.markdown("---")

# 2. 데이터 로드 (주식, 채권, 금, 환율 등)
@st.cache_data(ttl=3600)
def get_analysis_data():
    tickers = {
        "금리": "^TNX", "환율": "KRW=X", "VIX": "^VIX", 
        "나스닥": "^IXIC", "유가": "CL=F", "금시세": "GC=F", "채권": "TLT"
    }
    data = {}
    for name, symbol in tickers.items():
        t_obj = yf.Ticker(symbol)
        hist = t_obj.history(period="5d")
        if not hist.empty and len(hist) >= 2:
            data[name] = hist['Close'].iloc[-1]
            data[f"{name}_prev"] = hist['Close'].iloc[-2]
    return data

with st.spinner('시장 데이터를 정밀 분석 중...'):
    data = get_analysis_data()

# 3. 변동성 및 가중치 기반 점수 산정 알고리즘
def calculate_advanced_score(d):
    score = 100
    reasons = []
    
    # 지표별 변동률 및 점수 차감 로직
    # 1. 환율 (가중치 1.5)
    krw_chg = ((d['환율'] - d['환율_prev']) / d['환율_prev']) * 100
    if krw_chg > 0.5:
        penalty = 30 * 1.5
        score -= penalty
        reasons.append(f"🚩 **환율 급등({krw_chg:.2f}%):** 외국인 자금 이탈 압력이 거세졌습니다.")
    
    # 2. 금리 (가중치 1.2)
    tnx_chg = d['금리'] - d['금리_prev']
    if tnx_chg > 0.05:
        penalty = 20 * 1.2
        score -= penalty
        reasons.append(f"🚩 **금리 상승({tnx_chg:.2f}%p):** 채권 가격 하락 및 기술주 밸류에이션 부담이 커졌습니다.")
    
    # 3. 유가 (가중치 1.1)
    oil_chg = ((d['유가'] - d['유가_prev']) / d['유가_prev']) * 100
    if oil_chg > 2.0:
        penalty = 15 * 1.1
        score -= penalty
        reasons.append(f"🚩 **유가 급등({oil_chg:.2f}%):** 인플레이션 우려로 인해 시장의 비용 부담이 증가했습니다.")

    return max(0, score), reasons

# 현재 점수 및 전일 점수 계산
curr_score, curr_reasons = calculate_advanced_score(data)
# 전일 데이터로 이전 점수 가상 계산 (변동폭 표시용)
prev_data = {k.replace('_prev', ''): v for k, v in data.items() if '_prev' in k}
# 간단한 구현을 위해 여기서는 전일 대비 '변동' 자체에 집중합니다.

# 4. 상단 대시보드 (종합 점수 및 변동폭)
left_score, right_metrics = st.columns([1, 2])

with left_score:
    # 점수 변동폭 계산 (여기서는 예시로 변동 사유 유무에 따라 - 표시)
    score_delta = (curr_score - 100) # 100점 만점 기준 하락폭
    st.metric("🎯 종합 투자 스코어", f"{curr_score:.0f}점", f"{score_delta:.0f}점")
    
    if curr_score >= 80: st.success("상태: 적극 매수 ✅")
    elif curr_score >= 50: st.warning("상태: 비중 중립 ⚠️")
    else: st.error("상태: 위험 관리 🚨")

with right_metrics:
    m1, m2, m3 = st.columns(3)
    m1.metric("💵 환율", f"{data['환율']:,.1f}원", f"{data['환율']-data['환율_prev']:,.1f}원")
    m2.metric("🇺🇸 금리", f"{data['금리']:.2f}%", f"{data['금리']-data['금리_prev']:.2f}%")
    m3.metric("🛢️ 유가", f"${data['유가']:.1f}", f"{data['유가']-data['유가_prev']:.2f}")

st.divider()

# 5. 변동 이유 및 시장 영향 표시 섹션
st.subheader("🧐 점수 변동 이유와 시장 영향")
if curr_reasons:
    for r in curr_reasons:
        st.markdown(f"<div class='reason-box'>{r}</div>", unsafe_allow_html=True)
        st.write("") # 간격
else:
    st.success("현재 시장 지표가 안정적입니다. 점수 차감 요인이 없습니다.")

st.divider()

# 6. 추천 4대 자산 비중 (주식, 채권, 금, 현금)
st.subheader("📊 전략적 자산 배분 제안")
if curr_score >= 80: weights = [70, 15, 5, 10]
elif curr_score >= 50: weights = [45, 25, 10, 20]
else: weights = [20, 40, 20, 20]

c1, c2, c3, c4 = st.columns(4)
c1.metric("📈 주식", f"{weights[0]}%")
c2.metric("🏦 채권", f"{weights[1]}%")
c3.metric("✨ 금", f"{weights[2]}%")
c4.metric("💵 현금", f"{weights[3]}%")

# 7. AI 리포트
st.divider()
if st.button("🤖 AI 정밀 변동 분석 리포트 생성", use_container_width=True):
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        prompt = f"자산운용가로서 오늘 점수가 {curr_score}점으로 변한 이유와 시장에 미치는 영향을 분석해줘. 감점요인: {curr_reasons}. 공격적 투자자가 오늘 가장 조심해야 할 한 가지를 포함해 3문장 요약해줘."
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        st.info(res.choices.message.content)
    except:
        st.error("API 키를 확인하세요.")
