import pandas as pd
import requests

URL = "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/117.0 Safari/537.36"
}

# Fetch HTML
response = requests.get(URL, headers=headers)
response.raise_for_status()

# Parse all tables on the page
tables = pd.read_html(response.text)

# Find the one that actually has the 'Symbol' column (the real data)
djia_table = None
for table in tables:
    if "Symbol" in table.columns or "Company" in table.columns:
        djia_table = table
        break

if djia_table is None:
    raise ValueError("Could not find the Dow Jones table.")

print(djia_table.head())

# Optional: save to CSV
djia_table.to_csv("dow_jones_list.csv", index=False)
