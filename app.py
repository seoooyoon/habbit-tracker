import streamlit as st
import requests
from datetime import datetime
from openai import OpenAI

# =====================
# Streamlit 설정
# =====================
st.set_page_config(
    page_title="Pawbit | AI Habit Tracker",
    page_icon="🐾",
    layout="centered"
)

# =====================
# API Keys (Streamlit Secrets)
# =====================
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
WEATHER_API_KEY = st.secrets["WEATHER_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

# =====================
# 함수 영역
# =====================
def get_weather(city):
    """OpenWeatherMap 날씨 조회 (안정 버전)"""
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": WEATHER_API_KEY,
            "units": "metric",
            "lang": "kr"
        }

        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if response.status_code != 200:
            return None, None, data.get("message", "unknown error")

        weather = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        return weather, temp, None

    except Exception as e:
        return None, None, str(e)


def get_dog_image():
    url = "https://dog.ceo/api/breeds/image/random"
    res = requests.get(url).json()
    return res["message"]


def generate_ai_feedback(name, habits, percent, weather_text):
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
# 사이드바
# =====================
st.sidebar.header("⚙️ 사용자 설정")

nickname = st.sidebar.text_input("닉네임", value="서윤")

city = st.sidebar.text_input(
    "도시명 (영문 권장)",
    value="Seoul",
    help="예: Seoul, Busan, Tokyo, New York"
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
# 메인 화면
# =====================
st.title("🐾 오늘도 한 걸음, 습관을 키워요")

today = datetime.now().strftime("%Y.%m.%d")
st.write(f"📅 {today}")

# =====================
# 날씨 영역 (에러 처리 강화)
# =====================
weather, temp, weather_error = get_weather(city)

if weather:
    weather_text = f"{weather} / {temp}°C"
    st.write(f"☀️ 오늘의 날씨: **{weather_text}**")
else:
    weather_text = "날씨 정보 없음"
    st.warning("날씨 정보를 불러오지 못했어요 😢")
    st.caption(f"원인: {weather_error}")
    st.caption("👉 도시명을 영문으로 입력해 보세요 (예: Seoul, Busan)")

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
if progress > 0:
    st.subheader("🤖 AI의 한마디")

    with st.spinner("AI가 응원 메시지를 작성 중..."):
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

    dog_image = get_dog_image()
    st.image(dog_image, use_container_width=True)
    st.caption("칭찬 받으러 온 강아지 🐾")

    if progress == 100:
        st.balloons()
        st.success("🎉 오늘 습관 100% 달성! 진짜 최고예요!")

# =====================
# 회고
# =====================
st.divider()
st.subheader("📝 오늘의 한 줄 회고")

reflection = st.text_area(
    "오늘 하루를 한 문장으로 남겨보세요",
    placeholder="예: 날씨는 흐렸지만 습관은 맑았다"
)

if st.button("저장하기 💾"):
    st.success("오늘의 기록이 저장됐어요 (추후 파일 저장 가능)")
