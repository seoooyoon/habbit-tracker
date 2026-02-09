# app.py
import os
from datetime import date, timedelta
import calendar

import altair as alt
import pandas as pd
import requests
import streamlit as st

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(page_title="AI 습관 트래커", page_icon="📊", layout="wide")
st.title("📊 AI 습관 트래커")

# ----------------------------
# Sidebar: API keys
# ----------------------------
with st.sidebar:
    st.header("🔑 API 설정")
    openai_api_key = st.text_input(
        "OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", "")
    )
    weather_api_key = st.text_input(
        "OpenWeatherMap API Key", type="password", value=os.getenv("OPENWEATHER_API_KEY", "")
    )
    st.caption("키는 세션에만 사용되며 앱 종료 시 초기화됩니다.")

    st.divider()
    city = st.text_input("도시명 (영문)", value="Seoul")

# ----------------------------
# Helpers
# ----------------------------
def get_weather(city: str, api_key: str):
    """현재 날씨 조회"""
    if not city or not api_key:
        return None

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric",
            "lang": "kr",
        }
        res = requests.get(url, params=params, timeout=5)
        data = res.json()

        if res.status_code != 200:
            return None

        return {
            "desc": data["weather"][0]["description"],
            "temp": data["main"]["temp"],
        }
    except Exception:
        return None


def get_dog_image():
    try:
        return requests.get(
            "https://dog.ceo/api/breeds/image/random", timeout=5
        ).json()["message"]
    except Exception:
        return None


def generate_report(habits, mood, weather, dog, coach_style, openai_key):
    if not openai_key:
        return "⚠️ OpenAI API Key를 입력하면 AI 리포트를 생성할 수 있어요."

    weather_text = (
        f"{weather['desc']} / {weather['temp']}°C" if weather else "날씨 정보 없음"
    )

    return f"""
오늘의 습관 요약 🧠

- 체크한 습관 수: {habits}
- 오늘 기분 점수: {mood}/10
- 날씨: {weather_text}

{coach_style} 코치의 한마디:
“완벽하지 않아도 괜찮아요. 오늘을 기록한 것 자체가 이미 충분히 잘한 일이에요.”
"""


def _init_demo_records():
    base = date.today() - timedelta(days=6)
    return [
        {"date": (base + timedelta(days=i)).isoformat(), "ach_rate": v, "checked": c, "mood": m}
        for i, (v, c, m) in enumerate(
            [(40, 2, 5), (60, 3, 6), (80, 4, 7), (20, 1, 4), (100, 5, 8), (60, 3, 6)]
        )
    ]


# ----------------------------
# Session state init
# ----------------------------
if "records" not in st.session_state:
    st.session_state.records = _init_demo_records()

if "day_plans" not in st.session_state:
    st.session_state.day_plans = {}

if "calendar_month" not in st.session_state:
    st.session_state.calendar_month = date.today().replace(day=1)

if "selected_date" not in st.session_state:
    st.session_state.selected_date = date.today()

# ----------------------------
# Habit check-in
# ----------------------------
st.subheader("✅ 오늘의 체크인")

habits = st.slider("오늘 체크한 습관 개수", 0, 5, 3)
mood = st.slider("오늘 기분 점수", 1, 10, 6)

ach_rate = int((habits / 5) * 100)

# 기록 업데이트
today_str = date.today().isoformat()
st.session_state.records.append(
    {"date": today_str, "ach_rate": ach_rate, "checked": habits, "mood": mood}
)
st.session_state.records = st.session_state.records[-7:]

# ----------------------------
# Chart
# ----------------------------
df = pd.DataFrame(st.session_state.records)
df["date"] = pd.to_datetime(df["date"])

chart = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X("date:T", title="날짜", axis=alt.Axis(format="%m-%d")),
        y=alt.Y("ach_rate:Q", title="달성률(%)", scale=alt.Scale(domain=[0, 100])),
        tooltip=["ach_rate", "checked", "mood"],
    )
    .properties(height=280)
)

st.altair_chart(chart, use_container_width=True)

# ----------------------------
# AI Report
# ----------------------------
st.subheader("🧠 AI 코치 리포트")

coach_style = st.selectbox("코치 스타일", ["다정한", "현실적인", "에너지 넘치는"])

if st.button("리포트 생성", type="primary", use_container_width=True):
    weather = get_weather(city, weather_api_key)
    dog = get_dog_image()

    report = generate_report(
        habits=habits,
        mood=mood,
        weather=weather,
        dog=dog,
        coach_style=coach_style,
        openai_key=openai_api_key,
    )

    st.success(report)

    if dog:
        st.image(dog, caption="오늘의 응원 강아지 🐶", use_container_width=True)
