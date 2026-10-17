import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="서울 기온 분석", layout="wide", page_icon="🌡️")

# ---------- 데이터 로드 ----------
@st.cache_data
def load_data(path: str = "seoul_temperature.csv") -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig", dtype={"날짜": str})
    df["날짜"] = pd.to_datetime(df["날짜"].str.strip())
    df["연도"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month
    df["일교차"] = df["최고기온(℃)"] - df["최저기온(℃)"]
    return df

df = load_data()

# ---------- 연도 범위 선택 (사이드바) ----------
min_year, max_year = int(df["연도"].min()), int(df["연도"].max())
year_range = st.sidebar.slider(
    "연도 범위 선택",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1,
)

mask = (df["연도"] >= year_range[0]) & (df["연도"] <= year_range[1])
sel = df[mask]

# ---------- 1. 연도별 평균기온 + 5년 이동평균 ----------
annual = (
    df.groupby("연도")["평균기온(℃)"]
    .mean()
    .reset_index()
    .rename(columns={"평균기온(℃)": "연평균기온"})
)
annual["5년 이동평균"] = annual["연평균기온"].rolling(5, center=True).mean()

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=annual["연도"],
        y=annual["연평균기온"],
        mode="lines+markers",
        name="연평균기온",
        line=dict(color="#1f77b4", width=2.2),
        marker=dict(size=5),
    )
)
fig.add_trace(
    go.Scatter(
        x=annual["연도"],
        y=annual["5년 이동평균"],
        mode="lines",
        name="5년 이동평균",
        line=dict(color="#d62728", width=2.5, dash="dash"),
    )
)
fig.add_vrect(
    x0=year_range[0],
    x1=year_range[1],
    fillcolor="powderblue",
    opacity=0.35,
    line_width=0,
    name="선택 구간",
)
fig.update_layout(
    title="연도별 평균기온과 5년 이동평균 (서울, 지점 108)",
    xaxis_title="연도",
    yaxis_title="기온 (℃)",
    hovermode="x unified",
    margin=dict(l=50, r=20, t=60, b=50),
)
st.plotly_chart(fig, use_container_width=True)

# ---------- 선택 구간 통계 ----------
avg = sel["평균기온(℃)"].mean()
max_avg = sel["최고기온(℃)"].mean()
min_avg = sel["최저기온(℃)"].mean()

c1, c2, c3 = st.columns(3)
c1.metric("선택 구간 평균기온", f"{avg:.2f} ℃")
c2.metric("선택 구간 평균 최고기온", f"{max_avg:.2f} ℃")
c3.metric("선택 구간 평균 최저기온", f"{min_avg:.2f} ℃")

yearly_stats = (
    sel.groupby("연도")
    .agg(
        평균기온=("평균기온(℃)", "mean"),
        최고기온=("최고기온(℃)", "mean"),
        최저기온=("최저기온(℃)", "mean"),
    )
    .reset_index()
    .sort_values("연도")
)
st.dataframe(
    yearly_stats.style.format({"평균기온": "{:.2f}", "최고기온": "{:.2f}", "최저기온": "{:.2f}"}),
    use_container_width=True,
    height=260,
)

# ---------- 2. 월별 히트맵 ----------
heatmap_data = df.pivot_table(index="연도", columns="월", values="평균기온(℃)", aggfunc="mean")
fig_heatmap = go.Figure(
    go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale="RdYlBu_r",
        colorbar=dict(title="평균기온 (℃)"),
    )
)
fig_heatmap.update_layout(
    title="월별 평균기온 히트맵",
    xaxis_title="월",
    yaxis_title="연도",
    margin=dict(l=50, r=20, t=70, b=50),
)
st.plotly_chart(fig_heatmap, use_container_width=True)

# ---------- 3. 최고기온 상위 10일 / 최저기온 하위 10일 ----------
top10 = (
    df.nlargest(10, "최고기온(℃)")[
        ["날짜", "연도", "평균기온(℃)", "최저기온(℃)", "최고기온(℃)"]
    ]
    .rename(columns={"최고기온(℃)": "최고기온"})
)
bottom10 = (
    df.nsmallest(10, "최저기온(℃)")[
        ["날짜", "연도", "평균기온(℃)", "최저기온(℃)"]
    ]
    .rename(columns={"최저기온(℃)": "최저기온"})
)

c4, c5 = st.columns(2)
with c4:
    st.subheader("최고기온 상위 10일")
    st.dataframe(top10, use_container_width=True)
with c5:
    st.subheader("최저기온 하위 10일")
    st.dataframe(bottom10, use_container_width=True)

# ---------- 4. 일교차 컬럼 + 연도별 평균 일교차 ----------
annual_range = (
    df.groupby("연도")["일교차"]
    .mean()
    .reset_index()
    .rename(columns={"일교차": "평균 일교차"})
)
fig_range = go.Figure(
    go.Scatter(
        x=annual_range["연도"],
        y=annual_range["평균 일교차"],
        mode="lines+markers",
        name="평균 일교차",
        line=dict(color="#2ca02c", width=2.2),
        marker=dict(size=5),
    )
)
fig_range.update_layout(
    title="연도별 평균 일교차",
    xaxis_title="연도",
    yaxis_title="평균 일교차 (℃)",
    hovermode="x unified",
    margin=dict(l=50, r=20, t=60, b=50),
)
st.plotly_chart(fig_range, use_container_width=True)

# ---------- 참고 ----------
with st.expander("데이터 정보"):
    st.write(f"전체 기간: {df['날짜'].min().date()} ~ {df['날짜'].max().date()}")
    st.write(f"전체 연도 수: {df['연도'].nunique()}년, 총 관측 일수: {len(df):,}일")
    st.write("지점 108 = 서울")
