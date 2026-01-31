import os
from datetime import datetime
import folium
from folium.plugins import MarkerCluster
import streamlit as st
from streamlit_folium import st_folium
import urllib.parse

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

# =========================================================
# 🔧 CHANGE: Authority contacts (Hyderabad)
# =========================================================
AUTHORITY_CONTACTS = {
    "Air quality": {
        "dept": "Telangana Pollution Control Board",
        "email": "pcb@telangana.gov.in",
        "phone": "040-23887500",
    },
    "Noise": {
        "dept": "Hyderabad Traffic Police",
        "email": "trafficpolice@hyderabad.gov.in",
        "phone": "100",
    },
    "Heat": {
        "dept": "GHMC – Environment Wing",
        "email": "environment-ghmc@telangana.gov.in",
        "phone": "040-21111111",
    },
    "Cycling / Walking": {
        "dept": "GHMC – Urban Planning",
        "email": "planning-ghmc@telangana.gov.in",
        "phone": "040-21111111",
    },
    "Odor": {
        "dept": "GHMC – Sanitation",
        "email": "sanitation-ghmc@telangana.gov.in",
        "phone": "040-21111111",
    },
}

# =========================================================
# GLOBAL STYLE (GREEN THEME)
# =========================================================
def apply_global_style():
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background-color: #f1ffe8;
            padding-top: 4.5rem;
        }

        [data-testid="stSidebar"] {
            background-color: #e1f5dd;
            border-right: 1px solid #c4e4be;
            margin-top: 4.5rem !important;
        }

        .top-banner {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            background-color: #d5f5c8;
            padding: 0.75rem 2rem;
            border-bottom: 1px solid #b9e6ae;
        }

        .top-banner-title {
            margin: 0;
            font-size: 1.6rem;
        }

        .top-banner-subtitle {
            margin: 0.1rem 0 0 0;
            font-size: 0.95rem;
        }

        .report-card {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 1rem 1.2rem;
            border: 1px solid #cfe7c7;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-top: 0.8rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# TOP BANNER
# =========================================================
def render_banner():
    st.markdown(
        """
        <div class="top-banner">
            <h1 class="top-banner-title">🌱 Smart Complaint Map</h1>
            <p class="top-banner-subtitle">
                Citizen-powered urban issue reporting – Hyderabad
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# HOME PAGE (MAP + FORM)
# =========================================================
def render_report_home():
    st.subheader("Report an issue on the map")

    df_all = load_complaints()
    clicked = st.session_state.get("clicked_location")

    center = [DEFAULT_LAT, DEFAULT_LON]
    if not df_all.empty:
        center = [df_all["lat"].mean(), df_all["lon"].mean()]

    m = folium.Map(location=center, zoom_start=DEFAULT_ZOOM)

    if not df_all.empty:
        cluster = MarkerCluster().add_to(m)
        for _, row in df_all.iterrows():
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=5,
                color=COLOR_MAP.get(row["issue_type"], "#4caf50"),
                fill=True,
                fill_opacity=0.8,
                popup=f"{row['issue_type']} (Intensity {row['intensity']})",
            ).add_to(cluster)

    if clicked:
        folium.Marker(
            [clicked["lat"], clicked["lon"]],
            icon=folium.Icon(color="green", icon="plus"),
        ).add_to(m)

    left, right = st.columns([2.5, 1])

    with left:
        # 🔧 CHANGE: responsive map (no white space)
        map_data = st_folium(
            m,
            height=600,
            use_container_width=True,
        )

    if map_data and map_data.get("last_clicked"):
        st.session_state["clicked_location"] = {
            "lat": map_data["last_clicked"]["lat"],
            "lon": map_data["last_clicked"]["lng"],
        }
        clicked = st.session_state["clicked_location"]

    with right:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)

        if not clicked:
            st.info("Click a location on the map to report an issue.")
        else:
            st.markdown("### 📍 Report an issue")

            ISSUE_TYPES = [
                "Air quality",
                "Noise",
                "Heat",
                "Cycling / Walking",
                "Odor",
                "Other",
            ]

            issue_type = st.selectbox("Issue type", ISSUE_TYPES)
            intensity = st.slider("Intensity (1 = low, 5 = high)", 1, 5, 3)
            description = st.text_area("Description (optional)")

            # 🔧 ADD: Photo upload
            photo_file = st.file_uploader(
                "Upload a photo (optional)",
                type=["jpg", "jpeg", "png"],
            )

            # Authority info
            authority = AUTHORITY_CONTACTS.get(issue_type)
            if authority:
                st.markdown("**Responsible authority**")
                st.write(f"🏛️ {authority['dept']}")
                st.write(f"📞 {authority['phone']}")
                st.write(f"📧 {authority['email']}")

            send_email = st.checkbox(
                "📧 Generate email to send this complaint to the authority"
            )

            if st.button("✅ Submit report"):
                photo_path = None

                # 🔧 ADD: Save photo
                if photo_file:
                    os.makedirs(UPLOAD_DIR, exist_ok=True)
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{ts}_{photo_file.name}"
                    save_path = os.path.join(UPLOAD_DIR, filename)
                    with open(save_path, "wb") as f:
                        f.write(photo_file.getbuffer())
                    photo_path = save_path

                add_complaint(
                    issue_type,
                    intensity,
                    clicked["lat"],
                    clicked["lon"],
                    description,
                    photo_path,
                )

                st.success("Thank you! Your report has been submitted.")

                if send_email and authority:
                    subject = f"Citizen complaint – {issue_type} issue in Hyderabad"
                    body = f"""
Dear Sir/Madam,

I would like to report a {issue_type.lower()} issue at:

Latitude: {clicked['lat']}
Longitude: {clicked['lon']}
Intensity: {intensity}

Description:
{description or "Not provided"}

This message was generated using a Smart Complaint Map
(academic project).

Regards,
A concerned citizen
"""
                    mailto = (
                        f"mailto:{authority['email']}?"
                        f"subject={urllib.parse.quote(subject)}&"
                        f"body={urllib.parse.quote(body)}"
                    )
                    st.markdown(f"[📨 Click here to open email]({mailto})")

                st.session_state["clicked_location"] = None

        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# MAIN APP
# =========================================================
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
    page = pages[choice]

    if page == "home":
        render_report_home()
    else:
        df_all = load_complaints()
        if page == "map":
            map_heatmap.render(df_all)
        elif page == "stats":
            statistics_page.render(df_all)
        elif page == "solutions":
            solutions_page.render(df_all)
        elif page == "air":
            air_heatmap_page.render()
        elif page == "about":
            about_page.render()

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    main()
