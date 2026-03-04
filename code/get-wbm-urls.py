'''
This script takes a WBM CDX api call for a set of snapshots 
and formats them into the snapshot URLs and writes them out 
to a file.

An example to run for usaid:
 $ python get-wbm-urls.py --output "usaid_snapshots.csv" --url "https://catalog.data.gov/harvest/usaid-json" --from "20230101" --to "20250501"

Last modified: 2/16/2026

'''
import requests
import argparse
import os

# 1. Setup Command Line Argument Parsing
parser = argparse.ArgumentParser(description="Fetch Wayback Machine snapshots.")
parser.add_argument("--url", default="data.gov", help="The URL to search (default: data.gov)")
parser.add_argument("--from", dest="from_date",default="20230101", help="Start date YYYYMMDD (default: 20230101)")
parser.add_argument("--to", dest="to_date",default="20251231", help="End date YYYYMMDD (default: 20251231)")
parser.add_argument("--output", default="snapshots_datagov.csv", help="Output filename (default: snapshots_datagov.csv)")
args = parser.parse_args()

# 2. Construct the URL using f-string and arguments
api_url = (
    f"https://web.archive.org/cdx/search/cdx?url={args.url}"
    f"&from={args.from_date}&to={args.to_date}"
    "&collapse=timestamp:6&output=json&fl=timestamp,original"
)

# 3. Fetch and Process
data = requests.get(api_url).json()

# 4. Write to the variable filename
# This ensures the output is saved in the directory you specify
output_path = os.path.join("../data", args.output)

# Optional: Create the directory if it doesn't exist
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w") as f:
    if len(data) > 1:
        for row in data[1:]:
            f.write(f"http://web.archive.org/web/{row[0]}/{row[1]}\n")
        print(f"Successfully saved {len(data)-1} snapshots to {output_path}")
    else:
        print("No snapshots found for the given parameters.")