'''
This script takes a WBM CDX api call for a set of snapshots 
and formats them into the snapshot URLs and writes them out 
to a file.

Last modified: 1/23/2026
'''
import requests

url = "https://web.archive.org/cdx/search/cdx?url=data.gov&from=20230101&to=20251231&collapse=timestamp:6&output=json&fl=timestamp,original"
data = requests.get(url).json()

with open("../data/snapshots_datagov.csv", "w") as f:
    for row in data[1:]:
        f.write(f"http://web.archive.org/web/{row[0]}/{row[1]}\n")
