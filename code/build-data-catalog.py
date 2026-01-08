import requests
import csv
import time
import os

def fetch_datagov_inventory(output_file="datagov_inventory.csv"):
    base_url = "https://catalog.data.gov/api/3/action/package_search"
    rows_per_page = 1000  # Maximum allowed by Data.gov CKAN API
    start = 0
    all_records = []
    
    print("Initiating connection to Data.gov API...")
    
    # Initial request to get the total count and verify against the website report
    params = {
        'q': '*:*',
        'rows': 0,
        'start': 0
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        total_found = data['result']['count']
        print(f"Total datasets found on Data.gov: {total_found}")
    except Exception as e:
        print(f"Error connecting to API: {e}")
        return

    # Loop through the catalog in pages
    while start < total_found:
        print(f"Fetching records {start} to {min(start + rows_per_page, total_found)}...")
        
        params = {
            'q': '*:*',
            'rows': rows_per_page,
            'start': start,
            'sort': 'metadata_created asc' # Sorting helps ensure consistency across pages
        }
        
        try:
            resp = requests.get(base_url, params=params, timeout=30)
            resp.raise_for_status()
            page_data = resp.json()['result']['results']
            
            for item in page_data:
                # 1) Dataset Name
                name = item.get('title', 'N/A')
                
                # 2) Link to record in data.gov
                # Use 'name' for the URL slug as per Data.gov conventions
                slug = item.get('name', '')
                datagov_link = f"https://catalog.data.gov/dataset/{slug}" if slug else "N/A"
                
                # 3) Link to agency website where data can be found
                # Usually stored in the 'url' field of the package or the first resource
                agency_data_link = item.get('url')
                if not agency_data_link and item.get('resources'):
                    agency_data_link = item['resources'][0].get('url', 'N/A')
                
                # 4) Metadata created date
                created_date = item.get('metadata_created', 'N/A')
                
                # 5) Metadata updated date
                updated_date = item.get('metadata_modified', 'N/A')
                
                # 6) Agency that owns the dataset
                org_info = item.get('organization')
                agency_name = org_info.get('title', 'N/A') if org_info else 'N/A'
                
                all_records.append({
                    'Dataset Name': name,
                    'Data.gov Link': datagov_link,
                    'Agency Data Link': agency_data_link,
                    'Metadata Created': created_date,
                    'Metadata Updated': updated_date,
                    'Owning Agency': agency_name
                })
            
            start += rows_per_page
            # Rate limiting courtesy: sleep briefly between large requests
            time.sleep(1) 
            
        except Exception as e:
            print(f"Failed to fetch batch starting at {start}: {e}")
            break

    # Verification Step
    actual_count = len(all_records)
    print("\n--- Verification ---")
    print(f"Datasets reported by API: {total_found}")
    print(f"Datasets successfully collected: {actual_count}")
    
    if actual_count == total_found:
        print("Success: Total record count matches the reported number.")
    else:
        print("Warning: Count mismatch. Check network stability or API rate limits.")

    # Write to CSV
    keys = ['Dataset Name', 'Data.gov Link', 'Agency Data Link', 'Metadata Created', 'Metadata Updated', 'Owning Agency']
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(all_records)
    
    print(f"\nCSV script complete. Data headers prepared for {output_file}.")

if __name__ == "__main__":
    fetch_datagov_inventory()