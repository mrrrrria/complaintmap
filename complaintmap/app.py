import os
from datetime import datetime
import requests
import folium
from folium.plugins import MarkerCluster
import streamlit as st
from streamlit_folium import st_folium
import urllib.parse

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(layout="wide")

from config import (
    setup,
    DEFAULT_LAT,
    DEFAULT_LON,
    DEFAULT_ZOOM,
    UPLOAD_DIR,
    COLOR_MAP,
)
from db import init_db, load_complaints, add_complaint

from modules import (
    map_heatmap,
    statistics_page,
    solutions_page,
    air_heatmap_page,
    about_page,
)

# ---------------------------------------------------------
# AUTHORITY CONTACTS (Hyderabad)
# ---------------------------------------------------------
AUTHORITY_EMAILS = {
    "Air quality": "pcb@telangana.gov.in",
    "Noise": "trafficpolice@hyderabad.gov.in",
    "Heat": "environment-ghmc@telangana.gov.in",
    "Cycling / Walking": "planning-ghmc@telangana.gov.in",
    "Odor": "sanitation-ghmc@telangana.gov.in",
    "Other": "info.ghmc@telangana.gov.in",
}

# ---------------------------------------------------------
# GLOBAL STYLE (GREEN THEME – STABLE)
# ---------------------------------------------------------
def apply_global_style():
    st.markdown(
        """
        <style>
        header[data-testid="stHeader"] {
            background: transparent;
            box-shadow: none;
        }

        .block-container {
            padding-top: 5rem;
        }

        [data-testid="stSidebar"] {
            background-color: #d8f3dc;
            border-right: 1px solid #b7e4c7;
        }

        .top-banner {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            background-color: #95d5b2;
            padding: 0.8rem 2rem;
            border-bottom: 1px solid #74c69d;
        }

        .top-banner h1 {
            margin: 0;
            color: #1b4332;
        }

        .top-banner p {
            margin: 0;
            color: #2d6a4f;
        }

        .report-card {
            background-color: white;
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid #b7e4c7;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_banner():
    st.markdown(
        """
        <div class="top-banner">
            <h1>🌱 Smart Complaint Map</h1>
            <p>Citizen-powered urban issue reporting – Hyderabad</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------
def render_report_home():
    st.subheader("Report an issue on the map")

    # ---------- STATE ----------
    if "location" not in st.session_state:
        st.session_state["location"] = None
    if "search_results" not in st.session_state:
        st.session_state["search_results"] = []

    # ---------- SEARCH ----------
    search_query = st.text_input("🔎 Search location (Hyderabad)")

    if search_query and len(search_query) >= 3:
        try:
            r = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": f"{search_query}, Hyderabad",
                    "format": "json",
                    "limit": 5,
                    "countrycodes": "in",
                },
                headers={"User-Agent": "smart-complaint-map"},
                timeout=5,
            )
            if r.ok:
                st.session_state["search_results"] = r.json()
        except Exception:
            st.session_state["search_results"] = []

    if st.session_state["search_results"]:
        options = [r["display_name"] for r in st.session_state["search_results"]]
        selected = st.selectbox("Select address", options)

        if selected:
            idx = options.index(selected)
            loc = st.session_state["search_results"][idx]
            st.session_state["location"] = {
                "lat": float(loc["lat"]),
                "lon": float(loc["lon"]),
            }
            st.session_state["search_results"] = []

    # ---------- MAP CENTER ----------
    center = [DEFAULT_LAT, DEFAULT_LON]
    if st.session_state["location"]:
        center = [
            st.session_state["location"]["lat"],
            st.session_state["location"]["lon"],
        ]

    # ---------- MAP ----------
    m = folium.Map(location=center, zoom_start=DEFAULT_ZOOM)

    df_all = load_complaints()
    if not df_all.empty:
        cluster = MarkerCluster().add_to(m)
        for _, row in df_all.iterrows():
            folium.CircleMarker(
                [row["lat"], row["lon"]],
                radius=5,
                color=COLOR_MAP.get(row["issue_type"], "#2d6a4f"),
                fill=True,
                fill_opacity=0.8,
            ).add_to(cluster)

    if st.session_state["location"]:
        folium.Marker(
            [
                st.session_state["location"]["lat"],
                st.session_state["location"]["lon"],
            ],
            icon=folium.Icon(color="green", icon="plus"),
        ).add_to(m)

    col_map, col_form = st.columns([2.5, 1])

    with col_map:
        map_data = st_folium(m, height=600, use_container_width=True)

        if map_data and map_data.get("last_clicked"):
            st.session_state["location"] = {
                "lat": map_data["last_clicked"]["lat"],
                "lon": map_data["last_clicked"]["lng"],
            }

    # ---------- FORM ----------
    with col_form:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)

        if not st.session_state["location"]:
            st.info("Search for a place or click on the map to report an issue.")
        else:
            ISSUE_TYPES = [
                "Air quality",
                "Noise",
                "Heat",
                "Cycling / Walking",
                "Odor",
                "Other",
            ]

            issue_type = st.selectbox("Issue type", ISSUE_TYPES)
            intensity = st.slider("Intensity (1–5)", 1, 5, 3)
            description = st.text_area("Description (optional)")
            photo = st.file_uploader("Upload a photo (optional)", ["jpg", "jpeg", "png"])

            send_email = st.checkbox("Send this complaint to authorities")

            if st.button("Submit complaint"):
                photo_path = None
                if photo:
                    os.makedirs(UPLOAD_DIR, exist_ok=True)
                    fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{photo.name}"
                    photo_path = os.path.join(UPLOAD_DIR, fname)
                    with open(photo_path, "wb") as f:
                        f.write(photo.getbuffer())

                add_complaint(
                    issue_type,
                    intensity,
                    st.session_state["location"]["lat"],
                    st.session_state["location"]["lon"],
                    description,
                    photo_path,
                )

                st.success("Complaint submitted successfully!")

                if send_email:
                    email = AUTHORITY_EMAILS.get(issue_type, AUTHORITY_EMAILS["Other"])
                    subject = f"Citizen complaint – {issue_type}"
                    body = f"""
Location: {st.session_state["location"]["lat"]}, {st.session_state["location"]["lon"]}
Intensity: {intensity}

Description:
{description or "No description provided."}
"""
                    mailto = (
                        f"mailto:{email}?"
                        f"subject={urllib.parse.quote(subject)}&"
                        f"body={urllib.parse.quote(body)}"
                    )
                    st.markdown(f"[📧 Click here to send email to authority]({mailto})")

                st.session_state["location"] = None

        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------
def main():
    setup()
    init_db()
    apply_global_style()
    render_banner()

    st.sidebar.markdown("## 🌿 Menu")

    pages = {
        "🏠 Report": "home",
        "Map & Heatmap": "map",
        "Statistics": "stats",
        "Proposed solutions": "solutions",
        "Air heatmap": "air",
        "About": "about",
    }

    choice = st.sidebar.radio("Go to", list(pages.keys()))
    key = pages[choice]

    if key == "home":
        render_report_home()
    else:
        df_all = load_complaints()
        if key == "map":
            map_heatmap.render(df_all)
        elif key == "stats":
            statistics_page.render(df_all)
        elif key == "solutions":
            solutions_page.render(df_all)
        elif key == "air":
            air_heatmap_page.render()
        elif key == "about":
            about_page.render()

if __name__ == "__main__":
    main()
