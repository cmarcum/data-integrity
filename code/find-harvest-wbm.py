'''
This script evaluates whether a search term could be found on a particular snapshot 
 of a dynamic set of pages from the WBM nearest to a specific date. The script returns a notice when
 the term is matched. In the present case, the script was designed for https://catalog.data.gov/harvest/
 search results but it could be adapted to use any URL (and the argparser would be a good place to do that).
 
 The script takes three arguments "keyword", "--pages", and "--date".

From the command line, this can be run with:
 $ python find-harvest-wbm.py "usaid" --pages 44 --date "20231201"

Last Modified: 2/2/2026
'''
import requests
import time
import argparse
import sys

def search_wayback_refined(search_term, total_pages, target_date="20240121"):
    base_url = "https://catalog.data.gov/harvest/?organization_type=Federal+Government"
    availability_api = "https://archive.org/wayback/available"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })

    search_term = search_term.strip().lower()
    print(f"Starting search for '{search_term}' up to {total_pages} pages...")

    for i in range(1, total_pages + 1):
        if i > 1:
            current_url = f"{base_url}&page={i}" 
        else:
            current_url = base_url
        print(f"Checking Page {i} ({current_url})...", end=" ", flush=True)
        
        params = {'url': current_url, 'timestamp': target_date}

        try:
            # 1. Get the closest snapshot metadata
            resp = session.get(availability_api, params=params, timeout=10)
            
            if resp.status_code != 200:
                print(f"API Error: Status {resp.status_code}")
                continue

            data = resp.json()
            snapshot = data.get('archived_snapshots', {}).get('closest')
            
            if snapshot and snapshot.get('available'):
                wayback_url = snapshot['url']
                print(f"Found snapshot: {wayback_url}", end=" ", flush=True)
                
                # 2. Fetch the actual snapshot content
                page_data = session.get(wayback_url, timeout=20, allow_redirects=True)
                
                # Using 'ignore' for decoding to prevent any crash on weird bytes
                content = page_data.content.decode('utf-8', errors='ignore').lower()

                if search_term in content:
                    print("\n[!!! MATCH FOUND !!!]")
                    break
                else:
                    print(f"(No '{search_term}' in {len(content)} bytes)")
            else:
                print("No snapshot available for this date.")
            
            time.sleep(1.5)
            
        except Exception as e:
            print(f"\nERROR on Page {i}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search Wayback for specific content.")
    parser.add_argument("keyword", help="The term to search for")
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--date", default="20250121")
    
    args = parser.parse_args()
    
    # Ensure we actually have arguments before running
    if not args.keyword:
        parser.print_help()
        sys.exit(1)

    search_wayback_refined(args.keyword, args.pages, args.date)