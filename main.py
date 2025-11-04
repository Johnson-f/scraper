import pandas as pd
import requests

URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

# Pretend to be a browser
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0 Safari/537.36"
    )
}

# Fetch the page
response = requests.get(URL, headers=headers)
response.raise_for_status()

# Parse all HTML tables on the page
tables = pd.read_html(response.text)

# The first table is the one containing the S&P 500 data
sp500 = tables[0]

# Extract only the "Symbol" column
symbols = sp500["Symbol"]

# Print first few symbols
print(symbols.head())

# Save only the symbols to CSV
symbols.to_csv("sp500_symbols.csv", index=False, header=["Symbol"])
