import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
from datetime import datetime
import io

# 1. 앱 설정 및 세션 초기화
st.set_page_config(page_title="Pro Global Investment Master", layout="wide")

if 'trading_log' not in st.session_state:
    st.session_state.trading_log = [
        {"날짜": "2025-01-02", "내용": "초기 투자 시작 (1,000만원)", "수익률": "0.0%"},
        {"날짜": "2026-04-30", "내용": "KOSPI 6,700선 랠리 대응", "수익률": "145.8%"}
    ]

# 2. 실시간 데이터 분석 엔진 (금, 금리, 환율, VIX, 지수 통합)
@st.cache_data(ttl=60)
def get_comprehensive_analysis():
    try:
        # 데이터 호출
        ks = yf.download("^KS11", period="5d", interval="1d")
        gold = yf.download("GC=F", period="5d", interval="1d")
        bond = yf.download("^TNX", period="5d", interval="1d")
        fx = yf.download("USDKRW=X", period="5d", interval="1d")
        vix = yf.download("^VIX", period="5d", interval="1d")
        
        def get_stats(df):
            curr = df['Close'].iloc[-1].item()
            prev = df['Close'].iloc[-2].item()
            pct = ((curr - prev) / prev) * 100
            return curr, pct

        ks_c, ks_p = get_stats(ks)
        g_c, g_p = get_stats(gold)
        b_c, b_p = get_stats(bond)
        fx_c, fx_p = get_stats(fx)
        v_c, v_p = get_stats(vix)
        
        ma20 = yf.download("^KS11", period="60d")['Close'].rolling(window=20).mean().iloc[-1].item()
        
        # 전문가 점수 산출 로직
        ms = min(max(50 + (ks_p * 15), 0), 100) # 추세
        vs = min(max(100 - (v_c - 15) * 4, 0), 100) # 심리
        es = min(max(100 - (b_c - 3.5) * 40, 0), 100) # 매크로
        
        f_score = (ms * 0.4) + (vs * 0.3) + (es * 0.3)
        return {
            "ks": [ks_c, ks_p], "gold": [g_c, g_p], "bond": [b_c, b_p], 
            "fx": [fx_c, fx_p], "vix": [v_c, v_p], "ma20": ma20, "score": f_score
        }
    except: return None

data = get_comprehensive_analysis()

# ---------------------------------------------------------
# [섹션 1] 글로벌 매크로 정밀 브리핑
# ---------------------------------------------------------
st.title("🛡️ Pro Global Investment Master Dashboard")

if data:
    # 5대 지표 메트릭
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("KOSPI 지수", f"{data['ks'][0]:,.2f}", f"{data['ks'][1]:+.2f}%")
    m2.metric("🥇 국제 금 시세", f"${data['gold'][0]:,.1f}", f"{data['gold'][1]:+.2f}%")
    m3.metric("🇺🇸 美 10년 금리", f"{data['bond'][0]:.3f}%", f"{data['bond'][1]:+.3f}%p", delta_color="inverse")
    m4.metric("💵 원/달러 환율", f"{data['fx'][0]:,.1f}원", f"{data['fx'][1]:+.2f}%", delta_color="inverse")
    m5.metric("📉 공포지수(VIX)", f"{data['vix'][0]:.2f}", f"{data['vix'][1]:+.2f}%", delta_color="inverse")

    st.write("---")
    col_g, col_a = st.columns([1, 1.8])
    with col_g:
        fig = go.Figure(go.Indicator(mode="gauge+number", value=data['score'],
            gauge={'axis':{'range':[0, 100]}, 'bar':{'color':"black"},
                   'steps':[{'range':[0, 40],'color':"#1E90FF"},
                             {'range':[40, 70],'color':"#90EE90"},
                             {'range':[70, 100],'color':"#FF4B4B"}]}))
        fig.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20), title="종합 투자 심리 점수")
        st.plotly_chart(fig, use_container_width=True)
    with col_a:
        st.subheader("📝 Macro & Market Intelligence")
        # 금 및 기술적 분석
        gap = ((data['ks'][0]/data['ma20'])-1)*100
        if data['gold'][1] > 1.0: st.warning("🌟 **안전 자산 쏠림:** 금 시세 급등으로 시장 내 지정학적/인플레이션 경계감이 높습니다.")
        if gap < 0: st.error(f"🚨 **추세 이탈:** 지수가 20일선 아래로 **{abs(gap):.2f}%** 하회 중입니다. 방어적 태세가 필요합니다.")
        else: st.success(f"📈 **추세 유지:** 지수가 20일선 대비 **{gap:+.2f}%** 상단에 위치하여 상승 에너지가 유효합니다.")
        st.info(f"💡 종합 점수 **{data['score']:.1f}점** 기반: {'적극적인 종목 발굴' if data['score']>60 else '보수적인 현금 비중 확대'} 권장.")

