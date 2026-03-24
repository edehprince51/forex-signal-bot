"""
Efficient Pair Scanner - Handles large number of currency pairs
"""

import time
import pandas as pd
from datetime import datetime

class PairScanner:
    def __init__(self, data_fetcher, signal_generator, telegram):
        self.data_fetcher = data_fetcher
        self.signal_generator = signal_generator
        self.telegram = telegram
        self.scan_history = {}
        
    def scan_all_pairs(self, pairs, timeframes):
        """Efficiently scan all pairs across timeframes"""
        signals_found = []
        total_pairs = len(pairs)
        
        print(f"\n📊 Scanning {total_pairs} pairs across {len(timeframes)} timeframes")
        
        for timeframe_name, interval in timeframes.items():
            print(f"\n⏰ Scanning {timeframe_name} timeframe...")
            
            for i, pair in enumerate(pairs):
                # Progress indicator
                if (i + 1) % 10 == 0:
                    print(f"  Progress: {i+1}/{total_pairs} pairs scanned")
                
                # Skip if we scanned this pair recently
                if self._should_skip_pair(pair, timeframe_name):
                    continue
                
                df = self.data_fetcher.fetch_forex_data(pair, interval)
                
                if df is not None:
                    signal = self.signal_generator.analyze_pair(df, pair, timeframe_name)
                    
                    if signal:
                        signals_found.append(signal)
                        message = self.signal_generator.format_professional_signal(signal)
                        self.telegram.send_message(message)
                        time.sleep(1)  # Small delay between signals
                
                # Rate limiting
                time.sleep(0.5)
        
        return signals_found
    
    def _should_skip_pair(self, pair, timeframe):
        """Skip pairs that were scanned recently to save API calls"""
        key = f"{pair}_{timeframe}"
        last_scan = self.scan_history.get(key)
        
        if last_scan:
            time_since = (datetime.now() - last_scan).seconds
            # Skip if scanned in last 2 minutes
            if time_since < 120:
                return True
        
        self.scan_history[key] = datetime.now()
        return False
    
    def get_priority_pairs(self, pairs):
        """Return pairs sorted by priority (majors first)"""
        # Priority order: Majors > Minors > Exotics > Commodities
        priority_order = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
        
        prioritized = []
        for p in priority_order:
            if p in pairs:
                prioritized.append(p)
                pairs.remove(p)
        
        return prioritized + pairs