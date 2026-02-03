#!/usr/bin/env python3
"""
This script extracts a minimal inventory of datasets from from a Socrata /api/views JSON export 
 (i.e., from the WBM snapshot of such) and returns a csv with columns:
        Dataset Name, Agency Data Link, Metadata Created, Metadata Updated, Access Level.
  Note that the script is tuned around the elements in the (former) usaid data.usaid.gov/api/views
  api.

Usage:
  python apiviews2csv.py 
      --input /path/to/usaid-20250129060913-data.usaid.gov.json 
      --output usaid_api_views_inventory.csv
      
Last Modified: 2/3/2026
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional


NA = "NA"


def epoch_to_iso_utc(value: Any) -> str:
    """
    Convert epoch seconds to ISO-8601 UTC (e.g., 2025-01-29T06:11:24Z).
    Returns 'NA' if value is missing or not an int/float-like epoch.
    """
    if value is None:
        return NA
    try:
        # Socrata timestamps here appear as epoch seconds (ints).
        ts = float(value)
    except (TypeError, ValueError):
        return NA
    try:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return NA
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def first_url_from_access_points(metadata: Dict[str, Any]) -> Optional[str]:
    """
    metadata.accessPoints is sometimes a dict like {"Dataset": "https://..."}
    or {"URL": "https://..."}.
    Return the first string value found, else None.
    """
    access_points = metadata.get("accessPoints")
    if isinstance(access_points, dict):
        for _, v in access_points.items():
            if isinstance(v, str) and v.strip():
                return v.strip()
    return None


def safe_str(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return NA


def build_agency_data_link(item: Dict[str, Any]) -> str:
    """
    Preferred link order:
      1) item['permalink'] (if present)
      2) item['metadata']['accessPoints'] first URL
      3) fallback: https://{domainCName}/d/{id}  (if both exist)
      else 'NA'
    """
    permalink = item.get("permalink")
    if isinstance(permalink, str) and permalink.strip():
        return permalink.strip()

    md = item.get("metadata")
    if isinstance(md, dict):
        ap = first_url_from_access_points(md)
        if ap:
            return ap

    domain = item.get("domainCName")
    vid = item.get("id")
    if isinstance(domain, str) and domain.strip() and isinstance(vid, str) and vid.strip():
        # Socrata "short link" pattern used throughout this export (e.g., https://data.usaid.gov/d/<id>)
        return f"https://{domain.strip()}/d/{vid.strip()}"

    return NA


def pick_updated_epoch(item: Dict[str, Any]) -> Any:
    """
    Choose a best-effort "metadata updated" timestamp from common keys in this export.
    Preference:
      - viewLastModified
      - rowsUpdatedAt
      - updatedAt
    """
    for key in ("viewLastModified", "rowsUpdatedAt", "updatedAt"):
        if key in item:
            return item.get(key)
    return None

def proposed_access_level(item: dict) -> str:
    md = item.get("metadata")
    if not isinstance(md, dict):
        return NA

    cf = md.get("custom_fields")
    if not isinstance(cf, dict):
        return NA

    rua = cf.get("Risk Utility Assessment")
    if not isinstance(rua, dict):
        return NA

    pal = rua.get("Proposed Access Level")
    if isinstance(pal, str) and pal.strip():
        return pal.strip()

    return NA
    
def iter_items(data):
    if isinstance(data, list):
        for x in data:
            if isinstance(x, dict):
                yield x
        return

    if isinstance(data, dict):
        for key in ("results", "data", "items", "views"):
            maybe = data.get(key)
            if isinstance(maybe, list):
                for x in maybe:
                    if isinstance(x, dict):
                        yield x
                return

        # If it’s a dict-of-dicts (e.g., {id: {...}, id2: {...}})
        if all(isinstance(v, dict) for v in data.values()):
            for v in data.values():
                yield v
            return

    raise ValueError(
        f"Unrecognized JSON structure: top-level type={type(data).__name__}"
    )

def main() -> None:
    parser = argparse.ArgumentParser(description="Extract inventory CSV from a Socrata /api/views JSON export.")
    parser.add_argument("--input", required=True, help="Path to the /api/views JSON file.")
    parser.add_argument("--output", required=True, help="Path to write the output CSV.")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8", errors="replace") as f:
        data = json.load(f)

    # If the JSON is double-encoded (i.e., a JSON string containing JSON), unwrap it.
    if isinstance(data, str):
        data = json.loads(data)        

    rows = []
    for item in iter_items(data):
        name = safe_str(item.get("name"))
        link = build_agency_data_link(item)

        created_iso = epoch_to_iso_utc(item.get("createdAt"))
        updated_iso = epoch_to_iso_utc(pick_updated_epoch(item))
        access_level = proposed_access_level(item)

        rows.append({
            "Dataset Name": name,
            "Agency Data Link": link,
            "Metadata Created": created_iso,
            "Metadata Updated": updated_iso,
            "Proposed Access Level": access_level
        })

    # Write CSV with stable column order
    fieldnames = ["Dataset Name", "Agency Data Link", "Metadata Created", "Metadata Updated", "Proposed Access Level"]
    with open(args.output, "w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()