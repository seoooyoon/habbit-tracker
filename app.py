# app.py
import os
import re
from datetime import date, timedelta

import altair as alt
import pandas as pd
import requests
import streamlit as st
import calendar

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
    openai_api_key = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    weather_api_key = st.text_input("OpenWeatherMap API Key", type="password", value=os.getenv("OPENWEATHER_API_KEY", ""))
    st.caption("키는 세션에만 사용되며, 앱 종료 시 초기화됩니다.")

# ----------------------------
# Helpers: APIs
# ----------------------------
def get_weather(city: str, api_key: str):
    """
    OpenWeatherMap 현재 날씨 조회 (한국어, 섭씨)
    실패 시 None 반환
    """
    if not city or not api_key:
@@ -212,50 +213,90 @@ def _init_demo_records():
    # date 오름차순
    base = date.today() - timedelta(days=6)
    demo = [
        {"date": (base + timedelta(days=0)).isoformat(), "ach_rate": 40, "checked": 2, "mood": 5},
        {"date": (base + timedelta(days=1)).isoformat(), "ach_rate": 60, "checked": 3, "mood": 6},
        {"date": (base + timedelta(days=2)).isoformat(), "ach_rate": 80, "checked": 4, "mood": 7},
        {"date": (base + timedelta(days=3)).isoformat(), "ach_rate": 20, "checked": 1, "mood": 4},
        {"date": (base + timedelta(days=4)).isoformat(), "ach_rate": 100, "checked": 5, "mood": 8},
        {"date": (base + timedelta(days=5)).isoformat(), "ach_rate": 60, "checked": 3, "mood": 6},
    ]
    return demo


if "records" not in st.session_state:
    st.session_state.records = _init_demo_records()

if "last_report" not in st.session_state:
    st.session_state.last_report = None

if "last_weather" not in st.session_state:
    st.session_state.last_weather = None

if "last_dog" not in st.session_state:
    st.session_state.last_dog = None

if "day_plans" not in st.session_state:
    st.session_state.day_plans = {}

if "calendar_month" not in st.session_state:
    st.session_state.calendar_month = date.today().replace(day=1)

if "selected_date" not in st.session_state:
    st.session_state.selected_date = date.today()


def _normalize_date_key(target_date: date) -> str:
    return target_date.isoformat()


def add_day_plan(target_date: date, hour: int, title: str, note: str):
    date_key = _normalize_date_key(target_date)
    st.session_state.day_plans.setdefault(date_key, [])
    st.session_state.day_plans[date_key].append(
        {"hour": hour, "title": title.strip(), "note": note.strip()}
    )
    st.session_state.day_plans[date_key] = sorted(
        st.session_state.day_plans[date_key], key=lambda item: item["hour"]
    )


def delete_day_plans(target_date: date, hours: list[int]):
    date_key = _normalize_date_key(target_date)
    if date_key not in st.session_state.day_plans:
        return
    st.session_state.day_plans[date_key] = [
        item for item in st.session_state.day_plans[date_key] if item["hour"] not in hours
    ]


def shift_month(base_date: date, delta: int) -> date:
    month = base_date.month - 1 + delta
    year = base_date.year + month // 12
    month = month % 12 + 1
    return date(year, month, 1)


def upsert_today_record(ach_rate: int, checked: int, mood: int):
    today_str = date.today().isoformat()
    found = False
    for r in st.session_state.records:
        if r["date"] == today_str:
            r.update({"ach_rate": ach_rate, "checked": checked, "mood": mood})
            found = True
            break
    if not found:
        st.session_state.records.append({"date": today_str, "ach_rate": ach_rate, "checked": checked, "mood": mood})

    # 최근 7일만 유지(요구사항: 6일 샘플 + 오늘로 7일)
    st.session_state.records = sorted(st.session_state.records, key=lambda x: x["date"])[-7:]


# ----------------------------
# UI: Habit check-in
# ----------------------------
st.subheader("✅ 오늘의 체크인")

left, right = st.columns([1.2, 1])

with left:
    st.markdown("**습관 체크**")
@@ -299,50 +340,150 @@ m3.metric("기분", f"{mood}/10")

# 오늘 기록을 세션에 반영 (항상 최신 상태로 7일 차트 유지)
upsert_today_record(ach_rate=ach_rate, checked=checked_count, mood=mood)

df = pd.DataFrame(st.session_state.records)
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

chart = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X("date:T", title="날짜", axis=alt.Axis(format="%m-%d")),
        y=alt.Y("ach_rate:Q", title="달성률(%)", scale=alt.Scale(domain=[0, 100])),
        tooltip=[
            alt.Tooltip("date:T", title="날짜", format="%Y-%m-%d"),
            alt.Tooltip("ach_rate:Q", title="달성률(%)"),
            alt.Tooltip("checked:Q", title="체크 수"),
            alt.Tooltip("mood:Q", title="기분"),
        ],
    )
    .properties(height=260)
)
st.altair_chart(chart, use_container_width=True)

