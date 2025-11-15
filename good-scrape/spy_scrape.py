# spy_scraper.py
import pandas as pd
from datetime import datetime
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from io import StringIO
import time

def fetch_sp500_symbols():
    """Fetch S&P 500 constituent symbols from Wikipedia with retry logic"""
    print("Fetching S&P 500 constituents from Wikipedia...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    
    # Try Wikipedia with retries
    for attempt in range(3):
        try:
            print(f"Attempt {attempt + 1}/3...")
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Use StringIO to avoid FutureWarning
                tables = pd.read_html(StringIO(response.text))
                print(f"Found {len(tables)} tables on the page")
                
                # Find the right table - look for one with proper columns and data
                for i, df in enumerate(tables):
                    print(f"\nChecking table {i}: shape={df.shape}, columns={df.columns.tolist()}")
                    
                    # Skip tables that are too small or have error messages
                    if df.shape[0] < 100:  # S&P 500 should have ~500 rows
                        print(f"  Skipping - too few rows ({df.shape[0]})")
                        continue
                    
                    # Look for Symbol column (case insensitive)
                    symbol_col = None
                    for col in df.columns:
                        if isinstance(col, str) and 'symbol' in col.lower():
                            symbol_col = col
                            break
                    
                    if symbol_col:
                        print(f"  Found Symbol column: '{symbol_col}'")
                        symbols = df[symbol_col].tolist()
                        # Clean symbols (BRK.B -> BRK-B) and filter out NaN
                        symbols = [str(s).replace('.', '-') for s in symbols if pd.notna(s) and str(s).strip()]
                        
                        # Validate - should have stock-like symbols
                        if len(symbols) > 100 and all(len(str(s)) <= 5 for s in symbols[:10]):
                            print(f"✓ Fetched {len(symbols)} S&P 500 symbols from table {i}")
                            return symbols
                
                print("Could not find valid S&P 500 table")
                
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                wait_time = (attempt + 1) * 5
                print(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
    
    # Fallback: Use yfinance to get SPY holdings
    print("\nTrying fallback method: Fetching from SPY ETF...")
    try:
        spy = yf.Ticker("SPY")
        holdings = spy.get_holdings()
        if holdings is not None and len(holdings) > 0:
            symbols = holdings['Symbol'].tolist()
            symbols = [str(s).replace('.', '-') for s in symbols if pd.notna(s)]
            print(f"✓ Fetched {len(symbols)} symbols from SPY holdings")
            return symbols
    except Exception as e:
        print(f"Fallback method failed: {e}")
    
    # Last resort: Return a hardcoded list of major S&P 500 stocks
    print("\nUsing backup list of major S&P 500 stocks...")
    backup_symbols = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'LLY', 'AVGO',
        'JPM', 'V', 'UNH', 'XOM', 'WMT', 'MA', 'JNJ', 'PG', 'COST', 'HD',
        'ORCL', 'ABBV', 'MRK', 'KO', 'CVX', 'BAC', 'NFLX', 'PEP', 'CRM', 'AMD',
        'ADBE', 'TMO', 'MCD', 'ACN', 'CSCO', 'LIN', 'ABT', 'WFC', 'TMUS', 'DHR',
        'DIS', 'TXN', 'INTU', 'VZ', 'PM', 'CMCSA', 'NEE', 'QCOM', 'IBM', 'AMGN'
    ]
    print(f"✓ Using {len(backup_symbols)} major stocks")
    return backup_symbols

def get_stock_info(symbol):
    """Fetch market cap and price for a single symbol"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        market_cap = info.get('marketCap', 0)
        company_name = info.get('longName') or info.get('shortName', '')
        sector = info.get('sector', '')
        industry = info.get('industry', '')
        
        if current_price and market_cap and current_price > 0 and market_cap > 0:
            return {
                'Symbol': symbol,
                'Name': company_name,
                'Sector': sector,
                'Industry': industry,
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
            if completed % 50 == 0 or completed == total:
                print(f"Progress: {completed}/{total} ({completed/total*100:.1f}%) - Found {len(results)} stocks")
    
    return results

def main():
    print("=" * 70)
    print("S&P 500 (SPY) SCRAPER")
    print("=" * 70)
    
    symbols = fetch_sp500_symbols()
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
    
    filename = f"SP500_SPY_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(filename, index=False)
    
    print(f"\n{'='*70}")
    print(f"✓ Found {len(filtered_stocks)} S&P 500 stocks")
    print(f"✓ Saved to: {filename}")
    print(f"{'='*70}")
    
    print("\nTop 10 by market cap:")
    print(df[['Symbol', 'Name', 'Sector', 'MarketCapFormatted']].head(10).to_string(index=False))
    
    print("\nSector breakdown:")
    print(df['Sector'].value_counts())

if __name__ == "__main__":
    main()