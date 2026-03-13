#!/usr/bin/env python3
"""
datagov_inventory_audit.py

A practical, reproducible workflow helper for:
- Enumerating Data.gov harvest sources (CKAN harvest packages)
- Finding and fetching an agency data.json (DCAT-US inventory)
- Validating basic structure of data.json
- Snapshotting Data.gov catalog metadata for an org
- Diffing snapshots (added/removed/modified)
- Generating + optionally querying Internet Archive Wayback CDX evidence for URLs
- Comparing live downloadable dataset URLs vs the latest Wayback capture (hash + lightweight CSV/JSON checks)

Data.gov CKAN API notes:
- Data.gov recommends using package_search (package_list is disabled). See user guide.
- If you get 403s on catalog.data.gov directly, use the api.gsa.gov gateway.
  (Requires api.data.gov key or DEMO_KEY; can also be passed as x-api-key header.)

Wayback notes:
- CDX API is used to list captures.
- Replay URL pattern: https://web.archive.org/web/{timestamp}id_/{original_url}
  The 'id_' modifier helps retrieve raw content with minimal rewriting.
"""

from __future__ import annotations
import argparse
import requests
import datetime as dt
import hashlib
import json
import re
import os
import sys
import textwrap
import csv
import io
from typing import Any, Dict, List, Optional, Tuple, Callable, Iterable, Set
from urllib.parse import urlencode

DEFAULT_CKAN_BASE = "https://api.gsa.gov/technology/datagov/v3/action"
DEFAULT_API_KEY_ENV = "DATAGOV_API_KEY"
DEFAULT_USER_AGENT = "datagov-inventory-audit/1.2 (research; contact: none)"

def die(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)

def read_api_key(env_var: str = DEFAULT_API_KEY_ENV) -> str:
    return os.getenv(env_var, "DEMO_KEY")

def make_session(api_key: str, user_agent: str = DEFAULT_USER_AGENT) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": user_agent,
        "x-api-key": api_key,
        "Accept": "application/json",
    })
    return s

def ckan_action(session: requests.Session, base: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{base.rstrip('/')}/{action}"
    params = dict(params or {})
    params.setdefault("api_key", session.headers.get("x-api-key", "DEMO_KEY"))
    r = session.get(url, params=params, timeout=60)
    r.raise_for_status()
    payload = r.json()
    if not payload.get("success", False):
        die(f"CKAN action failed: {payload}")
    return payload["result"]

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def now_utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

def write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_identifier(item: Dict[str, Any]) -> str:
    for k in ("identifier", "landingPage", "title"):
        v = item.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""

def coerce_list(v: Any) -> List[Any]:
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]

def basic_validate_datajson(doc: Dict[str, Any]) -> Tuple[bool, List[str], int]:
    msgs: List[str] = []
    ok = True
    if not isinstance(doc, dict):
        return False, ["Root is not a JSON object."], 0
    datasets = doc.get("dataset")
    if not isinstance(datasets, list):
        ok = False
        msgs.append("Missing or invalid 'dataset' list.")
        return ok, msgs, 0
    missing_id = 0
    for i, d in enumerate(datasets):
        if not isinstance(d, dict):
            ok = False
            msgs.append(f"dataset[{i}] is not an object.")
            continue
        if not normalize_identifier(d):
            missing_id += 1
    if missing_id:
        msgs.append(f"{missing_id} dataset entries lacked identifier/title/landingPage (diff may be less reliable).")
    msgs.append(f"Found {len(datasets)} dataset entries.")
    return ok, msgs, len(datasets)

def wayback_cdx_url(target_url: str, limit: int = 2000, from_ts: Optional[str] = None) -> str:
    base = "https://web.archive.org/cdx/search/cdx"
    params = {
        "url": target_url,
        "output": "json",
        "fl": "timestamp,original,statuscode,mimetype,digest,length",
        "filter": "statuscode:200",
        "collapse": "digest",
        "limit": str(limit),
    }
    if from_ts:
        params["from"] = from_ts
    return f"{base}?{urlencode(params)}"

def is_url(s: str) -> bool:
    return isinstance(s, str) and (s.startswith("http://") or s.startswith("https://"))

# ----------------------------
# Harvest sources (robust)
# ----------------------------

