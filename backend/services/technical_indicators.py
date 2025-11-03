"""
Technical indicator calculation service for AI trading decisions.

This service provides technical analysis indicators (RSI, EMA, Bollinger Bands, ATR, Volume)
for cryptocurrency trading. Indicators are calculated using pandas-ta library with
aggressive caching (15-minute TTL) to prevent API rate limits.

Features:
- RSI(14) - Relative Strength Index for overbought/oversold conditions
- EMA(20, 50, 100) - Exponential Moving Averages for trend identification
- Bollinger Bands(20, 2) - Volatility and price extremes
- ATR(14) - Average True Range for volatility measurement
- Volume Analysis - Volume spikes and trends

Author: Hyper Alpha Arena Team
"""

import pandas as pd
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from services.market_data import get_kline_data

logger = logging.getLogger(__name__)

# Import pandas_ta with fallback error handling
try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    logger.warning("pandas-ta not installed. Run: uv add pandas-ta")
    PANDAS_TA_AVAILABLE = False


class TechnicalIndicatorService:
    """
    Service for calculating technical indicators with caching.

    Uses 15-minute timeframe by default (good balance for crypto trading).
    Caches results for 15 minutes to prevent API rate limits and reduce latency.
    """

    def __init__(self, timeframe: str = '15m', lookback: int = 100, cache_ttl_minutes: int = 15):
        """
        Initialize the technical indicator service.

        Args:
            timeframe: Candlestick timeframe ('1m', '5m', '15m', '1h', '1d')
            lookback: Number of historical candles to fetch (default 100)
            cache_ttl_minutes: Cache time-to-live in minutes (default 15)
        """
        self.timeframe = timeframe
        self.lookback = lookback
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self._cache: Dict[str, Dict[str, Any]] = {}  # {symbol: {indicators, timestamp}}

        if not PANDAS_TA_AVAILABLE:
            logger.error("pandas-ta is required but not installed. Technical indicators will not work.")

    def calculate_indicators(self, symbol: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Calculate all technical indicators for a symbol.

        Args:
            symbol: Trading symbol (e.g., 'BTC', 'ETH', 'SOL')
            force_refresh: Skip cache and recalculate (default False)

        Returns:
            Dictionary with indicators and interpretations, or None if insufficient data

        Example return:
            {
                'symbol': 'BTC',
                'timeframe': '15m',
                'timestamp': '2025-11-03T12:30:00Z',
                'current_price': 95000.0,
                'rsi_14': 87.3,
                'rsi_signal': 'OVERBOUGHT (consider selling)',
                'ema_20': 88000.0,
                'ema_50': 85000.0,
                'ema_100': 80000.0,
                'ema_trend': 'STRONG UPTREND (price > EMA20 > EMA50 > EMA100)',
                'bb_upper': 92000.0,
                'bb_middle': 88000.0,
                'bb_lower': 84000.0,
                'bb_signal': 'OVERBOUGHT (price at upper band)',
                'bb_width_pct': 8.5,
                'atr_14': 2450.0,
                'volume': 1250000000,
                'volume_ma_20': 950000000,
                'volume_spike': True,
                'data_points': 100,
            }
        """
        if not PANDAS_TA_AVAILABLE:
            logger.error("pandas-ta not available. Cannot calculate indicators.")
            return None

        # Check cache first (unless force_refresh)
        if not force_refresh and symbol in self._cache:
            cached_data = self._cache[symbol]
            cache_age = datetime.now() - cached_data['cached_at']
            if cache_age < self.cache_ttl:
                logger.debug(f"Using cached indicators for {symbol} (age: {cache_age.total_seconds():.0f}s)")
                return cached_data['indicators']

        try:
            # Fetch OHLCV data from market data service
            logger.info(f"Fetching {self.lookback} {self.timeframe} candles for {symbol}...")
            klines = get_kline_data(symbol, period=self.timeframe, count=self.lookback)

            if not klines or len(klines) < 50:
                logger.warning(f"Insufficient data for {symbol}: only {len(klines) if klines else 0} candles (need 50+)")
                return None

            # Convert to pandas DataFrame
            df = pd.DataFrame(klines)

            # Ensure numeric types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # Drop any rows with NaN values
            df = df.dropna(subset=['open', 'high', 'low', 'close'])

            if len(df) < 50:
                logger.warning(f"Insufficient valid data for {symbol} after cleaning: {len(df)} rows")
                return None

            logger.info(f"Calculating indicators for {symbol} using {len(df)} candles...")

            # Initialize indicators dictionary
            indicators = {
                'symbol': symbol,
                'timeframe': self.timeframe,
                'timestamp': datetime.now().isoformat(),
                'current_price': float(df['close'].iloc[-1]),
                'data_points': len(df),
            }

            # Calculate RSI(14)
            try:
                rsi = ta.rsi(df['close'], length=14)
                if rsi is not None and not rsi.empty and not pd.isna(rsi.iloc[-1]):
                    indicators['rsi_14'] = float(rsi.iloc[-1])
                    indicators['rsi_signal'] = self._interpret_rsi(indicators['rsi_14'])
                else:
                    indicators['rsi_14'] = None
                    indicators['rsi_signal'] = 'N/A'
            except Exception as e:
                logger.error(f"Error calculating RSI for {symbol}: {e}")
                indicators['rsi_14'] = None
                indicators['rsi_signal'] = 'ERROR'

            # Calculate EMA(20, 50, 100)
            try:
                ema20 = ta.ema(df['close'], length=20)
                ema50 = ta.ema(df['close'], length=50)
                ema100 = ta.ema(df['close'], length=100)

                indicators['ema_20'] = float(ema20.iloc[-1]) if ema20 is not None and not ema20.empty and not pd.isna(ema20.iloc[-1]) else None
                indicators['ema_50'] = float(ema50.iloc[-1]) if ema50 is not None and not ema50.empty and not pd.isna(ema50.iloc[-1]) else None
                indicators['ema_100'] = float(ema100.iloc[-1]) if ema100 is not None and not ema100.empty and not pd.isna(ema100.iloc[-1]) else None

                indicators['ema_trend'] = self._interpret_ema_trend(
                    indicators['current_price'],
                    indicators['ema_20'],
                    indicators['ema_50'],
                    indicators['ema_100']
                )
            except Exception as e:
                logger.error(f"Error calculating EMA for {symbol}: {e}")
                indicators['ema_20'] = None
                indicators['ema_50'] = None
                indicators['ema_100'] = None
                indicators['ema_trend'] = 'ERROR'

            # Calculate Bollinger Bands(20, 2)
            try:
                bb = ta.bbands(df['close'], length=20, std=2)
                if bb is not None and not bb.empty:
                    # pandas-ta column naming: BBL_length_std, BBM_length_std, BBU_length_std
                    # Find the columns dynamically to handle different pandas-ta versions
                    bb_cols = bb.columns.tolist()

                    # Look for upper, middle, lower band columns
                    upper_col = next((col for col in bb_cols if col.startswith('BBU_')), None)
                    middle_col = next((col for col in bb_cols if col.startswith('BBM_')), None)
                    lower_col = next((col for col in bb_cols if col.startswith('BBL_')), None)

                    if upper_col and middle_col and lower_col:
                        indicators['bb_upper'] = float(bb[upper_col].iloc[-1]) if not pd.isna(bb[upper_col].iloc[-1]) else None
                        indicators['bb_middle'] = float(bb[middle_col].iloc[-1]) if not pd.isna(bb[middle_col].iloc[-1]) else None
                        indicators['bb_lower'] = float(bb[lower_col].iloc[-1]) if not pd.isna(bb[lower_col].iloc[-1]) else None

                        # Calculate Bollinger Band Width as percentage
                        if indicators['bb_upper'] and indicators['bb_lower'] and indicators['bb_middle']:
                            bb_width = indicators['bb_upper'] - indicators['bb_lower']
                            indicators['bb_width_pct'] = (bb_width / indicators['bb_middle']) * 100

                            indicators['bb_signal'] = self._interpret_bollinger(
                                indicators['current_price'],
                                indicators['bb_upper'],
                                indicators['bb_middle'],
                                indicators['bb_lower']
                            )
                        else:
                            indicators['bb_width_pct'] = None
                            indicators['bb_signal'] = 'N/A'
                    else:
                        logger.warning(f"Bollinger Bands columns not found for {symbol}. Available: {bb_cols}")
                        indicators['bb_upper'] = None
                        indicators['bb_middle'] = None
                        indicators['bb_lower'] = None
                        indicators['bb_width_pct'] = None
                        indicators['bb_signal'] = 'N/A'
                else:
                    indicators['bb_upper'] = None
                    indicators['bb_middle'] = None
                    indicators['bb_lower'] = None
                    indicators['bb_width_pct'] = None
                    indicators['bb_signal'] = 'N/A'
            except Exception as e:
                logger.error(f"Error calculating Bollinger Bands for {symbol}: {e}")
                indicators['bb_upper'] = None
                indicators['bb_middle'] = None
                indicators['bb_lower'] = None
                indicators['bb_width_pct'] = None
                indicators['bb_signal'] = 'ERROR'

            # Calculate ATR(14)
            try:
                atr = ta.atr(df['high'], df['low'], df['close'], length=14)
                indicators['atr_14'] = float(atr.iloc[-1]) if atr is not None and not atr.empty and not pd.isna(atr.iloc[-1]) else None
            except Exception as e:
                logger.error(f"Error calculating ATR for {symbol}: {e}")
                indicators['atr_14'] = None

            # Volume Analysis
            try:
                vol_ma = df['volume'].rolling(window=20).mean()
                indicators['volume'] = float(df['volume'].iloc[-1]) if not pd.isna(df['volume'].iloc[-1]) else None
                indicators['volume_ma_20'] = float(vol_ma.iloc[-1]) if not pd.isna(vol_ma.iloc[-1]) else None

                # Detect volume spike (>1.5x average)
                if indicators['volume'] and indicators['volume_ma_20'] and indicators['volume_ma_20'] > 0:
                    indicators['volume_spike'] = indicators['volume'] > (indicators['volume_ma_20'] * 1.5)
                else:
                    indicators['volume_spike'] = False
            except Exception as e:
                logger.error(f"Error calculating volume metrics for {symbol}: {e}")
                indicators['volume'] = None
                indicators['volume_ma_20'] = None
                indicators['volume_spike'] = False

            # Cache the results
            self._cache[symbol] = {
                'indicators': indicators,
                'cached_at': datetime.now()
            }

            logger.info(f"Successfully calculated indicators for {symbol}: RSI={indicators.get('rsi_14', 'N/A')}, "
                       f"Price vs EMA20={indicators.get('current_price', 0) - indicators.get('ema_20', 0):.2f}")

            return indicators

        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol}: {e}", exc_info=True)
            return None

    def _interpret_rsi(self, rsi: Optional[float]) -> str:
        """
        Interpret RSI value and return trading signal.

        RSI ranges from 0-100:
        - Above 70: Overbought (potential sell signal)
        - Below 30: Oversold (potential buy signal)
        - 50-70: Bullish momentum
        - 30-50: Bearish momentum
        """
        if rsi is None:
            return "N/A"

        if rsi >= 80:
            return "EXTREMELY OVERBOUGHT ⚠️ (strong sell signal)"
        elif rsi >= 70:
            return "OVERBOUGHT (consider selling or taking profit)"
        elif rsi >= 60:
            return "BULLISH MOMENTUM (uptrend continuing)"
        elif rsi >= 40:
            return "NEUTRAL (no clear signal)"
        elif rsi >= 30:
            return "BEARISH MOMENTUM (downtrend continuing)"
        elif rsi >= 20:
            return "OVERSOLD (consider buying)"
        else:
            return "EXTREMELY OVERSOLD ✅ (strong buy signal)"

    def _interpret_ema_trend(
        self,
        price: float,
        ema20: Optional[float],
        ema50: Optional[float],
        ema100: Optional[float]
    ) -> str:
        """
        Interpret EMA crossover and trend strength.

        Trend hierarchy:
        1. Price > EMA20 > EMA50 > EMA100 = Strong uptrend
        2. Price > EMA20 > EMA50 = Moderate uptrend
        3. Price > EMA20 but EMA20 < EMA50 = Early bullish reversal
        4. Price < EMA20 < EMA50 < EMA100 = Strong downtrend
        5. Price < EMA20 < EMA50 = Moderate downtrend
        6. Price < EMA20 but EMA20 > EMA50 = Early bearish reversal
        """
        if ema20 is None:
            return "N/A (insufficient data)"

        # Calculate price position relative to EMAs
        above_ema20 = price > ema20

        if ema50 is None:
            if above_ema20:
                return "ABOVE EMA20 (short-term bullish)"
            else:
                return "BELOW EMA20 (short-term bearish)"

        above_ema50 = price > ema50
        ema20_above_ema50 = ema20 > ema50

        if ema100 is None:
            # Two EMA analysis
            if above_ema20 and above_ema50 and ema20_above_ema50:
                return "STRONG UPTREND (price > EMA20 > EMA50)"
            elif above_ema20 and ema20_above_ema50:
                return "UPTREND (price > EMA20 > EMA50)"
            elif above_ema20 and not ema20_above_ema50:
                return "POTENTIAL BULLISH REVERSAL (price > EMA20 but EMA20 < EMA50)"
            elif not above_ema20 and not ema20_above_ema50:
                return "STRONG DOWNTREND (price < EMA20 < EMA50)"
            elif not above_ema20 and ema20_above_ema50:
                return "POTENTIAL BEARISH REVERSAL (price < EMA20 but EMA20 > EMA50)"
            else:
                return "CONSOLIDATION (mixed signals)"

        # Three EMA analysis
        ema50_above_ema100 = ema50 > ema100

        if above_ema20 and ema20_above_ema50 and ema50_above_ema100:
            return "VERY STRONG UPTREND (price > EMA20 > EMA50 > EMA100) 🚀"
        elif above_ema20 and ema20_above_ema50:
            return "UPTREND (price > EMA20 > EMA50)"
        elif above_ema20 and not ema20_above_ema50:
            return "EARLY BULLISH REVERSAL (price > EMA20 but EMA20 < EMA50)"
        elif not above_ema20 and not ema20_above_ema50 and not ema50_above_ema100:
            return "VERY STRONG DOWNTREND (price < EMA20 < EMA50 < EMA100) 📉"
        elif not above_ema20 and not ema20_above_ema50:
            return "DOWNTREND (price < EMA20 < EMA50)"
        elif not above_ema20 and ema20_above_ema50:
            return "EARLY BEARISH REVERSAL (price < EMA20 but EMA20 > EMA50)"
        else:
            return "CONSOLIDATION (choppy, no clear trend)"

    def _interpret_bollinger(
        self,
        price: float,
        upper: Optional[float],
        middle: Optional[float],
        lower: Optional[float]
    ) -> str:
        """
        Interpret Bollinger Band position.

        - Price at/above upper band: Overbought, potential reversal
        - Price at/below lower band: Oversold, potential bounce
        - Price at middle band: Neutral, mean reversion point
        - Outside bands: Extreme move, likely unsustainable
        """
        if upper is None or middle is None or lower is None:
            return "N/A"

        # Calculate percentage position within bands
        band_range = upper - lower
        if band_range == 0:
            return "BANDS COLLAPSED (no volatility)"

        position_pct = ((price - lower) / band_range) * 100

        if price > upper:
            distance = ((price - upper) / middle) * 100
            return f"ABOVE UPPER BAND ⚠️ (+{distance:.1f}% extended, overbought)"
        elif position_pct >= 90:
            return "AT UPPER BAND (overbought, consider taking profit)"
        elif position_pct >= 60:
            return "ABOVE MIDDLE (bullish bias, room to run)"
        elif position_pct >= 40:
            return "AT MIDDLE BAND (neutral, mean reversion point)"
        elif position_pct >= 10:
            return "BELOW MIDDLE (bearish bias, potential support)"
        elif price < lower:
            distance = ((lower - price) / middle) * 100
            return f"BELOW LOWER BAND ✅ (-{distance:.1f}% extended, oversold)"
        else:
            return "AT LOWER BAND (oversold, potential bounce)"

    def clear_cache(self, symbol: Optional[str] = None):
        """
        Clear cached indicators.

        Args:
            symbol: Clear specific symbol, or all if None
        """
        if symbol:
            if symbol in self._cache:
                del self._cache[symbol]
                logger.info(f"Cleared indicator cache for {symbol}")
        else:
            self._cache.clear()
            logger.info("Cleared all indicator caches")

    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        now = datetime.now()
        cache_info = {
            'total_symbols': len(self._cache),
            'symbols': []
        }

        for symbol, data in self._cache.items():
            age = now - data['cached_at']
            cache_info['symbols'].append({
                'symbol': symbol,
                'age_seconds': age.total_seconds(),
                'expires_in_seconds': (self.cache_ttl - age).total_seconds(),
            })

        return cache_info


# Global instance with sensible defaults
# - 15-minute timeframe (good balance for crypto)
# - 100 candles lookback (enough for EMA100)
# - 15-minute cache TTL (matches timeframe)
technical_indicator_service = TechnicalIndicatorService(
    timeframe='15m',
    lookback=100,
    cache_ttl_minutes=15
)
