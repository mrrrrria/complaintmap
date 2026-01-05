import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta


def render(df_all):
    st.header("Statistics & Distributions")

    if df_all.empty:
        st.info("No data available yet to compute statistics.")
        return

    # Ensure timestamp is datetime
    df_all["timestamp"] = pd.to_datetime(df_all["timestamp"])

    #pie chart

    st.subheader("Complaint Types Distribution")

    counts = df_all["issue_type"].value_counts()
    percentages = (counts / counts.sum() * 100).round(1)

    col_pie, col_info = st.columns([1.2, 1])
    with col_pie:
        fig, ax = plt.subplots(figsize=(4,4), facecolor="none")  # figure transparent
        ax.set_facecolor("none")  # axes transparent
        ax.pie(counts, labels=counts.index, autopct="%1.1f%%")
        ax.set_title("Types of Complaints")
        st.pyplot(fig)

    with col_info:
        st.markdown("### Percentages")
        for t, pct in percentages.items():
            st.write(f"**{t}**: {pct}%")

    st.markdown("---")
    # filter

    st.subheader("Filters")

    colf1, colf2 = st.columns(2)

    with colf1:
        type_filter = st.multiselect(
            "Complaint type",
            options=sorted(df_all["issue_type"].unique()),
            default=sorted(df_all["issue_type"].unique()),
        )

    with colf2:
        intensite_min = st.slider(
            "Minimum intensity",
            1,
            5,
            1,
        )

    df = df_all[
        (df_all["issue_type"].isin(type_filter))
        & (df_all["intensity"] >= intensite_min)
    ]

    if df.empty:
        st.warning("No reports match these filters.")
        return

    st.markdown("---")

    #complaints of the current week per pay mon to sun

    st.subheader("Complaints During the Current Week")

    today = pd.Timestamp.today().normalize()
    start_week = today - pd.Timedelta(days=today.weekday())
    end_week = start_week + pd.Timedelta(days=6)

    df_week = df[
        (df["timestamp"].dt.date >= start_week.date())
        & (df["timestamp"].dt.date <= end_week.date())
    ]

    # Prepare full week (Mon–Sun)
    week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    week_counts = (
        df_week["timestamp"]
        .dt.day_name()
        .value_counts()
        .reindex(week_days, fill_value=0)
    )

    fig, ax = plt.subplots(figsize=(8, 3), facecolor="none")
    ax.set_facecolor("none")
    ax.bar(week_days, week_counts.values)
    ax.set_ylabel("Number of complaints")
    ax.set_title("Complaints per Day (Current Week)")
    st.pyplot(fig)

    st.markdown("---")

    # complaints of the current day per hour


    st.subheader("Complaints During the Current Day")

    df_day = df[df["timestamp"].dt.date == today.date()]

    hourly_counts = (
        df_day["timestamp"]
        .dt.hour
        .value_counts()
        .sort_index()
        .reindex(range(24), fill_value=0)
    )

    fig, ax = plt.subplots(figsize=(8, 3), facecolor="none")
    ax.set_facecolor("none")
    ax.bar(hourly_counts.index, hourly_counts.values)
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Number of complaints")
    ax.set_xticks(range(0, 24))
    ax.set_title("Complaints per Hour (Today)")
    st.pyplot(fig)
