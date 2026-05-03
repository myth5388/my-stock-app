import streamlit as st
import yfinance as yf
import pandas as pd
from openai import OpenAI  # OpenAI 라이브러리 추가

# (기존 데이터 로드 및 점수 계산 로직은 동일하다고 가정)

# --- AI 리포트 생성 함수 ---
def get_ai_report(data, score, weights):
    # 1. API 키 설정 (보안을 위해 실제 서비스 시에는 st.secrets 등을 사용하세요)
    client = OpenAI(api_key="여러분의_OPENAI_API_KEY_입력") 
    
    # 2. AI에게 전달할 프롬프트 구성
    prompt = f"""
    당신은 전문 자산운용가(Portfolio Manager)입니다. 
    공격적 투자 성향을 가진 사용자에게 현재 시장 지표를 분석하여 조언을 제공하세요.

    [현재 시장 데이터]
    - 미 10년물 금리: {data['금리']:.2f}%
    - 원/달러 환율: {data['환율']:.1f}원
    - VIX 지수 (공포지수): {data['VIX']:.2f}
    - 비트코인 가격: ${data['비트코인']:,.0f}
    - 자체 마켓 스코어: {score}/100 점

    [추천 포트폴리오 비중]
    - 주식: {weights['주식']}% / 가상자산: {weights['가상자산']}% / 현금: {weights['현금']}%

    위 데이터를 바탕으로 다음 세 가지를 포함하여 3~4문장으로 분석 리포트를 작성해줘:
    1. 현재 시장의 가장 큰 리스크와 기회
    2. 공격적 투자자가 지금 당장 취해야 할 행동
    3. 추천 비중의 근거
    결론은 아주 단호하고 전문적인 말투로 해줘.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o", # 또는 gpt-3.5-turbo
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 리포트를 생성하는 중 오류가 발생했습니다: {e}"

# --- UI 부분 (기존 코드 아래에 추가) ---
st.divider()
st.subheader("🤖 AI 맞춤형 전략 리포트")

# 버튼을 눌러야 AI 리포트가 생성되도록 하여 API 비용을 절감합니다.
if st.button("AI 리포트 생성하기"):
    with st.spinner("AI가 시장 상황을 정밀 분석 중입니다..."):
        # weights 변수는 이전 단계에서 계산된 값을 사용합니다.
        report = get_ai_report(data, market_score, weights)
        st.info(report)
