import os
import requests
import folium
import streamlit as st
from folium.plugins import HeatMap
from streamlit_folium import st_folium

from config import DEFAULT_ZOOM, COLOR_MAP

# -------------------------------------------------
# HYDERABAD BOUNDING BOX (GHMC area)
# -------------------------------------------------
HYD_LAT_MIN = 17.2
HYD_LAT_MAX = 17.6
HYD_LON_MIN = 78.2
HYD_LON_MAX = 78.7

# -------------------------------------------------
# OpenAQ config
# -------------------------------------------------
PARAM_IDS = {
    "pm25": 2,
    "pm10": 1,
}

MAX_LOCATIONS = 500


def get_openaq_api_key():
    key = os.getenv("OPENAQ_API_KEY")
    if key:
        return key
    try:
        from config import OPENAQ_API_KEY
        return OPENAQ_API_KEY
    except Exception:
        return None


# -------------------------------------------------
# OpenAQ helpers
# -------------------------------------------------
def fetch_locations_hyderabad(parameter):
    api_key = get_openaq_api_key()
    if not api_key:
        raise RuntimeError("Missing OpenAQ API key")

    url = "https://api.openaq.org/v3/locations"
    params = {
        "parameters_id": PARAM_IDS[parameter],
        "limit": MAX_LOCATIONS,
        "iso": "IN",
    }
    headers = {"X-API-Key": api_key}

    r = requests.get(url, params=params, headers=headers, timeout=15)
    r.raise_for_status()
    data = r.json()

    locations = []
    for loc in data.get("results", []):
        coords = loc.get("coordinates") or {}
        lat, lon = coords.get("latitude"), coords.get("longitude")
        if lat is None or lon is None:
            continue

        lat, lon = float(lat), float(lon)

        if HYD_LAT_MIN <= lat <= HYD_LAT_MAX and HYD_LON_MIN <= lon <= HYD_LON_MAX:
            locations.append({"id": loc["id"], "lat": lat, "lon": lon})

    return locations


def fetch_sensor_id(location_id, parameter):
    api_key = get_openaq_api_key()
    url = f"https://api.openaq.org/v3/locations/{location_id}/sensors"
    params = {"parameters_id": PARAM_IDS[parameter], "limit": 1}
    headers = {"X-API-Key": api_key}

    r = requests.get(url, params=params, headers=headers, timeout=15)
    r.raise_for_status()
    res = r.json().get("results", [])
    return res[0]["id"] if res else None


def fetch_latest_value(sensor_id):
    api_key = get_openaq_api_key()
    url = f"https://api.openaq.org/v3/sensors/{sensor_id}/measurements/hourly"
    headers = {"X-API-Key": api_key}
    params = {"limit": 1, "sort_order": "desc"}

    r = requests.get(url, params=params, headers=headers, timeout=15)
    r.raise_for_status()
    res = r.json().get("results", [])
    return float(res[0]["value"]) if res else None


def fetch_aqi_points_hyderabad(parameter):
    points = []
    locations = fetch_locations_hyderabad(parameter)

    for loc in locations:
        try:
            sensor_id = fetch_sensor_id(loc["id"], parameter)
            if not sensor_id:
                continue
            value = fetch_latest_value(sensor_id)
            if value is None:
                continue
            points.append([loc["lat"], loc["lon"], value])
        except Exception:
            continue

    return points


# -------------------------------------------------
# MAIN RENDER FUNCTION
# -------------------------------------------------
def render(df_all):
    st.header("🌍 Environmental Heatmap – Hyderabad")

    pollutant = st.selectbox(
        "Air pollutant (OpenAQ – real time)",
        ["pm25", "pm10"],
        index=0,
    )

    if not get_openaq_api_key():
        st.error("Missing OpenAQ API key")
        return

    if st.button("🔄 Load / Refresh air quality data"):
        with st.spinner("Fetching real-time air quality for Hyderabad…"):
            st.session_state["aqi_points"] = fetch_aqi_points_hyderabad(pollutant)

    aqi_points = st.session_state.get("aqi_points")

    if not aqi_points:
        st.info("Click **Load / Refresh** to display air pollution data.")
        return

    # Normalize AQI values
    values = [p[2] for p in aqi_points]
    vmin, vmax = min(values), max(values)

    aqi_heat = (
        [[p[0], p[1], 1.0] for p in aqi_points]
        if vmax == vmin
        else [[p[0], p[1], (p[2] - vmin) / (vmax - vmin)] for p in aqi_points]
    )

    # Map center = Hyderabad
    center = [17.385, 78.4867]
    m = folium.Map(location=center, zoom_start=DEFAULT_ZOOM)

    # AQI heatmap
    HeatMap(
        aqi_heat,
        radius=18,
        blur=15,
        gradient={0.0: "green", 0.5: "yellow", 1.0: "red"},
    ).add_to(m)

    # Citizen complaints heatmap
    if not df_all.empty:
        issue_heat = [
            [row["lat"], row["lon"], row["intensity"]]
            for _, row in df_all.iterrows()
        ]
        HeatMap(issue_heat, radius=12, blur=10).add_to(m)

        # Markers for reported issues
        for _, row in df_all.iterrows():
            folium.CircleMarker(
                [row["lat"], row["lon"]],
                radius=4,
                color=COLOR_MAP.get(row["issue_type"], "black"),
                fill=True,
                fill_opacity=0.9,
            ).add_to(m)

    st_folium(m, height=650, use_container_width=True)

    st.caption(
        f"""
**City:** Hyderabad  
**Air pollutant:** {pollutant.upper()} (µg/m³)  
**Stations used:** {len(aqi_points)}  
**Min value:** {vmin:.1f} · **Max value:** {vmax:.1f}  
Citizen issue density and air pollution are visualised together.
"""
    )
