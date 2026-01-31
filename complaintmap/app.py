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

# 🔧 CHANGE: Authority mapping for Hyderabad (replaces Lyon context)
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

def render_report_home():
    st.subheader("Report an issue on the map")

    df_all = load_complaints()
    clicked = st.session_state.get("clicked_location", None)

    center = [DEFAULT_LAT, DEFAULT_LON]
    if not df_all.empty:
        center = [df_all["lat"].mean(), df_all["lon"].mean()]

    m = folium.Map(location=center, zoom_start=DEFAULT_ZOOM)

    if not df_all.empty:
        cluster = MarkerCluster().add_to(m)
        for _, row in df_all.iterrows():
            color = COLOR_MAP.get(row["issue_type"], "#5c7cfa")
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=5,
                color=color,
                fill=True,
                fill_opacity=0.8,
                popup=f"{row['issue_type']} (Intensity {row['intensity']})",
            ).add_to(cluster)

    if clicked is not None:
        folium.Marker(
            location=[clicked["lat"], clicked["lon"]],
            popup="New issue here",
            icon=folium.Icon(color="green", icon="plus"),
        ).add_to(m)

    left, right = st.columns([2.5, 1])

    with left:
        map_data = st_folium(m, width=750, height=550)

    if map_data and map_data.get("last_clicked"):
        st.session_state["clicked_location"] = {
            "lat": map_data["last_clicked"]["lat"],
            "lon": map_data["last_clicked"]["lng"],
        }
        clicked = st.session_state["clicked_location"]

    with right:
        if clicked:
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
            intensity = st.slider("Intensity (1–5)", 1, 5, 3)
            description = st.text_area("Description (optional)")

            # 🔧 CHANGE: Show responsible authority (Hyderabad)
            authority = AUTHORITY_CONTACTS.get(issue_type)
            if authority:
                st.markdown("**Responsible authority**")
                st.write(f"🏛️ {authority['dept']}")
                st.write(f"📞 {authority['phone']}")
                st.write(f"📧 {authority['email']}")

            # 🔧 CHANGE: User consent for email
            send_email = st.checkbox(
                "📧 Send this complaint to the responsible authority"
            )

            if st.button("✅ Submit report"):
                add_complaint(
                    issue_type,
                    intensity,
                    clicked["lat"],
                    clicked["lon"],
                    description,
                    None,
                )

                st.success("Report submitted successfully.")

                # 🔧 CHANGE: Generate email (user-controlled, ethical)
                if send_email and authority:
                    subject = f"Citizen complaint – {issue_type} issue in Hyderabad"
                    body = f"""
Dear Sir/Madam,

I would like to report a {issue_type.lower()} issue at the following location:

Latitude: {clicked['lat']}
Longitude: {clicked['lon']}
Intensity: {intensity}
Description: {description or "Not provided"}

This message was generated using a Smart Complaint Map
as part of an academic project.

Regards,
A concerned citizen
"""
                    mailto = (
                        f"mailto:{authority['email']}?"
                        f"subject={urllib.parse.quote(subject)}&"
                        f"body={urllib.parse.quote(body)}"
                    )
                    st.markdown(f"[📨 Click here to send email]({mailto})")

                st.session_state["clicked_location"] = None

def main():
    setup()
    init_db()

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

    if pages[choice] == "home":
        render_report_home()
    elif pages[choice] == "about":
        about_page.render()

if __name__ == "__main__":
    main()
