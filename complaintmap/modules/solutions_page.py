import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import pandas as pd


# =========================================================
# NORMALIZE ISSUE NAMES (ENGLISH ONLY)
# =========================================================
def normalize_issue(value):
    if not isinstance(value, str):
        return "Other"

    v = value.strip().lower()
    mapping = {
        "air": "Air",
        "noise": "Noise",
        "bruit": "Noise",
        "heat": "Heat",
        "chaleur": "Heat",
        "odor": "Odour",
        "odeur": "Odour",
        "water": "Water",
        "flood": "Water",
        "cycling / walking": "Cycling / Walking",
        "cycling": "Cycling / Walking",
        "walking": "Cycling / Walking",
        "other": "Other"
    }
    return mapping.get(v, value.capitalize())


# =========================================================
# PREDEFINED, INTENSITY-BASED SOLUTION ENGINE
# =========================================================
def generate_solution(issue, intensity, variant):
    intensity = int(intensity)

    SOLUTIONS = {

        "Air": {
            "low": [
                "Monitor local air quality and inform residents about pollution levels.",
                "Promote awareness campaigns to reduce air pollution."
            ],
            "medium": [
                "Encourage reduced vehicle use and promote public transport.",
                "Support cleaner mobility options such as cycling and car sharing."
            ],
            "high": [
                "Restrict high-emission vehicles in the affected area.",
                "Create low-emission zones and increase urban greenery."
            ]
        },

        "Heat": {
            "low": [
                "Increase shaded areas and raise heat awareness.",
                "Encourage the use of shaded pedestrian routes."
            ],
            "medium": [
                "Install shaded seating and expand tree coverage.",
                "Improve access to cooling spaces in public areas."
            ],
            "high": [
                "Apply cool-surface technologies on roads and buildings.",
                "Redesign public spaces to reduce heat accumulation."
            ]
        },

        "Noise": {
            "low": [
                "Monitor noise levels and remind residents of regulations.",
                "Increase public awareness about noise pollution."
            ],
            "medium": [
                "Introduce traffic calming measures in affected streets.",
                "Adjust traffic flow to reduce noise exposure."
            ],
            "high": [
                "Install noise barriers near major roads.",
                "Restrict heavy vehicle traffic during sensitive hours."
            ]
        },

        "Odour": {
            "low": [
                "Inspect sanitation conditions and cleaning schedules.",
                "Increase monitoring of waste collection practices."
            ],
            "medium": [
                "Improve waste collection frequency and sanitation services.",
                "Identify and address local odor sources."
            ],
            "high": [
                "Upgrade waste treatment infrastructure.",
                "Enforce environmental regulations on odor-producing activities."
            ]
        },

        "Water": {
            "low": [
                "Inspect drainage systems and monitor water accumulation.",
                "Ensure drains are clear and functioning properly."
            ],
            "medium": [
                "Clean and maintain local drainage infrastructure.",
                "Address recurring water pooling in the area."
            ],
            "high": [
                "Upgrade drainage systems and implement flood mitigation measures.",
                "Restrict access to flooded areas and plan infrastructure improvements."
            ]
        },

        "Cycling / Walking": {
            "low": [
                "Improve signage and visibility for pedestrians and cyclists.",
                "Repair minor surface issues on sidewalks and paths."
            ],
            "medium": [
                "Improve crossings and shared-space safety.",
                "Enhance separation between pedestrians and vehicles."
            ],
            "high": [
                "Build dedicated cycling lanes.",
                "Redesign intersections to improve pedestrian safety."
            ]
        },

        "Other": {
            "low": ["Monitor the situation and collect additional reports."],
            "medium": ["Conduct a local assessment of the reported issue."],
            "high": ["Plan infrastructure-level intervention with authorities."]
        }
    }

    if intensity <= 2:
        tier = "low"
    elif intensity == 3:
        tier = "medium"
    else:
        tier = "high"

    issue_solutions = SOLUTIONS.get(issue, SOLUTIONS["Other"])
    tier_solutions = issue_solutions[tier]

    return tier_solutions[variant % len(tier_solutions)]


# =========================================================
# MAIN RENDER FUNCTION
# =========================================================
def render(df_all: pd.DataFrame):

    st.title("Smart Complaint Solution Map")
    st.markdown(
        "<h4 style='color: gray; margin-top:-10px;'>Proposed Solutions</h4>",
        unsafe_allow_html=True
    )

    if df_all is None or df_all.empty:
        st.info("No complaint data available.")
        return

    df = df_all.copy()

    # --------------------------------------------------
    # REQUIRED COLUMNS (MATCH YOUR DATABASE)
    # --------------------------------------------------
    required_cols = ["issue_type", "intensity", "lat", "lon", "timestamp"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Missing required column: {col}")
            st.write("Available columns:", df.columns.tolist())
            return

    # --------------------------------------------------
    # NORMALIZE DATA
    # --------------------------------------------------
    df["issue"] = df["issue_type"].apply(normalize_issue)
    df["intensity"] = df["intensity"].fillna(1).astype(int)

    # --------------------------------------------------
    # ISSUE FILTER
    # --------------------------------------------------
    issues = ["All"] + sorted(df["issue"].unique().tolist())
    selected_issue = st.selectbox("Reported Issue", issues)

    if selected_issue != "All":
        df = df[df["issue"] == selected_issue]

    if df.empty:
        st.info("No complaints found for this issue.")
        return

    # --------------------------------------------------
    # GROUP BY LOCATION (LATEST PER LOCATION & ISSUE)
    # --------------------------------------------------
    df_sorted = df.sort_values("timestamp")

    grouped = (
        df_sorted
        .groupby(["lat", "lon", "issue"], as_index=False)
        .last()
    )

    latest_row = grouped.loc[grouped["timestamp"].idxmax()]

    # --------------------------------------------------
    # MAP INITIALIZATION
    # --------------------------------------------------
    m = folium.Map(
        location=[latest_row["lat"], latest_row["lon"]],
        zoom_start=14
    )

    HeatMap(
        grouped[["lat", "lon"]].values.tolist(),
        radius=25,
        blur=18
    ).add_to(m)

    # --------------------------------------------------
    # MARKERS
    # --------------------------------------------------
    for i, row in grouped.iterrows():
        solution = generate_solution(row["issue"], row["intensity"], i)
        color = "red" if row["timestamp"] == latest_row["timestamp"] else "blue"

        popup_html = f"""
        <div style="width:330px; font-family:Arial;">
            <div style="background:#f2f2f2; padding:12px;">
                <b>Reported Issue:</b> {row['issue']}<br>
                <b>Intensity:</b> {row['intensity']}
            </div>
            <div style="background:white; padding:14px;">
                <b>Proposed Solution:</b><br><br>
                {solution}
            </div>
        </div>
        """

        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=popup_html,
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)

    st_folium(m, width=1400, height=650)

    # --------------------------------------------------
    # CURRENT SOLUTION BELOW MAP
    # --------------------------------------------------
    st.subheader("📌 Current Reported Solution")

    current_solution = generate_solution(
        latest_row["issue"],
        latest_row["intensity"],
        0
    )

    st.markdown(
        f"""
        <div style="background:white; padding:20px; border-radius:12px;">
            <div style="background:#f2f2f2; padding:12px;">
                <b>Reported Issue:</b> {latest_row['issue']}<br>
                <b>Intensity:</b> {latest_row['intensity']}
            </div>
            <div style="margin-top:12px;">
                <b>Recommended Solution:</b><br><br>
                {current_solution}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
