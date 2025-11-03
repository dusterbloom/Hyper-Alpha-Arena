"""
Unit tests for technical indicators service.

Tests indicator calculation, interpretation, and caching functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd

from services.technical_indicators import TechnicalIndicatorService


class TestTechnicalIndicatorInterpretation:
    """Test indicator interpretation methods"""

    def setup_method(self):
        """Setup test service instance"""
        self.service = TechnicalIndicatorService(timeframe='15m', lookback=100, cache_ttl_minutes=15)

    def test_interpret_rsi_extremely_overbought(self):
        """Test RSI interpretation for extremely overbought conditions (>80)"""
        result = self.service._interpret_rsi(85.0)
        assert "EXTREMELY OVERBOUGHT" in result
        assert "sell" in result.lower()

    def test_interpret_rsi_overbought(self):
        """Test RSI interpretation for overbought conditions (70-80)"""
        result = self.service._interpret_rsi(75.0)
        assert "OVERBOUGHT" in result
        assert "sell" in result.lower() or "profit" in result.lower()

    def test_interpret_rsi_bullish_momentum(self):
        """Test RSI interpretation for bullish momentum (60-70)"""
        result = self.service._interpret_rsi(65.0)
        assert "BULLISH MOMENTUM" in result

    def test_interpret_rsi_neutral(self):
        """Test RSI interpretation for neutral range (40-60)"""
        result = self.service._interpret_rsi(50.0)
        assert "NEUTRAL" in result

    def test_interpret_rsi_bearish_momentum(self):
        """Test RSI interpretation for bearish momentum (30-40)"""
        result = self.service._interpret_rsi(35.0)
        assert "BEARISH MOMENTUM" in result

    def test_interpret_rsi_oversold(self):
        """Test RSI interpretation for oversold conditions (20-30)"""
        result = self.service._interpret_rsi(25.0)
        assert "OVERSOLD" in result
        assert "buy" in result.lower()

    def test_interpret_rsi_extremely_oversold(self):
        """Test RSI interpretation for extremely oversold conditions (<20)"""
        result = self.service._interpret_rsi(15.0)
        assert "EXTREMELY OVERSOLD" in result
        assert "buy" in result.lower()

    def test_interpret_rsi_none(self):
        """Test RSI interpretation with None value"""
        result = self.service._interpret_rsi(None)
        assert result == "N/A"

    def test_interpret_ema_strong_uptrend(self):
        """Test EMA interpretation for strong uptrend (price > EMA20 > EMA50 > EMA100)"""
        result = self.service._interpret_ema_trend(
            price=100.0,
            ema20=95.0,
            ema50=90.0,
            ema100=85.0
        )
        assert "VERY STRONG UPTREND" in result or "STRONG UPTREND" in result

    def test_interpret_ema_strong_downtrend(self):
        """Test EMA interpretation for strong downtrend (price < EMA20 < EMA50 < EMA100)"""
        result = self.service._interpret_ema_trend(
            price=80.0,
            ema20=85.0,
            ema50=90.0,
            ema100=95.0
        )
        assert "DOWNTREND" in result

    def test_interpret_ema_bullish_reversal(self):
        """Test EMA interpretation for potential bullish reversal"""
        result = self.service._interpret_ema_trend(
            price=92.0,
            ema20=90.0,
            ema50=95.0,
            ema100=100.0
        )
        assert "BULLISH" in result or "UPTREND" in result

    def test_interpret_ema_none_values(self):
        """Test EMA interpretation with None values"""
        result = self.service._interpret_ema_trend(
            price=100.0,
            ema20=None,
            ema50=None,
            ema100=None
        )
        assert "N/A" in result or "insufficient" in result.lower()

    def test_interpret_bollinger_above_upper(self):
        """Test Bollinger Band interpretation when price is above upper band"""
        result = self.service._interpret_bollinger(
            price=105.0,
            upper=100.0,
            middle=90.0,
            lower=80.0
        )
        assert "ABOVE UPPER BAND" in result
        assert "overbought" in result.lower()

    def test_interpret_bollinger_at_upper(self):
        """Test Bollinger Band interpretation when price is at upper band"""
        result = self.service._interpret_bollinger(
            price=99.0,
            upper=100.0,
            middle=90.0,
            lower=80.0
        )
        assert "UPPER BAND" in result or "ABOVE MIDDLE" in result

    def test_interpret_bollinger_at_middle(self):
        """Test Bollinger Band interpretation when price is at middle band"""
        result = self.service._interpret_bollinger(
            price=90.0,
            upper=100.0,
            middle=90.0,
            lower=80.0
        )
        assert "MIDDLE" in result

    def test_interpret_bollinger_at_lower(self):
        """Test Bollinger Band interpretation when price is at lower band"""
        result = self.service._interpret_bollinger(
            price=81.0,
            upper=100.0,
            middle=90.0,
            lower=80.0
        )
        assert "LOWER BAND" in result or "BELOW MIDDLE" in result

    def test_interpret_bollinger_below_lower(self):
        """Test Bollinger Band interpretation when price is below lower band"""
        result = self.service._interpret_bollinger(
            price=75.0,
            upper=100.0,
            middle=90.0,
            lower=80.0
        )
        assert "BELOW LOWER BAND" in result
        assert "oversold" in result.lower()

    def test_interpret_bollinger_none_values(self):
        """Test Bollinger Band interpretation with None values"""
        result = self.service._interpret_bollinger(
            price=100.0,
            upper=None,
            middle=None,
            lower=None
        )
        assert result == "N/A"


class TestTechnicalIndicatorCaching:
    """Test indicator caching functionality"""

    def setup_method(self):
        """Setup test service instance with short cache TTL"""
        self.service = TechnicalIndicatorService(timeframe='15m', lookback=100, cache_ttl_minutes=1)

    def test_cache_clear_specific_symbol(self):
        """Test clearing cache for specific symbol"""
        # Manually add to cache
        self.service._cache['BTC'] = {
            'indicators': {'rsi_14': 50.0},
            'cached_at': datetime.now()
        }
        self.service._cache['ETH'] = {
            'indicators': {'rsi_14': 60.0},
            'cached_at': datetime.now()
        }

        # Clear BTC only
        self.service.clear_cache('BTC')

        assert 'BTC' not in self.service._cache
        assert 'ETH' in self.service._cache

    def test_cache_clear_all(self):
        """Test clearing all cache"""
        # Manually add to cache
        self.service._cache['BTC'] = {
            'indicators': {'rsi_14': 50.0},
            'cached_at': datetime.now()
        }
        self.service._cache['ETH'] = {
            'indicators': {'rsi_14': 60.0},
            'cached_at': datetime.now()
        }

        # Clear all
        self.service.clear_cache()

        assert len(self.service._cache) == 0

    def test_cache_info(self):
        """Test cache info retrieval"""
        # Manually add to cache
        now = datetime.now()
        self.service._cache['BTC'] = {
            'indicators': {'rsi_14': 50.0},
            'cached_at': now - timedelta(seconds=30)
        }

        cache_info = self.service.get_cache_info()

        assert cache_info['total_symbols'] == 1
        assert len(cache_info['symbols']) == 1
        assert cache_info['symbols'][0]['symbol'] == 'BTC'
        assert cache_info['symbols'][0]['age_seconds'] >= 30

    def test_cache_expiration(self):
        """Test that cache expires after TTL"""
        # Create service with very short TTL (1 second for testing)
        service = TechnicalIndicatorService(timeframe='15m', lookback=100, cache_ttl_minutes=0.016)  # ~1 second

        # Manually add expired cache entry
        expired_time = datetime.now() - timedelta(seconds=2)
        service._cache['BTC'] = {
            'indicators': {'rsi_14': 50.0},
            'cached_at': expired_time
        }

        # Mock get_kline_data to avoid actual API call
        with patch('services.technical_indicators.get_kline_data') as mock_kline:
            mock_kline.return_value = None  # Will return None (insufficient data)

            # Should not use cache (expired)
            result = service.calculate_indicators('BTC', force_refresh=False)

            # get_kline_data should be called (cache expired)
            assert mock_kline.called


class TestTechnicalIndicatorCalculation:
    """Test indicator calculation with mocked data"""

    def setup_method(self):
        """Setup test service instance"""
        self.service = TechnicalIndicatorService(timeframe='15m', lookback=100, cache_ttl_minutes=15)

    def test_calculate_indicators_insufficient_data(self):
        """Test that insufficient data returns None"""
        with patch('services.technical_indicators.get_kline_data') as mock_kline:
            # Return only 30 candles (need 50+)
            mock_kline.return_value = [
                {'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000}
                for _ in range(30)
            ]

            result = self.service.calculate_indicators('BTC')

            assert result is None

    def test_calculate_indicators_no_data(self):
        """Test that no data returns None"""
        with patch('services.technical_indicators.get_kline_data') as mock_kline:
            mock_kline.return_value = []

            result = self.service.calculate_indicators('BTC')

            assert result is None

    def test_calculate_indicators_force_refresh(self):
        """Test force refresh bypasses cache"""
        # Add to cache
        self.service._cache['BTC'] = {
            'indicators': {'rsi_14': 50.0, 'symbol': 'BTC'},
            'cached_at': datetime.now()
        }

        with patch('services.technical_indicators.get_kline_data') as mock_kline:
            mock_kline.return_value = None  # Will fail

            # Should call get_kline_data (not use cache)
            result = self.service.calculate_indicators('BTC', force_refresh=True)

            assert mock_kline.called


class TestTechnicalIndicatorServiceInitialization:
    """Test service initialization and configuration"""

    def test_default_initialization(self):
        """Test service initializes with default values"""
        service = TechnicalIndicatorService()

        assert service.timeframe == '15m'
        assert service.lookback == 100
        assert service.cache_ttl == timedelta(minutes=15)
        assert service._cache == {}

    def test_custom_initialization(self):
        """Test service initializes with custom values"""
        service = TechnicalIndicatorService(
            timeframe='1h',
            lookback=200,
            cache_ttl_minutes=30
        )

        assert service.timeframe == '1h'
        assert service.lookback == 200
        assert service.cache_ttl == timedelta(minutes=30)

    def test_pandas_ta_not_available(self):
        """Test service handles missing pandas-ta gracefully"""
        with patch('services.technical_indicators.PANDAS_TA_AVAILABLE', False):
            service = TechnicalIndicatorService()

            result = service.calculate_indicators('BTC')

            assert result is None


# Integration test marker for tests that require actual market data
@pytest.mark.integration
class TestTechnicalIndicatorIntegration:
    """Integration tests requiring actual market data (run separately)"""

    def setup_method(self):
        """Setup test service instance"""
        self.service = TechnicalIndicatorService(timeframe='15m', lookback=100, cache_ttl_minutes=15)

    @pytest.mark.skip(reason="Requires actual market data API")
    def test_calculate_real_indicators_btc(self):
        """Test calculating real indicators for BTC (requires API access)"""
        result = self.service.calculate_indicators('BTC')

        assert result is not None
        assert result['symbol'] == 'BTC'
        assert 'rsi_14' in result
        assert 'ema_20' in result
        assert 'bb_upper' in result
        assert 'atr_14' in result
        assert 'volume' in result

    @pytest.mark.skip(reason="Requires actual market data API")
    def test_calculate_real_indicators_eth(self):
        """Test calculating real indicators for ETH (requires API access)"""
        result = self.service.calculate_indicators('ETH')

        assert result is not None
        assert result['symbol'] == 'ETH'
