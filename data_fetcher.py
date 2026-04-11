"""
Data Fetcher - Fallback when Pocket Option WebSocket is disconnected
Provides prices from free APIs
"""

import requests
import logging

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self):
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 60  # Cache for 60 seconds

    def _is_cache_valid(self, key):
        """Check if cached data is still valid"""
        import time
        if key not in self.cache_time:
            return False
        return (time.time() - self.cache_time[key]) < self.cache_duration

    def get_price_eurusd(self):
        """Get EUR/USD price from free API (Frankfurter)"""
        cache_key = "EURUSD"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]

        try:
            url = "https://api.frankfurter.app/latest?from=EUR&to=USD"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                price = data['rates']['USD']
                self.cache[cache_key] = price
                self.cache_time[cache_key] = __import__('time').time()
                return price
        except Exception as e:
            logger.warning(f"Failed to fetch EURUSD: {e}")

        return 1.09234  # Fallback

    def get_price_gold(self):
        """Get Gold price from Yahoo Finance"""
        cache_key = "Gold"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]

        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                result = data.get('chart', {}).get('result', [])
                if result:
                    price = result[0].get('meta', {}).get('regularMarketPrice')
                    if price:
                        self.cache[cache_key] = price
                        self.cache_time[cache_key] = __import__('time').time()
                        return price
        except Exception as e:
            logger.warning(f"Failed to fetch Gold: {e}")

        return 2350.00  # Fallback

    def get_price_bitcoin(self):
        """Get Bitcoin price from CoinGecko"""
        cache_key = "Bitcoin"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]

        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                price = data['bitcoin']['usd']
                self.cache[cache_key] = price
                self.cache_time[cache_key] = __import__('time').time()
                return price
        except Exception as e:
            logger.warning(f"Failed to fetch Bitcoin: {e}")

        return 65000.00  # Fallback

    def get_price(self, pair):
        """Generic price fetcher with fallback"""
        pair_upper = pair.upper()

        # Map common pairs to fetchers
        if pair_upper in ["EURUSD", "EUR/USD"]:
            return self.get_price_eurusd()
        elif pair_upper in ["GOLD", "XAUUSD", "XAU/USD"]:
            return self.get_price_gold()
        elif pair_upper in ["BITCOIN", "BTC", "BTCUSD"]:
            return self.get_price_bitcoin()

        # Default fallback prices
        fallback_prices = {
            "GBPUSD": 1.28560,
            "USDJPY": 148.50,
            "SILVER": 28.50,
            "APPLE": 175.00,
            "TESLA": 240.00,
            "ETHEREUM": 3500.00,
        }

        return fallback_prices.get(pair_upper, 1.09234)
