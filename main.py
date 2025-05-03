from dotenv import load_dotenv

load_dotenv()

import os
import time
import requests
from datetime import datetime
from gcp_pal import Firestore
from jobspy import scrape_jobs


CURRENT_TIME = datetime.now()
FIRESTORE_SEARCH_TERMS_LOCATION = f"metadata/job_notifications/search_terms"


def get_search_terms():
    search_terms = Firestore(FIRESTORE_SEARCH_TERMS_LOCATION).ls()
    return search_terms


def construct_message(new_jobs):
    """
    Turn a dataframe of job listings into a text block grouped by company
    and sorted alphabetically by company name.

    Expected columns: 'company', 'title', 'job_url'
    """
    lines = []

    # ➊  Sort by company so the groups appear alphabetically
    for company, grp in new_jobs.sort_values("company").groupby("company"):
        lines.append(company)  # company header
        # ➋  Preserve the row order within each company (or sort if you prefer)
        for _, row in grp.iterrows():
            lines.append(row["title"])
            lines.append(row["job_url"])
        lines.append("")  # blank line between companies

    output = "\n".join(lines).rstrip()
    # Strip the trailing blank line and return the whole thing
    return output


def send_notification(new_jobs, search_term=""):
    """
    Send a notification to an iPhone using Pushover.
    """
    search_term = search_term.replace("_", " ").title()
    url = "https://api.pushover.net/1/messages.json"
    message = construct_message(new_jobs)
    data = {
        "token": os.getenv("PUSHOVER_API_TOKEN", None),
        "user": os.getenv("PUSHOVER_USER_KEY", None),
        "title": f"New Job Alert ({search_term})",
        "message": message,
        "priority": 1,
    }
    response = requests.post(url, data=data)
    times_to_retry = 3
    while times_to_retry > 0:
        if response.status_code != 200:
            print(
                f"Failed to send notification. Retrying {times_to_retry} more times. CODE: {response.status_code} {response.text}"
            )
            times_to_retry -= 1
        else:
            print("Notification sent.")
            return
        time.sleep(5)
    print("Failed to send notification.")
    return


def main():
    search_terms = get_search_terms()

    for search_term in search_terms:
        print(f"Processing search term: '{search_term}'")

        current_jobs_location = f"{FIRESTORE_SEARCH_TERMS_LOCATION}/{search_term}/current_jobs/company_title_pairs"

        existing_jobs = Firestore(current_jobs_location).read(allow_empty=True)
        existing_jobs = existing_jobs or []
        if "data" in existing_jobs:
            existing_jobs = set(existing_jobs["data"])
        print(f"Existing jobs: {len(existing_jobs)}")

        linkedin_jobs = scrape_jobs(
            site_name=["linkedin"],
            search_term=search_term.replace("_", " "),
            location="London, UK",
            results_wanted=1000,
            hours_old=3,
        ).loc[:, ["company", "title", "job_url"]]

        jobs_company_title_pairs = linkedin_jobs.apply(
            lambda x: f"{x['company'].lower()}--{x['title'].lower()}", axis=1
        )
        linkedin_jobs = linkedin_jobs.assign(
            company_title_pair=jobs_company_title_pairs
        )

        jobs_company_title_pairs = set(jobs_company_title_pairs)
        existing_jobs = set(existing_jobs)

        new_jobs = jobs_company_title_pairs - existing_jobs
        new_jobs = (
            linkedin_jobs[linkedin_jobs["company_title_pair"].isin(new_jobs)]
            .drop(columns=["company_title_pair"])
            .reset_index(drop=True)
        )
        print(f"New jobs:")
        print(new_jobs)

        send_notification(new_jobs, search_term=search_term)

        print(f"Writing {len(new_jobs)} current jobs to Firestore")
        Firestore(current_jobs_location).write(jobs_company_title_pairs)


if __name__ == "__main__":
    main()
