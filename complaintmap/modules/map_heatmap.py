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

    v = value.lower().strip()
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
# SOLUTION GENERATORS (HYDERABAD-SPECIFIC)
# --------------------------------------------------
def generate_solution(issue, intensity):
    if intensity <= 2:
        return {
            "Air": "Monitor local emissions and promote low-pollution mobility.",
            "Noise": "Enforce local noise regulations and awareness.",
            "Heat": "Increase shaded areas and drinking water points.",
            "Odour": "Inspect sanitation conditions.",
            "Cycling / Walking": "Improve signage and minor repairs.",
            "Other": "Monitor the situation."
        }.get(issue, "Monitor the situation.")

    if intensity == 3:
        return {
            "Air": "Reduce vehicle emissions and improve green buffers.",
            "Noise": "Traffic calming and time-based restrictions.",
            "Heat": "Add tree cover and cool roofing.",
            "Odour": "Improve waste collection and treatment.",
            "Cycling / Walking": "Improve crossings and lighting.",
            "Other": "Conduct a local assessment."
        }.get(issue, "Conduct a local assessment.")

    return {
        "Air": "Restrict high-emission vehicles and enforce pollution control.",
        "Noise": "Install noise barriers and restrict heavy vehicles.",
        "Heat": "Urban redesign with cooling infrastructure.",
        "Odour": "Upgrade waste processing facilities.",
        "Cycling / Walking": "Build protected lanes and redesign streets.",
        "Other": "Plan infrastructure-level intervention."
    }.get(issue, "Plan infrastructure-level intervention.")


def additional_actions(issue):
    return {
        "Air": [
            "Promote public transport and EV adoption.",
            "Increase urban greenery."
        ],
        "Noise": [
            "Enforce silent zones near hospitals and schools.",
            "Restrict night-time construction."
        ],
        "Heat": [
            "Deploy cool pavements.",
            "Expand urban green corridors."
        ],
        "Odour": [
            "Improve waste segregation.",
            "Inspect odor-generating facilities."
        ],
        "Cycling / Walking": [
            "Add protected cycling lanes.",
            "Improve pedestrian crossings."
        ],
        "Other": [
            "Escalate to city authorities."
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

    df_sorted = df.sort_values("timestamp")
    latest = df_sorted.iloc[-1]

    # --------------------------------------------------
    # MAP
    # --------------------------------------------------
    m = folium.Map(
        location=[latest["lat"], latest["lon"]],
        zoom_start=13
    )

    # Heatmap of reported issues
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
        <div style="width:260px;">
            <b>Issue:</b> {row['issue']}<br>
            <b>Intensity:</b> {row['intensity']} / 5<br>
            <b>Reported on:</b> {row['timestamp']}<br><br>
            <b>Description:</b><br>
            {row['description'] or '—'}<br><br>
            <b>Suggested action:</b><br>
            {generate_solution(row['issue'], row['intensity'])}
        </div>
        """

        folium.Marker(
            [row["lat"], row["lon"]],
            popup=popup_html,
            icon=folium.Icon(color=color, icon="info-sign"),
        ).add_to(m)

    st_folium(m, height=650, use_container_width=True)

    # --------------------------------------------------
    # BOTTOM SOLUTION PANEL
    # --------------------------------------------------
    issue = latest["issue"]
    authority = AUTHORITIES.get(issue, AUTHORITIES["Other"])
    primary_solution = generate_solution(issue, latest["intensity"])
    extras = additional_actions(issue)
    extras_html = "".join(f"<li>{e}</li>" for e in extras)

    html_block = f"""
    <div style="
        background:#f4f6f8;
        padding:22px;
        border-radius:14px;
        font-family:Arial;
        border:1px solid #d1d5db;
    ">

        <div style="
            background:#e5e7eb;
            padding:14px;
            border-radius:10px;
            font-weight:700;
        ">
            📝 Latest Report – Recommended Actions
        </div>

        <div style="margin-top:14px;">
            <b>Issue:</b> <span style="color:#b91c1c;">{issue}</span><br>
            <b>Intensity:</b> {latest['intensity']} / 5<br>
            <b>Reported on:</b> {latest['timestamp']}
        </div>

        <hr>

        <div style="background:white; padding:14px; border-left:5px solid #16a34a; border-radius:10px;">
            <b>Primary action</b><br><br>
            {primary_solution}
        </div>

        <div style="background:white; padding:14px; margin-top:12px; border-left:5px solid #2563eb; border-radius:10px;">
            <b>Additional actions</b>
            <ul>{extras_html}</ul>
        </div>

        <div style="background:#fff7ed; padding:14px; margin-top:14px;
                    border-left:5px solid #f97316; border-radius:10px;">
            <b>Responsible authority</b><br><br>
            <b>{authority['dept']}</b><br>
            📞 {authority['phone']}<br>
            📧 {authority['email']}
        </div>

    </div>
    """

    components.html(html_block, height=420)
