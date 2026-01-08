'''
This code can be used to extract the number of datasets reported by data.gov 
or an WBM snapshot of data.gov. 

Last Modified: 1/6/2026
'''

import csv, requests, re
from bs4 import BeautifulSoup

# Input: 'urls.csv' (URLs in first column) | Output: 'results.csv'
with open('urls.csv', 'r') as f_in, open('results.csv', 'w', newline='') as f_out:
    writer = csv.writer(f_out)
    for row in csv.reader(f_in):
        try:
            html = requests.get(row[0], headers={'User-Agent': 'Mozilla/5.0'}).text
            # Chain find, get text, regex search, and clean in minimal steps
            text = BeautifulSoup(html, 'html.parser').find('div', class_='hero__dataset-count').get_text()
            count = re.search(r'([\d,]+)', text).group(1).replace(',', '')
            writer.writerow([row[0], count])
        except:
            pass # Skips invalid URLs or extraction errors silently