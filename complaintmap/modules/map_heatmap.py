import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import pandas as pd
import streamlit.components.v1 as components


# ---------------------------------------------------------
# NORMALIZE ISSUE NAMES
# ---------------------------------------------------------
def normalize_issue(value):
    if not isinstance(value, str):
        return "Other"

    v = value.strip().lower()

    if "air" in v:
        return "Air"
    if "noise" in v:
        return "Noise"
    if "heat" in v:
        return "Heat"
    if "odor" in v or "odour" in v or "smell" in v:
        return "Odour"
    if "cycling" in v or "walking" in v:
        return "Cycling / Walking"

    return "Other"


# ---------------------------------------------------------
# HYDERABAD-SPECIFIC SOLUTIONS
# ---------------------------------------------------------
def generate_solutions(issue, intensity):
    intensity = int(intensity)

    SOLUTIONS = {
        "Odour": {
            "primary": [
                "Inspect waste collection points and sanitation facilities.",
                "Upgrade waste processing and treatment systems.",
                "Identify and control odor-generating sources."
            ],
            "additional": [
                "Increase waste collection frequency.",
                "Improve waste segregation at source.",
                "Enforce sanitation regulations in affected areas."
            ]
        },
        "Air": {
            "primary": [
                "Reduce traffic congestion in affected zones.",
                "Control emissions from nearby industries."
            ],
            "additional": [
                "Promote public transport usage.",
                "Increase urban green cover.",
                "Conduct regular air quality monitoring."
            ]
        },
        "Noise": {
            "primary": [
                "Enforce noise limits in residential areas.",
                "Restrict heavy vehicle movement during night hours."
            ],
            "additional": [
                "Install noise barriers.",
                "Improve traffic flow management."
            ]
        },
        "Heat": {
            "primary": [
                "Increase shaded areas and tree cover.",
                "Apply heat-reflective materials on roads and buildings."
            ],
            "additional": [
                "Develop urban green corridors.",
                "Improve water sprinkling in high-heat zones."
            ]
        },
        "Cycling / Walking": {
            "primary": [
                "Improve pedestrian crossings and footpaths.",
                "Develop dedicated cycling lanes."
            ],
            "additional": [
                "Improve street lighting.",
                "Implement traffic calming measures."
            ]
        },
        "Other": {
            "primary": ["Conduct a site inspection."],
            "additional": ["Coordinate with relevant departments."]
        }
    }

    data = SOLUTIONS.get(issue, SOLUTIONS["Other"])
    primary = data["primary"][min(intensity - 1, len(data["primary"]) - 1)]
    additional = data["additional"]

    return primary, additional


# ---------------------------------------------------------
# RESPONSIBLE AUTHORITIES (HYDERABAD)
# ---------------------------------------------------------
AUTHORITIES = {
    "Odour": ("GHMC – Sanitation Department", "040-21111111", "sanitation-ghmc@telangana.gov.in"),
    "Air": ("Telangana Pollution Control Board", "040-23887500", "pcb@telangana.gov.in"),
    "Noise": ("Hyderabad Traffic Police", "100", "trafficpolice@hyderabad.gov.in"),
    "Heat": ("GHMC – Environment Wing", "040-21111111", "environment-ghmc@telangana.gov.in"),
    "Cycling / Walking": ("GHMC – Urban Planning", "040-21111111", "planning-ghmc@telangana.gov.in"),
    "Other": ("Greater Hyderabad Municipal Corporation", "040-21111111", "info.ghmc@telangana.gov.in"),
}


# ---------------------------------------------------------
# MAIN RENDER FUNCTION
# ---------------------------------------------------------
def render(df_all: pd.DataFrame):

    st.title("🗺️ Smart Complaint Solution Map – Hyderabad")

    if df_all is None or df_all.empty:
        st.info("No complaint data available.")
        return

    df = df_all.copy()

    required = ["issue_type", "intensity", "lat", "lon", "timestamp", "description"]
    for col in required:
        if col not in df.columns:
            st.error(f"Missing column: {col}")
            return

    df["issue"] = df["issue_type"].apply(normalize_issue)
    df["intensity"] = df["intensity"].fillna(1).astype(int)

    # Latest report
    df = df.sort_values("timestamp")
    latest = df.iloc[-1]

    # -----------------------------------------------------
    # MAP
    # -----------------------------------------------------
    m = folium.Map(
        location=[latest["lat"], latest["lon"]],
        zoom_start=14
    )

    # Heatmap of all complaints
    HeatMap(df[["lat", "lon"]].values.tolist(), radius=25, blur=18).add_to(m)

    for _, row in df.iterrows():
        primary, _ = generate_solutions(row["issue"], row["intensity"])

        popup_html = f"""
        <div style="width:320px;font-family:Arial;">
            <b>Issue:</b> {row['issue']}<br>
            <b>Intensity:</b> {row['intensity']} / 5<br>
            <b>Reported:</b> {row['timestamp']}<br><br>
            <b>Description:</b><br>{row['description'] or '—'}<br><br>
            <b>Suggested action:</b><br>{primary}
        </div>
        """

        color = "red" if row.name == latest.name else "blue"

        folium.Marker(
            [row["lat"], row["lon"]],
            popup=popup_html,
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)

    st_folium(m, width=1400, height=650)

    # -----------------------------------------------------
    # BOTTOM SOLUTION BOX (CLEAN GREY STYLE)
    # -----------------------------------------------------
    primary, additional = generate_solutions(latest["issue"], latest["intensity"])
    auth = AUTHORITIES.get(latest["issue"], AUTHORITIES["Other"])

    html = f"""
    <div style="
        background:#f4f4f4;
        padding:26px;
        border-radius:14px;
        border:1px solid #d0d0d0;
        font-family: Arial, sans-serif;
        color:#222;
    ">
        <div style="
            background:#e6e6e6;
            padding:14px 18px;
            border-radius:10px;
            font-size:18px;
            font-weight:600;
            margin-bottom:18px;
        ">
            📌 Current Reported Solution
        </div>

        <b>Reported Issue:</b> {latest['issue']}<br>
        <b>Intensity:</b> {latest['intensity']} / 5<br>
        <b>Reported on:</b> {latest['timestamp']}<br>

        <hr style="margin:18px 0;">

        <b>Primary suggested action</b><br>
        {primary}

        <br><br>

        <b>Additional actions</b>
        <ul>
            {''.join(f"<li>{s}</li>" for s in additional)}
        </ul>

        <hr style="margin:18px 0;">

        <b>Responsible authority</b><br>
        {auth[0]}<br>
        📞 {auth[1]}<br>
        📧 {auth[2]}
    </div>
    """

    components.html(html, height=560)
