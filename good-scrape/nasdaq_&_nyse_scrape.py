# /// script
# requires-python = ">=3.8"
# dependencies = [
#   "pandas",
#   "yfinance",
#   "requests",
# ]
# ///

import pandas as pd
from datetime import datetime
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

def fetch_nasdaq_symbols():
    """Fetch NASDAQ listed stock symbols using HTTP instead of FTP"""
    url = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt"
    try:
        response = requests.get(url, timeout=30)
        from io import StringIO
        df = pd.read_csv(StringIO(response.text), sep='|')
        df = df[:-1]
        # Filter out test symbols and delisted stocks
        df = df[~df['Symbol'].str.contains(r'\$|\.', na=False)]
        # Only keep actively traded stocks (Test Issue = 'N' means not a test)
        df = df[df['Test Issue'] == 'N']
        return df['Symbol'].tolist()
    except Exception as e:
        print(f"Error fetching NASDAQ list: {e}")
        return []

def fetch_nyse_symbols():
    """Fetch NYSE listed stock symbols using HTTP instead of FTP"""
    url = "https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt"
    try:
        response = requests.get(url, timeout=30)
        from io import StringIO
        df = pd.read_csv(StringIO(response.text), sep='|')
        df = df[:-1]
        nyse_df = df[df['Exchange'] == 'N']
        # Filter out test symbols and delisted stocks
        nyse_df = nyse_df[~nyse_df['ACT Symbol'].str.contains(r'\$|\.', na=False)]
        # Only keep actively traded stocks
        nyse_df = nyse_df[nyse_df['Test Issue'] == 'N']
        return nyse_df['ACT Symbol'].tolist()
    except Exception as e:
        print(f"Error fetching NYSE list: {e}")
        return []

def get_stock_info(symbol):
    """Fetch market cap and price for a single symbol"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Get current price
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        
        # Get market cap
        market_cap = info.get('marketCap', 0)
        
        # Check if stock is delisted or suspended (these often have no price or market cap)
        quote_type = info.get('quoteType', '')
        market_state = info.get('marketState', '')
        
        # Additional check: if the stock has a valid price and market cap
        if current_price and market_cap and current_price > 0 and market_cap > 0:
            return {
                'Symbol': symbol,
                'MarketCap': market_cap,
                'Price': current_price,
                'QuoteType': quote_type
            }
    except:
        pass
    return None

def fetch_stock_data(symbols, min_market_cap=100_000_000, min_price=1.0):
    """Fetch stock data and apply filters"""
    results = []
    total = len(symbols)
    
    print(f"\nFetching stock data for {total} symbols...")
    print(f"Filters: Market Cap > ${min_market_cap/1_000_000:.0f}M, Price > ${min_price}")
    print("This will take 10-20 minutes due to API rate limits...\n")
    
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
            if completed % 50 == 0 or completed == total:
                print(f"Progress: {completed}/{total} ({completed/total*100:.1f}%) - Found {len(results)} qualifying stocks")
    
    return results

def main():
    print("Fetching stock symbols from NASDAQ...")
    
    # Fetch both exchanges
    nasdaq_symbols = fetch_nasdaq_symbols()
    print(f"✓ Fetched {len(nasdaq_symbols)} NASDAQ symbols")
    
    nyse_symbols = fetch_nyse_symbols()
    print(f"✓ Fetched {len(nyse_symbols)} NYSE symbols")
    
    # Combine the lists
    all_symbols = nasdaq_symbols + nyse_symbols
    
    print(f"\nTotal symbols found: {len(all_symbols)}")
    
    # Fetch stock data and apply filters
    min_market_cap = 100_000_000  # $100 million
    min_price = 1.0  # $1
    
    filtered_stocks = fetch_stock_data(all_symbols, min_market_cap, min_price)
    
    # Create dataframe
    df = pd.DataFrame(filtered_stocks)
    df = df.sort_values('MarketCap', ascending=False)
    df['MarketCapFormatted'] = df['MarketCap'].apply(
        lambda x: f"${x/1_000_000_000:.2f}B" if x >= 1_000_000_000 else f"${x/1_000_000:.2f}M"
    )
    df['PriceFormatted'] = df['Price'].apply(lambda x: f"${x:.2f}")
    
    print(f"\n{'='*60}")
    print(f"Stocks with market cap > ${min_market_cap/1_000_000:.0f}M and price > ${min_price}: {len(filtered_stocks)}")
    print(f"{'='*60}")
    
    # Save to CSV
    filename = f"stock_symbols_filtered_{datetime.now().strftime('%Y%m%d')}.csv"
    df[['Symbol', 'Price', 'MarketCap', 'MarketCapFormatted', 'PriceFormatted']].to_csv(filename, index=False)
    
    print(f"\nSymbols saved to: {filename}")
    print("✓ Done!")
    
    # Show statistics
    if len(df) > 0:
        print(f"\nPrice statistics:")
        print(f"  - Average price: ${df['Price'].mean():.2f}")
        print(f"  - Median price: ${df['Price'].median():.2f}")
        print(f"  - Min price: ${df['Price'].min():.2f}")
        print(f"  - Max price: ${df['Price'].max():.2f}")
        
        print("\nTop 10 by market cap:")
        print(df[['Symbol', 'PriceFormatted', 'MarketCapFormatted']].head(10).to_string(index=False))

if __name__ == "__main__":
    main()