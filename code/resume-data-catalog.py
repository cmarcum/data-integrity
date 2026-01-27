'''
This code can be used to extract information from data.gov using the CKAN API
 it currently writes out the following information to a csv file from all datasets indexed in the Federal Data Catalog:
    'Dataset Name'
    'Data.gov Link' 
    'Agency Data Link' 
    'Metadata Created' 
    'Metadata Updated' 
    'Owning Agency' 
    'Harvest Source'

The script has resume capability in case of an interruption.

While the script is "headless" and uses the public, non-authenticated API gateway, it can easily be modified to use
 the authenticated gateway with an API key instead. Please refer to the repository README file for instructions on how to modify these scripts for using the authenticated gateway.
 
Last Modified: 1/27/2026
'''
import requests
import csv
import time
import os

def fetch_datagov_inventory(output_file="datagov_inventory.csv", resume=True):
    base_url = "https://catalog.data.gov/api/3/action/package_search"
    rows_per_page = 1000 
    
    # --- RESUME LOGIC ---
    start = 0
    file_exists = os.path.isfile(output_file)
    
    if resume and file_exists:
        with open(output_file, 'r', encoding='utf-8') as f:
            # Count existing rows (subtract 1 for the header)
            existing_rows = sum(1 for line in f) - 1
            if existing_rows > 0:
                start = existing_rows
                print(f"Resuming from record index: {start}")
            else:
                print("File exists but is empty. Starting from scratch.")
    else:
        print("Starting a new data collection task.")

    # Get total count for verification
    try:
        params = {'q': '*:*', 'rows': 0}
        total_found = requests.get(base_url, params=params).json()['result']['count']
        print(f"Total datasets reported by Data.gov: {total_found}")
    except Exception as e:
        print(f"Initial connection failed: {e}")
        return

    # --- CSV SETUP ---
    keys = ['Dataset Name', 'Data.gov Link', 'Agency Data Link', 'Metadata Created', 'Metadata Updated', 'Owning Agency', 'Harvest Source']
    
    # Use 'a' (append) if resuming, 'w' (write/overwrite) if starting fresh
    mode = 'a' if (resume and file_exists) else 'w'
    
    with open(output_file, mode, newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        
        # Only write header if we are starting a fresh file
        if mode == 'w':
            writer.writeheader()

        while start < total_found:
            print(f"Fetching records {start} to {min(start + rows_per_page, total_found)}...")
            
            params = {
                'q': '*:*',
                'rows': rows_per_page,
                'start': start,
                'sort': 'metadata_created asc' # Mandatory for resume to work correctly
            }
            
            try:
                resp = requests.get(base_url, params=params, timeout=30)
                resp.raise_for_status()
                page_data = resp.json()['result']['results']
                
                batch = []
                for item in page_data:
                    # CKAN Field Mappings
                    slug = item.get('name', '')
                    org_info = item.get('organization')
                    item_extras = item.get('extras', [])
                    harvest_source = next((x['value'] for x in item_extras if x['key'] == 'harvest_source_title'), 'N/A')
                    
                    batch.append({
                        'Dataset Name': item.get('title', 'N/A'),
                        'Data.gov Link': f"https://catalog.data.gov/dataset/{slug}" if slug else "N/A",
                        'Agency Data Link': item.get('url') or (item.get('resources')[0].get('url') if item.get('resources') else "N/A"),
                        'Metadata Created': item.get('metadata_created', 'N/A'),
                        'Metadata Updated': item.get('metadata_modified', 'N/A'),
                        'Owning Agency': org_info.get('title', 'N/A') if org_info else 'N/A',
                        'Harvest Source': harvest_source
                    })
                
                writer.writerows(batch)
                f.flush() # Force write to disk in case of crash
                
                start += rows_per_page
                time.sleep(1) # Slightly longer delay to avoid aggressive rate limiting
                
            except Exception as e:
                print(f"\nINTERRUPTION at record {start}: {e}")
                print("The script has saved progress. Run again with resume=True to continue.")
                break

    print(f"\nTask complete. Current records in file: {start}")

if __name__ == "__main__":
    # Set resume=True to automatically pick up where you left off
    # Set resume=False to overwrite the file and start over
    fetch_datagov_inventory(output_file="datagov_inventory.csv", resume=True)