# ----------------------------
# 24h Calendar Scheduler
# ----------------------------
st.subheader("🗓️ 24시간 일정 캘린더")

cal_controls = st.columns([0.2, 0.6, 0.2])
with cal_controls[0]:
    if st.button("◀️ 이전 달", use_container_width=True):
        st.session_state.calendar_month = shift_month(st.session_state.calendar_month, -1)
with cal_controls[1]:
    st.markdown(
        f"<div style='text-align:center; font-weight:600; font-size:18px;'>"
        f"{st.session_state.calendar_month.strftime('%Y년 %m월')}</div>",
        unsafe_allow_html=True,
    )
with cal_controls[2]:
    if st.button("다음 달 ▶️", use_container_width=True):
        st.session_state.calendar_month = shift_month(st.session_state.calendar_month, 1)

weekdays = ["월", "화", "수", "목", "금", "토", "일"]
weekday_cols = st.columns(7)
for idx, day_name in enumerate(weekdays):
    weekday_cols[idx].markdown(f"**{day_name}**")

year = st.session_state.calendar_month.year
month = st.session_state.calendar_month.month
weeks = calendar.monthcalendar(year, month)
for week in weeks:
    day_cols = st.columns(7)
    for idx, day_num in enumerate(week):
        if day_num == 0:
            day_cols[idx].markdown("&nbsp;", unsafe_allow_html=True)
            continue
        current_date = date(year, month, day_num)
        is_selected = current_date == st.session_state.selected_date
        button_label = f"{day_num}{'  +' if is_selected else ''}"
        if day_cols[idx].button(
            button_label,
            key=f"cal-{year}-{month}-{day_num}",
            use_container_width=True,
        ):
            st.session_state.selected_date = current_date
            st.session_state.plan_date_input = current_date

st.caption(f"선택한 날짜: {st.session_state.selected_date.isoformat()}")

planner_left, planner_right = st.columns([1.1, 1.4])

with planner_left:
    plan_date = st.date_input(
        "일정 날짜",
        value=st.session_state.selected_date,
        key="plan_date_input",
    )
    if plan_date != st.session_state.selected_date:
        st.session_state.selected_date = plan_date

    with st.form("add_plan_form", clear_on_submit=True):
        plan_hour = st.selectbox(
            "시간 (24h)", list(range(0, 24)), format_func=lambda h: f"{h:02d}:00"
        )
        plan_title = st.text_input("일정 제목", placeholder="예: 아침 스트레칭")
        plan_note = st.text_area("메모", placeholder="짧은 메모를 남겨보세요.", height=80)
        submitted = st.form_submit_button("일정 추가", use_container_width=True)
        if submitted:
            if not plan_title.strip():
                st.warning("일정 제목을 입력해 주세요.")
            else:
                add_day_plan(plan_date, plan_hour, plan_title, plan_note)
                st.success("일정을 추가했어요!")

    date_key = _normalize_date_key(plan_date)
    existing_hours = [
        f"{item['hour']:02d}:00 · {item['title']}"
        for item in st.session_state.day_plans.get(date_key, [])
    ]
    if existing_hours:
        selected = st.multiselect("삭제할 일정 선택", existing_hours)
        if st.button("선택 일정 삭제", use_container_width=True):
            selected_hours = [int(value.split(":")[0]) for value in selected]
            delete_day_plans(plan_date, selected_hours)
            st.info("선택 일정을 삭제했어요.")

with planner_right:
    plan_date_key = _normalize_date_key(plan_date)
    hour_rows = []
    plans = {item["hour"]: item for item in st.session_state.day_plans.get(plan_date_key, [])}
    for hour in range(24):
        plan = plans.get(hour)
        hour_rows.append(
            {
                "시간": f"{hour:02d}:00",
                "일정": plan["title"] if plan else "",
                "메모": plan["note"] if plan else "",
            }
        )

    schedule_df = pd.DataFrame(hour_rows)
    st.dataframe(schedule_df, use_container_width=True, height=500)

# ----------------------------
# Generate report
# ----------------------------
st.subheader("🧠 AI 코치 리포트")

btn = st.button("컨디션 리포트 생성", type="primary", use_container_width=True)

if btn:
    # Fetch external info
    weather = get_weather(city, weather_api_key)
    dog = get_dog_image()

    st.session_state.last_weather = weather
    st.session_state.last_dog = dog

    # Generate AI report
    report = generate_report(
        habits=habits,
        mood=mood,
        weather=weather,
        dog=dog,
        coach_style=coach_style,
        openai_key=openai_api_key,
    )
    st.session_state.last_report = report
