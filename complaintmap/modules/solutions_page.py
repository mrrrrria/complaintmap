import streamlit as st
import pandas as pd

# --------------------------------------------------
# Normalize complaint categories (French → English)
# --------------------------------------------------
def normalize_issue(raw_type):
    if not isinstance(raw_type, str):
        return "Other"

    t = raw_type.strip().lower()

    mapping = {
        "air": "Air quality",
        "chaleur": "Heat",
        "bruit": "Noise",
        "mobilité": "Cycling / Walking",
        "mobilite": "Cycling / Walking",
        "odeur": "Odor",

        "heat": "Heat",
        "noise": "Noise",
        "air quality": "Air quality",
        "odor": "Odor",
        "mobility": "Cycling / Walking",
        "cycling / walking": "Cycling / Walking",
    }

    return mapping.get(t, "Other")


# --------------------------------------------------
# Solutions knowledge base
# --------------------------------------------------
SOLUTIONS = {
    "Heat": [
        "Increase urban greenery and tree coverage",
        "Install solar canopies for shading",
        "Use reflective and cool materials",
        "Create shaded pedestrian corridors",
    ],
    "Noise": [
        "Low-noise road surfaces",
        "Traffic calming measures",
        "Noise barriers near busy roads",
        "Time-based traffic restrictions",
    ],
    "Air quality": [
        "Low-emission zones",
        "Promote public transport",
        "Urban green buffers",
        "Continuous air-quality monitoring",
    ],
    "Cycling / Walking": [
        "Protected cycling lanes",
        "Wider sidewalks",
        "Reduced car traffic",
        "Improved street lighting",
    ],
    "Odor": [
        "Improved waste management",
        "Industrial odor monitoring",
        "Better sewage ventilation",
        "Regular inspections",
    ],
    "Other": [
        "Further investigation required",
        "Field surveys and citizen feedback",
    ],
}


# --------------------------------------------------
# MAIN RENDER FUNCTION
# Called from app.py → solutions_page.render(df_all)
# --------------------------------------------------
def render(df):
    st.title("💡 Urban Solutions")

    st.markdown(
        """
        This page links **citizen-reported problems** to
        **practical urban solutions**, following Smart City principles.
        """
    )

    if df is None or df.empty:
        st.warning("No complaint data available.")
        return

    # --------------------------------------------------
    # Detect issue column safely (FIX)
    # --------------------------------------------------
    possible_columns = ["type", "category", "issue", "problem", "complaint_type"]
    issue_col = None

    for col in possible_columns:
        if col in df.columns:
            issue_col = col
            break

    if issue_col is None:
        st.error("No complaint category column found.")
        st.write("Available columns:", list(df.columns))
        return

    # --------------------------------------------------
    # Normalize issues
    # --------------------------------------------------
    df = df.copy()
    df["issue"] = df[issue_col].apply(normalize_issue)

    # --------------------------------------------------
    # User selection
    # --------------------------------------------------
    st.subheader("Select problem type")
    issue_list = sorted(df["issue"].unique())
    selected_issue = st.selectbox("Urban issue", issue_list)

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------
    count = df[df["issue"] == selected_issue].shape[0]
    st.info(f"Number of reports: **{count}**")

    # --------------------------------------------------
    # Show solutions
    # --------------------------------------------------
    st.subheader("Suggested solutions")

    for sol in SOLUTIONS.get(selected_issue, SOLUTIONS["Other"]):
        st.markdown(f"- {sol}")

    # --------------------------------------------------
    # Smart City context
    # --------------------------------------------------
    st.markdown("---")
    st.markdown(
        """
        These recommendations demonstrate how **citizen data**
        can be transformed into **actionable urban strategies**.
        """
    )


# --------------------------------------------------
# Local test protection
# --------------------------------------------------
if __name__ == "__main__":
    st.warning("This module is intended to be called from app.py")
