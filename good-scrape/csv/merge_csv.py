import pandas as pd

# This script merges multiple stock symbol CSV files into a single file.
# It reads 6 different CSV files containing stock symbols from various indices
# (Dow Jones, NASDAQ 100, Russell 2000, S&P 400 Mid Cap, S&P 500, and a filtered stock list).
# 
# The script then:
# 1. Combines all dataframes into one using pd.concat()
# 2. Sorts by MarketCap (descending) if that column exists, to prioritize higher market cap stocks
# 3. Removes duplicate symbols, keeping only the first occurrence (which has the highest market cap)
# 4. Saves the merged and deduplicated data to 'merged_all_stocks.csv'
# 5. Prints the total count of unique stocks in the merged file

files = [
    'dow_jones_list.csv',
    'NASDAQ100_QQQ_20251115.csv',
    'Russell2000_IWM_filtered_20251115.csv',
    'SP400_MidCap_IJH_20251115.csv',
    'SP500_SPY_20251115.csv',
    'stock_symbols_filtered_20251115.csv',
    'VTI_TotalMarket_20251115.csv'
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