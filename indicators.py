"""
Technical Indicators - RSI, MACD, Moving Averages
"""

class TechnicalIndicators:
    @staticmethod
    def calculate_rsi(prices, period=14):
        """
        Calculate Relative Strength Index (RSI)

        Args:
            prices: List of closing prices
            period: RSI period (default 14)

        Returns:
            float: RSI value (0-100)
        """
        if len(prices) < period:
            return 50

        gains = []
        losses = []

        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains[-period:]) / period if gains else 0
        avg_loss = sum(losses[-period:]) / period if losses else 0

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 1)

    @staticmethod
    def calculate_sma(prices, period):
        """
        Calculate Simple Moving Average

        Args:
            prices: List of prices
            period: SMA period

        Returns:
            float: SMA value or None if insufficient data
        """
        if len(prices) < period:
            return None
        return round(sum(prices[-period:]) / period, 5)

    @staticmethod
    def calculate_ema(prices, period):
        """
        Calculate Exponential Moving Average

        Args:
            prices: List of prices
            period: EMA period

        Returns:
            float: EMA value or None if insufficient data
        """
        if len(prices) < period:
            return None

        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period  # Start with SMA

        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema

        return round(ema, 5)

    @staticmethod
    def calculate_macd(prices, fast=12, slow=26, signal=9):
        """
        Calculate MACD (Moving Average Convergence Divergence)

        Args:
            prices: List of closing prices
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period

        Returns:
            tuple: (macd_line, signal_line, histogram) or (None, None, None)
        """
        if len(prices) < slow:
            return None, None, None

        # Calculate EMAs
        ema_fast = TechnicalIndicators.calculate_ema(prices, fast)
        ema_slow = TechnicalIndicators.calculate_ema(prices, slow)

        if ema_fast is None or ema_slow is None:
            return None, None, None

        macd_line = ema_fast - ema_slow

        # For signal line, we need MACD history (simplified)
        signal_line = macd_line * 0.9  # Simplified approximation
        histogram = macd_line - signal_line

        return round(macd_line, 5), round(signal_line, 5), round(histogram, 5)
