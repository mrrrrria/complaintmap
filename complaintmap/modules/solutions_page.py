import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import pandas as pd


# =========================================================
# HELPER: SAFE COLUMN DETECTION
# =========================================================
def detect_column(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


# =========================================================
# NORMALISE ISSUE NAMES (DISPLAY IN ENGLISH)
# =========================================================
def normalize_issue(value):
    if not isinstance(value, str):
        return "Other"

    v = value.strip().lower()
    mapping = {
        "air": "Air",
        "chaleur": "Heat",
        "bruit": "Noise",
        "odeur": "Odour",
        "noise": "Noise",
        "heat": "Heat"
    }
    return mapping.get(v, value.capitalize())


# =========================================================
# SOLUTION ENGINE
# =========================================================
def generate_solution(issue, intensity, idx):
    intensity = int(intensity)

    solutions = {
        "Air": (
            [
                "Monitor local air quality and share information with residents.",
                "Encourage walking, cycling, and public transport use."
            ],
            [
                "Limit high-emission vehicles in the affected area.",
                "Introduce low-emission zones and increase urban greenery.",
                "Promote electric vehicle infrastructure."
            ]
        ),
        "Heat": (
            [
                "Increase shaded areas and plant more trees.",
                "Install shaded seating in public spaces."
            ],
            [
                "Apply cool-roof and reflective surface technologies.",
                "Redesign public spaces to reduce heat accumulation.",
                "Improve airflow through urban layout adjustments."
            ]
        ),
        "Noise": (
            [
                "Monitor noise levels and enforce existing regulations.",
                "Inform residents about noise reduction practices."
            ],
            [
                "Install noise barriers near busy roads.",
                "Restrict heavy traffic during night hours.",
                "Introduce traffic calming measures."
            ]
        ),
        "Odour": (
            [
                "Inspect sanitation and waste collection schedules.",
                "Increase cleaning frequency in affected areas."
            ],
            [
                "Improve waste management systems.",
                "Install odor filtering or treatment solutions."
            ]
        )
    }

    low, high = solutions.get(issue, (["Further monitoring is recommended."], []))
    selected = low if intensity <= 3 else high
    return selected[idx % len(selected)]


# =========================================================
# MAIN RENDER FUNCTION
# =========================================================
def render(df_all: pd.DataFrame):

    st.title("🗺️ Smart Complaint Solution Map")
    st.markdown(
        "<h4 style='color:gray; margin-top:-10px;'>Proposed Solutions</h4>",
        unsafe_allow_html=True
    )

    if df_all is None or df_all.empty:
        st.info("No complaint data available.")
        return

    df = df_all.copy()

    # --------------------------------------------------
    # COLUMN DETECTION (MATCHES REPO DATA)
    # --------------------------------------------------
    issue_col = detect_column(df, ["categorie", "category", "type"])
    lat_col = detect_column(df, ["lat", "latitude"])
    lon_col = detect_column(df, ["lon", "longitude"])
    intensity_col = detect_column(df, ["intensite", "intensity"])
    date_col = detect_column(df, ["date_heure", "date"])

    if not all([issue_col, lat_col, lon_col, intensity_col, date_col]):
        st.error("Dataset format not supported.")
        st.write("Available columns:", df.columns.tolist())
        return

    # --------------------------------------------------
    # NORMALISE DATA
    # --------------------------------------------------
    df["issue"] = df[issue_col].apply(normalize_issue)
    df["intensity"] = df[intensity_col].fillna(1).astype(int)

    # --------------------------------------------------
    # ISSUE FILTER
    # --------------------------------------------------
    issue_filter = ["All"] + sorted(df["issue"].unique().tolist())
    selected_issue = st.selectbox("Reported Issue", issue_filter)

    if selected_issue != "All":
        df = df[df["issue"] == selected_issue]

    if df.empty:
        st.info("No complaints found.")
        return

    # --------------------------------------------------
    # GROUP BY LOCATION (LATEST COMPLAINT)
    # --------------------------------------------------
    df_sorted = df.sort_values(date_col)

    grouped = (
        df_sorted
        .groupby([lat_col, lon_col, "issue"], as_index=False)
        .last()
    )

    latest_row = grouped.loc[grouped[date_col].idxmax()]

    # --------------------------------------------------
    # MAP INITIALISATION
    # --------------------------------------------------
    m = folium.Map(
        location=[latest_row[lat_col], latest_row[lon_col]],
        zoom_start=14
    )

    HeatMap(grouped[[lat_col, lon_col]].values.tolist(), radius=25, blur=18).add_to(m)

    # --------------------------------------------------
    # MARKERS
    # --------------------------------------------------
    for i, row in grouped.iterrows():
        solution = generate_solution(row["issue"], row["intensity"], i)
        color = "red" if row[date_col] == latest_row[date_col] else "blue"

        popup = f"""
        <div style="width:320px;">
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
            location=[row[lat_col], row[lon_col]],
            popup=popup,
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)

    st_folium(m, width=1400, height=650)

    # --------------------------------------------------
    # CURRENT SOLUTION BELOW MAP
    # --------------------------------------------------
    st.subheader("📌 Current Reported Solution")

    current_solution = generate_solution(
        latest_row["issue"], latest_row["intensity"], 0
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
