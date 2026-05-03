import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

# ---------------------------------------------------
# 1. 앱 설정
# ---------------------------------------------------
st.set_page_config(page_title="오늘의 주식 동향 (확장형)", layout="wide")

st.markdown("""
    <style>
    h1 { font-size: 2.8rem !important; color: #1E88E5; text-align: center; }
    h2, h3 { color: #263238; }
    .regime-box {
        padding: 20px; border-radius: 12px; text-align: center;
        font-weight: bold; font-size: 1.4rem; margin-bottom: 20px;
    }
    .reason-box {import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="AI 통합 투자 전략 대시보드", layout="wide")
st.title("📈 2026 AI 동적 리밸런싱 및 통합 전략")

# 2. 투자 설정 및 국면 선택 (사이드바 분석 기능)
total_budget = 10000000  # 1,000만 원 기준
st.sidebar.header("🌐 현 시장 국면 분석")
market_state = st.sidebar.selectbox(
    "현재 시장의 추세를 선택하세요",
    ["추세 상승기 (Bull)", "추세 하락기 (Bear)", "박스권/횡보분출기 (Sideways)"]
)

# 국면별 로직 설정
def get_market_logic(state):
    if "상승기" in state:
        return {"ratios": {"QQQ": 0.45, "IVV": 0.15, "005930.KS": 0.30, "BTC-USD": 0.10},
                "sl_rate": 0.88, "tp_rate": 1.30, "cash_ratio": 0.0, "desc": "실적 장세 / AI 슈퍼사이클", "risk_adj": "공격적"}
    elif "하락기" in state:
        return {"ratios": {"QQQ": 0.10, "IVV": 0.20, "005930.KS": 0.05, "BTC-USD": 0.05},
                "sl_rate": 0.96, "tp_rate": 1.05, "cash_ratio": 0.6, "desc": "금리/매크로 불확실성", "risk_adj": "보수적"}
    else:
        return {"ratios": {"QQQ": 0.25, "IVV": 0.25, "005930.KS": 0.10, "BTC-USD": 0.05},
                "sl_rate": 0.92, "tp_rate": 1.15, "cash_ratio": 0.35, "desc": "고점 부담 / 순환매 장세", "risk_adj": "중립적"}

logic = get_market_logic(market_state)

st.sidebar.info(f"""
**[전략 기조: {logic['risk_adj']}]**
- {logic['desc']}
- **현금 비중**: {logic['cash_ratio']*100:.0f}% 확보
- **손절 대응**: {((1-logic['sl_rate'])*100):.0f}% 이내
""")

# 3. 데이터 로드
@st.cache_data
def load_full_data():
    symbols = {"나스닥100(QQQ)": "QQQ", "S&P500(IVV)": "IVV", "삼성전자": "005930.KS", "비트코인(BTC)": "BTC-USD"}
    data = {}
    for name, ticker in symbols.items():
        try:
            df = yf.Ticker(ticker).history(start="2024-01-01")
            if not df.empty: data[ticker] = {"df": df, "name": name}
        except: continue
    return data

assets = load_full_data()

# 4. 성과 요약 메트릭 (차트 삭제됨)
st.header("🔍 자산별 성과 요약")
cols = st.columns(len(assets))
for i, (ticker, info) in enumerate(assets.items()):
    df = info['df']
    start_p = df['Close'].iloc[0]
    curr_p = df['Close'].iloc[-1]
    ret = ((curr_p - start_p) / start_p) * 100
    with cols[i]:
        st.metric(info['name'], f"{curr_p:,.2f}", f"{ret:+.2f}%")

# 5. 통합 리밸런싱 및 상세 매매 전략 테이블
st.divider()
st.header("🎯 통합 리밸런싱 및 상세 전략")

strategy_list = []
for ticker, info in assets.items():
    curr_p = info['df']['Close'].iloc[-1]
    target_ratio = logic['ratios'].get(ticker, 0)
    target_amt = total_budget * target_ratio
    
    # 리스크 등급 및 액션 판단
    risk_lv = "높음" if "BTC" in ticker or "005930" in ticker else "보통"
    if "IVV" in ticker: risk_lv = "낮음"
    
    action = "매수 확대" if target_ratio >= 0.3 else ("축소/대기" if target_ratio <= 0.05 else "비중 유지")
    status = "안전" if curr_p > (curr_p * logic['sl_rate'] * 1.05) else "경계"

    strategy_list.append({
        "자산명": info['name'],
        "권장 비중": f"{target_ratio*100:.0f}%",
        "목표 금액": f"{target_amt:,.0f}원",
        "현재가": f"{curr_p:,.2f}",
        "손절가": f"{curr_p * logic['sl_rate']:,.2f}",
        "목표가": f"{curr_p * logic['tp_rate']:,.2f}",
        "리스크": risk_lv,
        "상태": status,
        "액션": action
    })

st.table(pd.DataFrame(strategy_list))

# 6. 리밸런싱 자산 현황 요약
c1, c2, c3 = st.columns(3)
with c1: st.success(f"✅ 투자 집행 금액: {total_budget * (1-logic['cash_ratio']):,.0f}원")
with c2: st.warning(f"💰 현금 확보 금액: {total_budget * logic['cash_ratio']:,.0f}원")
with c3: st.info(f"📊 국면: {market_state}")

with st.expander("💡 2024년 이후 데이터 기반 리밸런싱 가이드"):
    st.write(f"""
    - **하락장 대응**: 2024년 8월 급락 시 '추세 하락기'를 선택했다면 손절선 **-4%**가 작동해 현금을 보존했을 것입니다.
    - **수익 극대화**: 2025년 삼성전자 상승기엔 '추세 상승기'를 통해 손절선을 **-12%**로 넓혀 수익을 끝까지 가져갔을 것입니다.
    - **리밸런싱 실행**: 현재 내 계좌의 비중이 위 '권장 비중'과 다르다면, 목표 금액에 맞춰 수량을 조절하세요.
    """)

st.caption(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 차트 제외 버전")

        background-color: #f8f9fa; padding: 15px; border-radius: 10px;
        border-left: 5px solid #ffa000; margin-top: 10px;
        font-size: 0.98rem; color: #333;
    }
    .etf-card {
        background-color: #ffffff; border: 1px solid #e0e0e0;
        border-radius: 12px; padding: 16px; margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .badge {
        display: inline-block; padding: 4px 10px; border-radius: 999px;
        font-size: 0.8rem; font-weight: 600; margin-right: 6px;
    }
    .badge-risk { background:#FFEBEE; color:#C62828; }
    .badge-core { background:#E3F2FD; color:#1565C0; }
    .badge-def { background:#E8F5E9; color:#2E7D32; }
    .badge-tac { background:#FFF3E0; color:#EF6C00; }
    [data-testid="stMetricValue"] { font-size: 2.1rem !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 국면별 투자 전략 · 경제 지표 · ETF 추천 통합 분석")

# ---------------------------------------------------
# 2. 티커/ETF 정의
# ---------------------------------------------------
MARKET_TICKERS = {
    "^IXIC": "나스닥",
    "^KS200": "코스피200",
    "^KQ11": "코스닥",
    "^TNX": "금리",
    "USDKRW=X": "환율",
    "^VIX": "VIX",
    "GC=F": "금"
}

ETF_UNIVERSE = {
    "QQQ": {
        "name": "Invesco QQQ",
        "category": "미국 성장",
        "style": "core",
        "reason_up": "나스닥100 중심의 성장주 강세 수혜 기대",
        "reason_side": "성장주 비중이 높아 금리 민감도 체크 필요",
        "reason_down": "하락장에서는 변동성이 커 방어용으로는 부적합",
        "risk": "기술주·금리 민감도 높음",
        "url": "https://www.invesco.com/qqq-etf/en/home.html",
        "fit": {"상승장": 94, "횡보장": 62, "하락장": 25}
    },
    "133690.KS": {
        "name": "TIGER 미국나스닥100",
        "category": "미국 성장",
        "style": "core",
        "reason_up": "국내 상장형으로 나스닥100 추종이 쉬움",
        "reason_side": "상승 추세가 유지될 때만 비중 확대가 유리",
        "reason_down": "하락장에서는 금리·성장주 부담이 커질 수 있음",
        "risk": "환율과 기술주 조정에 민감",
        "url": "http://investments.miraeasset.com/tigeretf/ko/product/search/detail/index.do?ksdFund=KR7133690008",
        "fit": {"상승장": 92, "횡보장": 60, "하락장": 22}
    },
    "069500.KS": {
        "name": "KODEX 200",
        "category": "국내 대형주",
        "style": "core",
        "reason_up": "국내 시장의 기본 코어 자산으로 활용 가능",
        "reason_side": "횡보장에서도 분할매수 대응에 적합",
        "reason_down": "방어력은 제한적이므로 비중 조절 필요",
        "risk": "국내 증시 전반 흐름에 연동",
        "url": "https://www.samsungfund.com/eng/etf/product/view.do?id=2ETF01",
        "fit": {"상승장": 82, "횡보장": 78, "하락장": 40}
    },
    "232080.KS": {
        "name": "TIGER 코스닥150",
        "category": "국내 성장주",
        "style": "tactical",
        "reason_up": "위험선호 확대 시 코스닥 탄력이 커질 수 있음",
        "reason_side": "박스권 장세에서는 변동성 관리가 중요",
        "reason_down": "하락장에서 낙폭 확대 가능성이 큼",
        "risk": "변동성 매우 높음",
        "url": "http://investments.miraeasset.com/tigeretf/ko/product/search/detail/index.do?ksdFund=KR7232080002",
        "fit": {"상승장": 84, "횡보장": 45, "하락장": 15}
    },
    "233740.KS": {
        "name": "KODEX 코스닥150 레버리지",
        "category": "국내 공격형",
        "style": "tactical",
        "reason_up": "강한 상승 추세에서 단기 탄력 대응용",
        "reason_side": "횡보장에서는 감가효과와 변동성에 주의",
        "reason_down": "하락장 장기보유는 매우 부적절",
        "risk": "레버리지 ETF, 단기 전술용",
        "url": "https://www.samsungfund.com/etf/product/view.do?id=2ETF56",
        "fit": {"상승장": 74, "횡보장": 20, "하락장": 5}
    },
    "GLD": {
        "name": "SPDR Gold Shares",
        "category": "금",
        "style": "defensive",
        "reason_up": "상승장에서는 우선순위가 낮지만 분산효과는 유효",
        "reason_side": "횡보장과 불확실성 구간에서 헤지 자산 역할",
        "reason_down": "위험회피 심리 강화 시 방어 자산 역할 가능",
        "risk": "달러·실질금리 흐름 영향",
        "url": "https://www.spdrgoldshares.com/",
        "fit": {"상승장": 45, "횡보장": 84, "하락장": 88}
    },
    "132030.KS": {
        "name": "KODEX 골드선물(H)",
        "category": "금",
        "style": "defensive",
        "reason_up": "상승장에서는 보조적 분산 자산",
        "reason_side": "횡보장·이벤트 대기 구간에서 헤지 수단",
        "reason_down": "하락장 방어용으로 관심 가질 수 있는 자산",
        "risk": "선물·헤지 구조 이해 필요",
        "url": "https://www.samsungfund.com/etf/product/view.do?id=2ETF24",
        "fit": {"상승장": 42, "횡보장": 82, "하락장": 86}
    },
    "TLT": {
        "name": "iShares 20+ Year Treasury Bond ETF",
        "category": "미국 장기채",
        "style": "defensive",
        "reason_up": "상승장에서는 우선순위가 낮음",
        "reason_side": "금리 하락 기대 시 완충 자산 역할 가능",
        "reason_down": "리스크오프 국면에서 방어용 후보",
        "risk": "장기채는 금리 방향성에 민감",
        "url": "https://www.ishares.com/us/products/239454/ishares-20-year-treasury-bond-etf",
        "fit": {"상승장": 35, "횡보장": 76, "하락장": 90}
    },
    "252670.KS": {
        "name": "KODEX 200선물인버스2X",
        "category": "국내 하락 헤지",
        "style": "tactical",
        "reason_up": "상승장에서는 기본적으로 부적합",
        "reason_side": "횡보장에서도 장기보유는 비효율적",
        "reason_down": "급락 구간 단기 헤지/전술 대응용",
        "risk": "인버스 2X, 단기 대응 전용",
        "url": "https://www.samsungfund.com/etf/product/view.do?id=2ETF70",
        "fit": {"상승장": 5, "횡보장": 18, "하락장": 95}
    }
}

REGIME_ETF_MAP = {
    "상승장": ["QQQ", "133690.KS", "069500.KS", "232080.KS", "233740.KS"],
    "횡보장": ["069500.KS", "GLD", "132030.KS", "TLT", "QQQ"],
    "하락장": ["252670.KS", "TLT", "GLD", "132030.KS", "069500.KS"]
}

COMMON_CHECKLIST = [
    "오늘 시장 국면(상승/횡보/하락)을 먼저 확인했다",
    "매수 전 손절선과 익절 기준을 미리 정했다",
    "한 번에 몰빵하지 않고 분할 진입 계획을 세웠다",
    "오늘 밤/이번 주 주요 이벤트(FOMC·CPI·고용)를 확인했다",
    "VIX와 미국 10년물 금리 흐름을 함께 봤다",
]

REGIME_CHECKLIST = {
    "상승장": [
        "전고점 돌파 시 거래량이 동반되는지 확인했다",
        "장대 양봉 이후 추격매수를 자제할 계획이다",
        "성장주 ETF 비중을 늘리더라도 현금 10~20%는 남긴다",
        "레버리지 ETF는 단기 대응용으로만 볼 계획이다",
    ],
    "횡보장": [
        "박스권 상단에서는 추격매수를 자제한다",
        "지지선 부근에서만 분할 접근할 계획이다",
        "성장주와 방어자산을 섞어서 비중을 조절한다",
        "이벤트 전날에는 신규 비중 확대를 줄인다",
    ],
    "하락장": [
        "반등과 추세 전환을 구분하고 있다",
        "인버스/현금/방어자산 중심으로 대응할 계획이다",
        "레버리지 ETF 장기보유를 피할 계획이다",
        "낙폭 과대만 보고 성급히 저가매수하지 않는다",
    ]
}

# ---------------------------------------------------
# 3. 데이터 함수
# ---------------------------------------------------
@st.cache_data(ttl=600)
def download_close_data(symbols, period="3mo"):
    raw = yf.download(
        tickers=symbols,
        period=period,
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False
    )

    if raw.empty:
        raise ValueError("Yahoo Finance에서 데이터를 가져오지 못했습니다.")

    if isinstance(raw.columns, pd.MultiIndex):
        if "Close" not in raw.columns.get_level_values(0):
            raise ValueError("Close 데이터가 없습니다.")
        df = raw.xs("Close", axis=1, level=0)
    else:
        if "Close" not in raw.columns:
            raise ValueError("Close 데이터가 없습니다.")
        if len(symbols) != 1:
            raise ValueError("단일 컬럼 데이터 구조 처리 중 오류가 발생했습니다.")
        df = raw[["Close"]].copy()
        df.columns = symbols

    for sym in symbols:
        if sym not in df.columns:
            df[sym] = pd.NA

    df = df[symbols].sort_index().ffill()
    return df


def get_latest_stats(df, symbol):
    if symbol not in df.columns:
        return None

    s = df[symbol].dropna()
    if len(s) < 2:
        return None

    current = float(s.iloc[-1])
    prev = float(s.iloc[-2])

    if prev == 0:
        return None

    diff = current - prev
    change_pct = (diff / prev) * 100
    return {
        "current": current,
        "prev": prev,
        "diff": diff,
        "change_pct": change_pct
    }


def get_regime(now_nasdaq, ma20):
    if now_nasdaq > ma20 * 1.035:
        return "상승장", "#E8F5E9", -3.0
    elif now_nasdaq < ma20 * 0.965:
        return "하락장", "#FFEBEE", -1.0
    else:
        return "횡보장", "#FFF3E0", -2.0


def get_market_score_reasons(sym, current, changes_pct):
    reasons = []
    score = 50

    # 모멘텀
    daily_momentum = changes_pct[sym]
    m_adj = max(-20, min(20, daily_momentum * 8))
    score += m_adj
    reasons.append(f"✅ 모멘텀 반영 ({int(m_adj):+d}점)")

    # 금리
    tnx_val = current["^TNX"]
    if tnx_val > 4.3:
        i_pen = min(30, (tnx_val - 4.3) * 20)
        score -= i_pen
        reasons.append(f"🏦 금리 압박 ({int(-i_pen)}점)")
    else:
        score += 10
        reasons.append("🏦 금리 안정 (+10점)")

    # 환율
    krw_val = current["USDKRW=X"]
    if krw_val > 1350:
        f_pen = min(15, (krw_val - 1350) / 5)
        score -= f_pen
        reasons.append(f"💵 환율 리스크 ({int(-f_pen)}점)")
    else:
        score += 5
        reasons.append("💵 환율 안정 (+5점)")

    return int(max(0, min(100, score))), reasons


def get_etf_reason_by_regime(meta, regime):
    if regime == "상승장":
        return meta["reason_up"]
    elif regime == "횡보장":
        return meta["reason_side"]
    return meta["reason_down"]


def get_style_badge(style):
    if style == "core":
        return '<span class="badge badge-core">코어</span>'
    elif style == "defensive":
        return '<span class="badge badge-def">방어</span>'
    return '<span class="badge badge-tac">전술</span>'


def get_regime_strategy_text(regime):
    if regime == "상승장":
        return "상승장에서는 코어 지수 ETF + 성장 ETF 중심으로 보되, 레버리지는 단기 대응용으로만 제한하는 구성이 유리합니다."
    elif regime == "횡보장":
        return "횡보장에서는 광범위 지수 ETF를 중심으로 하고, 금/채권 같은 방어 자산을 일부 섞는 바벨 전략이 유효합니다."
    return "하락장에서는 공격형 비중보다 현금·채권·금·인버스 등 방어/헤지 수단을 우선 검토하는 보수적 대응이 적합합니다."


# ---------------------------------------------------
# 4. 데이터 로딩
# ---------------------------------------------------
try:
    market_symbols = list(MARKET_TICKERS.keys())
    etf_symbols = list(ETF_UNIVERSE.keys())

    market_df = download_close_data(market_symbols, period="3mo")
    etf_df = download_close_data(etf_symbols, period="1mo")

    required = ["^IXIC", "^KS200", "^KQ11", "^TNX", "USDKRW=X", "^VIX", "GC=F"]
    market_df = market_df.dropna(subset=required)

    if len(market_df) < 21:
        raise ValueError("분석에 필요한 데이터가 충분하지 않습니다. (최소 21거래일 필요)")

    current = market_df.iloc[-1]
    prev = market_df.iloc[-2]
    changes_pct = ((current - prev) / prev) * 100
    diffs = current - prev

    ma20 = market_df["^IXIC"].rolling(window=20).mean().iloc[-1]
    now_nasdaq = current["^IXIC"]
    regime, regime_color, stop_limit = get_regime(now_nasdaq, ma20)

    # ---------------------------------------------------
    # 5. 국면 요약
    # ---------------------------------------------------
    st.markdown(
        f'<div class="regime-box" style="background-color: {regime_color};">'
        f'현재 시장은 【{regime}】 국면입니다. '
        f'(권장 손절선 예시: {stop_limit}%)'
        f'</div>',
        unsafe_allow_html=True
    )

    st.info(f"📌 전략 요약: {get_regime_strategy_text(regime)}")

    # ---------------------------------------------------
    # 6. 시장별 점수
    # ---------------------------------------------------
    st.header(f"🎯 국면맞춤형 투자점수 ({regime})")
    cols = st.columns(3)
    mkts = [("^IXIC", "나스닥"), ("^KS200", "코스피200"), ("^KQ11", "코스닥")]

    for i, (sym, name) in enumerate(mkts):
        score, reasons = get_market_score_reasons(sym, current, changes_pct)
        with cols[i]:
            st.metric(
                name,
                f"{score}점 ({diffs[sym]:+,.2f})",
                f"변동률: {changes_pct[sym]:+.2f}%"
            )
            st.markdown(
                '<div class="reason-box"><b>점수 근거:</b><br>' +
                '<br>'.join(reasons) +
                '</div>',
                unsafe_allow_html=True
            )

    st.divider()

    # ---------------------------------------------------
    # 7. 경제 지표
    # ---------------------------------------------------
    st.header("🌐 주요 경제 지표 1개월 상세 추이")
    inds = [
        ("🇺🇸 미국 10년물 금리 (%)", "^TNX", 3),
        ("💵 원/달러 환율 (KRW)", "USDKRW=X", 1),
        ("🟡 국제 금 시세 (USD)", "GC=F", 1)
    ]

    for label, sym, prec in inds:
        st.subheader(label)
        l_col, r_col = st.columns([1, 2])

        with l_col:
            st.metric(
                "현재 수치 (전일비)",
                f"{current[sym]:,.{prec}f} ({diffs[sym]:+,.{prec}f})",
                f"{changes_pct[sym]:+.2f}%"
            )
            if sym == "^TNX":
                if current[sym] > 4.3:
                    st.warning("금리 부담 구간입니다. 성장주·장기채 해석을 분리해서 보세요.")
                else:
                    st.success("금리 부담이 상대적으로 완화된 구간입니다.")
            elif sym == "USDKRW=X":
                if current[sym] > 1400:
                    st.warning("환율 부담이 큰 편입니다. 외국인 수급에 주의하세요.")
                else:
                    st.info("환율이 과도한 부담 구간은 아닙니다.")

        with r_col:
            st.line_chart(market_df[sym].tail(30), height=220)

        st.divider()

    # ---------------------------------------------------
    # 8. VIX / 일정
    # ---------------------------------------------------
    st.header("🚀 시장 심리 및 주요 일정")
    t1, t2 = st.columns([1, 1.5])

    with t1:
        vix_val = current["^VIX"]
        st.subheader("😱 공포 지수 (VIX)")
        st.metric(
            "현재 VIX",
            f"{vix_val:.2f} ({diffs['^VIX']:+.2f})",
            f"{changes_pct['^VIX']:+.2f}%"
        )

        if vix_val > 30:
            st.error("🔥 패닉 장세: 변동성 확대 구간")
        elif vix_val < 15:
            st.warning("🧊 과잉 낙관: 리스크 관리 주의")
        else:
            st.info("🙂 중립적 심리 구간")

    with t2:
        st.subheader("📅 이번 주 주요 일정")
        calendar_df = pd.DataFrame([
            {"날짜": "업데이트 필요", "이벤트": "FOMC / CPI / 고용지표", "예상": "-", "영향": "금리 및 성장주 변동성"}
        ])
        st.table(calendar_df)

    st.divider()

    # ---------------------------------------------------
    # 9. ETF 추천 섹션
    # ---------------------------------------------------
    st.header("🧩 시장 국면별 ETF 추천")

    recommended_symbols = REGIME_ETF_MAP[regime]
    etf_rows = []

    for sym in recommended_symbols:
        meta = ETF_UNIVERSE[sym]
        stats = get_latest_stats(etf_df, sym)

        if stats is None:
            price = None
            change_pct = None
            diff = None
        else:
            price = stats["current"]
            change_pct = stats["change_pct"]
            diff = stats["diff"]

        base_score = meta["fit"][regime]
        momentum_bonus = 0 if change_pct is None else max(-5, min(5, change_pct))
        final_score = int(max(0, min(100, base_score + momentum_bonus)))

        etf_rows.append({
            "티커": sym,
            "ETF명": meta["name"],
            "분류": meta["category"],
            "스타일": meta["style"],
            "추천점수": final_score,
            "현재가": price,
            "전일대비": diff,
            "전일등락률(%)": change_pct,
            "추천이유": get_etf_reason_by_regime(meta, regime),
            "주의사항": meta["risk"],
            "공식URL": meta["url"]
        })

    etf_rec_df = pd.DataFrame(etf_rows).sort_values(by="추천점수", ascending=False).reset_index(drop=True)

    # Top 3 카드
    top_n = min(3, len(etf_rec_df))
    top_cols = st.columns(top_n)

    for i in range(top_n):
        row = etf_rec_df.iloc[i]
        meta = ETF_UNIVERSE[row["티커"]]
        with top_cols[i]:
            price_text = "N/A" if pd.isna(row["현재가"]) else f"{row['현재가']:,.2f}"
            change_text = "N/A" if pd.isna(row["전일등락률(%)"]) else f"{row['전일등락률(%)']:+.2f}%"

            st.markdown(
                f"""
                <div class="etf-card">
                    {get_style_badge(meta["style"])}
                    <span class="badge badge-risk">{meta["category"]}</span>
                    <h4 style="margin-top:10px; margin-bottom:8px;">{row["ETF명"]}</h4>
                    <div><b>티커:</b> {row["티커"]}</div>
                    <div><b>추천점수:</b> {row["추천점수"]}점</div>
                    <div><b>현재가:</b> {price_text}</div>
                    <div><b>전일등락률:</b> {change_text}</div>
                    <div style="margin-top:10px; color:#444;">{row["추천이유"]}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown(f"[공식 상품 페이지 바로가기]({row['공식URL']})")

    st.subheader("📋 추천 ETF 상세표")

    display_df = etf_rec_df.copy()
    display_df["현재가"] = display_df["현재가"].map(lambda x: "-" if pd.isna(x) else f"{x:,.2f}")
    display_df["전일대비"] = display_df["전일대비"].map(lambda x: "-" if pd.isna(x) else f"{x:+,.2f}")
    display_df["전일등락률(%)"] = display_df["전일등락률(%)"].map(lambda x: "-" if pd.isna(x) else f"{x:+.2f}%")
    display_df["스타일"] = display_df["스타일"].map({
        "core": "코어",
        "defensive": "방어",
        "tactical": "전술"
    })

    st.dataframe(
        display_df[["ETF명", "티커", "분류", "스타일", "추천점수", "현재가", "전일등락률(%)", "추천이유", "주의사항"]],
        use_container_width=True,
        hide_index=True
    )

    # ETF 등락률 차트
    chart_df = etf_rec_df.dropna(subset=["전일등락률(%)"]).copy()
    if not chart_df.empty:
        chart = (
            alt.Chart(chart_df)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("ETF명:N", sort="-y", title="추천 ETF"),
                y=alt.Y("전일등락률(%):Q", title="전일 등락률 (%)"),
                color=alt.condition(
                    alt.datum["전일등락률(%)"] >= 0,
                    alt.value("#1E88E5"),
                    alt.value("#EF5350")
                ),
                tooltip=["ETF명", "티커", "추천점수", alt.Tooltip("전일등락률(%):Q", format=".2f")]
            )
            .properties(height=320)
        )
        st.subheader("📈 추천 ETF 전일 등락률 비교")
        st.altair_chart(chart, use_container_width=True)

    st.caption("※ 레버리지·인버스 ETF는 일반적으로 단기 전술 대응용으로만 보는 것이 적합합니다.")

    st.divider()

    # ---------------------------------------------------
    # 10. 매매 체크리스트
    # ---------------------------------------------------
    st.header("✅ 간단 매매 체크리스트")

    st.write(f"현재 국면은 **{regime}** 이므로, 아래 체크리스트를 점검해 보세요.")

    checklist_items = COMMON_CHECKLIST + REGIME_CHECKLIST[regime]
    checked_count = 0

    c1, c2 = st.columns(2)
    half = (len(checklist_items) + 1) // 2

    with c1:
        for i, item in enumerate(checklist_items[:half]):
            if st.checkbox(item, key=f"chk_{i}"):
                checked_count += 1

    with c2:
        for j, item in enumerate(checklist_items[half:], start=half):
            if st.checkbox(item, key=f"chk_{j}"):
                checked_count += 1

    progress = checked_count / len(checklist_items)
    st.progress(progress)
    st.write(f"체크 완료: **{checked_count} / {len(checklist_items)}**")

    if progress == 1:
        st.success("체크리스트를 모두 확인했습니다. 계획된 매매인지 다시 한 번만 점검해 보세요.")
    elif progress >= 0.7:
        st.info("대부분 점검 완료되었습니다. 마지막으로 손절/비중 계획만 다시 확인해 보세요.")
    else:
        st.warning("매매 전 확인 항목이 아직 남아 있습니다. 성급한 진입을 피하세요.")

    st.divider()

    # ---------------------------------------------------
    # 11. 하단 요약
    # ---------------------------------------------------
    st.header("📝 오늘의 한줄 가이드")
    if regime == "상승장":
        st.success("상승장: 코어 지수 ETF + 성장 ETF 중심, 단 레버리지는 짧게.")
    elif regime == "횡보장":
        st.info("횡보장: 지수 ETF 중심 + 금/채권 일부 혼합, 추격매수보다 분할 접근.")
    else:
        st.error("하락장: 방어 우선. 현금·채권·금·인버스 중심으로 보수적으로 대응.")

    st.caption("※ 본 앱은 학습/참고용 예시이며, 실제 투자 판단과 책임은 사용자에게 있습니다.")

except Exception as e:
    st.error(f"데이터 로딩 오류: {e}")
