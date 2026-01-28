'''
This code can be used to extract the number of harvest sources reported by data.gov 
from the WBM snapshots of catalog.data.gov/harvest

The code attempts to get the snapshot taken closest to the first of the month for 
 each month between the start year and end year (see lines 81-82)

Last Modified: 1/28/2026
'''
import requests
from bs4 import BeautifulSoup
import re
import time
import pandas as pd
import os

def get_monthly_snapshots(target_url, start_year, end_year):
    """
    Queries the Wayback Machine CDX API to get a list of snapshots 
    collapsed by month (YYYYMM).
    """
    cdx_url = "https://web.archive.org/cdx/search/cdx"
    
    # Construct parameters
    # collapse=timestamp:6 groups by YYYYMM (monthly)
    # filter=statuscode:200 ensures we only get successful captures
    params = {
        'url': target_url,
        'from': f"{start_year}0101",
        'to': f"{end_year}0101",
        'collapse': 'timestamp:6', 
        'output': 'json',
        'fl': 'timestamp,original',
        'filter': 'statuscode:200'
    }
    
    print(f"Querying CDX API for {target_url}...")
    try:
        response = requests.get(cdx_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # The first item in the list is the header ['timestamp', 'original']
        # We slice it off with [1:]
        if len(data) > 1:
            return data[1:]
        else:
            return []
    except Exception as e:
        print(f"Error fetching CDX data: {e}")
        return []

def scrape_harvest_count(timestamp, original_url):
    """
    Fetches the specific archived page and extracts the count.
    """
    # Construct the playback URL
    archive_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
    
    try:
        response = requests.get(archive_url, timeout=120)
        if response.status_code != 200:
            return "Failed to load"

        soup = BeautifulSoup(response.content, 'html.parser')
        text_content = soup.get_text()
        
        # Regex to find "X harvests found" (handles "1,234" and "1234")
        match = re.search(r'([\d,]+)\s+harvests?\s+found', text_content, re.IGNORECASE)
        
        if match:
            return int(match.group(1).replace(',', ''))
        else:
            return "Pattern not found"
            
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    target_url = "https://catalog.data.gov/harvest/"
    start_year = 2023
    end_year = 2026
    output_file = "../data/datagov_harvest_counts-01282026.csv"
    
    # 1. Get List of Snapshots via CDX
    snapshots = get_monthly_snapshots(target_url, start_year, end_year)
    
    print(f"Found {len(snapshots)} monthly snapshots from {start_year} to {end_year}.")
    print("-" * 60)
    
    results = []
    
    # 2. Iterate and Scrape
    for snapshot in snapshots:
        ts = snapshot[0]
        orig_url = snapshot[1]
        
        # Convert timestamp to readable date for the CSV
        date_readable = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"
        
        print(f"Processing snapshot: {date_readable} ({ts})...")
        
        count = scrape_harvest_count(ts, orig_url)
        
        results.append({
            "Date": date_readable,
            "Timestamp": ts,
            "Harvests Found": count,
            "Archive URL": f"https://web.archive.org/web/{ts}/{orig_url}"
        })
        
        # Sleep to prevent rate limiting (Wayback Machine can be strict)
        time.sleep(1.5)

    # 3. Export
    if results:
        df = pd.DataFrame(results)
        print("-" * 60)
        print(df[["Date", "Harvests Found"]].head()) # Show preview
        
        df.to_csv(output_file, index=False)
        print(f"\nSaved full results to: {os.path.abspath(output_file)}")
    else:
        print("No results to save.")

if __name__ == "__main__":
    main()