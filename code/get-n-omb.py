#!/usr/bin/env python3
"""
This script uses the OpenOMB API to estimate how many OMB apportionment files 
(as mirrored by OpenOMB) fall within a specified window.

Default window:
  - Administration start: 2025-01-21
  - OMB public database takedown: 2025-03-24

Example:
 python openomb.py --admin-start 2025-01-21 --takedown-date 2025-07-21 --count-only

Last updated: 3.1.2026
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import requests


OPENOMB_BASE = "https://openomb.org"
SEARCH_ENDPOINT = f"{OPENOMB_BASE}/api/v1/files/search"


@dataclass
class SearchResultPage:
    query: Dict[str, Any]
    paging: Dict[str, Any]
    results: List[Dict[str, Any]]


def _request_json(url: str, params: Dict[str, Any], timeout: int = 30, retries: int = 6) -> Dict[str, Any]:
    session = requests.Session()
    backoff = 1.0

    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, params=params, timeout=timeout)
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                sleep_s = float(retry_after) if retry_after and retry_after.isdigit() else backoff
                time.sleep(sleep_s)
                backoff = min(backoff * 2, 30)
                continue

            resp.raise_for_status()
            return resp.json()

        except requests.RequestException:
            if attempt == retries:
                raise
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)

    raise RuntimeError("Unreachable retry loop exit.")


def fetch_page(
    approved_start: str,
    approved_end: str,
    page: int,
    limit: int,
    sort: str = "approved_asc",
    extra_params: Optional[Dict[str, Any]] = None,
) -> SearchResultPage:
    params: Dict[str, Any] = {
        "approvedStart": approved_start,
        "approvedEnd": approved_end,
        "page": page,
        "limit": limit,
        "sort": sort,
    }
    if extra_params:
        params.update(extra_params)

    data = _request_json(SEARCH_ENDPOINT, params=params)
    return SearchResultPage(
        query=data.get("query", {}),
        paging=data.get("paging", {}),
        results=data.get("results", []) or [],
    )


def iter_all_results(
    approved_start: str,
    approved_end: str,
    limit: int = 1000,
    sort: str = "approved_asc",
    extra_params: Optional[Dict[str, Any]] = None,
    verbose: bool = False,
) -> Iterable[Dict[str, Any]]:
    first = fetch_page(approved_start, approved_end, page=1, limit=limit, sort=sort, extra_params=extra_params)
    total_count = int(first.paging.get("count", 0))
    page_size = int(first.paging.get("size", limit)) or limit
    total_pages = int(first.paging.get("pages", math.ceil(total_count / max(page_size, 1)) or 1))

    if verbose:
        print(f"[info] total_count={total_count} page_size={page_size} total_pages={total_pages}", file=sys.stderr)

    for item in first.results:
        yield item

    for p in range(2, total_pages + 1):
        page_obj = fetch_page(approved_start, approved_end, page=p, limit=limit, sort=sort, extra_params=extra_params)
        for item in page_obj.results:
            yield item


def get_total_count_only(
    approved_start: str,
    approved_end: str,
    extra_params: Optional[Dict[str, Any]] = None,
) -> int:
    page1 = fetch_page(approved_start, approved_end, page=1, limit=1, sort="approved_asc", extra_params=extra_params)
    return int(page1.paging.get("count", 0))


def summarize_by_key(items: Iterable[Dict[str, Any]], key: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for it in items:
        val = it.get(key) or "UNKNOWN"
        out[str(val)] = out.get(str(val), 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


def write_csv(items: List[Dict[str, Any]], path: str) -> None:
    fieldnames = [
        "fileId",
        "title",
        "approved",
        "fiscalYear",
        "folder",
        "agency",
        "bureau",
        "account",
        "apportionmentType",
        "lineNum",
        "url",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for it in items:
            fid = it.get("fileId") or it.get("id")
            w.writerow(
                {
                    "fileId": fid,
                    "title": it.get("title"),
                    "approved": it.get("approved") or it.get("approvedDate"),
                    "fiscalYear": it.get("fiscalYear"),
                    "folder": it.get("folder"),
                    "agency": it.get("agency"),
                    "bureau": it.get("bureau"),
                    "account": it.get("account"),
                    "apportionmentType": it.get("apportionmentType"),
                    "lineNum": it.get("lineNum"),
                    "url": f"{OPENOMB_BASE}/file/{fid}" if fid else "",
                }
            )


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Estimate OpenOMB apportionment file counts for an approval-date window (e.g., this administration through takedown)."
    )
    ap.add_argument("--admin-start", default="2025-01-21", help="Start date (YYYY-MM-DD). Default: 2025-01-21")
    ap.add_argument("--takedown-date", default="2025-03-24", help="End date (YYYY-MM-DD). Default: 2025-03-24")
    ap.add_argument("--limit", type=int, default=1000, help="API page size. Default: 1000")
    ap.add_argument("--count-only", action="store_true", help="Only fetch paging.count (1 call). No breakdowns.")
    ap.add_argument(
        "--by",
        choices=["agency", "folder", "fiscalYear", "bureau", "account", "apportionmentType"],
        default=None,
        help="Optional breakdown key (requires paging through all results).",
    )
    ap.add_argument("--csv", default=None, help="Optional path to write a CSV of all results in the window.")
    ap.add_argument("--verbose", action="store_true", help="Verbose progress to stderr.")
    return ap.parse_args()


def main() -> int:
    args = parse_args()

    start = args.admin_start
    end = args.takedown_date

    total = get_total_count_only(start, end)
    print(f"OpenOMB files approved between {start} and {end}: {total}")

    if args.count_only and not args.by and not args.csv:
        return 0

    items: List[Dict[str, Any]] = []
    for it in iter_all_results(start, end, limit=args.limit, verbose=args.verbose):
        items.append(it)

    if len(items) != total:
        print(f"[warn] paging returned {len(items)} items but paging.count said {total}.", file=sys.stderr)

    if args.by:
        grouped = summarize_by_key(items, args.by)
        print(f"\nBreakdown by {args.by}:")
        for k, v in grouped.items():
            print(f"{v:6d}  {k}")

    if args.csv:
        write_csv(items, args.csv)
        print(f"\nWrote CSV: {args.csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())