# ---------------------------------------------------------
# [섹션 2] 실시간 포트폴리오 관리 (엑셀 업로드)
# ---------------------------------------------------------
st.divider()
st.header("2. 📂 실시간 자산 현황 & 리스크 관리")
st.sidebar.header("📂 데이터 업로드")
uploaded_file = st.sidebar.file_uploader("보유 종목 엑셀 업로드", type=["xlsx"])

if uploaded_file:
    df_p = pd.read_excel(uploaded_file)
else:
    df_p = pd.DataFrame({"종목명": ["삼성전자", "SK하이닉스"], "티커": ["005930.KS", "000660.KS"], "매수단가":[75000, 185000], "수량":[20, 10]})

def calc_p(df):
    res, t_buy, t_eval = [], 0, 0
    for _, row in df.iterrows():
        try:
            stock = yf.Ticker(row['티커']).history(period="1d")
            curr = stock['Close'].iloc[-1].item()
            t_buy += row['매수단가'] * row['수량']; t_eval += curr * row['수량']
            res.append({"종목명": row['종목명'], "현재가": f"{int(curr):,}원", "수익률": f"{((curr/row['매수단가'])-1)*100:+.2f}%", "평가액": int(curr * row['수량'])})
        except: continue
    return pd.DataFrame(res), t_buy, t_eval

df_res, tb, te = calc_p(df_p)
col_p1, col_p2 = st.columns([1.5, 1])
with col_p1:
    st.table(df_res)
with col_p2:
    st.metric("실시간 총 자산", f"{te:,.0f}원", f"{te-tb:+,.0f}원")
    st.write("---")
    st.subheader("✅ 리스크 체크리스트")
    st.checkbox("매수가 대비 -5% 손절 원칙 준수", value=True)
    st.checkbox("매크로 분석에 따른 비중 조절 완료")

# ---------------------------------------------------------
# [섹션 3] 업종 모멘텀 및 뉴스 연동
# ---------------------------------------------------------
st.divider()
st.header("3. 🏆 업종 모멘텀 및 대장주 뉴스")
df_sector = pd.DataFrame({
    "업종": ["반도체", "AI", "밸류업/금융", "금/원자재", "바이오"], 
    "점수":[95, 92, 88, 75, 65],
    "대장주": ["SK하이닉스", "이수페타시스", "KB금융", "KODEX 금선물", "삼성바이오"]
}).sort_values("점수", ascending=False)

c_table, c_news = st.columns([1.5, 1])
with c_table:
    st.table(df_sector)
with c_news:
    sel = st.selectbox("뉴스 분석 업종 선택", df_sector["업종"])
    ldr = df_sector[df_sector["업종"] == sel]["대장주"].values[0]
    st.success(f"**{sel}** 대표주: **{ldr}**")
    st.link_button(f"🔗 {ldr} 실시간 뉴스 확인", f"https://naver.com{ldr}")

# ---------------------------------------------------------
# [섹션 4] 투자 패턴 및 데이터 저장
# ---------------------------------------------------------
st.divider()
st.header("4. 🎯 오늘의 투자 패턴 가이드")
v_f = data['vix'][0] / 20 if data else 1.0
c_s, c_m, c_l = st.columns(3)
with c_s:
    st.error(f"⏱️ **단기 (Swing)**\n\n- 추천 섹터: AI 반도체\n- 권장 손절: -{3.5*v_f:.1f}%")
with c_m:
    st.warning(f"📅 **중기 (Trend)**\n\n- 추천 섹터: 밸류업/금융\n- 권장 손절: -{10.0*v_f:.1f}%")
with c_l:
    st.success(f"⏳ **장기 (Value)**\n\n- 추천 섹터: 미국 기술주/금\n- 권장 손절: -{20.0*v_f:.1f}%")

st.write("---")
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    df_res.to_excel(writer, sheet_name='포트폴리오_수익률', index=False)
    df_sector.to_excel(writer, sheet_name='업종별_모멘텀', index=False)
    
st.download_button(
    label="📥 종합 투자 리포트(Excel) 내보내기",
    data=buffer.getvalue(),
    file_name=f"투자마스터_리포트_{datetime.now().strftime('%m%d')}.xlsx",
    mime="application/vnd.ms-excel"
)

st.caption(f"Last Intelligence Sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data by Yahoo Finance")
