import streamlit as st

def render():
    st.header("ℹ️ About the Project")

    # 🔧 CHANGE: City changed from Lyon to Hyderabad
    st.markdown(
        """
        This project was developed by three students from **Sapienza University of Rome**
        as part of the **Smart Cities** course.

        The application was initially designed for a European city (Lyon) to explore
        Smart City concepts. It was later adapted to **Hyderabad, India**, a rapidly
        growing metropolitan city facing challenges such as traffic congestion,
        air and noise pollution, urban heat stress, and pedestrian safety.

        The goal of the project is to provide an **interactive, map-based platform**
        where citizens can report local urban issues and visualize them spatially.
        """
    )

    st.subheader("Why Hyderabad?")
    st.markdown(
        """
        Hyderabad was chosen because it represents a dynamic urban environment with
        diverse and frequent citizen-reported issues. The city is part of India’s
        **Smart Cities Mission**, which emphasizes digital governance and citizen
        participation.

        Mapping complaints in Hyderabad helps demonstrate how citizen feedback can
        support data-driven urban planning and decision-making.
        """
    )

    st.subheader("Connecting Citizens and Authorities")
    st.markdown(
        """
        In addition to visualizing complaints, the platform assists citizens in
        connecting with relevant public authorities.

        When a complaint is submitted, the system:
        - Identifies the responsible department (e.g. GHMC, Traffic Police)
        - Displays official helpline numbers and contact details
        - Helps generate a structured complaint email with user consent

        The system does **not automatically submit complaints**, ensuring transparency,
        privacy, and ethical design.
        """
    )

    st.subheader("Technologies Used")
    st.markdown(
        """
        - Streamlit for the web interface  
        - Folium / Leaflet for interactive maps  
        - SQLite for complaint storage  
        - Pandas & NumPy for data handling  

        The application is modular and can be extended to other cities in the future.
        """
    )
