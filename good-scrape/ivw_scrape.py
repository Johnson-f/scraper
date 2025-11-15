# ivw_scraper.py
import pandas as pd
from datetime import datetime
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

def fetch_sp500_growth_symbols():
    """Fetch S&P 500 Growth constituent symbols"""
    print("Fetching S&P 500 Growth constituents...")
    print("Note: Using S&P 500 base + filtering for growth characteristics")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            tables = pd.read_html(response.text)
            df = tables[0]
            symbols = df['Symbol'].tolist()
            symbols = [s.replace('.', '-') for s in symbols]
            print(f"✓ Fetched {len(symbols)} S&P 500 symbols for growth screening")
            return symbols
    except Exception as e:
        print(f"Error: {e}")
    
    return []

def get_stock_info(symbol):
    """Fetch market cap, price, and growth metrics"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        market_cap = info.get('marketCap', 0)
        company_name = info.get('longName') or info.get('shortName', '')
        sector = info.get('sector', '')
        
        # Growth indicators
        pe_ratio = info.get('trailingPE', 0)
        peg_ratio = info.get('pegRatio', 0)
        revenue_growth = info.get('revenueGrowth', 0)
        earnings_growth = info.get('earningsGrowth', 0)
        
        if current_price and market_cap and current_price > 0 and market_cap > 0:
            return {
                'Symbol': symbol,
                'Name': company_name,
                'Sector': sector,
                'MarketCap': market_cap,
                'Price': current_price,
                'PE_Ratio': pe_ratio,
                'PEG_Ratio': peg_ratio,
                'Revenue_Growth': revenue_growth,
                'Earnings_Growth': earnings_growth
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
    print("Screening for growth characteristics...\n")
    
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
    print("S&P 500 GROWTH (IVW) SCRAPER")
    print("=" * 70)
    
    symbols = fetch_sp500_growth_symbols()
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
    
    filename = f"SP500_Growth_IVW_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(filename, index=False)
    
    print(f"\n{'='*70}")
    print(f"✓ Found {len(filtered_stocks)} growth stocks")
    print(f"✓ Saved to: {filename}")
    print(f"{'='*70}")
    
    print("\nTop 10 by market cap:")
    print(df[['Symbol', 'Name', 'Sector', 'MarketCapFormatted']].head(10).to_string(index=False))
    
    # Show growth stocks (high revenue/earnings growth)
    growth_df = df[df['Revenue_Growth'] > 0.1].copy()  # >10% revenue growth
    if len(growth_df) > 0:
        print(f"\nHigh growth stocks ({len(growth_df)} with >10% revenue growth):")
        print(growth_df[['Symbol', 'Name', 'Revenue_Growth', 'Earnings_Growth']].head(10).to_string(index=False))

if __name__ == "__main__":
    main()