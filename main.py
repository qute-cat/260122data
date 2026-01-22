import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="날짜별 기온 비교", layout="wide")
st.title("🌡️ 날짜별 기온 비교 대시보드")

# -----------------------------
# 기본 데이터 로딩
# -----------------------------
@st.cache_data
def load_base_data():
    df = pd.read_csv("ta_20260122174530.csv", encoding="cp949")

    df = df.rename(columns={
        df.columns[0]: "date",
        df.columns[2]: "tmin",
        df.columns[3]: "tmax"
    })

    df["date"] = pd.to_datetime(df["date"])
    df["tmean"] = (df["tmin"] + df["tmax"]) / 2

    return df[["date", "tmean", "tmin", "tmax"]]

df = load_base_data()

# -----------------------------
# 추가 데이터 업로드
# -----------------------------
st.sidebar.header("📂 데이터 업로드")
uploaded = st.sidebar.file_uploader(
    "같은 형식의 CSV 업로드",
    type="csv"
)

if uploaded:
    new_df = pd.read_csv(uploaded, encoding="cp949")
    new_df = new_df.rename(columns={
        new_df.columns[0]: "date",
        new_df.columns[2]: "tmin",
        new_df.columns[3]: "tmax"
    })
    new_df["date"] = pd.to_datetime(new_df["date"])
    new_df["tmean"] = (new_df["tmin"] + new_df["tmax"]) / 2
    new_df = new_df[["date", "tmean", "tmin", "tmax"]]

    df = (
        pd.concat([df, new_df])
        .drop_duplicates(subset="date", keep="last")
        .sort_values("date")
    )

# -----------------------------
# 날짜 선택
# -----------------------------
latest_date = df["date"].max()

selected_date = st.date_input(
    "📅 비교할 날짜 선택 (미선택 시 최근 날짜)",
    value=latest_date
)

selected_date = pd.to_datetime(selected_date)

# -----------------------------
# 비교 계산
# -----------------------------
target = df[df["date"] == selected_date]

if target.empty:
    st.warning("선택한 날짜의 데이터가 없습니다.")
    st.stop()

target_temp = target["tmean"].iloc[0]

df["month_day"] = df["date"].dt.strftime("%m-%d")
md = selected_date.strftime("%m-%d")

same_day_df = df[df["month_day"] == md]
historical_mean = same_day_df["tmean"].mean()
diff = target_temp - historical_mean

# -----------------------------
# 수치 요약
# -----------------------------
col1, col2, col3 = st.columns(3)

col1.metric("선택 날짜 평균기온", f"{target_temp:.1f} ℃")
col2.metric("과거 같은 날짜 평균", f"{historical_mean:.1f} ℃")
col3.metric(
    "기온 차이",
    f"{diff:+.1f} ℃",
    delta=diff
)

# -----------------------------
# Plotly 그래프
# -----------------------------
st.subheader("📈 과거 같은 날짜 기온 분포")

fig = px.scatter(
    same_day_df,
    x="date",
    y="tmean",
    labels={"tmean": "평균기온(℃)", "date": "연도"},
    title=f"{md} 기준 연도별 평균기온 분포"
)

fig.add_hline(
    y=historical_mean,
    line_dash="dash",
    annotation_text="과거 평균",
    annotation_position="top left"
)

fig.add_scatter(
    x=[selected_date],
    y=[target_temp],
    mode="markers",
    marker=dict(size=12, color="red"),
    name="선택 날짜"
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# 데이터 품질 정보
# -----------------------------
with st.expander("🔍 데이터 품질 확인"):
    st.write("결측치 개수")
    st.dataframe(df.isnull().sum())
