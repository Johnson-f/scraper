# vti_scraper.py
import pandas as pd
from datetime import datetime
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

def fetch_vti_symbols():
    """Fetch VTI (Total Stock Market) constituent symbols"""
    print("Fetching VTI constituents...")
    print("Note: VTI contains ~4000 stocks. This will take a while.")
    
    # VTI essentially includes all US stocks, so we'll combine multiple sources
    symbols = []
    
    # Get S&P 500
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            tables = pd.read_html(response.text)
            sp500 = tables[0]['Symbol'].tolist()
            sp500 = [s.replace('.', '-') for s in sp500]
            symbols.extend(sp500)
            print(f"✓ Added {len(sp500)} S&P 500 stocks")
    except Exception as e:
        print(f"S&P 500 fetch failed: {e}")
    
    # Get NASDAQ listed
    try:
        url = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt"
        df = pd.read_csv(url, sep='|')
        df = df[:-1]
        df = df[~df['Symbol'].str.contains(r'\$|\.', na=False)]
        df = df[df['Test Issue'] == 'N']
        nasdaq = df['Symbol'].tolist()
        symbols.extend(nasdaq)
        print(f"✓ Added {len(nasdaq)} NASDAQ stocks")
    except Exception as e:
        print(f"NASDAQ fetch failed: {e}")
    
    # Get NYSE listed
    try:
        url = "https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt"
        df = pd.read_csv(url, sep='|')
        df = df[:-1]
        nyse_df = df[df['Exchange'] == 'N']
        nyse_df = nyse_df[~nyse_df['ACT Symbol'].str.contains(r'\$|\.', na=False)]
        nyse_df = nyse_df[nyse_df['Test Issue'] == 'N']
        nyse = nyse_df['ACT Symbol'].tolist()
        symbols.extend(nyse)
        print(f"✓ Added {len(nyse)} NYSE stocks")
    except Exception as e:
        print(f"NYSE fetch failed: {e}")
    
    # Remove duplicates
    symbols = list(set(symbols))
    print(f"\n✓ Total unique symbols: {len(symbols)}")
    
    return symbols

def get_stock_info(symbol):
    """Fetch market cap and price for a single symbol"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        market_cap = info.get('marketCap', 0)
        company_name = info.get('longName') or info.get('shortName', '')
        
        if current_price and market_cap and current_price > 0 and market_cap > 0:
            return {
                'Symbol': symbol,
                'Name': company_name,
                'MarketCap': market_cap,
                'Price': current_price
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
    print("This will take 20-30 minutes...\n")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_symbol = {executor.submit(get_stock_info, symbol): symbol 
                           for symbol in symbols}
        
        completed = 0
        for future in as_completed(future_to_symbol):
            result = future.result()
            if result:
                if (result['MarketCap'] >= min_market_cap and 
                    result['Price'] >= min_price):
                    results.append(result)
            
            completed += 1
            if completed % 100 == 0 or completed == total:
                print(f"Progress: {completed}/{total} ({completed/total*100:.1f}%) - Found {len(results)} stocks")
    
    return results

def main():
    print("=" * 70)
    print("VTI (Total US Stock Market) SCRAPER")
    print("=" * 70)
    
    symbols = fetch_vti_symbols()
    if not symbols:
        print("❌ Failed to fetch symbols")
        return
    
    filtered_stocks = fetch_stock_data(symbols, min_market_cap=100_000_000, min_price=1.0)
    
    if not filtered_stocks:
        print("❌ No stocks met criteria")
        return
    
    df = pd.DataFrame(filtered_stocks)
    df = df.sort_values('MarketCap', ascending=False)
    df['MarketCapFormatted'] = df['MarketCap'].apply(
        lambda x: f"${x/1_000_000_000:.2f}B" if x >= 1_000_000_000 else f"${x/1_000_000:.2f}M"
    )
    df['PriceFormatted'] = df['Price'].apply(lambda x: f"${x:.2f}")
    
    filename = f"VTI_TotalMarket_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(filename, index=False)
    
    print(f"\n{'='*70}")
    print(f"✓ Found {len(filtered_stocks)} stocks")
    print(f"✓ Saved to: {filename}")
    print(f"{'='*70}")
    
    print("\nTop 10 by market cap:")
    print(df[['Symbol', 'Name', 'MarketCapFormatted']].head(10).to_string(index=False))

if __name__ == "__main__":
    main()