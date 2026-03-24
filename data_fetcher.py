"""
Alpha Vantage Data Fetcher
Gets forex market data from Alpha Vantage API
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import time

class AlphaVantageFetcher:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.call_count = 0
        self.minute_start = datetime.now()
        print(f"📊 Alpha Vantage fetcher initialized")
    
    def _check_rate_limit(self):
        current_time = datetime.now()
        
        if current_time - self.minute_start >= timedelta(minutes=1):
            self.call_count = 0
            self.minute_start = current_time
        
        if self.call_count >= 5:
            wait_time = 60 - (current_time - self.minute_start).seconds
            if wait_time > 0:
                print(f"⏳ Rate limit reached. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                self.call_count = 0
                self.minute_start = datetime.now()
        
        self.call_count += 1
    
    def fetch_forex_data(self, pair, interval="5min", output_size="compact"):
        print(f"🔍 Fetching {pair} ({interval})...")
        
        self._check_rate_limit()
        
        from_currency = pair[:3]
        to_currency = pair[3:]
        
        if interval == "daily":
            params = {
                'function': 'FX_DAILY',
                'from_symbol': from_currency,
                'to_symbol': to_currency,
                'outputsize': output_size,
                'apikey': self.api_key
            }
        else:
            params = {
                'function': 'FX_INTRADAY',
                'from_symbol': from_currency,
                'to_symbol': to_currency,
                'interval': interval,
                'outputsize': output_size,
                'apikey': self.api_key
            }
        
        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if "Error Message" in data:
                print(f"❌ API Error: {data['Error Message']}")
                return None
            
            if "Note" in data:
                print(f"⚠️ API Limit Note: {data['Note']}")
                return None
            
            if interval == "daily":
                time_series_key = "Time Series FX (Daily)"
            else:
                time_series_key = f"Time Series FX ({interval})"
            
            if time_series_key not in data:
                print(f"❌ No data found for {pair} at {interval}")
                return None
            
            df = pd.DataFrame.from_dict(data[time_series_key], orient='index')
            
            df = df.rename(columns={
                '1. open': 'open',
                '2. high': 'high',
                '3. low': 'low',
                '4. close': 'close'
            })
            
            df = df[['open', 'high', 'low', 'close']].astype(float)
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            print(f"✅ Successfully fetched {len(df)} candles for {pair}")
            return df
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

if __name__ == "__main__":
    print("Testing Alpha Vantage data fetcher...")
    
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    
    if not api_key or api_key == "your_alpha_vantage_api_key_here":
        print("❌ Please set your ALPHA_VANTAGE_API_KEY in the .env file")
    else:
        fetcher = AlphaVantageFetcher(api_key)
        df = fetcher.fetch_forex_data("EURUSD", "5min")
        
        if df is not None:
            print("\n📈 First few rows of data:")
            print(df.head())