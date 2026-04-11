"""
Pair Scanner - Manage multiple pairs
"""

import config

class PairScanner:
    def __init__(self):
        self.scan_history = {}
    
    def get_all_pairs(self):
        return config.ALL_PAIRS
    
    def get_pairs_by_category(self, category):
        return config.ALL_INSTRUMENTS.get(category, [])
    
    def get_priority_pairs(self, limit=20):
        # Return most important pairs first
        priority = config.MAJOR_PAIRS + config.INDICES[:5] + config.COMMODITIES[:3] + config.CRYPTOS[:3]
        return priority[:limit]
