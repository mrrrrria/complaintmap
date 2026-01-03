import os
st.write("SOLUTIONS PAGE FILE:", os.path.abspath(__file__))
import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import pandas as pd


# =========================================================
# COLUMN DETECTION (ROBUST & SAFE)
# =========================================================
def detect_column(df, names):
    for name in names:
        if name in df.columns:
            return name
    return None


# =========================================================
# ISSUE NORMALIZATION (FRENCH → ENGLISH)
# =========================================================
def normalize_issue(value):
    if not isinstance(value, str):
        return "Other"

    v = value.strip().lower()
    if v == "air":
        return "Air"
    if v == "chaleur":
        return "Heat"
    if v == "bruit":
        return "Noise"
    if v == "odeur":
        return "Odour"

    return value.capitalize()


# =========================================================
# SOLUTION LOGIC
# =========================================================
def get_solution(issue, intensity, variant):
    intensity = int(intensity)

    if issue == "Air":
        options = (
            [
                "Monitor air quality regularly and inform residents about pollution levels.",
                "Encourage reduced car usage and promote public transport or cycling."
            ] if intensity <= 3 else [
                "Restrict high-emission vehicles in the affected area during peak hours.",
                "Create urban green buffers to help absorb air pollutants.",
                "Introduce low-emission or electric-vehicle priority zones."
            ]
        )

    elif issue == "Heat":
        options = (
            [
                "Increase tree planting and shaded areas to reduce heat exposure.",
                "Install shaded public seating and pedestrian shelters."
            ] if intensity <= 3 else [
                "Apply cool-roof technologies to reduce temperatures.",
                "Use heat-reflective materials on roads and pavements.",
                "Redesign public spaces to improve airflow."
            ]
        )

    elif issue == "Noise":
        options = (
            [
                "Increase monitoring of noise levels and enforce regulations.",
                "Raise public awareness about noise pollution."
            ] if intensity <= 3 else [
                "Install noise barriers along major roads.",
                "Restrict heavy vehicle traffic during night hours.",
                "Implement traffic calming and speed limits."
            ]
        )

    elif issue == "Odour":
        options = (
            [
                "Inspect sanitation and waste collection practices.",
                "Ensure regular cleaning and maintenance."
            ] if intensity <= 3 else [
                "Improve waste management systems.",
                "Install odor treatment systems near the source."
            ]
        )

    else:
        options = ["Further monitoring and assessment are recommended."]

    return options[variant % len(options)]


# =========================================================
# MAIN PAGE RENDER
# =========================================================
def render(df_all: pd.DataFrame):

    st.title("🗺️ Smart Complaint Solution Map")
    st.markdown(
        "<h4 style='color:gray; margin-top:-10px;'>Proposed Solutions</h4>",
        unsafe_allow_html=True
    )

    if df_all is None or df_all.empty:
        st.warning("No complaint data available.")
        return

    df = df_all.copy()

    # --------------------------------------------------
    # AUTO-DETECT REQUIRED COLUMNS
    # --------------------------------------------------
    issue_col = detect_column(df, ["type", "categorie", "category", "probleme", "issue"])
    lat_col = detect_column(df, ["lat", "latitude"])
    lon_col = detect_column(df, ["lon", "longitude"])
    intensity_col = detect_column(df, ["intensite", "intensity"])
    date_col = detect_column(df, ["date_heure", "date", "timestamp"])

    if not all([issue_col, lat_col, lon_col, intensity_col, date_col]):
        st.error("Required columns are missing in the dataset.")
        st.write("Available columns:", df.columns.tolist())
        return

    # --------------------------------------------------
    # NORMALIZE DATA
    # --------------------------------------------------
    df["issue"] = df[issue_col].apply(normalize_issue)
    df["intensity"] = df[intensity_col].apply(
        lambda x: int(x) if pd.notna(x) and int(x) > 0 else 1
    )

    # --------------------------------------------------
    # ISSUE FILTER
    # --------------------------------------------------
    issues = ["All"] + sorted(df["issue"].unique())
    selected_issue = st.selectbox("Reported Issue", issues)

    if selected_issue != "All":
        df = df[df["issue"] == selected_issue]

    if df.empty:
        st.info("No complaints for selected issue.")
        return

    # --------------------------------------------------
    # GROUP BY LOCATION & ISSUE (LATEST)
    # --------------------------------------------------
    df_sorted = df.sort_values(date_col)

    grouped = (
        df_sorted
        .groupby([lat_col, lon_col, "issue"], as_index=False)
        .last()
    )

    latest_time = grouped[date_col].max()
    latest_row = grouped.loc[grouped[date_col].idxmax()]

    # --------------------------------------------------
    # MAP
    # --------------------------------------------------
    m = folium.Map(
        location=[latest_row[lat_col], latest_row[lon_col]],
        zoom_start=14
    )

    HeatMap(
        grouped[[lat_col, lon_col]].values.tolist(),
        radius=25,
        blur=18
    ).add_to(m)

    # --------------------------------------------------
    # MARKERS
    # --------------------------------------------------
    for i, row in grouped.iterrows():
        solution = get_solution(row["issue"], row["intensity"], i)
        color = "red" if row[date_col] == latest_time else "blue"

        popup = f"""
        <div style="width:320px; font-family:Arial;">
            <div style="background:#f2f2f2; padding:12px;">
                <b>Reported Issue:</b> {row['issue']}<br>
                <b>Intensity:</b> {row['intensity']}
            </div>
            <div style="background:#ffffff; padding:14px;">
                <b>Proposed Solution:</b><br><br>
                {solution}
            </div>
        </div>
        """

        folium.Marker(
            location=[row[lat_col], row[lon_col]],
            popup=popup,
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)

    st_folium(m, width=1400, height=650)

    # --------------------------------------------------
    # CURRENT SOLUTION BELOW MAP
    # --------------------------------------------------
    st.subheader("📌 Current Reported Solution")

    current_solution = get_solution(
        latest_row["issue"],
        latest_row["intensity"],
        0
    )

    st.markdown(
        f"""
        <div style="background:#ffffff; padding:20px; border-radius:12px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.1);">
            <div style="background:#f2f2f2; padding:12px; border-radius:8px;">
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
