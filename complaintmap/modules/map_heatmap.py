import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import pandas as pd
import streamlit.components.v1 as components


# ---------------------------------------------------
# NORMALIZE ISSUE TYPES
# ---------------------------------------------------
def normalize_issue(value):
    if not isinstance(value, str):
        return "Other"

    v = value.strip().lower()

    if "air" in v or "pollution" in v:
        return "Air"
    if "noise" in v or "bruit" in v:
        return "Noise"
    if "heat" in v or "chaleur" in v or "temperature" in v:
        return "Heat"
    if "odor" in v or "odour" in v or "odeur" in v or "smell" in v:
        return "Odour"
    if "cycling" in v or "walking" in v or "pedestrian" in v:
        return "Cycling / Walking"

    return "Other"


# ---------------------------------------------------
# HYDERABAD AUTHORITIES
# ---------------------------------------------------
AUTHORITIES = {
    "Air": {
        "dept": "Telangana Pollution Control Board (TSPCB)",
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
        "dept": "Greater Hyderabad Municipal Corporation (GHMC)",
        "phone": "040-21111111",
        "email": "info.ghmc@telangana.gov.in",
    },
}


# ---------------------------------------------------
# SOLUTION GENERATOR (SHORT)
# ---------------------------------------------------
def generate_solution(issue, intensity):
    intensity = int(intensity)

    SOLUTIONS = {
        "Air": {
            "low": "Encourage public transport and reduced vehicle use.",
            "medium": "Increase roadside greenery and emission checks.",
            "high": "Restrict polluting vehicles and inspect industries.",
        },
        "Noise": {
            "low": "Monitor noise levels and raise awareness.",
            "medium": "Traffic calming and speed regulation.",
            "high": "Restrict heavy vehicles and enforce noise limits.",
        },
        "Heat": {
            "low": "Increase shaded areas and drinking water points.",
            "medium": "Expand tree cover and reflective surfaces.",
            "high": "Implement cool roofs and green corridors.",
        },
        "Odour": {
            "low": "Increase cleaning frequency.",
            "medium": "Inspect waste collection points.",
            "high": "Upgrade waste processing and sanitation systems.",
        },
        "Cycling / Walking": {
            "low": "Improve signage and markings.",
            "medium": "Enhance crossings and footpaths.",
            "high": "Develop protected cycling lanes.",
        },
        "Other": {
            "low": "Monitor the situation.",
            "medium": "Conduct a local assessment.",
            "high": "Plan infrastructure-level intervention.",
        },
    }

    if intensity <= 2:
        tier = "low"
    elif intensity == 3:
        tier = "medium"
    else:
        tier = "high"

    return SOLUTIONS.get(issue, SOLUTIONS["Other"])[tier]


# ---------------------------------------------------
# DETAILED SOLUTIONS + AUTHORITY
# ---------------------------------------------------
def generate_detailed_solutions(issue):
    actions = {
        "Air": [
            "Promote electric mobility.",
            "Strengthen city-wide air monitoring.",
        ],
        "Noise": [
            "Introduce time-based traffic restrictions.",
            "Increase enforcement in residential zones.",
        ],
        "Heat": [
            "Expand urban green spaces.",
            "Implement city heat-action plans.",
        ],
        "Odour": [
            "Improve waste segregation.",
            "Inspect odor-generating facilities.",
        ],
        "Cycling / Walking": [
            "Develop pedestrian-first streets.",
            "Improve last-mile connectivity.",
        ],
        "Other": [
            "Conduct site-specific investigation.",
            "Coordinate with relevant departments.",
        ],
    }

    return actions.get(issue, actions["Other"]), AUTHORITIES.get(issue, AUTHORITIES["Other"])


# ---------------------------------------------------
# MAIN RENDER
# ---------------------------------------------------
def render(df_all: pd.DataFrame):

    st.title("🧠 Smart Complaint Solution Map – Hyderabad")
    st.markdown(
        "<h4 style='color: gray; margin-top:-10px;'>Citizen reports, hotspots, and proposed actions</h4>",
        unsafe_allow_html=True,
    )

    if df_all is None or df_all.empty:
        st.info("No complaint data available.")
        return

    df = df_all.copy()
    df["issue"] = df["issue_type"].apply(normalize_issue)
    df["intensity"] = df["intensity"].fillna(1).astype(int)

    df_sorted = df.sort_values("timestamp")
    grouped = df_sorted.groupby(["lat", "lon", "issue"], as_index=False).last()
    latest_row = grouped.loc[grouped["timestamp"].idxmax()]

    # ---------------- MAP ----------------
    m = folium.Map(
        location=[latest_row["lat"], latest_row["lon"]],
        zoom_start=13,
    )

    # Heatmap of all complaints
    HeatMap(
        grouped[["lat", "lon"]].values.tolist(),
        radius=25,
        blur=18,
    ).add_to(m)

    # Markers
    for _, row in grouped.iterrows():
        is_latest = row["timestamp"] == latest_row["timestamp"]
        color = "red" if is_latest else "blue"

        popup_html = f"""
        <div style="width:320px; font-family:Arial;">
            <b>Issue:</b> {row['issue']}<br>
            <b>Intensity:</b> {row['intensity']} / 5<br>
            <b>Reported on:</b> {row['timestamp'].strftime('%Y-%m-%d %H:%M')}<br><br>
            <b>Description:</b><br>
            {row.get('description') or 'No description provided.'}
            <hr>
            <b>Suggested solution:</b><br>
            {generate_solution(row['issue'], row['intensity'])}
        </div>
        """

        folium.Marker(
            [row["lat"], row["lon"]],
            popup=popup_html,
            icon=folium.Icon(color=color, icon="info-sign"),
        ).add_to(m)

    st_folium(m, width=1400, height=650)

    # ---------------- BOTTOM PANEL ----------------
    st.subheader("📌 Latest Report – Recommended Actions")

    primary_solution = generate_solution(
        latest_row["issue"],
        latest_row["intensity"],
    )

    additional, authority = generate_detailed_solutions(latest_row["issue"])
    additional_html = "".join([f"<li>{s}</li>" for s in additional])

    html_block = f"""
    <div style="background:white; padding:20px; border-radius:12px;">
        <b>Issue:</b> {latest_row["issue"]}<br>
        <b>Intensity:</b> {latest_row["intensity"]}<br>
        <b>Reported on:</b> {latest_row["timestamp"].strftime('%Y-%m-%d %H:%M')}<br><br>

        <b>Primary action:</b><br>
        {primary_solution}

        <br><br>
        <b>Additional actions:</b>
        <ul>{additional_html}</ul>

        <hr>
        <b>Responsible Authority:</b><br>
        {authority["dept"]}<br>
        📞 {authority["phone"]}<br>
        📧 {authority["email"]}
    </div>
    """

    components.html(html_block, height=340)
