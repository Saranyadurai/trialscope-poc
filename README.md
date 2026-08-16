# TrialScope

**Clinical Trial Efficiency Benchmarking using Public Real-World Data**

A Streamlit dashboard that pulls real clinical trial data from the public
[ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-api/api) and turns
it into interactive efficiency insights — trial duration, enrollment
performance, termination patterns, and sponsor benchmarking.

Built as a proof-of-concept using an AI-assisted ("vibe coding") development
workflow with Claude.

---

## 🧬 What it does

Upload a clinical trials CSV and instantly get:

- **Overview** — KPIs (total trials, % recruiting, % terminated, median
  enrollment), phase distribution, status mix, and trial starts over time
- **Timelines** — trial duration distribution (start → primary completion),
  broken down by phase
- **Enrollment** — enrollment count distribution, median enrollment by phase,
  actual vs. estimated enrollment
- **Termination Reasons** — terminated/withdrawn/suspended trials with
  available stated reasons
- **Sponsor Benchmark** — top sponsors by trial count, with a drill-down into
  any individual sponsor's performance

All charts respond live to sidebar filters for phase, status, and sponsor.

**Demo dataset:** ~300 real Type 2 Diabetes trials, pulled live from
ClinicalTrials.gov.


## 🗂 Project Structure

```
.
├── fetch_t2d_trials.py     # Pulls trial data from ClinicalTrials.gov API v2
├── streamlit_app.py        # The Streamlit dashboard
├── requirements.txt        # Python dependencies
├── t2d_trials.csv          # Generated dataset (output of fetch script)
├── .gitignore
└── README.md
```

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/YOUR-USERNAME/trialscope-poc.git
cd trialscope-poc
```

### 2. Set up a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Pull the data
```bash
python fetch_t2d_trials.py
```
This creates `t2d_trials.csv` using live data from ClinicalTrials.gov.

### 5. Run the app
```bash
streamlit run streamlit_app.py
```
Open `http://localhost:8501`, and upload `t2d_trials.csv` when prompted.

## 🔧 Tech Stack

- **[Streamlit](https://streamlit.io/)** — web app framework
- **[Plotly](https://plotly.com/python/)** — interactive charts
- **[pandas](https://pandas.pydata.org/)** — data processing
- **[requests](https://requests.readthedocs.io/)** — API calls
- **[ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-api/api)** —
  public data source (no API key required)

## 📊 Data Source & Schema

Data is pulled from ClinicalTrials.gov's official public API. Each row
represents one trial, with the following fields:

| Field | Description |
|---|---|
| `nct_id` | Unique ClinicalTrials.gov identifier |
| `brief_title` | Trial title |
| `condition` | Condition(s) studied |
| `phase` | Trial phase (1/2/3/4/NA) |
| `overall_status` | Recruiting, Completed, Terminated, Withdrawn, etc. |
| `start_date` | Trial start date |
| `primary_completion_date` | Primary endpoint completion date |
| `completion_date` | Full trial completion date |
| `enrollment_count` | Number of participants |
| `enrollment_type` | Actual vs. estimated enrollment |
| `why_stopped` | Stated reason if terminated/withdrawn |
| `sponsor_name` | Lead sponsor |
| `location_countries` | Countries with active trial sites |

To pull a different condition, edit the `condition` parameter in
`fetch_t2d_trials.py`.

## ⚠️ Known Limitations (POC Scope)

- `why_stopped` is often left blank in the registry, even for terminated
  trials — this isn't a bug, it reflects real data sparsity.
- The app reads a static uploaded CSV rather than calling the API live on
  each load, by design, to keep the POC simple.
- Scoped to a single condition (Type 2 Diabetes) for this demo; the fetch
  script generalizes to any condition in the registry.

## 🛣 Possible Next Steps

- Live "refresh from ClinicalTrials.gov" button instead of a static upload
- Multi-condition comparison view
- Site-level geographic mapping using facility lat/long data
- AACT database integration for deeper protocol-level analysis
- Exportable PDF trial feasibility briefs

## 📄 License

This project uses publicly available data from ClinicalTrials.gov, a
registry operated by the U.S. National Library of Medicine. Built for
educational/demonstration purposes.
