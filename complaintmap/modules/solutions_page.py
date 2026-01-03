import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import pandas as pd
import streamlit.components.v1 as components


def normalize_issue(value):
    if not isinstance(value, str):
        return "Other"

    v = value.strip().lower()

    if "air" in v or "pollution" in v:
        return "Air"
    if "noise" in v or "bruit" in v:
        return "Noise"
    if "heat" in v or "chaleur" in v or "temperature" in v:
        return "Heat"
    if "odor" in v or "odour" in v or "odeur" in v or "smell" in v:
        return "Odour"
    if "water" in v or "flood" in v or "drain" in v:
        return "Water"
    if "cycling" in v or "walking" in v or "pedestrian" in v:
        return "Cycling / Walking"

    return value.capitalize()


# Simple short solutions shown on the map
def generate_solution(issue, intensity, variant):
    intensity = int(intensity)

    SOLUTIONS = {
        "Air": {
            "low": [
                "Monitor air quality and raise awareness.",
                "Encourage low-impact mobility choices."
            ],
            "medium": [
                "Reduce car usage and promote public transport.",
                "Increase urban greenery in the area."
            ],
            "high": [
                "Restrict high-emission vehicles.",
                "Create low-emission zones."
            ]
        },
        "Heat": {
            "low": [
                "Increase shaded areas.",
                "Promote heat awareness."
            ],
            "medium": [
                "Install shaded seating.",
                "Expand tree coverage."
            ],
            "high": [
                "Apply cool-surface technologies.",
                "Redesign public spaces to reduce heat."
            ]
        },
        "Noise": {
            "low": [
                "Monitor noise levels.",
                "Reinforce noise regulations."
            ],
            "medium": [
                "Introduce traffic calming.",
                "Adjust local traffic flow."
            ],
            "high": [
                "Install noise barriers.",
                "Restrict heavy vehicle traffic."
            ]
        },
        "Odour": {
            "low": [
                "Inspect sanitation conditions.",
                "Increase cleaning frequency."
            ],
            "medium": [
                "Improve waste collection.",
                "Identify odor sources."
            ],
            "high": [
                "Upgrade waste treatment.",
                "Enforce environmental regulations."
            ]
        },
        "Water": {
            "low": [
                "Inspect drainage systems.",
                "Monitor water accumulation."
            ],
            "medium": [
                "Clean and maintain drainage.",
                "Address recurring pooling."
            ],
            "high": [
                "Upgrade drainage infrastructure.",
                "Implement flood mitigation."
            ]
        },
        "Cycling / Walking": {
            "low": [
                "Improve signage.",
                "Repair minor surface issues."
            ],
            "medium": [
                "Improve crossings.",
                "Enhance user separation."
            ],
            "high": [
                "Build dedicated cycling lanes.",
                "Redesign intersections."
            ]
        },
        "Other": {
            "low": ["Monitor the situation."],
            "medium": ["Conduct a local assessment."],
            "high": ["Plan infrastructure-level intervention."]
        }
    }

    if intensity <= 2:
        tier = "low"
    elif intensity == 3:
        tier = "medium"
    else:
        tier = "high"

    options = SOLUTIONS.get(issue, SOLUTIONS["Other"])[tier]
    return options[variant % len(options)]


# Additional solutions shown at the bottom
def generate_detailed_solutions(issue):
    if issue == "Air":
        return [
            "Encourage residents to adopt low-impact mobility options.",
            "Promote long-term urban greening strategies."
        ]
    if issue == "Heat":
        return [
            "Expand tree planting and green infrastructure.",
            "Apply heat-mitigation materials in public spaces."
        ]
    if issue == "Noise":
        return [
            "Introduce traffic calming measures.",
            "Restrict heavy vehicle traffic during sensitive hours."
        ]
    if issue == "Odour":
        return [
            "Improve waste collection frequency.",
            "Enforce environmental standards on odor sources."
        ]
    if issue == "Water":
        return [
            "Address recurring water accumulation areas.",
            "Implement flood mitigation strategies."
        ]
    if issue == "Cycling / Walking":
        return [
            "Enhance road safety through better crossings.",
            "Develop dedicated and protected mobility lanes."
        ]
    return []


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

    required_cols = ["issue_type", "intensity", "lat", "lon", "timestamp"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Missing required column: {col}")
            st.write("Available columns:", df.columns.tolist())
            return

    df["issue"] = df["issue_type"].apply(normalize_issue)
    df["intensity"] = df["intensity"].fillna(1).astype(int)

    df_sorted = df.sort_values("timestamp")
    grouped = df_sorted.groupby(["lat", "lon", "issue"], as_index=False).last()
    latest_row = grouped.loc[grouped["timestamp"].idxmax()]

    m = folium.Map(
        location=[latest_row["lat"], latest_row["lon"]],
        zoom_start=14
    )

    HeatMap(grouped[["lat", "lon"]].values.tolist(), radius=25, blur=18).add_to(m)

    for i, row in grouped.iterrows():
        popup_solution = generate_solution(row["issue"], row["intensity"], i)
        color = "red" if row["timestamp"] == latest_row["timestamp"] else "blue"

        popup_html = f"""
        <div style="width:320px; font-family:Arial; border-radius:10px; overflow:hidden;">
            <div style="background:#f2f2f2; padding:12px; font-weight:600;">
                Reported Issue: {row['issue']}<br>
                Intensity: {row['intensity']}
            </div>
            <div style="background:white; padding:14px;">
                <b>Solution:</b><br>
                {popup_solution}
            </div>
        </div>
        """

        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=popup_html,
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)

    st_folium(m, width=1400, height=650)

    st.subheader("📌 Current Reported Solution")

    primary_solution = generate_solution(
        latest_row["issue"],
        latest_row["intensity"],
        0
    )

    additional = generate_detailed_solutions(latest_row["issue"])
    additional_html = "".join([f"<li>{s}</li>" for s in additional])

    html_block = f"""
    <div style="background:white; padding:20px; border-radius:12px; font-family:Arial;">
        <div style="background:#f2f2f2; padding:12px; font-weight:600;">
            Reported Issue: {latest_row['issue']}<br>
            Intensity: {latest_row['intensity']}
        </div>

        <div style="margin-top:14px;">
            <b>Primary Suggested Action:</b><br>
            {primary_solution}
        </div>

        <div style="margin-top:14px;">
            <b>Additionally:</b>
            <ul>
                {additional_html}
            </ul>
        </div>
    </div>
    """

    components.html(html_block, height=260)
