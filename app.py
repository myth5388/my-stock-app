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

st.title("🎯 AI 전략적 자산 배분 & 포트폴리오")
st.markdown("<p style='text-align: center;'>거시지표 변동률 기반 실시간 비중 조절 시스템</p>", unsafe_allow_html=True)
st.markdown("---")

# 2. 데이터 로드 함수 (매크로 7대 지표)
@st.cache_data(ttl=3600)
def get_final_market_data():
    tickers = {
        "금리": "^TNX", "환율": "KRW=X", "VIX": "^VIX", 
        "나스닥": "^IXIC", "유가": "CL=F", "금시세": "GC=F", "채권": "TLT"
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

with st.spinner('글로벌 시장 데이터를 정밀 분석 중...'):
    data, history = get_final_market_data()

# 3. 전략적 자산 배분 로직 (점수대별 비중)
def get_asset_strategy(score):
    if score >= 80: # 적극 매수
        return {"주식": 70, "채권": 15, "금": 5, "현금": 10}, "✅ 적극 매수", "green"
    elif score >= 50: # 비중 중립
        return {"주식": 45, "채권": 25, "금": 10, "현금": 20}, "⚠️ 비중 중립", "orange"
    else: # 위험 관리
        return {"주식": 20, "채권": 40, "금": 20, "현금": 20}, "🚨 위험 관리", "red"

# 4. 변동률 및 가중치 기반 점수 산정
def calculate_advanced_score(d):
    score = 100
    reasons = []
    
    # 환율 변동률 (가중치 1.5)
    krw_chg = ((d['환율'] - d['환율_prev']) / d['환율_prev']) * 100
    if krw_chg > 0.5:
        score -= (30 * 1.5)
        reasons.append(f"💵 **환율 급변({krw_chg:.1f}%):** 외인 수급 악화 및 국장 하방 압력 증대")
        
    # 금리 변동폭 (가중치 1.2)
    tnx_chg = d['금리'] - d['금리_prev']
    if tnx_chg > 0.05:
        score -= (20 * 1.2)
        reasons.append(f"🇺🇸 **금리 급등({tnx_chg:.2f}%p):** 할인율 상승으로 성장주 밸류에이션 타격")
        
    # 유가 변동률 (가중치 1.1)
    oil_chg = ((d['유가'] - d['유가_prev']) / d['유가_prev']) * 100
    if oil_chg > 2.0:
        score -= (15 * 1.1)
        reasons.append(f"🛢️ **유가 급등({oil_chg:.1f}%):** 인플레이션 재점화 및 기업 비용 부담 증가")

    return max(0, score), reasons

# 최종 점수 및 비중 계산
curr_score, curr_reasons = calculate_advanced_score(data)
prev_score = 100 # 기본값 (변동폭 기준점)
score_delta = curr_score - prev_score

curr_w, status, color = get_asset_strategy(curr_score)
prev_w, _, _ = get_asset_strategy(prev_score)

# 5. 상단 대시보드 (핵심 지표)
st.subheader("📍 핵심 매크로 지표 현황")
m1, m2, m3, m4, m5 = st.columns(5)
metrics_list = [
    ("🇺🇸 금리", '금리', "{:.2f}%"), ("💵 환율", '환율', "{:,.1f}원"), 
    ("📉 VIX", 'VIX', "{:.2f}"), ("🛢️ 유가", '유가', "${:.1f}"), ("✨ 금시세", '금시세', "${:,.1f}")
]
cols = [m1, m2, m3, m4, m5]
for i, (label, key, fmt) in enumerate(metrics_list):
    with cols[i]:
        v, p = data.get(key, 0), data.get(f"{key}_prev", 0)
        st.metric(label, fmt.format(v), fmt.format(v-p))

st.divider()

# 6. 자산 배분 비중 및 증감률 표시
left, right = st.columns([1, 1.2])

with left:
    st.subheader("🎯 통합 투자 스코어 리포트")
    st.metric("종합 점수", f"{curr_score:.0f}점", f"{score_delta:.0f}점 (전일비)")
    st.markdown(f"### 현재 상태: :{color}[{status}]")
    st.progress(curr_score / 100)
    
    st.markdown("#### 📊 전략적 자산 배분 (전일 대비 증감)")
    w_col1, w_col2, w_col3, w_col4 = st.columns(4)
    assets_map = [("📈 주식", "주식"), ("🏦 채권", "채권"), ("✨ 금", "금"), ("💵 현금", "현금")]
    w_cols = [w_col1, w_col2, w_col3, w_col4]
    
    for i, (label, key) in enumerate(assets_map):
        diff = curr_w[key] - prev_w[key]
        with w_cols[i]:
            st.metric(label, f"{curr_w[key]}%", f"{diff:+} %p")

with right:
    st.subheader("📈 시장 흐름 시각화")
    chart_target = st.radio("분석 그래프 선택", ["나스닥", "금리", "환율", "유가", "금시세"], horizontal=True)
    st.line_chart(history[chart_target], color="#1E3A8A")

# 7. 비중 변경 이유 및 영향 분석
st.divider()
st.subheader("🧐 비중 변경 핵심 사유 및 시장 영향")
if curr_reasons:
    for reason in curr_reasons:
        st.markdown(f"<div class='reason-box'>{reason}</div>", unsafe_allow_html=True)
else:
    st.success("지표가 매우 안정적입니다. 현재의 공격적인 전략적 자산 배분을 유지하십시오.")

# 8. AI 전문가 리포트 생성
st.divider()
if st.button("🤖 AI 정밀 자산 전략 리포트 생성", use_container_width=True):
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        prompt = f"""
        자산운용가 리포트. 종합점수:{curr_score}점, 감점사유:{curr_reasons}
        비중 변화: 주식{curr_w['주식']}%({curr_w['주식']-prev_w['주식']}%p), 채권{curr_w['채권']}%({curr_w['채권']-prev_w['채권']}%p), 금{curr_w['금']}%({curr_w['금']-prev_w['금']}%p)
        이 변화의 경제적 배경과 공격적 투자자가 취해야 할 구체적 행동 강령을 3문장으로 요약해줘.
        """
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        st.info(res.choices.message.content)
    except:
        st.error("AI 기능을 활성화하려면 OpenAI API 키를 설정하세요.")

st.caption("※ 본 데이터는 실시간 매크로 지표를 근거로 산출되었으며, 최종 투자 판단은 본인에게 있습니다.")