def list_harvest_sources(session: requests.Session, base_url: str, rows: int = 1000) -> List[Dict[str, Any]]:
    start = 0
    unique_sources = {}
    
    while True:
        params = {
            "fq": "dataset_type:harvest",
            "rows": rows,
            "start": start
        }
        
        try:
            result = ckan_action(session, base_url, "package_search", params)
            results = result.get("results", [])
            
            if not results:
                break
                
            for source in results:
                url = source.get("url")
                harvest_id = source.get("id")          
                slug = source.get("name")              
                
                if url:
                    clean_url = url.strip()
                    
                    if clean_url not in unique_sources:
                        unique_sources[clean_url] = {
                            "id": harvest_id,         
                            "slug": slug,
                            "url": clean_url,
                            "title": source.get("title"),
                            "frequency": source.get("frequency"),
                            "source_type": source.get("source_type"),
                            "organization": (
                                source.get("organization", {}).get("name")
                                if isinstance(source.get("organization"), dict)
                                else None
                            ),
                        }
            
            start += rows
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed at offset {start}: {e}", file=sys.stderr)
            break
            
    return list(unique_sources.values())

def find_harvest_sources_by_text(sources: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    query_lower = query.lower()
    hits = []
    for s in sources:
        text_blob = f"{s.get('title', '')} {s.get('name', '')} {s.get('notes', '')} {s.get('url', '')}".lower()
        if query_lower in text_blob:
            hits.append(s)
    return hits

def fetch_url_bytes(session: requests.Session, url: str) -> Tuple[bytes, Dict[str, Any]]:
    r = session.get(url, timeout=60, allow_redirects=True)
    r.raise_for_status()
    return r.content, {
        "status_code": r.status_code,
        "content_type": r.headers.get("Content-Type"),
        "final_url": r.url,
    }

def fetch_json_any(session: requests.Session, url: str) -> Any:
    """
    Fetch JSON from a URL. Allows the JSON root to be either an object or a list. 
    If it's a list, we wrap it in {"items": ...} so the rest of the code can treat it uniformly.
    """
    b, meta = fetch_url_bytes(session, url)
    try:
        obj = json.loads(b.decode("utf-8"))
    except UnicodeDecodeError:
        obj = json.loads(b.decode("utf-8-sig"))

    fetch_meta = {
        "fetched_at": now_utc_iso(),
        "source_url": url,
        "final_url": meta.get("final_url"),
        "content_type": meta.get("content_type"),
        "sha256": sha256_bytes(b),
        "bytes": len(b),
    }

    if isinstance(obj, dict):
        obj["_fetch_meta"] = fetch_meta
        return obj
    # Wrap non-dict JSON (e.g., a list feed)
    return {"items": obj, "_fetch_meta": fetch_meta}

def fetch_datajson(session: requests.Session, url: str) -> Dict[str, Any]:
    doc = fetch_json_any(session, url)
    if not isinstance(doc, dict):
        die("data.json did not parse to a JSON object.")
    return doc

def snapshot_catalog_org(session: requests.Session, base: str, org: str, rows_per_page: int = 1000) -> Dict[str, Any]:
    start = 0
    all_results: List[Dict[str, Any]] = []
    while True:
        res = ckan_action(session, base, "package_search", {
            "q": "*:*",
            "fq": f"organization:{org}",
            "rows": rows_per_page,
            "start": start,
        })
        batch = res.get("results", [])
        all_results.extend(batch)
        if start + rows_per_page >= res.get("count", 0):
            break
        start += rows_per_page
    return {
        "snapshot_meta": {"fetched_at": now_utc_iso(), "ckan_base": base, "organization": org, "count": len(all_results)},
        "packages": all_results,
    }

def index_by_key(items: List[Dict[str, Any]], key: str) -> Dict[str, Dict[str, Any]]:
    out = {}
    for it in items:
        v = it.get(key)
        if isinstance(v, str) and v:
            out[v] = it
    return out

def diff_snapshots(old: Dict[str, Any], new: Dict[str, Any], key: str = "id") -> Dict[str, Any]:
    old_pkgs = old.get("packages", [])
    new_pkgs = new.get("packages", [])
    old_map = index_by_key(old_pkgs, key)
    new_map = index_by_key(new_pkgs, key)
    old_keys = set(old_map.keys())
    new_keys = set(new_map.keys())
    added = sorted(list(new_keys - old_keys))
    removed = sorted(list(old_keys - new_keys))
    common = sorted(list(old_keys & new_keys))
    changed: List[Dict[str, Any]] = []
    fields = ["name", "title", "notes", "metadata_modified", "state"]
    for k in common:
        o = old_map[k]
        n = new_map[k]
        o_sig = {f: o.get(f) for f in fields}
        n_sig = {f: n.get(f) for f in fields}
        o_sig["resources_n"] = len(coerce_list(o.get("resources")))
        n_sig["resources_n"] = len(coerce_list(n.get("resources")))
        if o_sig != n_sig:
            changed.append({key: k, "old": o_sig, "new": n_sig})
    return {
        "diff_meta": {"key": key, "old_fetched_at": old.get("snapshot_meta", {}).get("fetched_at"), "new_fetched_at": new.get("snapshot_meta", {}).get("fetched_at")},
        "added": added,
        "removed": removed,
        "modified": changed,
        "counts": {"added": len(added), "removed": len(removed), "modified": len(changed), "old_total": len(old_pkgs), "new_total": len(new_pkgs)},
    }

def best_wayback_capture(session: requests.Session, target_url: str, from_ts: Optional[str] = None) -> Optional[Dict[str, Any]]:
    cdx = wayback_cdx_url(target_url, limit=50, from_ts=from_ts)
    r = session.get(cdx, timeout=60)
    r.raise_for_status()
    data = r.json()
    if not data or len(data) < 2:
        return None
    header = data[0]
    rows = data[1:]
    row = rows[-1]
    return dict(zip(header, row))

def wayback_replay_url(timestamp: str, original_url: str, raw: bool = True) -> str:
    stamp = f"{timestamp}id_" if raw else timestamp
    return f"https://web.archive.org/web/{stamp}/{original_url}"

def sniff_format(url: str, content_type: Optional[str]) -> str:
    u = (url or "").lower()
    ct = (content_type or "").lower()
    if "text/csv" in ct or u.endswith(".csv"):
        return "csv"
    if "application/json" in ct or u.endswith(".json") or u.endswith(".geojson"):
        return "json"
    return "bytes"

def compare_csv_bytes(old_b: bytes, new_b: bytes, max_rows: int = 2000) -> Dict[str, Any]:
    def parse(b: bytes) -> List[List[str]]:
        txt = b.decode("utf-8", errors="replace")
        f = io.StringIO(txt)
        reader = csv.reader(f)
        rows = []
        for i, row in enumerate(reader):
            rows.append([c.strip() for c in row])
            if i + 1 >= max_rows:
                break
        return rows
    o = parse(old_b)
    n = parse(new_b)
    o_header = o[0] if o else []
    n_header = n[0] if n else []
    def norm_hash(rows: List[List[str]]) -> str:
        m = hashlib.sha256()
        for row in rows:
            m.update(("\x1f".join(row) + "\n").encode("utf-8"))
        return m.hexdigest()
    return {"csv": {"old_rows_sampled": len(o), "new_rows_sampled": len(n), "old_cols_header": len(o_header), "new_cols_header": len(n_header),
                    "header_equal": o_header == n_header, "old_sample_sha256": norm_hash(o), "new_sample_sha256": norm_hash(n)}}

# ----------------------------
# Wayback JSON cleaning (strip replay prefix injected into URLs)
# ----------------------------

def extract_wayback_prefix_token(wayback_url: str) -> Optional[str]:
    if not isinstance(wayback_url, str):
        return None
    m = re.match(r"^https?://web\.archive\.org/web/([^/]+)/", wayback_url.strip(), re.IGNORECASE)
    return m.group(1) if m else None

def load_json_input(session: requests.Session, s: str) -> Any:
    if is_url(s):
        return fetch_json_any(session, s)
    return read_json(s)

def load_inventory_input(session: requests.Session, s: str) -> Any:
    return load_json_input(session, s)

def clean_wayback_json_prefix(doc: Any, wayback_token: str) -> Tuple[Any, int]:
    if not wayback_token or not isinstance(wayback_token, str):
        die("clean-wayback: wayback_token must be a non-empty string")
    rx = re.compile(rf"https?://web\.archive\.org/web/{re.escape(wayback_token)}/", re.IGNORECASE)

    n = 0

    def rec(x: Any) -> Any:
        nonlocal n
        if isinstance(x, dict):
            return {k: rec(v) for k, v in x.items()}
        if isinstance(x, list):
            return [rec(v) for v in x]
        if isinstance(x, str):
            y, c = rx.subn("", x)
            n += c
            return y
        return x

    return rec(doc), n

def compare_json_bytes(old_b: bytes, new_b: bytes) -> Dict[str, Any]:
    def load(b: bytes) -> Any:
        try:
            return json.loads(b.decode("utf-8"))
        except UnicodeDecodeError:
            return json.loads(b.decode("utf-8-sig"))
    o = load(old_b); n = load(new_b)
    def canonical_hash(x: Any) -> str:
        s = json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(s.encode("utf-8")).hexdigest()
    out: Dict[str, Any] = {"json": {"old_type": type(o).__name__, "new_type": type(n).__name__, "same_type": type(o) == type(n)}}
    if isinstance(o, dict) and isinstance(n, dict):
        ok = set(o.keys()); nk = set(n.keys())
        out["json"].update({"old_top_keys_n": len(ok), "new_top_keys_n": len(nk),
                            "top_keys_added": sorted(list(nk - ok))[:200],
                            "top_keys_removed": sorted(list(ok - nk))[:200],
                            "old_canonical_sha256": canonical_hash(o),
                            "new_canonical_sha256": canonical_hash(n)})
    elif isinstance(o, list) and isinstance(n, list):
        out["json"].update({"old_length": len(o), "new_length": len(n),
                            "old_canonical_sha256": canonical_hash(o[:1000]),
                            "new_canonical_sha256": canonical_hash(n[:1000])})
    else:
        out["json"].update({"old_canonical_sha256": canonical_hash(o), "new_canonical_sha256": canonical_hash(n)})
    return out

def compare_live_vs_wayback(session: requests.Session, url: str, from_ts: Optional[str] = None) -> Dict[str, Any]:
    live_b, live_meta = fetch_url_bytes(session, url)
    live_sha = sha256_bytes(live_b)
    cap = best_wayback_capture(session, url, from_ts=from_ts)
    if not cap:
        return {"ok": False, "reason": "No successful Wayback capture found via CDX.", "target_url": url,
                "live": {"final_url": live_meta.get("final_url"), "content_type": live_meta.get("content_type"), "bytes": len(live_b), "sha256": live_sha},
                "wayback": None}
    ts = cap.get("timestamp")
    replay = wayback_replay_url(ts, url, raw=True)
    wb_r = session.get(replay, timeout=60, allow_redirects=True)
    wb_r.raise_for_status()
    wb_b = wb_r.content
    wb_sha = sha256_bytes(wb_b)
    fmt = sniff_format(url, live_meta.get("content_type"))
    extra: Dict[str, Any] = {}
    if fmt == "csv":
        extra = compare_csv_bytes(wb_b, live_b)
    elif fmt == "json":
        extra = compare_json_bytes(wb_b, live_b)
    return {"ok": True, "target_url": url, "format": fmt,
            "live": {"final_url": live_meta.get("final_url"), "content_type": live_meta.get("content_type"), "bytes": len(live_b), "sha256": live_sha},
            "wayback": {"capture": cap, "replay_url_raw": replay, "bytes": len(wb_b), "sha256": wb_sha},
            "match": {"sha256_equal": live_sha == wb_sha, "bytes_equal": len(live_b) == len(wb_b)},
            **extra}

def snapshot_catalog_source(session: requests.Session, base: str, harvest_source_id: str,
                            rows_per_page: int = 1000) -> Dict[str, Any]:
    start = 0
    all_results: List[Dict[str, Any]] = []

    fq = f'harvest_source_id:"{harvest_source_id}"'

    while True:
        res = ckan_action(session, base, "package_search", {
            "q": "*:*",
            "fq": fq,
            "rows": rows_per_page,
            "start": start,
        })
        batch = res.get("results", [])
        all_results.extend(batch)

        if start + rows_per_page >= res.get("count", 0):
            break
        start += rows_per_page

    return {
        "snapshot_meta": {
            "fetched_at": now_utc_iso(),
            "ckan_base": base,
            "harvest_source_id": harvest_source_id,
            "count": len(all_results),
            "fq": fq,
        },
        "packages": all_results,
    }

def stable_sha256_json(obj: Any) -> str:
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def canonicalize_inventory_dataset(obj: Any, ignore_keys: Set[str]) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k in sorted(obj.keys()):
            if k in ignore_keys:
                continue
            out[k] = canonicalize_inventory_dataset(obj[k], ignore_keys)
        return out
    if isinstance(obj, list):
        return [canonicalize_inventory_dataset(v, ignore_keys) for v in obj]
    return obj

def get_dataset_list_any(doc: Any, dataset_key: str = "dataset") -> List[Dict[str, Any]]:
    if not isinstance(doc, dict):
        return []

    if dataset_key in doc and isinstance(doc.get(dataset_key), list):
        return [d for d in doc.get(dataset_key, []) if isinstance(d, dict)]

    for k in ("dataset", "datasets", "items", "records", "results"):
        v = doc.get(k)
        if isinstance(v, list):
            return [d for d in v if isinstance(d, dict)]
    return []

def make_id_func(id_field: Optional[str]) -> Callable[[Dict[str, Any]], str]:
    if id_field:
        def _f(d: Dict[str, Any]) -> str:
            v = d.get(id_field)
            if isinstance(v, str) and v.strip():
                return v.strip()
            return normalize_identifier(d)
        return _f
    return normalize_identifier

def diff_agency_inventory_versions(
    old_doc: Any,
    new_doc: Any,
    *,
    dataset_key: str = "dataset",
    id_func: Callable[[Dict[str, Any]], str] = normalize_identifier,
    ignore_keys: Optional[Iterable[str]] = None,
    old_filename: Optional[str] = None,
    new_filename: Optional[str] = None,
) -> Dict[str, Any]:
    
    ignores = set(ignore_keys or [])
    ignores.update({"_fetch_meta"})

    old_list = get_dataset_list_any(old_doc, dataset_key=dataset_key)
    new_list = get_dataset_list_any(new_doc, dataset_key=dataset_key)

    old_map: Dict[str, Dict[str, Any]] = {}
    new_map: Dict[str, Dict[str, Any]] = {}

    for d in old_list:
        k = (id_func(d) or "").strip()
        if k:
            old_map[k] = d

    for d in new_list:
        k = (id_func(d) or "").strip()
        if k:
            new_map[k] = d

    old_keys = set(old_map.keys())
    new_keys = set(new_map.keys())

    removed = sorted(list(old_keys - new_keys))
    added = sorted(list(new_keys - old_keys))
    common = sorted(list(old_keys & new_keys))

    modified: List[Dict[str, Any]] = []
    for k in common:
        o_can = canonicalize_inventory_dataset(old_map[k], ignores)
        n_can = canonicalize_inventory_dataset(new_map[k], ignores)
        o_h = stable_sha256_json(o_can)
        n_h = stable_sha256_json(n_can)
        if o_h != n_h:
            modified.append({"id": k, "old_sha256": o_h, "new_sha256": n_h})

    return {
        "diff_meta": {
            "dataset_key": dataset_key,
            "id_mode": ("field:" + str(getattr(id_func, "__name__", "custom"))) if id_func != normalize_identifier else "normalize_identifier",
            "old_filename": old_filename, 
            "new_filename": new_filename, 
            "old_source": (old_doc.get("_fetch_meta", {}) or {}).get("source_url") if isinstance(old_doc, dict) else None,
            "new_source": (new_doc.get("_fetch_meta", {}) or {}).get("source_url") if isinstance(new_doc, dict) else None,
            "old_fetched_at": (old_doc.get("_fetch_meta", {}) or {}).get("fetched_at") if isinstance(old_doc, dict) else None,
            "new_fetched_at": (new_doc.get("_fetch_meta", {}) or {}).get("fetched_at") if isinstance(new_doc, dict) else None,
        },
        "removed": removed,
        "added": added,
        "modified": modified,
        "counts": {
            "removed": len(removed),
            "added": len(added),
            "modified": len(modified),
            "old_total": len(old_list),
            "new_total": len(new_list),
            "old_indexed": len(old_map),
            "new_indexed": len(new_map),
        },
    }
    
def get_ckan_agency_id(package: Dict[str, Any]) -> Optional[str]:
    """Extracts the original agency identifier from a Data.gov CKAN package."""
    if package.get("identifier"):
        return package.get("identifier")
    
    for extra in package.get("extras", []):
        if isinstance(extra, dict) and extra.get("key") == "identifier":
            return extra.get("value")
            
    return None
# ----------------------------
# CLI Handlers
# ----------------------------

def cmd_list_harvest(args: argparse.Namespace) -> None:
    api_key = args.api_key or read_api_key(args.api_key_env)
    s = make_session(api_key, user_agent=args.user_agent)
    sources = list_harvest_sources(s, args.ckan_base, rows=args.rows)
    out = []
    for h in sources:
        out.append({
            "id": h.get("id"),
            "title": h.get("title"),
            "source_url": h.get("url"),
            "frequency": h.get("frequency"),
            "source_type": h.get("source_type"),
        })
    print(json.dumps(out, ensure_ascii=False, indent=2))

def cmd_cross_check(args: argparse.Namespace) -> None:
    """Compare an agency data.json against a Data.gov CKAN snapshot."""
    agency_data = read_json(args.agency)
    ckan_data = read_json(args.ckan)
    
    # 1. Parse Agency IDs
    agency_list = get_dataset_list_any(agency_data, args.dataset_key)
    agency_ids = set()
    for d in agency_list:
        ident = str(d.get("identifier", d.get("title", ""))).strip()
        if ident:
            agency_ids.add(ident)
            
    # 2. Parse CKAN IDs
    ckan_packages = ckan_data.get("packages", [])
    ckan_ids = set()
    for pkg in ckan_packages:
        ident = get_ckan_agency_id(pkg)
        if ident:
            ckan_ids.add(str(ident).strip())
            
    # 3. Compare
    missing = sorted(list(agency_ids - ckan_ids))
    extra = sorted(list(ckan_ids - agency_ids))
    common = sorted(list(agency_ids & ckan_ids))
    
    report = {
        "cross_check_meta": {
            "agency_file": args.agency,
            "ckan_file": args.ckan,
        },
        "counts": {
            "agency_total": len(agency_ids),
            "ckan_total": len(ckan_ids),
            "missing_from_datagov": len(missing),
            "extra_on_datagov": len(extra),
            "common": len(common)
        },
        "missing_from_datagov": missing,
        "extra_on_datagov": extra
    }
    
    if args.out:
        write_json(args.out, report)
        
    # Print the summary counts to the console
    print(json.dumps(report["counts"], indent=2))
    
    # If no output file is specified, print a quick preview to the console
    if not args.out:
        print(f"\nMissing from Data.gov (Sample of first 10):")
        for m in missing[:10]: print(f"  - {m}")
        print(f"\nExtra on Data.gov (Sample of first 10):")
        for e in extra[:10]: print(f"  - {e}")    

def cmd_inspect_diff(args: argparse.Namespace) -> None:
    """Helper to show side-by-side field changes for specific ID(s)."""
    
    # Setup output stream (file or console)
    out_stream = open(args.out, "w", encoding="utf-8") if args.out else sys.stdout

    def _print_diff(o_item: dict, n_item: dict, t_id: str):
        all_keys = sorted(set(o_item.keys()) | set(n_item.keys()))
        lines = [f"\n--- Changes for ID: {t_id} ---"]
        for k in all_keys:
            val_old = o_item.get(k)
            val_new = n_item.get(k)
            if val_old != val_new:
                lines.append(f"FIELD: {k}")
                lines.append(f"  [-] OLD: {val_old}")
                lines.append(f"  [+] NEW: {val_new}\n")
        
        # Only write if there are actual differences
        if len(lines) > 1:
            out_stream.write("\n".join(lines) + "\n")

    # Mode 1: Batch Process from Report
    if args.report:
        report = read_json(args.report)
        meta = report.get("diff_meta", {})
        
        old_file = meta.get("old_filename")
        new_file = meta.get("new_filename")
        dataset_key = meta.get("dataset_key", args.dataset_key)
        
        if not old_file or not new_file:
            die("The provided report is missing 'old_filename' or 'new_filename' in its 'diff_meta' block.")
            
        old_doc = read_json(old_file)
        new_doc = read_json(new_file)
        
        old_list = get_dataset_list_any(old_doc, dataset_key)
        new_list = get_dataset_list_any(new_doc, dataset_key)
        
        id_func = make_id_func(args.id_field)
        
        # Index lists to dictionaries for fast lookup
        old_map = {id_func(d): d for d in old_list if id_func(d)}
        new_map = {id_func(d): d for d in new_list if id_func(d)}
        
        modified_records = report.get("modified", [])
        if not modified_records:
            out_stream.write("No modified records found in the report.\n")
            
        for mod in modified_records:
            t_id = mod.get("id")
            if not t_id:
                continue
                
            o_item = old_map.get(t_id)
            n_item = new_map.get(t_id)
            
            if o_item and n_item:
                _print_diff(o_item, n_item, t_id)
            else:
                out_stream.write(f"\n--- Changes for ID: {t_id} ---\n[Warning: ID missing from one or both source files.]\n")

    # Mode 2: Single Manual ID
    else:
        if not args.old or not args.new or not args.target_id:
            die("You must provide either '--report <file>' OR all three positional arguments (old new target_id).")
            
        old_doc = read_json(args.old)
        new_doc = read_json(args.new)
        
        old_list = get_dataset_list_any(old_doc, args.dataset_key)
        new_list = get_dataset_list_any(new_doc, args.dataset_key)
        
        id_func = make_id_func(args.id_field)
        old_item = next((d for d in old_list if id_func(d) == args.target_id), None)
        new_item = next((d for d in new_list if id_func(d) == args.target_id), None)
        
        if not old_item or not new_item:
            die(f"Could not find ID '{args.target_id}' in both files.")
            
        _print_diff(old_item, new_item, args.target_id)

    if args.out:
        out_stream.close()
        print(f"Diff inspection written successfully to {args.out}")
            
def cmd_find_datajson(args: argparse.Namespace) -> None:
    try:
        with open(args.filepath, "r", encoding="utf-8") as f:
            sources = json.load(f)
    except UnicodeDecodeError:
        with open(args.filepath, "r", encoding="utf-16") as f:
            sources = json.load(f)

    rx = re.compile(args.pattern, re.IGNORECASE)

    matches = []
    for record in sources:
        blob = json.dumps(record, ensure_ascii=False)
        if rx.search(blob):
            matches.append(record)

    if not matches:
        die(f"No harvest sources matched regex: {args.pattern!r}")

    print(json.dumps(matches[:args.limit], ensure_ascii=False, indent=2))

def cmd_fetch_datajson(args: argparse.Namespace) -> None:
    api_key = args.api_key or read_api_key(args.api_key_env)
    s = make_session(api_key, user_agent=args.user_agent)
    doc = fetch_datajson(s, args.url)
    ok, msgs, n = basic_validate_datajson(doc)
    if args.out:
        write_json(args.out, doc)
    print(json.dumps({"ok": ok, "messages": msgs, "dataset_count": n, "fetch_meta": doc.get("_fetch_meta", {})}, ensure_ascii=False, indent=2))

def cmd_wayback_cdx(args: argparse.Namespace) -> None:
    url = wayback_cdx_url(args.url, limit=args.limit, from_ts=args.from_ts)
    print(url)
    if args.fetch:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        data = r.json()
        header = data[0] if data else []
        rows = data[1:] if len(data) > 1 else []
        print(json.dumps({"query_url": url, "rows_returned": len(rows), "header": header, "first_rows": rows[: min(5, len(rows))]}, ensure_ascii=False, indent=2))

def cmd_snapshot_org(args: argparse.Namespace) -> None:
    api_key = args.api_key or read_api_key(args.api_key_env)
    s = make_session(api_key, user_agent=args.user_agent)
    snap = snapshot_catalog_org(s, args.ckan_base, args.org, rows_per_page=args.rows_per_page)
    if args.out:
        write_json(args.out, snap)
    print(json.dumps(snap["snapshot_meta"], ensure_ascii=False, indent=2))
    
def cmd_clean_wayback(args: argparse.Namespace) -> None:
    api_key = args.api_key or read_api_key(args.api_key_env)
    s = make_session(api_key, user_agent=args.user_agent)

    doc = load_json_input(s, args.input)

    token = args.wayback_token
    if not token:
        token = extract_wayback_prefix_token(args.input)

    if not token and args.wayback_url:
        token = extract_wayback_prefix_token(args.wayback_url)

    if not token:
        die("clean-wayback: could not determine Wayback token. Provide --wayback-token or --wayback-url (or pass a WBM replay URL as the input).")

    cleaned, replaced = clean_wayback_json_prefix(doc, token)

    if args.out:
        write_json(args.out, cleaned)

    print(json.dumps({
        "ok": True,
        "replacements": replaced,
        "wayback_token": token,
        "out": args.out,
    }, ensure_ascii=False, indent=2))    


def cmd_snapshot_source(args: argparse.Namespace) -> None:
    api_key = args.api_key or read_api_key(args.api_key_env)
    s = make_session(api_key, user_agent=args.user_agent)

    snap = snapshot_catalog_source(
        s,
        args.ckan_base,
        args.source_id,
        rows_per_page=args.rows_per_page,
    )

    if not args.out:
        die("--out is required for snapshot-source")

    write_json(args.out, snap)
    print(json.dumps(snap["snapshot_meta"], ensure_ascii=False, indent=2))

def cmd_diff(args: argparse.Namespace) -> None:
    old = read_json(args.old)
    new = read_json(args.new)
    d = diff_snapshots(old, new, key=args.key)
    if args.out:
        write_json(args.out, d)
    print(json.dumps(d["counts"], ensure_ascii=False, indent=2))

def cmd_compare_wayback(args: argparse.Namespace) -> None:
    api_key = args.api_key or read_api_key(args.api_key_env)
    s = make_session(api_key, user_agent=args.user_agent)
    report = compare_live_vs_wayback(s, args.url, from_ts=args.from_ts)
    if args.out:
        write_json(args.out, report)
    print(json.dumps({
        "ok": report.get("ok"),
        "target_url": report.get("target_url"),
        "format": report.get("format"),
        "sha256_equal": (report.get("match") or {}).get("sha256_equal"),
        "wayback_ts": ((report.get("wayback") or {}).get("capture") or {}).get("timestamp"),
        "wayback_replay": (report.get("wayback") or {}).get("replay_url_raw"),
    }, ensure_ascii=False, indent=2))

def cmd_diff_inventory(args: argparse.Namespace) -> None:
    api_key = args.api_key or read_api_key(args.api_key_env)
    s = make_session(api_key, user_agent=args.user_agent)

    old_doc = load_inventory_input(s, args.old)
    new_doc = load_inventory_input(s, args.new)

    id_func = make_id_func(args.id_field)

    d = diff_agency_inventory_versions(
        old_doc,
        new_doc,
        dataset_key=args.dataset_key,
        id_func=id_func,
        ignore_keys=args.ignore_key,
        old_filename=args.old, 
        new_filename=args.new,
    )

    if args.out:
        write_json(args.out, d)

    print(json.dumps(d["counts"], ensure_ascii=False, indent=2))

# ----------------------------
# CLI Parser Definition
# ----------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="datagov_inventory_audit.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
        Data.gov + agency inventory audit helper.

        Requires: pip install -r requirements.txt
        Suggested: export DATAGOV_API_KEY=YOUR_API_DATA_GOV_KEY
                   (falls back to DEMO_KEY)
        """)
    )

    p.add_argument("--api-key", help="API key for api.data.gov (overrides environment variable)")
    p.add_argument("--ckan-base", default=DEFAULT_CKAN_BASE)
    p.add_argument("--api-key-env", default=DEFAULT_API_KEY_ENV)
    p.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("list-harvest", help="List harvest sources (robust)")
    sp.add_argument("--rows", type=int, default=1000)
    sp.set_defaults(func=cmd_list_harvest)

    sp = sub.add_parser("inspect-diff", help="Show side-by-side changes for specific dataset(s)")
    sp.add_argument("old", nargs="?", help="Old inventory file (required if not using --report)")
    sp.add_argument("new", nargs="?", help="New inventory file (required if not using --report)")
    sp.add_argument("target_id", nargs="?", help="The identifier to inspect (required if not using --report)")
    sp.add_argument("--report", help="JSON output file from diff-inventory to process all modified records")
    sp.add_argument("--out", help="Write the detailed text diff to this file path")
    sp.add_argument("--dataset-key", default="dataset")
    sp.add_argument("--id-field", help="Field to use for identity")
    sp.set_defaults(func=cmd_inspect_diff)

    sp = sub.add_parser("find-datajson", help="Regex filter over a saved list-harvest JSON file")
    sp.add_argument("filepath", help="Path to list-harvest JSON file")
    sp.add_argument("pattern", help="Regex pattern to match")
    sp.add_argument("--limit", type=int, default=10)
    sp.set_defaults(func=cmd_find_datajson)

    sp = sub.add_parser("clean-wayback", help="Strip Wayback replay prefix from URLs embedded in a JSON snapshot")
    sp.add_argument("input", help="Local JSON path or URL (can be a Wayback replay URL)")
    sp.add_argument("--wayback-token", dest="wayback_token", help="Wayback token after /web/ (e.g., 20240807053438 or 20240807053438id_)")
    sp.add_argument("--wayback-url", help="A Wayback replay URL to infer the token from (optional)")
    sp.add_argument("--out", help="Write cleaned JSON to this path")
    sp.set_defaults(func=cmd_clean_wayback)

    sp = sub.add_parser("snapshot-source", help="Snapshot all Data.gov packages for a harvest source id")
    sp.add_argument("source_id", help="Harvest source UUID (harvest_source_id)")
    sp.add_argument("--rows-per-page", type=int, default=1000)
    sp.add_argument("--out", required=True, help="Output JSON path for snapshot")
    sp.set_defaults(func=cmd_snapshot_source)

    sp = sub.add_parser("fetch-datajson", help="Fetch and minimally validate an agency data.json")
    sp.add_argument("url")
    sp.add_argument("--out")
    sp.set_defaults(func=cmd_fetch_datajson)

    sp = sub.add_parser("wayback-cdx", help="Print (and optionally fetch) a Wayback CDX query for a URL")
    sp.add_argument("url")
    sp.add_argument("--from-ts")
    sp.add_argument("--limit", type=int, default=2000)
    sp.add_argument("--fetch", action="store_true")
    sp.set_defaults(func=cmd_wayback_cdx)

    sp = sub.add_parser("snapshot-org", help="Snapshot all Data.gov packages for a CKAN organization")
    sp.add_argument("org")
    sp.add_argument("--rows-per-page", type=int, default=1000)
    sp.add_argument("--out", required=True)
    sp.set_defaults(func=cmd_snapshot_org)

    sp = sub.add_parser("diff", help="Diff two org snapshots")
    sp.add_argument("old")
    sp.add_argument("new")
    sp.add_argument("--key", default="id")
    sp.add_argument("--out")
    sp.set_defaults(func=cmd_diff)
    
    sp = sub.add_parser("diff-inventory", help="Diff two agency inventory JSONs (file paths or URLs)")
    sp.add_argument("old", help="Old inventory input (file path or URL)")
    sp.add_argument("new", help="New inventory input (file path or URL)")
    sp.add_argument("--dataset-key", default="dataset", help="Key containing dataset list (default: dataset)")
    sp.add_argument("--id-field", help="Prefer this field for dataset identity (falls back to identifier/landingPage/title)")
    sp.add_argument("--ignore-key", action="append", default=[], help="Repeatable: ignore dataset key name during change detection")
    sp.add_argument("--out", help="Write full diff report JSON to this path")
    sp.set_defaults(func=cmd_diff_inventory)

    sp = sub.add_parser("compare-wayback", help="Compare a live downloadable URL to the latest Wayback capture")
    sp.add_argument("url")
    sp.add_argument("--from-ts")
    sp.add_argument("--out")
    sp.set_defaults(func=cmd_compare_wayback)
    
    sp = sub.add_parser("cross-check", help="Compare an agency data.json vs a Data.gov CKAN snapshot")
    sp.add_argument("agency", help="Agency metadata JSON file")
    sp.add_argument("ckan", help="Data.gov CKAN snapshot JSON file")
    sp.add_argument("--dataset-key", default="dataset", help="Key containing dataset list in agency file")
    sp.add_argument("--out", help="Write full cross-check report JSON to this path")
    sp.set_defaults(func=cmd_cross_check)

    return p

def main(argv: Optional[List[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)

if __name__ == "__main__":
    main()