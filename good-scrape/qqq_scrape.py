# qqq_scraper.py
import pandas as pd
from datetime import datetime
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

def fetch_nasdaq100_symbols():
    """Fetch NASDAQ-100 constituent symbols from Wikipedia"""
    print("Fetching NASDAQ-100 constituents from Wikipedia...")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            tables = pd.read_html(response.text)
            # Find the table with constituents
            for table in tables:
                if 'Ticker' in table.columns or 'Symbol' in table.columns:
                    col_name = 'Ticker' if 'Ticker' in table.columns else 'Symbol'
                    symbols = table[col_name].tolist()
                    symbols = [s.strip() for s in symbols if pd.notna(s)]
                    if len(symbols) >= 90:  # Should have ~100
                        print(f"✓ Fetched {len(symbols)} NASDAQ-100 symbols")
                        return symbols
    except Exception as e:
        print(f"Error: {e}")
    
    return []

def get_stock_info(symbol):
    """Fetch market cap and price for a single symbol"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        market_cap = info.get('marketCap', 0)
        company_name = info.get('longName') or info.get('shortName', '')
        sector = info.get('sector', '')
        
        if current_price and market_cap and current_price > 0 and market_cap > 0:
            return {
                'Symbol': symbol,
                'Name': company_name,
                'Sector': sector,
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
            if completed % 20 == 0 or completed == total:
                print(f"Progress: {completed}/{total} ({completed/total*100:.1f}%) - Found {len(results)} stocks")
    
    return results

def main():
    print("=" * 70)
    print("NASDAQ-100 (QQQ) SCRAPER")
    print("=" * 70)
    
    symbols = fetch_nasdaq100_symbols()
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
    
    filename = f"NASDAQ100_QQQ_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(filename, index=False)
    
    print(f"\n{'='*70}")
    print(f"✓ Found {len(filtered_stocks)} NASDAQ-100 stocks")
    print(f"✓ Saved to: {filename}")
    print(f"{'='*70}")
    
    print("\nTop 10 by market cap:")
    print(df[['Symbol', 'Name', 'Sector', 'MarketCapFormatted']].head(10).to_string(index=False))

if __name__ == "__main__":
    main()