import pandas as pd

# List your CSV files
files = [
    'stock_symbols_filtered_20251115.csv',
    'Russell2000_IWM_filtered_20251115.csv',
    'nasdaq_stocks.csv'
]

# Read and merge
dfs = [pd.read_csv(f) for f in files]
merged = pd.concat(dfs, ignore_index=True)

# Remove duplicates (keep highest market cap)
if 'MarketCap' in merged.columns:
    merged = merged.sort_values('MarketCap', ascending=False)

merged = merged.drop_duplicates(subset=['Symbol'], keep='first')

# Save
merged.to_csv('merged_all_stocks.csv', index=False)

print(f"Merged {len(merged)} unique stocks")