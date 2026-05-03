import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="AI 투자 성과 및 전략 대시보드", layout="wide")
st.title("📈 2025-2026 투자 성과 평가 및 실시간 전략")

# 2. 데이터 로드 함수 (기존 코드 유지 및 확장)
@st.cache_data
def get_investment_data():
    symbols = {
        "삼성전자": "005930.KS",
        "비트코인": "BTC-USD",
        "나스닥100(QQQ)": "QQQ",
        "S&P500(IVV)": "IVV"
    }
    data = {}
    for name, ticker in symbols.items():
        stock = yf.Ticker(ticker)
        # 2025년부터 현재까지의 데이터
        hist = stock.history(start="2025-01-01")
        data[name] = hist
    return data

data = get_investment_data()

# 3. 투자 성과 평가 섹션
st.header("🔍 자산별 투자 성과 (2025년 초 대비)")
cols = st.columns(len(data))

for i, (name, df) in enumerate(data.items()):
    if not df.empty:
        start_price = df.iloc[0]['Close']
        current_price = df.iloc[-1]['Close']
        return_pct = ((current_price - start_price) / start_price) * 100
        
        with cols[i]:
            st.metric(name, f"{current_price:,.0f}", f"{return_pct:.2f}%")
            st.line_chart(df['Close'], height=150)

# 4. [신규 추가] 오늘의 추천 ETF 및 종목 매매 전략
st.divider()
st.header("🎯 오늘의 추천 전략 및 리스크 관리")

# 전략 계산 로직 (가상의 알고리즘 기반 가이드라인)
def generate_strategy(name, current_price):
    # 예시: 손절가(매수가의 -10%), 목표가(+20%), 적정 매수 비중
    stop_loss = current_price * 0.90
    target_price = current_price * 1.20
    buy_ratio = "15~20%" if "삼성" in name or "QQQ" in name else "5~10%"
    
    return {
        "매수 권장 비중": buy_ratio,
        "목표 매도가": f"{target_price:,.0f}",
        "손절가 (Stop-Loss)": f"{stop_loss:,.0f}",
        "전략": "분할 매수" if current_price > stop_loss else "관망"
    }

# 추천 리스트 구성
recommendations = []
for name, df in data.items():
    price = df.iloc[-1]['Close']
    strat = generate_strategy(name, price)
    recommendations.append({
        "종목/ETF": name,
        "현재가": f"{price:,.0f}",
        **strat
    })

# 테이블로 표시
rec_df = pd.DataFrame(recommendations)
st.table(rec_df)

# 5. 투자자 맞춤형 포트폴리오 가이드
with st.expander("💡 투자 비중 및 리스크 관리 수칙"):
    st.write("""
    1. **분산 투자**: 특정 종목(삼성전자 등)의 비중이 전체 자산의 20%를 넘지 않도록 조정하세요.
    2. **ETF 활용**: 개별 종목의 변동성이 무서울 때는 **QQQ(나스닥)**나 **IVV(S&P500)** 비중을 40% 이상으로 높이는 것이 안전합니다.
    3. **손절매 준수**: 위 표에 제시된 **손절가(-10%)** 이탈 시에는 기계적으로 대응하여 원금을 보존하는 것이 중요합니다.
    4. **현금 비중**: 시장의 불확실성에 대비해 항상 **10~15%의 현금**은 보유하는 전략을 추천합니다.
    """)

st.caption("본 대시보드는 yfinance 데이터를 바탕으로 생성된 참고용 지표이며, 모든 투자의 책임은 본인에게 있습니다.")
