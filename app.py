import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="서울 기온 분석", layout="wide", page_icon="🌡️")

# ---------- 제목 ----------
st.title("서울 기온 분석")

# ---------- 우사기 이미지 (외부 URL이 없어 인라인 SVG로 대체, 실제 URL 있으면 교체) ----------
st.markdown(
    """
    <div style="text-align:center; margin:8px 0 16px 0;">
      <svg width="140" height="150" viewBox="0 0 140 150" xmlns="http://www.w3.org/2000/svg">
        <path d="M30 40 C10 20 5 55 35 70 L30 80 Z" fill="#f5c5dc"/>
        <path d="M110 40 C130 20 135 55 105 70 L110 80 Z" fill="#f5c5dc"/>
        <ellipse cx="70" cy="75" rx="45" ry="40" fill="#f5c5dc"/>
        <path d="M62 100 L70 115 L78 100 Z" fill="#a8d8a8"/>
        <circle cx="58" cy="62" r="4" fill="#333"/>
        <circle cx="82" cy="62" r="4" fill="#333"/>
        <circle cx="52" cy="82" r="6" fill="#f5c5dc" opacity="0.6"/>
        <circle cx="88" cy="82" r="6" fill="#f5c5dc" opacity="0.6"/>
        <line x1="50" y1="100" x2="35" y2="105" stroke="#333" stroke-width="1.5"/>
        <line x1="50" y1="105" x2="37" y2="112" stroke="#333" stroke-width="1.5"/>
        <line x1="88" y1="100" x2="103" y2="105" stroke="#333" stroke-width="1.5"/>
        <line x1="88" y1="105" x2="105" y2="112" stroke="#333" stroke-width="1.5"/>
      </svg>
      <p style="margin:6px 0 0 0; color:#555; font-size:14px;">🐰 우사기</p>
    </div>
    """,
    unsafe_allow_html=True,
)

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
show_trend = st.checkbox("연평균기온 추세선 표시", value=False)
if show_trend:
    x = annual["연도"].values
    y = annual["연평균기온"].values
    z = np.polyfit(x, y, 1)
    trend = np.poly1d(z)
    fig.add_trace(
        go.Scatter(
            x=annual["연도"],
            y=trend(annual["연도"]),
            mode="lines",
            name="추세선",
            line=dict(color="green", dash="dot"),
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

# ---------- 2. 월별 히트맵 (빨강-흰색-파랑) ----------
heatmap_data = df.pivot_table(index="연도", columns="월", values="평균기온(℃)", aggfunc="mean")
fig_heatmap = go.Figure(
    go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale=[[0, "#d62728"], [0.5, "#ffffff"], [1, "#1f77b4"]],
        colorbar=dict(title="평균기온 (℃)", tickprefix="℃"),
    )
)
fig_heatmap.update_layout(
    title="월별 평균기온 히트맵 (빨강-흰색-파랑)",
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

# ---------- 데이터 해석 시 주의사항 ----------
with st.expander("데이터 해석 시 주의사항"):
    st.markdown(
        """
        - 각 연도 평균은 해당 연도 모든 관측일의 단순 평균이며, 관측 일수·윤년 여부에 따라 달라질 수 있습니다.
        - 월별 히트맵은 월 전체 관측일 평균이므로, 관측 일수 차이가 색상에 영향을 줄 수 있습니다.
        - 5년 이동평균은 중심 기준 5년 창으로 계산되어, 1907~1909년에는 5년 미만 데이터로 값이 존재하지 않습니다.
        - 추세선은 단순 선형 회귀로, 계절적 변동이나 이상 기후를 반영하지 않습니다.
        - 역사적 관측 자료는 관측소 위치 변경, 관측 장비/방식 변화, 도시화(열섬) 효과 등으로 인해 현대 자료와 직접 비교 시 보정이 필요할 수 있습니다.
        - 극단값(폭염·혹한)은 연평균과 다른 패턴을 보일 수 있으므로 별도 검토가 필요합니다.
        - 결측치가 포함되어 있을 수 있으며, 일교차는 관측 시각·정오 관측 유무에 따라 달라질 수 있습니다.
        """,
        unsafe_allow_html=True,
    )
