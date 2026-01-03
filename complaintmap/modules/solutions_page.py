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
        "cycling / walking": "Cycling / Walking",
        "other": "Other"
    }
    return mapping.get(v, value.capitalize())


# =========================================================
# SOLUTION ENGINE
# =========================================================
def generate_solution(issue, intensity, variant):
    intensity = int(intensity)

    if issue == "Air":
        solutions = (
            [
                "Monitor air quality and share pollution levels with residents.",
                "Encourage the use of public transport, cycling, and walking."
            ] if intensity <= 3 else [
                "Restrict high-emission vehicles in the affected area.",
                "Create green buffers to absorb air pollutants.",
                "Promote electric and low-emission vehicles."
            ]
        )

    elif issue == "Heat":
        solutions = (
            [
                "Increase shaded areas and plant additional trees.",
                "Install shaded public seating and rest areas."
            ] if intensity <= 3 else [
                "Apply cool-roof technologies on nearby buildings.",
                "Use reflective materials on pavements and roads.",
                "Redesign public spaces to improve airflow."
            ]
        )

    elif issue == "Noise":
        solutions = (
            [
                "Monitor noise levels and enforce existing regulations.",
                "Raise awareness about noise pollution."
            ] if intensity <= 3 else [
                "Install noise barriers near major roads.",
                "Limit heavy vehicle traffic during night hours.",
                "Introduce speed limits and traffic calming measures."
            ]
        )

    elif issue == "Odour":
        solutions = (
            [
                "Inspect sanitation and waste collection practices.",
                "Increase cleaning frequency in the affected area."
            ] if intensity <= 3 else [
                "Improve waste management systems.",
                "Install odor filtering or treatment systems."
            ]
        )

    elif issue == "Cycling / Walking":
        solutions = (
            [
                "Improve road signage and pedestrian visibility.",
                "Repair sidewalks and cycling paths."
            ] if intensity <= 3 else [
                "Create dedicated cycling lanes.",
                "Redesign intersections for pedestrian safety.",
                "Reduce vehicle speed in shared spaces."
            ]
        )

    else:
        solutions = ["Further monitoring and assessment are recommended."]

    return solutions[variant % len(solutions)]


# =========================================================
# MAIN RENDER FUNCTION
# =========================================================
def render(df_all: pd.DataFrame):

    st.title("🗺️ Smart Complaint Solution Map")
    st.markdown(
        "<h4 style='color: gray; margin-top:-10px;'>Proposed Solutions</h4>",
        unsafe_allow_html=True
    )

    if df_all is None or df_all.empty:
        st.info("No complaint data available.")
        return

    df = df_all.copy()

    # --------------------------------------------------
    # REQUIRED COLUMNS (NOW EXACT MATCH)
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
    # GROUP BY LOCATION (LATEST REPORT PER LOCATION & ISSUE)
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
    # ADD MARKERS
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
