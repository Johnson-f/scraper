import pandas as pd
from datetime import datetime

def fetch_nasdaq_symbols():
    """Fetch NASDAQ listed stock symbols"""
    url = "ftp://ftp.nasdaqtrader.com/symboldirectory/nasdaqlisted.txt"
    try:
        df = pd.read_csv(url, sep='|')
        # Remove the last row (file creation timestamp)
        df = df[:-1]
        return df['Symbol'].tolist()
    except Exception as e:
        print(f"Error fetching NASDAQ list: {e}")
        return []

def fetch_nyse_symbols():
    """Fetch NYSE listed stock symbols"""
    url = "ftp://ftp.nasdaqtrader.com/symboldirectory/otherlisted.txt"
    try:
        df = pd.read_csv(url, sep='|')
        # Remove the last row (file creation timestamp)
        df = df[:-1]
        # Filter for NYSE stocks (Exchange code 'N')
        nyse_df = df[df['Exchange'] == 'N']
        return nyse_df['ACT Symbol'].tolist()
    except Exception as e:
        print(f"Error fetching NYSE list: {e}")
        return []

def main():
    print("Fetching stock symbols from NASDAQ FTP server...")
    
    # Fetch both exchanges
    nasdaq_symbols = fetch_nasdaq_symbols()
    nyse_symbols = fetch_nyse_symbols()
    
    # Combine the lists
    all_symbols = nasdaq_symbols + nyse_symbols
    
    print(f"\nTotal symbols found: {len(all_symbols)}")
    print(f"  - NASDAQ: {len(nasdaq_symbols)}")
    print(f"  - NYSE: {len(nyse_symbols)}")
    
    # Create dataframe with just symbols
    df = pd.DataFrame({'Symbol': all_symbols})
    
    # Save to CSV
    filename = f"stock_symbols_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(filename, index=False)
    
    print(f"\nSymbols saved to: {filename}")
    print("✓ Done!")

if __name__ == "__main__":
    main()