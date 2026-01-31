import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import pandas as pd
import streamlit.components.v1 as components


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
    if "cycle" in v or "walk" in v:
        return "Cycling / Walking"
    return "Other"


# --------------------------------------------------
# HYDERABAD AUTHORITIES
# --------------------------------------------------
AUTHORITIES = {
    "Air": {
        "dept": "Telangana Pollution Control Board",
        "phone": "040-23887500",
        "email": "pcb@telangana.gov.in",
    },
    "Noise": {
        "dept": "Hyderabad Traffic Police",
        "phone": "100",
        "email": "trafficpolice@hyderabad.gov.in",
    },
    "Heat": {
        "dept": "GHMC – Environment Wing",
        "phone": "040-21111111",
        "email": "environment-ghmc@telangana.gov.in",
    },
    "Odour": {
        "dept": "GHMC – Sanitation Department",
        "phone": "040-21111111",
        "email": "sanitation-ghmc@telangana.gov.in",
    },
    "Cycling / Walking": {
        "dept": "GHMC – Urban Planning",
        "phone": "040-21111111",
        "email": "planning-ghmc@telangana.gov.in",
    },
    "Other": {
        "dept": "Greater Hyderabad Municipal Corporation",
        "phone": "040-21111111",
        "email": "info-ghmc@telangana.gov.in",
    },
}


# --------------------------------------------------
# SOLUTION LOGIC (HYDERABAD)
# --------------------------------------------------
def primary_solution(issue, intensity):
    if intensity <= 2:
        return "Monitor the issue and raise local awareness."
    if intensity == 3:
        return "Implement medium-scale corrective measures."
    return "Immediate infrastructure-level intervention required."


def additional_solutions(issue):
    return {
        "Air": [
            "Promote public transport usage.",
            "Increase urban green cover."
        ],
        "Noise": [
            "Restrict heavy vehicles during peak hours.",
            "Enforce noise regulations."
        ],
        "Heat": [
            "Increase shaded public areas.",
            "Introduce heat-resilient urban design."
        ],
        "Odour": [
            "Improve waste segregation.",
            "Inspect sanitation infrastructure."
        ],
        "Cycling / Walking": [
            "Improve pedestrian crossings.",
            "Develop protected cycling lanes."
        ],
        "Other": [
            "Conduct a field inspection."
        ],
    }.get(issue, [])


# --------------------------------------------------
# MAIN RENDER FUNCTION
# --------------------------------------------------
def render(df_all: pd.DataFrame):

    st.title("🗺️ Smart Complaint Solution Map – Hyderabad")

    if df_all.empty:
        st.info("No complaints available.")
        return

    df = df_all.copy()
    df["issue"] = df["issue_type"].apply(normalize_issue)
    df["intensity"] = df["intensity"].fillna(1).astype(int)

    df = df.sort_values("timestamp")
    latest = df.iloc[-1]

    # --------------------------------------------------
    # MAP
    # --------------------------------------------------
    m = folium.Map(
        location=[latest["lat"], latest["lon"]],
        zoom_start=13
    )

    # Heatmap
    HeatMap(
        df[["lat", "lon"]].values.tolist(),
        radius=25,
        blur=18
    ).add_to(m)

    # Markers
    for _, row in df.iterrows():
        is_latest = row["timestamp"] == latest["timestamp"]
        color = "red" if is_latest else "blue"

        popup_html = f"""
        <div style="font-size:13px;">
            <b>Issue:</b> {row['issue']}<br>
            <b>Intensity:</b> {row['intensity']} / 5<br>
            <b>Reported:</b> {row['timestamp']}<br><br>
            <b>Description:</b><br>
            {row['description'] or "—"}
        </div>
        """

        folium.Marker(
            [row["lat"], row["lon"]],
            popup=popup_html,
            icon=folium.Icon(color=color, icon="info-sign"),
        ).add_to(m)

    st_folium(m, height=650, use_container_width=True)

    # --------------------------------------------------
    # CLEAN SOLUTION PANEL
    # --------------------------------------------------
    issue = latest["issue"]
    authority = AUTHORITIES.get(issue, AUTHORITIES["Other"])
    primary = primary_solution(issue, latest["intensity"])
    extras = additional_solutions(issue)

    extras_html = "".join(f"<li>{e}</li>" for e in extras)

    html_block = f"""
    <div style="
        background:#f9fafb;
        padding:22px;
        border-radius:12px;
        border:1px solid #e5e7eb;
        font-family:Arial;
    ">

        <h3 style="margin-top:0;">Latest Report – Recommended Actions</h3>

        <p>
            <b>Issue:</b> {issue}<br>
            <b>Intensity:</b> {latest['intensity']} / 5<br>
            <b>Reported on:</b> {latest['timestamp']}
        </p>

        <hr>

        <p><b>Primary action</b><br>
        {primary}</p>

        <p><b>Additional actions</b></p>
        <ul>{extras_html}</ul>

        <hr>

        <p>
            <b>Responsible authority</b><br>
            {authority['dept']}<br>
            📞 {authority['phone']}<br>
            📧 {authority['email']}
        </p>

    </div>
    """

    components.html(html_block, height=420)
