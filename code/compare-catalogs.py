'''
This script takes takes two snapshots of comprehensive data inventories (CDI) from a US
 Federal agency and compares them to return A \ B. Set A is presumed to be the snapshot at time 1 and set B at time 2. The script outputs the difference, giving the datasets that were removed from the CDI at time 2. Obviously, if the order of the sets is changed at input, the output provides a list of newly added datasets by time 2.

From the command line, this can be run with:
 $ python compare-catalogs.py A.json B.json

Last Modified: 1/23/2026
'''
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any, Dict, Iterable, List, Optional


def load_json(path: str) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise SystemExit(f"ERROR: File not found: {path}")
    except json.JSONDecodeError as e:
        raise SystemExit(f"ERROR: Invalid JSON in {path}: {e}")


def extract_dataset_list(obj: Any) -> List[Dict[str, Any]]:
    """
    Return the list of dataset dicts from a POD-style JSON object.
    Supports:
      - {"dataset": [ ... ]}
      - [ ... ] (list of dataset dicts)
      - fallback: recursive search for a key named "dataset" containing a list
    """
    # Common case: top-level dict with "dataset" list
    if isinstance(obj, dict) and isinstance(obj.get("dataset"), list):
        return [d for d in obj["dataset"] if isinstance(d, dict)]

    # Sometimes the file itself may just be a list of dataset dicts
    if isinstance(obj, list):
        ds = [d for d in obj if isinstance(d, dict)]
        # Heuristic: treat it as dataset list if entries look like datasets
        if ds and any("title" in d for d in ds[:10]):
            return ds

    # Fallback: search recursively for the first plausible "dataset" list
    stack: List[Any] = [obj]
    while stack:
        cur = stack.pop()

        if isinstance(cur, dict):
            for k, v in cur.items():
                if k == "dataset" and isinstance(v, list):
                    ds = [d for d in v if isinstance(d, dict)]
                    if ds and any("title" in d for d in ds[:10]):
                        return ds
                if isinstance(v, (dict, list)):
                    stack.append(v)

        elif isinstance(cur, list):
            for item in cur:
                if isinstance(item, (dict, list)):
                    stack.append(item)

    raise SystemExit("ERROR: Could not find a dataset list (key 'dataset') in the JSON.")


def normalize_title(title: str) -> str:
    """
    Normalize titles to reduce trivial mismatches:
    - trim
    - collapse internal whitespace
    - casefold (stronger than lower() for unicode)
    """
    collapsed = re.sub(r"\s+", " ", title.strip())
    return collapsed.casefold()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print dataset titles in file A that do not appear in file B."
    )
    parser.add_argument("file_a", help="Path to metadata JSON file A (baseline)")
    parser.add_argument("file_b", help="Path to metadata JSON file B (comparison)")

    parser.add_argument(
        "--no-normalize",
        dest="normalize",
        action="store_false",
        help="Disable normalization (compare titles exactly, case/whitespace sensitive).",
    )
    parser.set_defaults(normalize=True)

    parser.add_argument(
        "--allow-duplicates",
        action="store_true",
        help="Print missing titles even if the same missing title appears multiple times in file A.",
    )

    args = parser.parse_args()

    obj_a = load_json(args.file_a)
    obj_b = load_json(args.file_b)

    datasets_a = extract_dataset_list(obj_a)
    datasets_b = extract_dataset_list(obj_b)

    # Build a set of titles from B for membership testing
    if args.normalize:
        titles_b = {normalize_title(d.get("title", "")) for d in datasets_b if d.get("title")}
    else:
        titles_b = {d.get("title", "") for d in datasets_b if d.get("title")}

    printed = set()

    for d in datasets_a:
        title = d.get("title")
        if not isinstance(title, str) or not title.strip():
            continue

        key = normalize_title(title) if args.normalize else title

        if key not in titles_b:
            if (not args.allow_duplicates) and (key in printed):
                continue
            printed.add(key)
            print(title.strip())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())