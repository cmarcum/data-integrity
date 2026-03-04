---
title: Auditing Open Government Data Assets
nav_order: 70
---

This chapter outlines a reproducible, step-by-step process for auditing metadata and dataset changes of an agency's Data.gov harvest source and/or its comprehensive data inventory and individual data files. The process makes use of several external resources, especially the Internet Archive's [WaybackMachine](https://web.archive.org/) (WBM) to (re)establish historical baselines should they not exist. The workflow relies on a set of convenience functions written in python that provides an audit package for federal open government data (mainly, datagov-audit.py and the pra-icr-tools package).

The entire workflow is described by the diagram, which outlines a robust, time-series monitoring system designed to track changes to federal open government data. It begins by establishing a baseline, referred to as T0, and comparing it against subsequent monitoring runs, or Tn, to detect content drift, link rot, metadata alterations, and availability issues. The workflow pulls metadata references from both Data.gov and the specific agency's inventory and optionally from the WBM. Nodes in the diagram prefixed with "CLI" (short for command-line interface) indicate specific helper functions provided by datagov-audit.py; for example, the workflow's list-harvest node is executed by the list-harvest CLI to enumerate active Data.gov streams. Similarly, the snapshot-org node utilizes the snapshot-org CLI to capture the raw Data.gov catalog representation, while the fetch-datajson node relies on the fetch-datajson CLI to download the agency's live DCAT-US file.

![icr discontinuations](/assets/images/mermaid_datagov_diff.png "Workflow for Auditing Open Government Data Assets and Information Collections"){:.img-medium .img-center}

When monitoring specific data distributions, such as CSV or JSON files, the workflow leverages the WBM to capture historical snapshots of the dataset's state. To determine if data available for download from an agency at a specific moment in time has drifted from this archived version, the compare-wayback node provides comparative statistics and information. Based on the file type detected, this step automatically evaluates the data to mathematically prove modifications using file size, SHA-256 hashes, and other structural differences.

At the core of this monitoring system is the Diff Engine node, which is responsible for comparing the T0 baseline against the Tn run to quantify  changes. For comparing Data.gov CKAN metadata over time, the workflow maps to the script's diff CLI. Conversely, diffing the agency's internal data.json files over time is handled by the diff-inventory CLI. The generation of human-readable dataset dossiers and change logs from these comparisons is managed by the inspect-diff CLI, which iterates through the diff engine's output to reveal exact, field-level modifications.

Alongside the time-series Diff Engine, the workflow includes a parallel synchronization analysis using the newly integrated cross-check CLI. Rather than comparing historical baselines, this step compares two files from the exact same monitoring run (Tn): the agency's live data.json and Data.gov's live CKAN snapshot. By extracting and matching identifiers across the two different schemas, the cross-check CLI generates an "Ingestion Gap Report". This report feeds directly into the final outputs, revealing datasets the agency published but Data.gov failed to harvest, as well as stale "ghost" records lingering on Data.gov that the agency has already removed (such as was the case for several months with more than 2000 datasets previously provided by the [United States Agency for International Development](../02-usaid/)).

In addition to direct catalog monitoring of open government data assets, the workflow incorporates an Information Collection Request (ICR) subroutine. This component acts as a fallback when the underlying datasets associated with federal collections are not properly indexed or published within an agency's data inventory. To monitor these changes independently of the agency catalogs, the workflow utilizes external resources like [dataindex.us](https://www.dataindex.us) and the [pra-icr-tools](https://github.com/cmarcum/pra-icr-tools) package. By pulling Paperwork Reduction Act (PRA) XML reports, CSV exports, and collection documents, this subroutine normalizes and stores ICR tables during each monitoring run. It then maps these collections back to specific datasets using metadata keywords, documentation, or OMB Control Numbers (keeping in mind that newly submitted ICRs do not yet have an assigned OMB control number).

# EPA ScienceHub Data.gov Inventory Audit Workflow Example
To illustrate the workflow in action, consider the Environmental Protection Agency's (EPA) ScienceHub, which supplies a data inventory .json file that is used by Data.gov as a harvest source. ScienceHub is the agency’s central catalog for research datasets, models, code, and other scientific products generated across its laboratories. It was built to make EPA science easier to find, reuse, and evaluate, drawing heavily on the work historically produced by the Office of Research and Development (ORD), which was the program that coordinated EPA’s research programs, maintained specialized labs, and ensured scientific rigor across environmental and public‑health studies.

That foundation was disrupted when the Trump administration eliminated ORD in 2025, replacing it with a new structure and reducing the agency’s independent research capacity. Because ScienceHub depends on the continuity of EPA’s scientific programs, the loss of ORD introduced uncertainty about future dataset production, long‑term monitoring, and the stewardship of existing scientific resources, making it a good candidate for this exercise. 

---

## Step 0: Establish Baseline and Current Dates

Before pulling data, decide what you are comparing today's data against (e.g., January 1, 2025 vs. Today).

| Condition | Action | Next Step in Workflow |
| :--- | :--- | :--- |
| **Local Baseline Exists** | You already saved a `metadata.json` file from the agency at a previous date. | Skip to **Step 5** (use your local file as the old input). |
| **No Local Baseline** | You do not have historical files saved. | Proceed to **Step 1**, then extract a snapshot from the Internet Archive in Step 4. |

For completeness, this workflow assumes no local baseline files exist.

---

## Step 1: Capture Current List of All Harvest Sources

Download a master list of everything Data.gov is currently configured to harvest to get a landscape view of active sources.

```bash
python datagov-audit.py list-harvest --out harvest_sources.json
```
The first few lines of the output of this command saved in harvest_sources.json will look similar to this:
```bash
head harvest_sources.json -n 9
[
  {

    "id": "cc7df4cc-8036-4868-b422-5823c63957d7",
    "title": "Exim Data.json",
    "source_url": "https://img.exim.gov/s3fs-public/dataset/vbhv-d8am/data.json",
    "frequency": "WEEKLY",
    "source_type": "datajson"
  },

```

This file is useful for other purposes as well, as it can be used to monitor the changes to the Data.gov harvest sources.

---

## Step 2: Confirm the Source Exists

Search the master list you just downloaded to verify the EPA Pasteur metadata source is present and active on Data.gov. While this can be done using regular expressions, the datagov audit package provides a convenience function for this purpose with fuzzy-matching: 

```bash
python datagov-audit.py find-datajson harvest_sources.json pasteur.epa.gov
```
Which find the harvest source for epa's ScienceHub and reports the entry to the terminal:

```bash
[
  {
    "id": "04b59eaf-ae53-4066-93db-80f2ed0df446",
    "title": "EPA ScienceHub",
    "source_url": "https://pasteur.epa.gov/metadata.json",
    "frequency": "DAILY",
    "source_type": "datajson"
  }
]
```
---

## Step 3: Grab Live Version of Harvest Source Data Inventory

Download and validate the current, live metadata inventory directly from the EPA. The datagov audit scripts provide a convience function for wrapping the CURL call to download the file from the agency website. This serves as the 'current' or 'new' file for comparison.

```bash
python datagov-audit.py fetch-datajson https://pasteur.epa.gov/metadata.json --out epa-pasteur-metadata.json
```

---

## Step 4A: Find the Baseline Wayback Capture

Use the Internet Archive's WaybackMachine CDX query tool to list captures from a specific target date (e.g., 01/01/2025) to capture a snapshot with a timestamp closest to your baseline date for comparison to the live version.

```bash
python datagov-audit.py wayback-cdx https://pasteur.epa.gov/metadata.json --from-ts 20250101 --fetch 
```

The output will print options closest to the specified timestamp which can be used to locate the exact timestamp from the output (e.g., `20250105123000`) for the next step.

---

## Step 4B: Grab and Clean the Baseline Wayback Snapshot

Using the timestamp found in 4A, download the raw JSON from the Wayback Machine (using the `id_` modifier) and clean it to strip out any Wayback-injected HTML or URL rewriting. 

```bash
python datagov-audit.py clean-wayback "https://web.archive.org/web/20250105123000id_/https://pasteur.epa.gov/metadata.json" --out pasteur-wbm-20250105-metadata.json
```

Because WBM adds relay prefixes to URLs found in its snapshots that forward to other snapshots, this script automatically cleans them up so that comparisons with non-WBM snapshot equivalent files can be made. 

---

## Step 5: Compare WBM Baseline File to Current File

The datagov-audit script contains a useful differencing engine that can be used to compare the cleaned baseline against today's live inventory. This generates a machine-readable JSON report of all added, removed, and modified datasets.

```bash
python datagov-audit.py diff-inventory pasteur-wbm-20250105-metadata.json epa-pasteur-metadata.json --out pasteur-compare-diff.json
```

In addition to a machine-readable json list of added, removed, and modified datasets, the function prints a high-level summary to the termina:

```bash
{
  "removed": 0,
  "added": 800,
  "modified": 29,
  "old_total": 3457,
  "new_total": 4257,
  "old_indexed": 3457,
  "new_indexed": 4257
}
```

---

## Step 6: See Which Dataset Metadata Entries Were Modified

Convert the machine-readable JSON report into a human-readable text file that shows exactly which fields changed (e.g., description updates, modified dates, new contact emails) for every modified record.

```bash
python datagov-audit.py inspect-diff --report pasteur-compare-diff.json --out pasteur-changes.txt
```

In this case, inspecting the report reveals that the 29 modified metadata elements were mostly changed to update versions of files, new downloadURLs, or to remove the "Office of Research and Development" as the publishing office. 

---

## Step 7: Evaluate Modification of a Specific Downloadable Dataset

Often, metadata changes alone are insufficient to reveal whether underlying data were also modified. The datagov-audit scripts can also do rough checks of whether the actual downloadable files (i.e., .zip, .csv, .json) were also modified since the baseline date (assuming that the WBM actually captured the file around that time). The script mathematically evaluates differences in the files using hashing (specifically, by using the SHA-256 algorithm to create a digital fingerprint of the files to compare). 

As an example, we grab one of the files where the metadata had been modified. In this case, it's the file associated with advanced septic systems pilot data: [https://catalog.data.gov/dataset/performance-data-for-enhanced-innovative-alternative-i-a-septic-systems-for-nitrogen-remov](https://doi.org/10.23719/1529539).

```bash
python datagov-audit.py compare-wayback "https://pasteur.epa.gov/uploads/10.23719/1529539/V1%20data%20release.zip" --from-ts 20250101 --out dataset-diff.json
```

In this specific case, the underlying data have not been modified and the output clearly shows no changes in either the file sizes or the underlying structure per the hashing routine:

```bash
{
  "ok": true,
  "target_url": "https://pasteur.epa.gov/uploads/10.23719/1529539/V1%20data%20release.zip",
  "format": "bytes",
  "live": {
    "final_url": "https://pasteur.epa.gov/uploads/10.23719/1529539/V1%20data%20release.zip",
    "content_type": "application/zip",
    "bytes": 873201,
    "sha256": "d9772818ebeede03f4e099e5d3d6b47dcf3266640f9df369f2f36fb580b7c6e2"
  },
  "wayback": {
    "capture": {
      "timestamp": "20240621201154",
      "original": "https://pasteur.epa.gov/uploads/10.23719/1529539/V1%20data%20release.zip",
      "statuscode": "200",
      "mimetype": "application/zip",
      "digest": "BA7N5KHZEYODCVGQBLSP2P43QS5BADTV",
      "length": "838168"
    },
    "replay_url_raw": "https://web.archive.org/web/20240621201154id_/https://pasteur.epa.gov/uploads/10.23719/1529539/V1%20data%20release.zip",
    "bytes": 873201,
    "sha256": "d9772818ebeede03f4e099e5d3d6b47dcf3266640f9df369f2f36fb580b7c6e2"
  },
  "match": {
    "sha256_equal": true,
    "bytes_equal": true
  }
}
```

This routine could easily be extended to recursively iterate over a set of datasets. Of course, diligence to assess the fidelity of all federal data assets by a single entity would be infeasible but stakeholders with special interests in specific datasets could be done with some regularity. 

---

## Step 8: Verify Data.gov Ingestion

Finally, verify that Data.gov's harvester has successfully ingested the agency's updates into the public catalog. 

```bash
python datagov-audit.py snapshot-source "04b59eaf-ae53-4066-93db-80f2ed0df446" --out datagov-pasteur-snapshot.json
```

Running this function periodically will provide a mechanism to establish new baselines directly from what Data.gov injests and uses in the Federal Data Catalog. Two such instances can be compared using the `diff` command, or they can be to ensure Data.gov stays in sync with the EPA's live file. 

Two such snapshots can also be compared using the diff-inventory and inspect-diff functions, but with minor argument changes to ensure the json field mappings are comparable:

```bash
python datagov-audit.py diff-inventory datagov-old-snapshot.json datagov-new-snapshot.json --dataset-key packages --id-field id --out ckan-diff.json

python datagov-audit.py inspect-diff --report ckan-diff.json --id-field id --out ckan-changes.txt
```

## Step 9: Compare Federal Data Catalog with Agency Inventory

```bash
python datagov-audit.py cross-check epa-pasteur-metadata.json datagov-pasteur-snapshot.json --out cross-check-report.json
{
  "agency_total": 4257,
  "ckan_total": 4258,
  "missing_from_datagov": 0,
  "extra_on_datagov": 1,
  "common": 4257
}
```

In this case, one dataset appears in the FDC that is not in the agency inventory, and that's because there was a one-day difference between the time the two files were downloaded (with the Data.gov version being more recent). That dataset was added on 3/2/2026: [Assessing Flooding from Changes in Extreme Rainfall: Using the Design Rainfall Approach in Hydrologic Modeling](https://doi.org/10.23719/1532191).

# Conclusion
This chapter provided a replicable workflow for auditing and evaluating the integrity of federal data, using the EPA's ScienceHub repository as a practical example. By combining historical baselines from the Wayback Machinea and contemporary and historical snapshots of agency files, with the automated comparative routines, independent monitors can effectively track data disruptions, detect silent metadata alterations, and verify catalog synchronization. The audit routine can be adapted for dataset-specific, agency-wide, or system-wide monitoring.  While this specific example focused on the EPA, these methods are highly generalizable. The cross-schema checks, diffing engines, and hashing routines should operate seamlessly on almost any JSON-based inventory.