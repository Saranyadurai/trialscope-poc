"""
Pull Type 2 Diabetes clinical trials from ClinicalTrials.gov API v2
and shape them into a clean CSV for the Streamlit POC.

Usage:
    pip install requests pandas
    python fetch_t2d_trials.py

Output:
    t2d_trials.csv  (~300 rows, 12 columns)
"""

import requests
import pandas as pd
import time

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

# Fields we actually need (keeps payload small & fast)
FIELDS = [
    "NCTId",
    "BriefTitle",
    "Condition",
    "Phase",
    "OverallStatus",
    "StartDate",
    "PrimaryCompletionDate",
    "CompletionDate",
    "EnrollmentCount",
    "EnrollmentType",
    "WhyStopped",
    "LeadSponsorName",
    "LocationCountry",
]

def fetch_studies(condition="Type 2 Diabetes", target_rows=300, page_size=100):
    all_studies = []
    params = {
        "query.cond": condition,
        "fields": ",".join(FIELDS),
        "pageSize": page_size,
        "format": "json",
    }
    next_token = None

    while len(all_studies) < target_rows:
        if next_token:
            params["pageToken"] = next_token
        resp = requests.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        studies = data.get("studies", [])
        if not studies:
            break
        all_studies.extend(studies)

        next_token = data.get("nextPageToken")
        if not next_token:
            break
        time.sleep(0.2)  # be polite to the API

    return all_studies[:target_rows]


def flatten(study):
    ps = study.get("protocolSection", {})
    ident = ps.get("identificationModule", {})
    status = ps.get("statusModule", {})
    design = ps.get("designModule", {})
    sponsor = ps.get("sponsorCollaboratorsModule", {})
    conditions = ps.get("conditionsModule", {})
    contacts = ps.get("contactsLocationsModule", {})

    locations = contacts.get("locations", [])
    countries = sorted(set(loc.get("country", "") for loc in locations if loc.get("country")))

    phases = design.get("phases", [])
    enrollment = design.get("enrollmentInfo", {})

    return {
        "nct_id": ident.get("nctId"),
        "brief_title": ident.get("briefTitle"),
        "condition": "; ".join(conditions.get("conditions", [])),
        "phase": "; ".join(phases) if phases else None,
        "overall_status": status.get("overallStatus"),
        "start_date": status.get("startDateStruct", {}).get("date"),
        "primary_completion_date": status.get("primaryCompletionDateStruct", {}).get("date"),
        "completion_date": status.get("completionDateStruct", {}).get("date"),
        "enrollment_count": enrollment.get("count"),
        "enrollment_type": enrollment.get("type"),
        "why_stopped": status.get("whyStopped"),
        "sponsor_name": sponsor.get("leadSponsor", {}).get("name"),
        "location_countries": "; ".join(countries) if countries else None,
    }


if __name__ == "__main__":
    print("Fetching Type 2 Diabetes trials from ClinicalTrials.gov API v2...")
    studies = fetch_studies(condition="Type 2 Diabetes", target_rows=300)
    print(f"Retrieved {len(studies)} studies.")

    rows = [flatten(s) for s in studies]
    df = pd.DataFrame(rows)

    out_path = "t2d_trials.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows to {out_path}")
    print(df.head())
