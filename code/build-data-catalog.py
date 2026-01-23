import requests
import csv
import time

def fetch_datagov_inventory(output_file="datagov_inventory.csv", limit=None):
    base_url = "https://catalog.data.gov/api/3/action/package_search"
    # Cap the page size at 1000 or the user's limit, whichever is smaller
    rows_per_page = min(1000, limit) if limit else 1000
    start = 0
    all_records = []
    
    print("Initiating connection to Data.gov API...")
    
    try:
        response = requests.get(base_url, params={'q': '*:*', 'rows': 0})
        response.raise_for_status()
        total_found = response.json()['result']['count']
        
        # Determine exactly how many we are going to fetch
        target_count = min(limit, total_found) if limit is not None else total_found
        print(f"Targeting {target_count} datasets.")
    except Exception as e:
        print(f"Error connecting to API: {e}")
        return

    while len(all_records) < target_count:
        # Calculate exactly how many more rows are needed
        remaining = target_count - len(all_records)
        current_rows = min(rows_per_page, remaining)
        
        print(f"Fetching {current_rows} records (Start: {start})...")
        
        params = {
            'q': '*:*',
            'rows': current_rows,
            'start': start,
            'sort': 'metadata_created asc'
        }
        
        try:
            resp = requests.get(base_url, params=params, timeout=30)
            resp.raise_for_status()
            page_data = resp.json()['result']['results']
            
            if not page_data: # Safety break if API returns empty list
                break

            for item in page_data:
                # Ensure we don't exceed the limit if the API returns more than requested
                if len(all_records) >= target_count:
                    break

                # --- Extraction Logic ---
                item_extras = item.get('extras', [])
                harvest_source = next((x['value'] for x in item_extras if x['key'] == 'harvest_source_title'), 'N/A')
                
                org_info = item.get('organization')
                agency_name = org_info.get('title', 'N/A') if org_info else 'N/A'
                
                all_records.append({
                    'Dataset Name': item.get('title', 'N/A'),
                    'Data.gov Link': f"https://catalog.data.gov/dataset/{item.get('name', '')}",
                    'Agency Data Link': item.get('url', 'N/A'),
                    'Metadata Created': item.get('metadata_created', 'N/A'),
                    'Metadata Updated': item.get('metadata_modified', 'N/A'),
                    'Owning Agency': agency_name,
                    'Harvest Source': harvest_source
                })
            
            start += current_rows
            if len(all_records) < target_count:
                time.sleep(1) 
            
        except Exception as e:
            print(f"Failed to fetch batch: {e}")
            break

    # Save to CSV
    keys = ['Dataset Name', 'Data.gov Link', 'Agency Data Link', 'Metadata Created', 'Metadata Updated', 'Owning Agency', 'Harvest Source']
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(all_records)
    
    print(f"\nCollected: {len(all_records)} records.")

if __name__ == "__main__":
    # Test with 10
    fetch_datagov_inventory(limit=10)