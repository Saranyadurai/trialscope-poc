"""
TrialScope — Clinical Trial Efficiency Benchmarking (POC)
Upload a ClinicalTrials.gov-derived CSV and get instant efficiency insights.

Run locally:
    pip install streamlit pandas plotly
    streamlit run streamlit_app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="TrialScope", layout="wide", page_icon="🧬")

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

EXPECTED_COLS = [
    "nct_id", "brief_title", "condition", "phase", "overall_status",
    "start_date", "primary_completion_date", "completion_date",
    "enrollment_count", "enrollment_type", "why_stopped",
    "sponsor_name", "location_countries",
]

TERMINATED_STATUSES = {"TERMINATED", "WITHDRAWN", "SUSPENDED"}


@st.cache_data
def load_csv(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["start_date", "primary_completion_date", "completion_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def compute_duration_months(df: pd.DataFrame) -> pd.DataFrame:
    if "start_date" in df.columns and "primary_completion_date" in df.columns:
        df["duration_months"] = (
            (df["primary_completion_date"] - df["start_date"]).dt.days / 30.44
        )
        df.loc[df["duration_months"] < 0, "duration_months"] = None
    return df


def first_phase(phase_str):
    if pd.isna(phase_str):
        return "Not specified"
    parts = str(phase_str).split(";")
    return parts[0].strip()


# ----------------------------------------------------------------------
# Sidebar — upload & filters
# ----------------------------------------------------------------------

st.sidebar.title("🧬 TrialScope")
st.sidebar.caption("Clinical trial efficiency benchmarking from public RWD")

uploaded_file = st.sidebar.file_uploader(
    "Upload trials CSV",
    type=["csv"],
    help="Expected columns: nct_id, brief_title, condition, phase, overall_status, "
         "start_date, primary_completion_date, completion_date, enrollment_count, "
         "enrollment_type, why_stopped, sponsor_name, location_countries",
)

if not uploaded_file:
    st.title("🧬 TrialScope")
    st.markdown(
        "Upload a clinical trials CSV in the sidebar to get started. "
        "This works directly with the schema produced by `fetch_t2d_trials.py` "
        "(pulled live from the ClinicalTrials.gov API v2)."
    )
    st.info("No file uploaded yet — waiting for a CSV.")
    st.stop()

df = load_csv(uploaded_file)

missing = [c for c in EXPECTED_COLS if c not in df.columns]
if missing:
    st.warning(
        f"Heads up — these expected columns weren't found and related charts will be "
        f"skipped: {', '.join(missing)}"
    )

df = parse_dates(df)
df = compute_duration_months(df)

if "phase" in df.columns:
    df["phase_clean"] = df["phase"].apply(first_phase)

# --- Sidebar filters ---
st.sidebar.markdown("---")
st.sidebar.subheader("Filters")

if "phase_clean" in df.columns:
    phases = sorted(df["phase_clean"].dropna().unique().tolist())
    selected_phases = st.sidebar.multiselect("Phase", phases, default=phases)
    df = df[df["phase_clean"].isin(selected_phases)]

if "overall_status" in df.columns:
    statuses = sorted(df["overall_status"].dropna().unique().tolist())
    selected_statuses = st.sidebar.multiselect("Status", statuses, default=statuses)
    df = df[df["overall_status"].isin(selected_statuses)]

if "sponsor_name" in df.columns:
    top_sponsors = df["sponsor_name"].value_counts().head(30).index.tolist()
    sponsor_filter = st.sidebar.selectbox(
        "Focus sponsor (optional)", ["All"] + top_sponsors
    )
else:
    sponsor_filter = "All"

st.sidebar.markdown("---")
st.sidebar.metric("Trials in view", len(df))

# ----------------------------------------------------------------------
# Main — tabs
# ----------------------------------------------------------------------

st.title("🧬 TrialScope")
st.caption("Clinical trial efficiency benchmarking using public ClinicalTrials.gov data")

tab_overview, tab_timelines, tab_enrollment, tab_termination, tab_sponsor = st.tabs(
    ["Overview", "Timelines", "Enrollment", "Termination Reasons", "Sponsor Benchmark"]
)

# ---------------- Overview ----------------
with tab_overview:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Trials", len(df))
    if "overall_status" in df.columns:
        pct_recruiting = (df["overall_status"] == "RECRUITING").mean() * 100
        col2.metric("% Recruiting", f"{pct_recruiting:.0f}%")
    if "overall_status" in df.columns:
        pct_terminated = df["overall_status"].isin(TERMINATED_STATUSES).mean() * 100
        col3.metric("% Terminated/Withdrawn", f"{pct_terminated:.0f}%")
    if "enrollment_count" in df.columns:
        col4.metric("Median Enrollment", f"{df['enrollment_count'].median():.0f}")

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        if "phase_clean" in df.columns:
            phase_counts = df["phase_clean"].value_counts().reset_index()
            phase_counts.columns = ["Phase", "Count"]
            fig = px.bar(phase_counts, x="Phase", y="Count", title="Trials by Phase")
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        if "overall_status" in df.columns:
            status_counts = df["overall_status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            fig = px.pie(status_counts, names="Status", values="Count", title="Trial Status Mix")
            st.plotly_chart(fig, use_container_width=True)

    if "start_date" in df.columns:
        st.markdown("---")
        by_year = df.dropna(subset=["start_date"]).copy()
        by_year["start_year"] = by_year["start_date"].dt.year
        year_counts = by_year.groupby("start_year").size().reset_index(name="count")
        fig = px.line(year_counts, x="start_year", y="count", markers=True,
                      title="Trial Starts Over Time")
        st.plotly_chart(fig, use_container_width=True)

# ---------------- Timelines ----------------
with tab_timelines:
    st.subheader("Trial Duration Benchmarking")
    if "duration_months" in df.columns and df["duration_months"].notna().any():
        c1, c2 = st.columns(2)
        with c1:
            fig = px.histogram(
                df.dropna(subset=["duration_months"]), x="duration_months", nbins=30,
                title="Distribution of Trial Duration (Start → Primary Completion)"
            )
            fig.update_xaxes(title="Duration (months)")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            if "phase_clean" in df.columns:
                fig = px.box(
                    df.dropna(subset=["duration_months"]), x="phase_clean", y="duration_months",
                    title="Duration by Phase"
                )
                fig.update_xaxes(title="Phase")
                fig.update_yaxes(title="Duration (months)")
                st.plotly_chart(fig, use_container_width=True)

        median_dur = df["duration_months"].median()
        st.info(
            f"**Quick read:** median trial duration in this dataset is "
            f"**{median_dur:.1f} months** from start to primary completion."
        )
    else:
        st.warning("Need `start_date` and `primary_completion_date` columns to compute durations.")

# ---------------- Enrollment ----------------
with tab_enrollment:
    st.subheader("Enrollment Efficiency")
    if "enrollment_count" in df.columns:
        c1, c2 = st.columns(2)
        with c1:
            fig = px.histogram(df, x="enrollment_count", nbins=30, title="Enrollment Count Distribution")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            if "phase_clean" in df.columns:
                med_enroll = df.groupby("phase_clean")["enrollment_count"].median().reset_index()
                fig = px.bar(med_enroll, x="phase_clean", y="enrollment_count",
                             title="Median Enrollment by Phase")
                st.plotly_chart(fig, use_container_width=True)

        if "enrollment_type" in df.columns:
            st.markdown("---")
            type_counts = df["enrollment_type"].value_counts().reset_index()
            type_counts.columns = ["Enrollment Type", "Count"]
            fig = px.bar(type_counts, x="Enrollment Type", y="Count",
                         title="Actual vs. Estimated/Anticipated Enrollment")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Need an `enrollment_count` column for this view.")

# ---------------- Termination Reasons ----------------
with tab_termination:
    st.subheader("Termination & Withdrawal Analysis")
    if "overall_status" in df.columns:
        stopped = df[df["overall_status"].isin(TERMINATED_STATUSES)]
        st.metric("Terminated / Withdrawn / Suspended Trials", len(stopped))

        if "why_stopped" in df.columns:
            reasons = stopped.dropna(subset=["why_stopped"])
            if len(reasons) > 0:
                st.dataframe(
                    reasons[["nct_id", "brief_title", "overall_status", "why_stopped"]],
                    use_container_width=True, hide_index=True,
                )
            else:
                st.info(
                    "No `why_stopped` text present in this dataset for the filtered trials — "
                    "this field is often left blank in the registry even when a trial is stopped."
                )
        else:
            st.warning("No `why_stopped` column found in the uploaded CSV.")
    else:
        st.warning("Need an `overall_status` column for this view.")

# ---------------- Sponsor Benchmark ----------------
with tab_sponsor:
    st.subheader("Sponsor Benchmarking")
    if "sponsor_name" in df.columns:
        top_n = st.slider("Show top N sponsors by trial count", 5, 30, 15)
        sponsor_counts = df["sponsor_name"].value_counts().head(top_n).reset_index()
        sponsor_counts.columns = ["Sponsor", "Trial Count"]
        fig = px.bar(sponsor_counts, x="Trial Count", y="Sponsor", orientation="h",
                     title=f"Top {top_n} Sponsors by Trial Count")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

        if sponsor_filter != "All":
            st.markdown("---")
            st.subheader(f"Focus: {sponsor_filter}")
            sub = df[df["sponsor_name"] == sponsor_filter]
            c1, c2, c3 = st.columns(3)
            c1.metric("Trials", len(sub))
            if "duration_months" in sub.columns:
                c2.metric("Median Duration (mo)", f"{sub['duration_months'].median():.1f}"
                          if sub["duration_months"].notna().any() else "N/A")
            if "enrollment_count" in sub.columns:
                c3.metric("Median Enrollment", f"{sub['enrollment_count'].median():.0f}"
                          if sub["enrollment_count"].notna().any() else "N/A")
            st.dataframe(
                sub[[c for c in ["nct_id", "brief_title", "phase_clean", "overall_status",
                                 "duration_months", "enrollment_count"] if c in sub.columns]],
                use_container_width=True, hide_index=True,
            )
    else:
        st.warning("Need a `sponsor_name` column for this view.")

st.markdown("---")
st.caption(
    f"Data as uploaded • {len(df)} trials in current view • "
    f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}"
)
