"""
Advanced Indicators - Bollinger Bands, Stochastic RSI, ATR
"""

import numpy as np

class AdvancedIndicators:
    @staticmethod
    def calculate_bollinger_bands(prices, period=20, std_dev=2):
        """
        Calculate Bollinger Bands

        Args:
            prices: List of closing prices
            period: SMA period (default 20)
            std_dev: Standard deviation multiplier (default 2)

        Returns:
            tuple: (upper_band, sma, lower_band) or (None, None, None) if insufficient data
        """
        if len(prices) < period:
            return None, None, None

        prices_array = np.array(prices[-period:])
        sma = np.mean(prices_array)
        std = np.std(prices_array)

        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)

        return round(upper, 5), round(sma, 5), round(lower, 5)

    @staticmethod
    def calculate_stochastic_rsi(prices, rsi_period=14, stoch_period=14):
        """
        Calculate Stochastic RSI

        Args:
            prices: List of closing prices
            rsi_period: Period for RSI calculation
            stoch_period: Period for Stochastic calculation

        Returns:
            tuple: (k_value, d_value) or (None, None) if insufficient data
        """
        from indicators import TechnicalIndicators

        if len(prices) < rsi_period + stoch_period:
            return None, None

        # Calculate RSI values
        rsi_values = []
        for i in range(rsi_period, len(prices) + 1):
            rsi = TechnicalIndicators.calculate_rsi(prices[:i], rsi_period)
            rsi_values.append(rsi)

        if len(rsi_values) < stoch_period:
            return None, None

        # Calculate Stochastic of RSI
        recent_rsi = rsi_values[-stoch_period:]
        min_rsi = min(recent_rsi)
        max_rsi = max(recent_rsi)
        current_rsi = recent_rsi[-1]

        if max_rsi - min_rsi == 0:
            k_value = 50
        else:
            k_value = 100 * (current_rsi - min_rsi) / (max_rsi - min_rsi)

        # %D is 3-period SMA of %K
        d_value = np.mean(rsi_values[-3:]) if len(rsi_values) >= 3 else k_value

        return round(k_value, 1), round(d_value, 1)

    @staticmethod
    def calculate_atr(prices, period=14):
        """
        Calculate Average True Range (volatility indicator)

        Args:
            prices: List of closing prices
            period: ATR period (default 14)

        Returns:
            float: ATR value or None if insufficient data
        """
        if len(prices) < period + 1:
            return None

        # Simplified ATR using closing price changes
        price_changes = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices))]

        if len(price_changes) < period:
            return None

        atr = np.mean(price_changes[-period:])
        return round(atr, 5)

    @staticmethod
    def calculate_momentum(prices, period=10):
        """
        Calculate price momentum

        Args:
            prices: List of closing prices
            period: Momentum period

        Returns:
            float: Momentum value or None if insufficient data
        """
        if len(prices) < period:
            return None

        current = prices[-1]
        previous = prices[-period]
        momentum = ((current - previous) / previous) * 100

        return round(momentum, 2)
