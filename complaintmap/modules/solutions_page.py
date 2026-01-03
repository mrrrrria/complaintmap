import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import pandas as pd
# =========================================================
# NORMALIZE ISSUE NAMES
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
        "water": "Water",
        "flood": "Water",
        "cycling / walking": "Cycling / Walking",
        "cycling": "Cycling / Walking",
        "walking": "Cycling / Walking",
        "other": "Other"
    }
    return mapping.get(v, value.capitalize())

# =========================================================
# SHORT SOLUTION (MAP POPUP – SIMPLE & VARIED)
# =========================================================
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


# =========================================================
# DETAILED MULTI-SOLUTION (BOTTOM SECTION)
# =========================================================
def generate_detailed_solutions(issue, intensity):
    intensity = int(intensity)

    if issue == "Air":
        return [
            "Monitor air quality levels to identify recurring pollution patterns.",
            "Encourage residents to adopt low-impact mobility options.",
            "Promote long-term urban greening strategies."
        ]

    if issue == "Heat":
        return [
            "Increase shaded areas and access to cooling spaces.",
            "Expand tree planting and green infrastructure.",
            "Apply heat-mitigation materials in public spaces."
        ]

    if issue == "Noise":
        return [
            "Monitor noise levels and identify peak disturbance periods.",
            "Introduce traffic calming measures.",
            "Restrict heavy vehicle traffic during sensitive hours."
        ]

    if issue == "Odour":
        return [
            "Inspect sanitation conditions and waste management practices.",
            "Improve waste collection frequency.",
            "Enforce environmental standards on odor sources."
        ]

    if issue == "Water":
        return [
            "Inspect and maintain drainage systems.",
            "Address recurring water accumulation areas.",
            "Implement flood mitigation and infrastructure upgrades."
        ]

    if issue == "Cycling / Walking":
        return [
            "Improve pedestrian and cyclist visibility.",
            "Enhance road safety through better crossings.",
            "Develop dedicated and protected mobility lanes."
        ]

    return [
        "Collect additional reports.",
        "Conduct further assessment."
    ]


# =========================================================
# MAIN RENDER FUNCTION
# =========================================================
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

    issues = ["All"] + sorted(df["issue"].unique())
    selected_issue = st.selectbox("Reported Issue", issues)

    if selected_issue != "All":
        df = df[df["issue"] == selected_issue]

    df_sorted = df.sort_values("timestamp")
    grouped = df_sorted.groupby(["lat", "lon", "issue"], as_index=False).last()
    latest_row = grouped.loc[grouped["timestamp"].idxmax()]

    m = folium.Map(
        location=[latest_row["lat"], latest_row["lon"]],
        zoom_start=14
    )

    HeatMap(grouped[["lat", "lon"]].values.tolist(), radius=25, blur=18).add_to(m)

    # ---------------- MAP MARKERS ----------------
    for i, row in grouped.iterrows():
        popup_solution = generate_solution(row["issue"], row["intensity"], i)
        color = "red" if row["timestamp"] == latest_row["timestamp"] else "blue"

        popup_html = f"""
        <div style="
            width:320px;
            font-family: Arial, sans-serif;
            border-radius:10px;
            overflow:hidden;
        ">
            <div style="
                background-color:#f2f2f2;
                padding:12px;
                font-size:14px;
                font-weight:600;
            ">
                Reported Issue : {row['issue']}<br>
                Intensity : {row['intensity']}
            </div>
            <div style="
                background-color:#ffffff;
                padding:14px;
                font-size:14px;
                line-height:1.4;
            ">
                <b>Solution :</b><br>
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

    # ---------------- BOTTOM SECTION ----------------
    st.subheader("📌 Current Reported Solutions")

    detailed = generate_detailed_solutions(
        latest_row["issue"],
        latest_row["intensity"]
    )

    solutions_html = "".join([f"<li>{s}</li>" for s in detailed])

    st.markdown(
        f"""
        <div style="background:white; padding:20px; border-radius:12px;">
            <div style="background:#f2f2f2; padding:12px;">
                <b>Reported Issue:</b> {latest_row['issue']}<br>
                <b>Intensity:</b> {latest_row['intensity']}
            </div>
            <div style="margin-top:12px;">
                <b>Recommended Actions:</b>
                <ul>
                    {solutions_html}
                </ul>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
