import pandas as pd
from datetime import datetime
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import time

def fetch_russell2000_symbols():
    """Fetch Russell 2000 constituent symbols"""
    print("Fetching Russell 2000 constituents...")
    
    # Method 1: Try Wikipedia with proper headers
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        url = "https://en.wikipedia.org/wiki/Russell_2000_Index"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            tables = pd.read_html(response.text)
            
            for table in tables:
                if 'Ticker' in table.columns or 'Symbol' in table.columns:
                    col_name = 'Ticker' if 'Ticker' in table.columns else 'Symbol'
                    symbols = table[col_name].dropna().tolist()
                    symbols = [str(s).strip() for s in symbols if str(s) != 'nan']
                    
                    if len(symbols) > 50:  # Reasonable check
                        print(f"✓ Fetched {len(symbols)} symbols from Wikipedia")
                        return symbols
    except Exception as e:
        print(f"Wikipedia fetch failed: {e}")
    
    # Method 2: Try iShares with proper headers and error handling
    try:
        print("Trying iShares IWM holdings...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        # iShares holdings URL (this changes periodically)
        iwm_url = "https://www.ishares.com/us/products/239710/ishares-russell-2000-etf/1467271812596.ajax?fileType=csv&fileName=IWM_holdings&dataType=fund"
        
        response = requests.get(iwm_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            from io import StringIO
            # Try different skiprows values
            for skip in [10, 9, 11, 8]:
                try:
                    df = pd.read_csv(StringIO(response.text), skiprows=skip)
                    
                    # Look for ticker column with different possible names
                    ticker_col = None
                    for col in df.columns:
                        if 'ticker' in col.lower() or 'symbol' in col.lower():
                            ticker_col = col
                            break
                    
                    if ticker_col:
                        symbols = df[ticker_col].dropna().tolist()
                        symbols = [str(s).strip() for s in symbols if str(s) not in ['-', 'nan', '']]
                        
                        if len(symbols) > 50:
                            print(f"✓ Fetched {len(symbols)} symbols from iShares")
                            return symbols
                except:
                    continue
                    
    except Exception as e:
        print(f"iShares fetch failed: {e}")
    
    # Method 3: Fallback - Use a manually curated list of top Russell 2000 stocks
    print("\nUsing fallback method with known Russell 2000 stocks...")
    print("Note: This is a sample list. For complete data, consider using a data provider.")
    
    # These are some well-known Russell 2000 constituents (you can expand this list)
    fallback_symbols = [
        "SAIA", "FTDR", "CRUS", "ONTO", "CHH", "RUSHA", "RUSHB", "BCC", "EXPO", "DORM",
        "UFPI", "CVCO", "GTLS", "FN", "EPRT", "PECO", "AVNT", "CEIX", "KTB", "APAM",
        "CALM", "RHP", "CELH", "MLI", "PJT", "CRVL", "APOG", "SKYW", "HQY", "TBBK",
        "SHOO", "NEOG", "PRIM", "FORM", "CFFI", "SXI", "ALKS", "SANM", "PATK", "ATKR",
        "CENX", "MTDR", "SM", "FELE", "IOSP", "ABM", "CADE", "HLIO", "KFRC", "VITL",
        # Add more as needed
    ]
    
    print(f"✓ Using {len(fallback_symbols)} sample symbols")
    print("To get complete Russell 2000 list, consider:")
    print("  - Bloomberg Terminal")
    print("  - Russell Indexes official data")
    print("  - Financial data APIs (Polygon, Alpha Vantage, etc.)")
    
    return fallback_symbols

def get_stock_info(symbol):
    """Fetch market cap and price for a single symbol"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Get current price
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        
        # Get market cap
        market_cap = info.get('marketCap', 0)
        
        # Get company name
        company_name = info.get('longName') or info.get('shortName', '')
        
        # Check if stock is delisted or suspended
        quote_type = info.get('quoteType', '')
        
        # Additional check: if the stock has a valid price and market cap
        if current_price and market_cap and current_price > 0 and market_cap > 0:
            return {
                'Symbol': symbol,
                'Name': company_name,
                'MarketCap': market_cap,
                'Price': current_price,
                'QuoteType': quote_type
            }
    except Exception as e:
        pass
    return None

def fetch_stock_data(symbols, min_market_cap=100_000_000, min_price=1.0):
    """Fetch stock data and apply filters"""
    results = []
    total = len(symbols)
    
    print(f"\nFetching stock data for {total} symbols...")
    print(f"Filters: Market Cap > ${min_market_cap/1_000_000:.0f}M, Price > ${min_price}")
    print("This will take several minutes due to API rate limits...\n")
    
    # Use ThreadPoolExecutor for parallel requests
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_symbol = {executor.submit(get_stock_info, symbol): symbol 
                           for symbol in symbols}
        
        completed = 0
        for future in as_completed(future_to_symbol):
            result = future.result()
            if result:
                # Apply filters: market cap, price, and active trading
                if (result['MarketCap'] >= min_market_cap and 
                    result['Price'] >= min_price):
                    results.append(result)
            
            completed += 1
            if completed % 10 == 0 or completed == total:
                print(f"Progress: {completed}/{total} ({completed/total*100:.1f}%) - Found {len(results)} qualifying stocks")
    
    return results

def main():
    print("=" * 70)
    print("RUSSELL 2000 (IWM) CONSTITUENT SCRAPER")
    print("=" * 70)
    
    # Fetch Russell 2000 symbols
    all_symbols = fetch_russell2000_symbols()
    
    if not all_symbols:
        print("\n❌ No symbols found. Exiting.")
        return
    
    print(f"\nTotal symbols found: {len(all_symbols)}")
    
    # Set filters
    min_market_cap = 100_000_000  # $100 million
    min_price = 1.0  # $1
    
    # Fetch stock data and apply filters
    filtered_stocks = fetch_stock_data(all_symbols, min_market_cap, min_price)
    
    if not filtered_stocks:
        print("\n❌ No stocks met the filter criteria.")
        return
    
    # Create dataframe
    df = pd.DataFrame(filtered_stocks)
    df = df.sort_values('MarketCap', ascending=False)
    df['MarketCapFormatted'] = df['MarketCap'].apply(
        lambda x: f"${x/1_000_000_000:.2f}B" if x >= 1_000_000_000 else f"${x/1_000_000:.2f}M"
    )
    df['PriceFormatted'] = df['Price'].apply(lambda x: f"${x:.2f}")
    
    print(f"\n{'='*70}")
    print(f"Russell 2000 stocks with market cap > ${min_market_cap/1_000_000:.0f}M and price > ${min_price}: {len(filtered_stocks)}")
    print(f"{'='*70}")
    
    # Save to CSV
    filename = f"Russell2000_IWM_filtered_{datetime.now().strftime('%Y%m%d')}.csv"
    df[['Symbol', 'Name', 'Price', 'MarketCap', 'MarketCapFormatted', 'PriceFormatted']].to_csv(filename, index=False)
    
    print(f"\nSymbols saved to: {filename}")
    print("✓ Done!")
    
    # Show statistics
    if len(df) > 0:
        print(f"\nPrice statistics:")
        print(f"  - Average price: ${df['Price'].mean():.2f}")
        print(f"  - Median price: ${df['Price'].median():.2f}")
        print(f"  - Min price: ${df['Price'].min():.2f}")
        print(f"  - Max price: ${df['Price'].max():.2f}")
        
        print(f"\nMarket cap statistics:")
        print(f"  - Average: ${df['MarketCap'].mean()/1_000_000_000:.2f}B")
        print(f"  - Median: ${df['MarketCap'].median()/1_000_000_000:.2f}B")
        
        print("\nTop 10 by market cap:")
        print(df[['Symbol', 'Name', 'PriceFormatted', 'MarketCapFormatted']].head(10).to_string(index=False))

if __name__ == "__main__":
    main()