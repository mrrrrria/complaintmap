import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import streamlit.components.v1 as components


# ----------------------------
# NORMALIZE ISSUE TYPES
# ----------------------------
def normalize_issue(value):
    if not isinstance(value, str):
        return "Other"
    v = value.lower()
    if "air" in v:
        return "Air"
    if "noise" in v:
        return "Noise"
    if "heat" in v:
        return "Heat"
    if "odor" in v or "smell" in v:
        return "Odour"
    if "cycling" in v or "walking" in v:
        return "Cycling / Walking"
    return "Other"


# ----------------------------
# HYDERABAD AUTHORITIES
# ----------------------------
AUTHORITIES = {
    "Air": ("Telangana Pollution Control Board", "040-23887500", "pcb@telangana.gov.in"),
    "Noise": ("Hyderabad Traffic Police", "100", "trafficpolice@hyderabad.gov.in"),
    "Heat": ("GHMC – Environment Wing", "040-21111111", "environment-ghmc@telangana.gov.in"),
    "Odour": ("GHMC – Sanitation Department", "040-21111111", "sanitation-ghmc@telangana.gov.in"),
    "Cycling / Walking": ("GHMC – Urban Planning", "040-21111111", "planning-ghmc@telangana.gov.in"),
    "Other": ("Greater Hyderabad Municipal Corporation", "040-21111111", "info.ghmc@telangana.gov.in"),
}


# ----------------------------
# SOLUTION ENGINE
# ----------------------------
def generate_solutions(issue, intensity, nearby_count):
    intensity = int(intensity)

    SOLUTIONS = {
        "Air": {
            "low": ["Monitor air quality trends.", "Encourage reduced vehicle use."],
            "medium": ["Increase roadside tree cover.", "Promote public transport usage."],
            "high": ["Restrict high-emission vehicles.", "Introduce low-emission zones."],
        },
        "Noise": {
            "low": ["Monitor noise levels.", "Enforce time-based restrictions."],
            "medium": ["Implement traffic calming.", "Reroute heavy vehicles."],
            "high": ["Install noise barriers.", "Restrict night-time traffic."],
        },
        "Heat": {
            "low": ["Increase shaded walkways.", "Promote heat awareness."],
            "medium": ["Add reflective surfaces.", "Expand green infrastructure."],
            "high": ["Redesign public spaces for cooling.", "Apply cool-roof technologies."],
        },
        "Odour": {
            "low": ["Increase cleaning frequency.", "Inspect sanitation conditions."],
            "medium": ["Improve waste collection.", "Identify odor sources."],
            "high": ["Upgrade waste processing facilities.", "Enforce sanitation regulations."],
        },
        "Cycling / Walking": {
            "low": ["Improve signage.", "Fix minor surface issues."],
            "medium": ["Improve crossings.", "Separate traffic flows."],
            "high": ["Build dedicated lanes.", "Redesign dangerous intersections."],
        },
        "Other": {
            "low": ["Monitor the situation."],
            "medium": ["Conduct a site assessment."],
            "high": ["Plan infrastructure intervention."],
        },
    }

    tier = "low" if intensity <= 2 else "medium" if intensity == 3 else "high"
    primary = SOLUTIONS[issue][tier][0]
    additional = SOLUTIONS[issue][tier][1:]

    if nearby_count >= 3:
        additional.append(
            "Multiple nearby complaints detected – recommend immediate coordinated inspection."
        )

    return primary, additional


# ----------------------------
# MAIN RENDER
# ----------------------------
def render(df_all: pd.DataFrame):

    st.title("🗺️ Smart Complaint Solution Map – Hyderabad")

    if df_all.empty:
        st.info("No complaints available.")
        return

    df = df_all.copy()
    df["issue"] = df["issue_type"].apply(normalize_issue)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["intensity"] = df["intensity"].astype(int)

    df = df.sort_values("timestamp")
    latest = df.iloc[-1]

    distances = np.sqrt(
        (df["lat"] - latest["lat"]) ** 2 + (df["lon"] - latest["lon"]) ** 2
    )
    nearby_count = (distances < 0.002).sum()

    primary, additional = generate_solutions(
        latest["issue"], latest["intensity"], nearby_count
    )

    # Map
    m = folium.Map(location=[latest["lat"], latest["lon"]], zoom_start=14)
    HeatMap(df[["lat", "lon"]].values.tolist(), radius=25, blur=18).add_to(m)

    for _, row in df.iterrows():
        short, _ = generate_solutions(row["issue"], row["intensity"], nearby_count)
        popup = f"""
        <div style="width:320px;">
            <b>Issue:</b> {row['issue']}<br>
            <b>Intensity:</b> {row['intensity']} / 5<br>
            <b>Reported:</b> {row['timestamp']}<br><br>
            <b>Description:</b><br>{row['description'] or "—"}<br><br>
            <b>Suggested action:</b><br>{short}
        </div>
        """
        color = "red" if row["timestamp"] == latest["timestamp"] else "blue"
        folium.Marker(
            [row["lat"], row["lon"]],
            popup=popup,
            icon=folium.Icon(color=color, icon="info-sign"),
        ).add_to(m)

    st_folium(m, use_container_width=True, height=650)

    # ----------------------------
    # GREY SOLUTION BOX (FIXED)
    # ----------------------------
    auth = AUTHORITIES.get(latest["issue"], AUTHORITIES["Other"])

    html = f"""
    <div style="
        background:#f2f2f2;
        padding:24px;
        border-radius:12px;
        border:1px solid #ccc;
        font-family:Arial;
        line-height:1.5;
    ">
        <h3>Latest Report – Recommended Actions</h3>

        <p>
            <b>Issue:</b> {latest['issue']}<br>
            <b>Intensity:</b> {latest['intensity']} / 5<br>
            <b>Reported on:</b> {latest['timestamp']}
        </p>

        <hr>

        <p><b>Primary action</b><br>{primary}</p>

        <p><b>Additional actions</b></p>
        <ul>
            {''.join(f"<li>{s}</li>" for s in additional)}
        </ul>

        <hr>

        <p>
            <b>Responsible authority</b><br>
            {auth[0]}<br>
            📞 {auth[1]}<br>
            📧 {auth[2]}
        </p>
    </div>
    """

    # ⬇️ HEIGHT INCREASED SO NOTHING GETS CUT
    components.html(html, height=520)
