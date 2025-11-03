"""
Technical Indicators API routes for testing and monitoring.

Provides endpoints to:
- Calculate indicators for a specific symbol
- Get cached indicator data
- Clear indicator cache
- View cache statistics
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import logging

from services.technical_indicators import technical_indicator_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/indicators", tags=["indicators"])


@router.get("/{symbol}")
async def get_indicators(
    symbol: str,
    force_refresh: bool = Query(False, description="Skip cache and recalculate indicators")
) -> Dict[str, Any]:
    """
    Get technical indicators for a symbol.

    Returns RSI, EMA, Bollinger Bands, ATR, and volume analysis with interpretations.

    Args:
        symbol: Trading symbol (e.g., 'BTC', 'ETH', 'SOL')
        force_refresh: Force recalculation (skip cache)

    Returns:
        Dictionary with all technical indicators and interpretations

    Example response:
        {
            "symbol": "BTC",
            "timeframe": "15m",
            "timestamp": "2025-11-03T12:30:00Z",
            "current_price": 95000.0,
            "rsi_14": 87.3,
            "rsi_signal": "EXTREMELY OVERBOUGHT ⚠️ (strong sell signal)",
            "ema_20": 88000.0,
            "ema_50": 85000.0,
            "ema_100": 80000.0,
            "ema_trend": "VERY STRONG UPTREND (price > EMA20 > EMA50 > EMA100) 🚀",
            "bb_upper": 92000.0,
            "bb_middle": 88000.0,
            "bb_lower": 84000.0,
            "bb_signal": "OVERBOUGHT (price at upper band)",
            "bb_width_pct": 8.5,
            "atr_14": 2450.0,
            "volume": 1250000000,
            "volume_ma_20": 950000000,
            "volume_spike": true,
            "data_points": 100
        }
    """
    try:
        logger.info(f"Fetching indicators for {symbol} (force_refresh={force_refresh})")
        indicators = technical_indicator_service.calculate_indicators(
            symbol=symbol,
            force_refresh=force_refresh
        )

        if indicators is None:
            raise HTTPException(
                status_code=404,
                detail=f"Unable to calculate indicators for {symbol}. Check if symbol exists and has sufficient historical data (50+ candles)."
            )

        return indicators

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching indicators for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/cache/info")
async def get_cache_info() -> Dict[str, Any]:
    """
    Get cache statistics for monitoring.

    Returns information about cached indicators including:
    - Total number of symbols in cache
    - Age of each cached entry
    - Time until cache expiration

    Example response:
        {
            "total_symbols": 3,
            "symbols": [
                {
                    "symbol": "BTC",
                    "age_seconds": 450.5,
                    "expires_in_seconds": 449.5
                },
                {
                    "symbol": "ETH",
                    "age_seconds": 120.2,
                    "expires_in_seconds": 779.8
                }
            ]
        }
    """
    try:
        cache_info = technical_indicator_service.get_cache_info()
        return cache_info
    except Exception as e:
        logger.error(f"Error getting cache info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.delete("/cache/clear")
async def clear_cache(
    symbol: Optional[str] = Query(None, description="Symbol to clear (or all if not specified)")
) -> Dict[str, str]:
    """
    Clear indicator cache.

    Args:
        symbol: Specific symbol to clear, or clear all if not provided

    Returns:
        Success message

    Examples:
        - DELETE /api/indicators/cache/clear?symbol=BTC → Clear BTC cache only
        - DELETE /api/indicators/cache/clear → Clear all caches
    """
    try:
        technical_indicator_service.clear_cache(symbol)

        if symbol:
            message = f"Cleared indicator cache for {symbol}"
        else:
            message = "Cleared all indicator caches"

        logger.info(message)
        return {"message": message, "status": "success"}

    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/batch")
async def get_indicators_batch(
    symbols: str = Query(..., description="Comma-separated list of symbols (e.g., 'BTC,ETH,SOL')"),
    force_refresh: bool = Query(False, description="Skip cache and recalculate indicators")
) -> Dict[str, Any]:
    """
    Get technical indicators for multiple symbols in a single request.

    Args:
        symbols: Comma-separated list of symbols (e.g., 'BTC,ETH,SOL')
        force_refresh: Force recalculation for all symbols

    Returns:
        Dictionary with indicators for each symbol

    Example response:
        {
            "BTC": { "rsi_14": 87.3, "ema_trend": "STRONG UPTREND", ... },
            "ETH": { "rsi_14": 34.2, "ema_trend": "OVERSOLD", ... },
            "SOL": { "rsi_14": 55.1, "ema_trend": "NEUTRAL", ... }
        }
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(',') if s.strip()]

        if not symbol_list:
            raise HTTPException(status_code=400, detail="No symbols provided")

        if len(symbol_list) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 symbols per request")

        results = {}
        errors = {}

        for symbol in symbol_list:
            try:
                indicators = technical_indicator_service.calculate_indicators(
                    symbol=symbol,
                    force_refresh=force_refresh
                )
                if indicators:
                    results[symbol] = indicators
                else:
                    errors[symbol] = "Insufficient data or symbol not found"
            except Exception as e:
                logger.error(f"Error calculating indicators for {symbol}: {e}")
                errors[symbol] = str(e)

        response = {"results": results}
        if errors:
            response["errors"] = errors

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch indicator request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
