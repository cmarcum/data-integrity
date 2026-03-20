# The Integrity of Federal Data
**Evaluating Disruptions to Open Government Data, 2025-2026**

This repository contains the source code, raw data, and the complete text for a report evaluating the state of open government data and the impacts of administrative disruptions between 2025 and 2026. The report is not yet finalized and is currently in-revision and under-review. 

## Repository Structure

This project is organized into several directories:

* **`/report`**: Contains the full text of the report, built using Jekyll and the Just the Docs theme. It includes chapters on executive summaries, agency-specific audits (e.g., OMB, USAID, VA), administrative actions, data tools, and a glossary. The report is configured to be served as a static website or compiled directly into a full-bleed PDF (once finalized).
* **`/code`**: Houses the analytical and data-gathering scripts. It includes Python scripts for interacting with CKAN APIs (Data.gov), auditing data catalogs, and parsing Wayback Machine archives, as well as R scripts for statistical analysis and visualization of the data.
* **`/data`**: Stores the raw and processed datasets used in the report. This includes JSON data dictionary snapshots from various federal agencies, Data.gov inventory counts, reginfo.gov data pulls, and more.
* **`/images`**: A placeholder for the charts, screenshots, graphs, and workflow diagrams generated from the data that supplement information featured in the report.
* * **`/workflows`**: Contains the source files for mermaid.js workflows developed for the data auditing routines used in the report.

# Scripts for Data.gov

The scripts in this repository that access data from Data.gov's CKAN API were written to use the either the public, unauthenticated API
hosted at [https://catalog.data.gov/api/3/action/](https://catalog.data.gov/api/3/action/) or the api-key authenticated version which has a different baseurl: [https://api.gsa.gov/technology/datagov/v3/action/package_search?api_key=DEMO_KEY](https://api.gsa.gov/technology/datagov/v3/action/package_search?api_key=DEMO_KEY). This was done intentionally
to maximize public accessibility and ease-of-use.

For many use cases these scripts work just fine using the unauthenticated API. However, some endpoints (notably `package_show`, and sometimes high-volume calls to `package_search` can return **HTTP 403 Forbidden** error responses due to access controls or rate limiting.

## Steps to use authentication 
To make these scripts more robust, some modification will be needed to make them compatible with the official GSA Data.gov API gateway using an API key. 

### 1) Obtain an API key

API keys are issued by GSA’s API platform (not directly by Data.gov):

- Sign up at: https://api.data.gov/signup/
- After registration, you will receive an API key via email that can be used with the Data.gov CKAN gateway.


### 2) Provide the API key securely via the terminal

Never hard-code API keys into your scripts. Instead, provide the key via an environment variable:

**macOS / Linux (bash, zsh):**
```bash
export DATAGOV_API_KEY="YOUR API KEY"
```

**Windows PowerShell:**
```powershell
$env:DATAGOV_API_KEY="YOUR_API_KEY"
```

### 3) Change the base-urls in the scripts

In many cases, the scripts in this repository accept an api-key and will automatically switch between baseurls. In some cases, however, you will need to manually edit the scripts. In general, to use the authenticated gateway, the CKAN API paths are the same, but the host for the baseurls needs to be modified in the scripts:

Replace:

- `https://catalog.data.gov/api/3/action/package_search`
- `https://catalog.data.gov/api/3/action/package_show`

with:

- `https://api.gsa.gov/technology/datagov/v3/action/package_search`
- `https://api.gsa.gov/technology/datagov/v3/action/package_show`

If the specific script only uses `package_search`, you only need to switch that one.


### 4) Update the scripts with new headers and requests 

Somewhere after `import requests` add a minimal header dictionary to the script. Something like this should work:

```python
HEADERS = {
    "User-Agent": "MyScript/1.0",
    "x-api-key": os.environ.get("DATAGOV_API_KEY"),
}
```
replacing MyScript with the appropriate script name. 

Notes on the headers:
- `User-Agent` is strongly recommended for bulk API usage.
- If `DATAGOV_API_KEY` is not set, the value becomes `None` (which is fine if using the unauthenticated gateway.
- You can add additional headers here too, including your email if you want. These are documented in the [full CKAN API guide](https://docs.ckan.org/en/2.9/api/).

Find every API call that starts with:

```python
requests.get(...)
```

and pass the headers:

```python
requests.get(..., headers=HEADERS, ...)
```
