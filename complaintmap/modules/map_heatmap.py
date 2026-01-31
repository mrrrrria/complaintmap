import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import pandas as pd
import streamlit.components.v1 as components


# ---------------------------------------------------
# NORMALIZE ISSUE TYPES (handles mixed inputs)
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
# HYDERABAD-SPECIFIC AUTHORITIES
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
# SHORT SOLUTIONS (marker popups)
# ---------------------------------------------------
def generate_solution(issue, intensity):
    intensity = int(intensity)

    SOLUTIONS = {
        "Air": {
            "low": "Encourage reduced vehicle usage and public transport.",
            "medium": "Increase roadside greenery and monitor emissions.",
            "high": "Restrict high-emission vehicles and inspect industries.",
        },
        "Noise": {
            "low": "Monitor noise levels and awareness campaigns.",
            "medium": "Traffic calming and speed regulation.",
            "high": "Restrict heavy vehicles and enforce noise limits.",
        },
        "Heat": {
            "low": "Increase shaded areas and drinking water points.",
            "medium": "Expand tree cover and reflective surfaces.",
            "high": "Urban redesign with cool roofs and green corridors.",
        },
        "Odour": {
            "low": "Increase cleaning frequency.",
            "medium": "Inspect waste collection points.",
            "high": "Upgrade waste processing and enforce sanitation rules.",
        },
        "Cycling / Walking": {
            "low": "Improve signage and markings.",
            "medium": "Enhance crossings and footpath continuity.",
            "high": "Develop protected cycling lanes and redesign streets.",
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
# DETAILED SOLUTIONS + AUTHORITY CONTACTS
# ---------------------------------------------------
def generate_detailed_solutions(issue):
    authority = AUTHORITIES.get(issue, AUTHORITIES["Other"])

    actions = {
        "Air": [
            "Promote electric mobility and public transport.",
            "Strengthen air-quality monitoring across the city.",
        ],
        "Noise": [
            "Implement time-based traffic restrictions.",
            "Increase enforcement of noise regulations.",
        ],
        "Heat": [
            "Expand urban green spaces and water bodies.",
            "Adopt heat-action plans in vulnerable areas.",
        ],
        "Odour": [
            "Improve waste segregation and disposal.",
            "Inspect and regulate odor-generating facilities.",
        ],
        "Cycling / Walking": [
            "Develop safe pedestrian-first streets.",
            "Improve last-mile connectivity.",
        ],
        "Other": [
            "Conduct site-specific investigation.",
            "Coordinate with relevant city departments.",
        ],
    }

    return actions.get(issue, actions["Other"]), authority


# ---------------------------------------------------
# MAIN RENDER FUNCTION
# ---------------------------------------------------
def render(df_all: pd.DataFrame):

    st.title("🧠 Smart Complaint Solution Map – Hyderabad")
    st.markdown(
        "<h4 style='color: gray; margin-top:-10px;'>Citizen-reported issues and proposed actions</h4>",
        unsafe_allow_html=True,
    )

    if df_all is None or df_all.empty:
        st.info("No complaint data available.")
        return

    df = df_all.copy()

    required_cols = ["issue_type", "intensity", "lat", "lon", "timestamp"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Missing required column: {col}")
            return

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

    # Heatmap of complaints
    HeatMap(
        grouped[["lat", "lon"]].values.tolist(),
        radius=25,
        blur=18,
    ).add_to(m)

    # Markers with solutions
    for _, row in grouped.iterrows():
        solution = generate_solution(row["issue"], row["intensity"])
        popup_html = f"""
        <div style="width:300px;">
            <b>Issue:</b> {row['issue']}<br>
            <b>Intensity:</b> {row['intensity']}<br><br>
            <b>Suggested action:</b><br>
            {solution}
        </div>
        """

        folium.Marker(
            [row["lat"], row["lon"]],
            popup=popup_html,
            icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(m)

    st_folium(m, width=1400, height=650)

    # ---------------- SOLUTION PANEL ----------------
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
        <b>Intensity:</b> {latest_row["intensity"]}<br><br>

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

    components.html(html_block, height=300)
