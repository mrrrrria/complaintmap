import os
from datetime import datetime
import folium
from folium.plugins import MarkerCluster
import streamlit as st
from streamlit_folium import st_folium
import urllib.parse
import requests

# ---------------------------------------------------------
# PAGE CONFIG (must be first)
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
    "Other": {
        "dept": "Greater Hyderabad Municipal Corporation",
        "email": "info.ghmc@telangana.gov.in",
        "phone": "040-21111111"
    }
}

# ---------------------------------------------------------
# GLOBAL STYLE
# ---------------------------------------------------------
def apply_global_style():
    st.markdown(
        """
        <style>
        header[data-testid="stHeader"] {
            height: 0px;
            visibility: hidden;
        }

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

    # ---------------- Search with suggestions ----------------
    search_query = st.text_input("🔎 Search address / area (type at least 3 chars)")

    if "addr_suggestions" not in st.session_state:
        st.session_state["addr_suggestions"] = []

    if search_query and len(search_query) >= 3:
        try:
            r = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": search_query, "format": "json", "limit": 5},
                headers={"User-Agent": "smart-complaint-map"},
                timeout=5,
            )
            if r.ok:
                st.session_state["addr_suggestions"] = r.json()
        except Exception:
            st.session_state["addr_suggestions"] = []

    if st.session_state["addr_suggestions"]:
        options = [
            f"{s['display_name']}" for s in st.session_state["addr_suggestions"]
        ]
        selected = st.selectbox("Select suggestion", options)
        if selected:
            idx = options.index(selected)
            loc = st.session_state["addr_suggestions"][idx]
            st.session_state["clicked_location"] = {
                "lat": float(loc["lat"]),
                "lon": float(loc["lon"]),
            }

    # ---------------- Current location ----------------
    if st.button("📍 Use my current location"):
        st.markdown(
            """
            <script>
            navigator.geolocation.getCurrentPosition(
              (pos) => {
                window.parent.postMessage(
                  {lat: pos.coords.latitude, lon: pos.coords.longitude},
                  "*"
                );
              }
            );
            </script>
            """,
            unsafe_allow_html=True,
        )

    # ---------------- Map rendering ----------------
    df_all = load_complaints()
    clicked = st.session_state.get("clicked_location")

    center = [DEFAULT_LAT, DEFAULT_LON]
    if clicked:
        center = [clicked["lat"], clicked["lon"]]

    m = folium.Map(location=center, zoom_start=DEFAULT_ZOOM)

    if not df_all.empty:
        cluster = MarkerCluster().add_to(m)
        for _, row in df_all.iterrows():
            folium.CircleMarker(
                [row["lat"], row["lon"]],
                radius=5,
                color=COLOR_MAP.get(row["issue_type"], "#4caf50"),
                fill=True,
                fill_opacity=0.8,
            ).add_to(cluster)

    if clicked:
        folium.Marker(
            [clicked["lat"], clicked["lon"]],
            icon=folium.Icon(color="green", icon="plus"),
        ).add_to(m)

    left, right = st.columns([2.5, 1])

    with left:
        returned = st_folium(
            m,
            height=600,
            use_container_width=True,
            returned_objects=["last_clicked"],
        )

        if returned and returned.get("last_clicked"):
            lat = returned["last_clicked"]["lat"]
            lon = returned["last_clicked"]["lng"]
            st.session_state["clicked_location"] = {"lat": lat, "lon": lon}

    # ---------------- Complaint form ----------------
    with right:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)

        if "clicked_location" not in st.session_state:
            st.info("Click on the map or use search/current location to report an issue.")
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
            photo_file = st.file_uploader("Upload a photo (optional)", ["jpg", "jpeg", "png"])

            authority = AUTHORITY_CONTACTS.get(issue_type)
            if authority:
                st.write(f"🏛️ {authority['dept']}")
                st.write(f"📞 {authority['phone']}")
                st.write(f"📧 {authority['email']}")

            send_email = st.checkbox("Generate email to send this complaint")

            if st.button("✅ Submit"):
                photo_path = None
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
                    st.session_state["clicked_location"]["lat"],
                    st.session_state["clicked_location"]["lon"],
                    description,
                    photo_path,
                )

                st.success("Complaint submitted successfully!")

                if send_email and authority:
                    subject = f"Citizen complaint – {issue_type}"
                    body = f"""
Location: {st.session_state["clicked_location"]["lat"]}, {st.session_state["clicked_location"]["lon"]}
Intensity: {intensity}

{description or ""}
"""
                    mailto = (
                        f"mailto:{authority['email']}?"
                        f"subject={urllib.parse.quote(subject)}&"
                        f"body={urllib.parse.quote(body)}"
                    )
                    st.markdown(f"[📨 Click here to send email]({mailto})")

                st.session_state["clicked_location"] = None

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
