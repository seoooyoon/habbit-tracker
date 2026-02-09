import streamlit as st
import requests
from datetime import datetime
from openai import OpenAI

# =====================
# Streamlit 기본 설정
# =====================
st.set_page_config(
    page_title="Pawbit | AI Habit Tracker",
    page_icon="🐾",
    layout="centered"
)

# =====================
# 사이드바 – API KEY 입력
# =====================
st.sidebar.header("🔑 API 설정")

openai_key = st.sidebar.text_input(
    "OpenAI API Key",
    type="password",
    help="sk- 로 시작하는 OpenAI API 키"
)

weather_key = st.sidebar.text_input(
    "OpenWeather API Key",
    type="password",
    help="OpenWeatherMap에서 발급받은 API 키"
)

api_ready = openai_key != "" and weather_key != ""

st.sidebar.divider()

# =====================
# 사용자 설정
# =====================
st.sidebar.header("⚙️ 사용자 설정")

nickname = st.sidebar.text_input("닉네임", value="서윤")

city = st.sidebar.text_input(
    "도시명 (영문)",
    value="Seoul",
    help="예: Seoul, Busan, Tokyo"
)

st.sidebar.subheader("오늘의 습관")

habit_candidates = [
    "🏃 운동하기",
    "💧 물 2L 마시기",
    "📚 공부 / 과제",
    "🧘 명상 / 휴식",
    "✍️ 나만의 습관"
]

selected_habits = []
for habit in habit_candidates:
    if st.sidebar.checkbox(habit):
        selected_habits.append(habit)

# =====================
# OpenAI Client (조건부)
# =====================
client = None
if openai_key:
    client = OpenAI(api_key=openai_key)

# =====================
# 함수 정의
# =====================
def get_weather(city, api_key):
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric",
            "lang": "kr"
        }

        res = requests.get(url, params=params, timeout=5)
        data = res.json()

        if res.status_code != 200:
            return None, None, data.get("message", "날씨 정보 오류")

        weather = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        return weather, temp, None

    except Exception as e:
        return None, None, str(e)


def get_dog_image():
    url = "https://dog.ceo/api/breeds/image/random"
    return requests.get(url).json()["message"]


def generate_ai_feedback(name, habits, percent, weather_text):
    if not client:
        return "⚠️ OpenAI API Key를 입력하면 AI 응원 메시지를 받을 수 있어요."

    prompt = f"""
사용자 이름: {name}
오늘 완료한 습관: {', '.join(habits)}
달성률: {percent}%
오늘 날씨: {weather_text}

조건:
- 한국어
- 따뜻하고 친구 같은 말투
- 3~5줄
- 공감 위주, 부담 주는 조언 금지
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "너는 다정한 AI 습관 코치야."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

# =====================
# 메인 화면
# =====================
st.title("🐾 오늘도 한 걸음, 습관을 키워요")

today = datetime.now().strftime("%Y.%m.%d")
st.write(f"📅 {today}")

# =====================
# 날씨 표시
# =====================
if weather_key:
    weather, temp, error = get_weather(city, weather_key)

    if weather:
        weather_text = f"{weather} / {temp}°C"
        st.write(f"☀️ 오늘의 날씨: **{weather_text}**")
    else:
        weather_text = "날씨 정보 없음"
        st.warning("날씨 정보를 불러오지 못했어요 😢")
        st.caption(f"원인: {error}")
else:
    weather_text = "날씨 정보 없음"
    st.info("ℹ️ 날씨를 보려면 OpenWeather API Key를 입력하세요")

st.divider()

# =====================
# 습관 체크
# =====================
st.subheader("✅ 오늘의 습관 체크")

checked_habits = []
for habit in selected_habits:
    if st.checkbox(habit, key=f"main_{habit}"):
        checked_habits.append(habit)

progress = int(len(checked_habits) / len(selected_habits) * 100) if selected_habits else 0

st.progress(progress)
st.write(f"🎯 오늘 습관 달성률: **{progress}%**")

st.divider()

# =====================
# AI 피드백
# =====================
st.subheader("🤖 AI의 한마디")

feedback = generate_ai_feedback(
    nickname,
    checked_habits,
    progress,
    weather_text
)

st.success(feedback)

# =====================
# 보상 (강아지)
# =====================
if progress > 0:
    st.subheader("🐶 오늘의 보상")

    st.image(get_dog_image(), use_container_width=True)
    st.caption("칭찬 받으러 온 강아지 🐾")

    if progress == 100:
        st.balloons()
        st.success("🎉 오늘 습관 100% 달성! 완벽해요!")

# =====================
# 회고
# =====================
st.divider()
st.subheader("📝 오늘의 한 줄 회고")

reflection = st.text_area(
    "오늘 하루를 한 문장으로 남겨보세요",
    placeholder="예: 귀찮았지만 결국 해냈다"
)

if st.button("저장하기 💾"):
    st.success("오늘의 기록이 저장됐어요 (확장 가능)")
