import folium
import streamlit as st
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import requests

from config import COLOR_MAP, DEFAULT_ZOOM


# -------------------------------------------------
# Fetch air pollution data (OpenAQ – Hyderabad)
# -------------------------------------------------
def fetch_pollutant(pollutant):
    url = "https://api.openaq.org/v2/measurements"
    params = {
        "city": "Hyderabad",
        "parameter": pollutant,
        "limit": 200,
        "sort": "desc",
    }
    try:
        r = requests.get(url, params=params, timeout=6)
        results = r.json().get("results", [])
        return [
            [d["coordinates"]["latitude"], d["coordinates"]["longitude"], d["value"]]
            for d in results
            if "coordinates" in d
        ]
    except Exception:
        return []


# -------------------------------------------------
# MAIN RENDER
# -------------------------------------------------
def render(df_all):
    st.header("🗺️ Environmental Issues & Air Quality – Hyderabad")

    if df_all.empty:
        st.info("No complaints reported yet.")
        return

    # ---------------- Filters ----------------
    st.subheader("Filters")

    c1, c2, c3 = st.columns(3)
    with c1:
        issue_filter = st.multiselect(
            "Issue type",
            sorted(df_all["issue_type"].unique()),
            default=sorted(df_all["issue_type"].unique()),
        )
    with c2:
        min_intensity = st.slider("Minimum intensity", 1, 5, 1)
    with c3:
        start_date = st.date_input(
            "From date", df_all["timestamp"].min().date()
        )

    # ✅ APPLY FILTERS FIRST
    df = df_all[
        (df_all["issue_type"].isin(issue_filter))
        & (df_all["intensity"] >= min_intensity)
        & (df_all["timestamp"].dt.date >= start_date)
    ]

    if df.empty:
        st.warning("No reports match the selected filters.")
        return

    # ---------------- Map center based on FILTERED data ----------------
    center = [df["lat"].mean(), df["lon"].mean()]
    m = folium.Map(location=center, zoom_start=DEFAULT_ZOOM)

    # -------------------------------------------------
    # 1️⃣ Heatmap of REPORTED ISSUES (FILTERED)
    # -------------------------------------------------
    issue_heat = [
        [r["lat"], r["lon"], r["intensity"]]
        for _, r in df.iterrows()
    ]

    HeatMap(
        issue_heat,
        radius=20,
        blur=15,
        min_opacity=0.3,
        name="Reported issues (citizens)",
    ).add_to(m)

    # -------------------------------------------------
    # 2️⃣ Markers of REPORTED ISSUES (FILTERED)
    # -------------------------------------------------
    for _, r in df.iterrows():
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=6,
            color=COLOR_MAP.get(r["issue_type"], "#2d6a4f"),
            fill=True,
            fill_opacity=0.9,
            popup=(
                f"<b>Issue:</b> {r['issue_type']}<br>"
                f"<b>Intensity:</b> {r['intensity']} / 5<br>"
                f"<b>Date:</b> {r['timestamp'].strftime('%Y-%m-%d')}"
            ),
        ).add_to(m)

    # -------------------------------------------------
    # 3️⃣ Air pollution heatmaps (OpenAQ)
    # -------------------------------------------------
    st.subheader("Air Pollution Layers (OpenAQ – real measurements)")

    show_pm25 = st.checkbox("Show PM2.5", True)
    show_pm10 = st.checkbox("Show PM10", False)

    if show_pm25:
        pm25 = fetch_pollutant("pm25")
        if pm25:
            HeatMap(
                pm25,
                radius=25,
                blur=18,
                min_opacity=0.2,
                name="PM2.5 concentration",
            ).add_to(m)
        else:
            st.warning("⚠️ No PM2.5 data currently available for Hyderabad (OpenAQ).")

    if show_pm10:
        pm10 = fetch_pollutant("pm10")
        if pm10:
            HeatMap(
                pm10,
                radius=25,
                blur=18,
                min_opacity=0.2,
                name="PM10 concentration",
            ).add_to(m)
        else:
            st.warning("⚠️ No PM10 data currently available for Hyderabad (OpenAQ).")

    folium.LayerControl(collapsed=False).add_to(m)

    st_folium(m, height=600, use_container_width=True)
