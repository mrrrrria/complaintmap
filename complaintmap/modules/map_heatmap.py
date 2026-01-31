import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import streamlit.components.v1 as components
from datetime import datetime


# --------------------------------------------------
# NORMALIZE ISSUE TYPES
# --------------------------------------------------
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


# --------------------------------------------------
# HYDERABAD AUTHORITIES
# --------------------------------------------------
AUTHORITIES = {
    "Air": ("Telangana Pollution Control Board", "040-23887500", "pcb@telangana.gov.in"),
    "Noise": ("Hyderabad Traffic Police", "100", "trafficpolice@hyderabad.gov.in"),
    "Heat": ("GHMC – Environment Wing", "040-21111111", "environment-ghmc@telangana.gov.in"),
    "Odour": ("GHMC – Sanitation Department", "040-21111111", "sanitation-ghmc@telangana.gov.in"),
    "Cycling / Walking": ("GHMC – Urban Planning", "040-21111111", "planning-ghmc@telangana.gov.in"),
    "Other": ("Greater Hyderabad Municipal Corporation", "040-21111111", "info.ghmc@telangana.gov.in"),
}


# --------------------------------------------------
# SOLUTION ENGINE
# --------------------------------------------------
def generate_solutions(issue, intensity, nearby_count):
    intensity = int(intensity)

    # Base solutions by issue & intensity
    SOLUTIONS = {
        "Air": {
            "low": [
                "Monitor air quality trends.",
                "Encourage reduced vehicle use."
            ],
            "medium": [
                "Increase roadside tree cover.",
                "Promote public transport usage."
            ],
            "high": [
                "Restrict high-emission vehicles.",
                "Introduce low-emission zones."
            ],
        },
        "Noise": {
            "low": [
                "Monitor noise levels.",
                "Enforce time-based restrictions."
            ],
            "medium": [
                "Implement traffic calming.",
                "Reroute heavy vehicles."
            ],
            "high": [
                "Install noise barriers.",
                "Restrict night-time heavy traffic."
            ],
        },
        "Heat": {
            "low": [
                "Increase shaded walkways.",
                "Promote heat awareness."
            ],
            "medium": [
                "Add reflective surfaces.",
                "Expand green infrastructure."
            ],
            "high": [
                "Redesign public spaces for cooling.",
                "Deploy cool-roof technologies."
            ],
        },
        "Odour": {
            "low": [
                "Increase cleaning frequency.",
                "Inspect sanitation conditions."
            ],
            "medium": [
                "Improve waste collection.",
                "Identify odor sources."
            ],
            "high": [
                "Upgrade waste processing facilities.",
                "Enforce sanitation regulations."
            ],
        },
        "Cycling / Walking": {
            "low": [
                "Improve signage.",
                "Fix minor surface issues."
            ],
            "medium": [
                "Improve crossings.",
                "Separate traffic flows."
            ],
            "high": [
                "Build dedicated lanes.",
                "Redesign dangerous intersections."
            ],
        },
        "Other": {
            "low": ["Monitor the situation."],
            "medium": ["Conduct a site assessment."],
            "high": ["Plan infrastructure intervention."],
        },
    }

    # Intensity tier
    if intensity <= 2:
        tier = "low"
    elif intensity == 3:
        tier = "medium"
    else:
        tier = "high"

    primary = SOLUTIONS[issue][tier][0]
    additional = SOLUTIONS[issue][tier][1:]

    # Escalation based on proximity
    if nearby_count >= 3:
        additional.append(
            "Multiple complaints detected nearby – recommend immediate inspection and coordinated action."
        )

    return primary, additional


# --------------------------------------------------
# MAIN RENDER FUNCTION
# --------------------------------------------------
def render(df_all: pd.DataFrame):

    st.title("🗺️ Smart Complaint Solution Map – Hyderabad")

    if df_all is None or df_all.empty:
        st.info("No complaints available.")
        return

    df = df_all.copy()

    required = ["issue_type", "intensity", "lat", "lon", "timestamp", "description"]
    for col in required:
        if col not in df.columns:
            st.error(f"Missing column: {col}")
            return

    df["issue"] = df["issue_type"].apply(normalize_issue)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["intensity"] = df["intensity"].astype(int)

    # Sort & get latest
    df = df.sort_values("timestamp")
    latest = df.iloc[-1]

    # Proximity count (simple radius check)
    distances = np.sqrt(
        (df["lat"] - latest["lat"]) ** 2 + (df["lon"] - latest["lon"]) ** 2
    )
    nearby_count = (distances < 0.002).sum()  # ~200m

    # Generate solutions
    primary_solution, additional_solutions = generate_solutions(
        latest["issue"], latest["intensity"], nearby_count
    )

    # Map
    m = folium.Map(
        location=[latest["lat"], latest["lon"]],
        zoom_start=14
    )

    # Heatmap
    HeatMap(df[["lat", "lon"]].values.tolist(), radius=25, blur=18).add_to(m)

    # Markers
    for _, row in df.iterrows():
        short_solution, _ = generate_solutions(
            row["issue"], row["intensity"], nearby_count
        )

        popup_html = f"""
        <div style="width:320px; font-size:14px;">
            <b>Issue:</b> {row['issue']}<br>
            <b>Intensity:</b> {row['intensity']} / 5<br>
            <b>Reported:</b> {row['timestamp']}<br><br>
            <b>Description:</b><br>
            {row['description'] or "—"}<br><br>
            <b>Suggested action:</b><br>
            {short_solution}
        </div>
        """

        color = "red" if row["timestamp"] == latest["timestamp"] else "blue"

        folium.Marker(
            [row["lat"], row["lon"]],
            popup=popup_html,
            icon=folium.Icon(color=color, icon="info-sign"),
        ).add_to(m)

    st_folium(m, use_container_width=True, height=650)

    # --------------------------------------------------
    # CLEAN SOLUTION PANEL
    # --------------------------------------------------
    authority = AUTHORITIES.get(latest["issue"], AUTHORITIES["Other"])

    html = f"""
    <div style="
        background:#ffffff;
        padding:22px;
        border-radius:12px;
        border:1px solid #ddd;
        margin-top:20px;
        font-family:Arial;
    ">
        <h3>📝 Latest Report – Recommended Actions</h3>

        <p>
            <b>Issue:</b> {latest['issue']}<br>
            <b>Intensity:</b> {latest['intensity']} / 5<br>
            <b>Reported on:</b> {latest['timestamp']}
        </p>

        <hr>

        <p><b>Primary action</b><br>{primary_solution}</p>

        <p><b>Additional actions</b></p>
        <ul>
            {''.join(f'<li>{s}</li>' for s in additional_solutions)}
        </ul>

        <hr>

        <p><b>Responsible authority</b><br>
        {authority[0]}<br>
        📞 {authority[1]}<br>
        📧 {authority[2]}
        </p>
    </div>
    """

    components.html(html, height=380)
