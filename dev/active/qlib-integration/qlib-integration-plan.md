# Qlib Integration Plan
**Strategic Implementation Plan for Microsoft Qlib Integration**

**Document Version**: 1.0
**Created**: 2025-11-03
**Status**: Planning (Not Started)
**Prerequisites**: Hyperliquid Phases 4-8 Complete
**Estimated Start**: Week 9 (Post-Hyperliquid)

---

## Executive Summary

### What is Qlib?

Microsoft Qlib is an AI-oriented quantitative investment platform designed for professional algorithmic trading research. It provides:
- 40+ state-of-the-art ML models (LightGBM, LSTM, Transformer, etc.)
- Professional-grade backtesting with transaction costs and market impact
- Advanced feature engineering (200+ technical indicators)
- Portfolio optimization algorithms
- Point-in-time database for historical accuracy

### Integration Recommendation

**SELECTIVE INTEGRATION** - Use qlib as a **toolbox**, not a framework.

**Integrate**:
- ✅ Feature Engineering (technical indicators for LLM context)
- ✅ Backtesting Engine (historical validation infrastructure)

**Skip**:
- ❌ Full ML model integration (conflicts with LLM-first philosophy)
- ❌ Portfolio optimization (reduces LLM autonomy)
- ❌ RD-Agent (competes with LLM approach)

### Strategic Rationale

Qlib enhances Hyper Alpha Arena's core mission (LLM trading competition) by:
1. **Better Input → Better Decisions**: Professional technical indicators improve LLM decision quality
2. **Credibility**: Academic-grade backtesting ("Powered by Microsoft Research")
3. **Research Value**: Historical validation before live trading reduces risk
4. **Institutional Appeal**: Professional infrastructure attracts serious users

### Complexity Assessment

- **Effort**: 12-16 weeks (spread across 3 phases)
- **Risk**: Medium-High (architectural changes required)
- **Team Size**: 1.5 FTE average
- **Budget**: ~$50k (labor only, no infrastructure costs)

---

## Phase 1: Feature Engineering Pilot

**Duration**: 2-3 weeks
**Effort**: 1.0 FTE
**Risk**: LOW
**Priority**: ⭐⭐⭐⭐⭐

### Objective

Prove that qlib-powered technical indicators improve LLM decision quality without breaking existing systems.

### Current State Problem

**Current Prompt Context** (`ai_decision_service.py`):
```python
# Simple momentum calculation
change_pct = ((last_price - first_price) / first_price) * 100
trend = "BULLISH" if change_pct > 0 else "BEARISH"

# Prompt context
f"BTC momentum: {change_pct:.2f}% ({trend})"
```

**Issue**: Oversimplified analysis. LLMs need richer context for informed decisions.

### Target State Solution

**Enhanced Prompt Context with Qlib**:
```
=== TECHNICAL INDICATORS (BTC) ===
Momentum & Trend:
  - Price Change (5min): +2.3%
  - RSI (14-period): 67.2 (approaching overbought)
  - MACD Signal: Bullish crossover detected
  - Moving Average (20): $63,150 (price above MA → bullish)

Volatility:
  - ATR (14-period): $1,240 (high volatility)
  - Bollinger Bands: Price at upper band (+1.8σ)
  - Standard Deviation (30min): 0.024 (2.4%)

Volume Analysis:
  - Volume Surge: 1.8x (above 20-period average)
  - VWAP: $63,050 (current price above VWAP → bullish)

Support & Resistance:
  - Support Level (20-period low): $62,450
  - Resistance Level (20-period high): $64,800
  - Distance to Support: -1.2% | Distance to Resistance: +2.6%
```

### Implementation Tasks

#### Task 1.1: Install Qlib and Dependencies (2-4 hours)

**Files Modified**: `backend/pyproject.toml`

```toml
[project.dependencies]
pyqlib = "^0.9.6"
lightgbm = "^4.5.0"
torch-cpu = "^2.0.0"  # CPU-only to minimize image size
```

**Acceptance Criteria**:
- [ ] `uv add pyqlib lightgbm` succeeds
- [ ] Docker image size < 1GB (check with `docker images`)
- [ ] Import test: `python -c "import qlib; print(qlib.__version__)"` works

**Risks**:
- Dependency bloat: PyTorch adds 200-800MB
- Mitigation: Use `torch-cpu` wheel (200MB instead of 800MB)

---

#### Task 1.2: Create QlibFeatureEngine Wrapper (4-6 hours)

**New File**: `backend/services/qlib_feature_engine.py`

**Class Design**:
```python
from qlib.data import D
from qlib.data.dataset import DataHandlerLP
from typing import Dict, List
import pandas as pd

class QlibFeatureEngine:
    """Wrapper around qlib for calculating technical indicators"""

    def __init__(self):
        """Initialize qlib with in-memory data handler"""
        self.indicators = self._define_indicators()

    def _define_indicators(self) -> Dict[str, str]:
        """Define qlib expressions for technical indicators"""
        return {
            # Momentum
            "rsi_14": "RSI($close, 14)",
            "momentum_5min": "Ref($close, 5) / $close - 1",
            "ma_20": "Mean($close, 20)",

            # Volatility
            "atr_14": "ATR($high, $low, $close, 14)",
            "std_30": "Std($close, 30)",
            "bollinger_upper": "Mean($close, 20) + 2 * Std($close, 20)",
            "bollinger_lower": "Mean($close, 20) - 2 * Std($close, 20)",

            # Volume
            "volume_surge": "$volume / Mean($volume, 20)",
            "vwap": "Sum($close * $volume, 20) / Sum($volume, 20)",

            # Support/Resistance
            "support_20": "Min($low, 20)",
            "resistance_20": "Max($high, 20)",
        }

    def convert_ccxt_to_qlib(self, ohlcv_data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Convert CCXT OHLCV data to qlib format

        Args:
            ohlcv_data: DataFrame with columns [timestamp, open, high, low, close, volume]
            symbol: Crypto symbol (e.g., 'BTC')

        Returns:
            DataFrame in qlib format (datetime index, OHLCV columns)
        """
        df = ohlcv_data.copy()
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.set_index('datetime')
        df = df.rename(columns={
            'open': '$open',
            'high': '$high',
            'low': '$low',
            'close': '$close',
            'volume': '$volume'
        })
        return df[['$open', '$high', '$low', '$close', '$volume']]

    def calculate_features(self, symbol: str, ohlcv_data: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate all technical indicators for a symbol

        Args:
            symbol: Crypto symbol (e.g., 'BTC')
            ohlcv_data: CCXT OHLCV DataFrame (last 200 rows for context)

        Returns:
            Dict of indicator name → current value
        """
        # Convert to qlib format
        qlib_data = self.convert_ccxt_to_qlib(ohlcv_data, symbol)

        # Calculate indicators
        features = {}
        for name, expression in self.indicators.items():
            try:
                result = self._evaluate_expression(expression, qlib_data)
                features[name] = float(result.iloc[-1])  # Latest value
            except Exception as e:
                logger.warning(f"Failed to calculate {name} for {symbol}: {e}")
                features[name] = None

        return features

    def _evaluate_expression(self, expression: str, data: pd.DataFrame) -> pd.Series:
        """Evaluate qlib expression on data (internal method)"""
        # Use qlib's expression engine
        from qlib.data.ops import ElemOperator
        # Simplified - actual implementation needs qlib's DataHandler
        raise NotImplementedError("To be implemented with qlib DataHandler")

    def format_for_prompt(self, symbol: str, features: Dict[str, float]) -> str:
        """
        Format features as human-readable text for LLM prompt

        Args:
            symbol: Crypto symbol
            features: Dict from calculate_features()

        Returns:
            Formatted string for prompt injection
        """
        current_price = features.get('close', 0)

        return f"""
=== TECHNICAL INDICATORS ({symbol}) ===
Momentum & Trend:
  - RSI (14): {features['rsi_14']:.1f} {self._interpret_rsi(features['rsi_14'])}
  - MACD Signal: {self._interpret_macd(features)}
  - 20-period MA: ${features['ma_20']:.2f} (price {'above' if current_price > features['ma_20'] else 'below'} MA)

Volatility:
  - ATR (14): ${features['atr_14']:.2f}
  - Bollinger Bands: {self._interpret_bollinger(current_price, features)}

Volume:
  - Volume Surge: {features['volume_surge']:.1f}x ({self._interpret_volume(features['volume_surge'])})

Support & Resistance:
  - Support: ${features['support_20']:.2f}
  - Resistance: ${features['resistance_20']:.2f}
"""

    def _interpret_rsi(self, rsi: float) -> str:
        """Interpret RSI value"""
        if rsi > 70:
            return "(overbought)"
        elif rsi < 30:
            return "(oversold)"
        else:
            return "(neutral)"
```

**Acceptance Criteria**:
- [ ] Class instantiates without errors
- [ ] `calculate_features()` returns dict with all indicators
- [ ] `format_for_prompt()` generates readable text
- [ ] Unit tests pass (mock OHLCV data)

---

#### Task 1.3: Integrate with AI Decision Service (3-4 hours)

**File Modified**: `backend/services/ai_decision_service.py`

**Changes**:
```python
# Add import
from services.qlib_feature_engine import QlibFeatureEngine

class AIDecisionService:
    def __init__(self):
        # ... existing code ...
        self.qlib_engine = QlibFeatureEngine()

    async def call_ai_for_decision(self, account_id: int, symbol: str, market_data: dict) -> dict:
        # ... existing code to fetch prompt template ...

        # NEW: Calculate qlib features
        ohlcv_data = self._fetch_historical_ohlcv(symbol, periods=200)
        qlib_features = self.qlib_engine.calculate_features(symbol, ohlcv_data)
        feature_text = self.qlib_engine.format_for_prompt(symbol, qlib_features)

        # Inject into prompt context
        prompt = prompt_template.replace("{TECHNICAL_INDICATORS}", feature_text)

        # ... rest of existing code ...
```

**Prompt Template Update** (`config/prompt_templates.py`):
```python
DEFAULT_PROMPT_TEMPLATE = """
=== MARKET DATA ===
{symbol}: ${current_price}
24h Change: {change_24h}%

{TECHNICAL_INDICATORS}

=== YOUR PORTFOLIO ===
Cash: ${cash_balance}
Positions: {positions}

=== DECISION REQUIRED ===
... rest of prompt ...
"""
```

**Acceptance Criteria**:
- [ ] Feature section appears in AI decision logs
- [ ] Prompts include qlib indicators
- [ ] No performance degradation (< 50ms added latency)
- [ ] System logs show feature calculation time

---

#### Task 1.4: Add Feature Selection UI (4-5 hours)

**File Modified**: `frontend/app/components/prompt/PromptManager.tsx`

**UI Changes**:
- Add "Technical Indicators" section to prompt editor
- Checkboxes for each indicator (user can enable/disable)
- Preview shows actual qlib calculations
- Save indicator preferences per account

**Acceptance Criteria**:
- [ ] Users can toggle indicators on/off
- [ ] Preview updates with qlib calculations
- [ ] Preferences persist to database

---

#### Task 1.5: A/B Testing and Validation (1-2 weeks)

**Methodology**:
1. Create 2 identical AI accounts (same model, same prompt)
2. Account A: With qlib features (experimental)
3. Account B: Without qlib features (control)
4. Run for 1 week (minimum 50 trades each)
5. Compare performance metrics

**Success Metrics**:
- [ ] Sharpe ratio improvement > 20% (experimental vs control)
- [ ] Max drawdown reduction > 15%
- [ ] User survey: 80%+ find indicators helpful
- [ ] Docker image < 1GB
- [ ] Feature calculation < 50ms per symbol

**Rollback Criteria** (abort Phase 1 if):
- Performance degrades by >10%
- Docker image > 1.2GB
- Feature calculation > 200ms
- User feedback predominantly negative

---

## Phase 2: Backtesting Infrastructure

**Duration**: 4-6 weeks
**Effort**: 1.5 FTE
**Risk**: MEDIUM
**Priority**: ⭐⭐⭐⭐

### Objective

Enable professional-grade historical strategy validation using qlib's backtesting framework.

### Why Backtesting Matters

**Current Problem**:
- Users deploy LLM strategies directly to paper/live trading
- No way to validate performance on historical data
- High risk of unexpected behavior
- No institutional-grade metrics (Sharpe, max drawdown, etc.)

**Qlib Solution**:
- Test strategies on 6+ months of historical data
- Realistic transaction costs (0.05% open, 0.15% close)
- Market impact modeling based on volume
- Professional reports (HTML + JSON)

### Implementation Tasks

#### Task 2.1: Historical Data Pipeline (1-2 weeks)

**New File**: `backend/services/qlib_data_pipeline.py`

**Objective**: Download CCXT OHLCV data and convert to qlib's .bin format

**Process**:
```python
class QlibDataPipeline:
    def download_historical_data(self, symbol: str, start_date: str, end_date: str):
        """
        Download OHLCV data from CCXT for backtesting

        Args:
            symbol: 'BTC/USDT'
            start_date: '2024-05-01'
            end_date: '2025-11-03'
        """
        # Use ccxt to download 1-minute candles
        # Store in database: klines table
        # Convert to qlib .bin format
        pass

    def convert_to_qlib_format(self, symbol: str):
        """Convert SQLite klines data to qlib .bin files"""
        # Read from klines table
        # Write to ~/.qlib/crypto_data/{symbol}.bin
        pass
```

**Storage**:
- Location: `~/.qlib/crypto_data/`
- Format: qlib binary (.bin)
- Size: ~10GB for 6 months of BTC/ETH/SOL at 1-minute resolution

**Acceptance Criteria**:
- [ ] Downloads 6 months of data for BTC, ETH, SOL
- [ ] Converts to qlib format successfully
- [ ] Data validation: no gaps, correct timestamps
- [ ] Total download time < 30 minutes

---

#### Task 2.2: LLM Strategy Adapter (1 week)

**New File**: `backend/services/qlib_backtest_adapter.py`

**Challenge**: Qlib expects strategy classes, Arena uses function-based AI decisions.

**Solution**: Wrap AI decision function in qlib `BaseStrategy` class.

```python
from qlib.contrib.strategy import BaseStrategy
from services.ai_decision_service import AIDecisionService

class LLMTradingStrategy(BaseStrategy):
    """Adapter to run LLM decisions in qlib backtests"""

    def __init__(self, account_id: int, model: str):
        self.account_id = account_id
        self.ai_service = AIDecisionService()

    def generate_trade_decision(self, execute_result=None):
        """Called by qlib executor on each time step"""
        # Fetch current market data from qlib context
        symbol = self.get_current_symbol()
        price = self.get_current_price()

        # Call LLM via existing AI decision service
        decision = self.ai_service.call_ai_for_decision(
            account_id=self.account_id,
            symbol=symbol,
            market_data={'price': price, 'timestamp': self.get_current_time()}
        )

        # Convert Arena decision format to qlib format
        if decision['operation'] == 'buy':
            target_weight = decision['target_portion_of_balance']
            return {'BTC': target_weight}
        elif decision['operation'] == 'sell':
            return {'BTC': 0.0}  # Close position
        else:
            return {}  # Hold (no change)
```

**Acceptance Criteria**:
- [ ] Adapter class implements qlib `BaseStrategy` interface
- [ ] Can run LLM decisions in backtest context
- [ ] Correctly converts decision formats
- [ ] Logs all decisions to database (same as live trading)

---

#### Task 2.3: Backtesting API Endpoint (1 week)

**File Modified**: `backend/api/account_routes.py`

**New Endpoint**: `POST /api/accounts/{account_id}/backtest`

**Request Body**:
```json
{
  "start_date": "2024-05-01",
  "end_date": "2025-11-03",
  "symbols": ["BTC", "ETH"],
  "initial_capital": 10000,
  "config": {
    "trade_cost": 0.0005,
    "min_cost": 5
  }
}
```

**Response**:
```json
{
  "backtest_id": "uuid",
  "status": "running",
  "estimated_completion": "2025-11-03T12:35:00Z"
}
```

**Implementation**:
```python
from qlib.backtest import backtest_daily
from services.qlib_backtest_adapter import LLMTradingStrategy

@router.post("/accounts/{account_id}/backtest")
async def start_backtest(account_id: int, request: BacktestRequest, db: Session = Depends(get_db)):
    """Start a backtest for an AI account"""

    # Validate account exists
    account = account_repo.get_account_by_id(db, account_id)
    if not account:
        raise HTTPException(404, "Account not found")

    # Create qlib backtest configuration
    config = {
        "strategy": {
            "class": "LLMTradingStrategy",
            "kwargs": {"account_id": account_id, "model": account.model}
        },
        "executor": {
            "class": "SimulatorExecutor",
            "kwargs": {
                "generate_report": True,
                "verbose": False
            }
        },
        "backtest": {
            "start_time": request.start_date,
            "end_time": request.end_date,
            "account": request.initial_capital,
            "exchange_kwargs": {
                "open_cost": request.config['trade_cost'],
                "close_cost": request.config['trade_cost'],
                "min_cost": request.config['min_cost']
            }
        }
    }

    # Run backtest asynchronously (use Celery or background task)
    task_id = start_backtest_task.delay(config)

    return {"backtest_id": task_id, "status": "running"}
```

**Async Execution**:
- Use Celery or Dramatiq for background tasks
- Store results in database: `backtest_results` table
- Polling endpoint: `GET /api/backtests/{backtest_id}/status`

**Acceptance Criteria**:
- [ ] Endpoint accepts backtest requests
- [ ] Runs asynchronously (doesn't block API)
- [ ] Stores results in database
- [ ] Returns backtest_id for tracking

---

#### Task 2.4: Backtest Results UI (1-2 weeks)

**New Component**: `frontend/app/components/backtest/BacktestResultsDialog.tsx`

**Features**:
- Performance chart (equity curve over time)
- Key metrics table:
  - Total Return: +12.5%
  - Sharpe Ratio: 1.45
  - Max Drawdown: -8.2%
  - Win Rate: 55%
  - Total Trades: 87
- Trade history table (all orders with timestamps)
- Download HTML report button

**Integration**:
- Add "Backtest" button to SettingsDialog (per account)
- Date range picker for backtest period
- Progress indicator while running
- Results modal on completion

**Acceptance Criteria**:
- [ ] UI launches backtest via API
- [ ] Shows progress during execution
- [ ] Displays results in clear format
- [ ] Allows downloading HTML report
- [ ] Responsive design (works on mobile)

---

## Phase 3: Advanced Features (Optional)

**Duration**: 3-4 weeks
**Effort**: 1.0 FTE
**Risk**: MEDIUM-HIGH
**Priority**: ⭐⭐⭐ (Defer if time-constrained)

### Features

#### 3.1: Portfolio Optimization

**Objective**: Use qlib's `WeightStrategyBase` for multi-asset allocation

**Challenge**: Conflicts with LLM autonomy (optimizer overrides decisions)

**Recommendation**: Only implement if institutional users demand it. Add as opt-in feature.

---

#### 3.2: Multi-Timeframe Analysis

**Objective**: Combine 1min + 5min + 1hour indicators in single prompt

**Example**:
```
=== TECHNICAL INDICATORS (BTC) ===
1-Minute Timeframe:
  - RSI: 72.3 (overbought)
  - MACD: Bullish

5-Minute Timeframe:
  - RSI: 58.1 (neutral)
  - MACD: Neutral

1-Hour Timeframe:
  - RSI: 45.2 (neutral)
  - MACD: Bearish

Multi-Timeframe Signal: CONFLICTING (short-term bullish, long-term bearish)
```

**Value**: Helps LLMs identify divergences between timeframes.

---

#### 3.3: Risk Management Dashboard

**Objective**: Integrate qlib's risk metrics into frontend

**Features**:
- Value at Risk (VaR) calculator
- Correlation heatmap (between crypto assets)
- Portfolio volatility decomposition
- Tail risk analysis

**UI**: New "Risk Dashboard" page in frontend

---

## Architecture Decisions

### 1. Data Pipeline Strategy

**Decision**: Use **in-memory qlib DataHandler** for real-time features, **.bin files** only for backtesting.

**Rationale**:
- Real-time: No disk I/O latency, features calculate in <50ms
- Backtesting: .bin files required for historical data (qlib limitation)

**Implementation**:
- `QlibFeatureEngine`: In-memory only
- `QlibDataPipeline`: Writes .bin files for backtests

---

### 2. Strategy Execution Model

**Decision**: **Separate** qlib backtests from live/paper trading. Don't merge executors.

**Rationale**:
- Live trading: order_executor.py (production-tested, real-time)
- Backtesting: qlib Executor (historical only, research context)
- Merging would complicate both without clear benefit

**Implementation**:
- Keep existing `order_executor.py` unchanged
- Use qlib `SimulatorExecutor` only in backtests

---

### 3. LLM vs ML Models

**Decision**: **LLMs remain primary**. qlib features are input data, not decision-makers.

**Rationale**:
- Platform mission: LLM trading competition
- qlib ML models compete with LLMs, confusing narrative
- Use qlib for data/infrastructure, not strategy logic

**Implementation**:
- qlib indicators → LLM context (✅)
- qlib ML models → Not integrated (❌)

---

### 4. Feature Flags

**Decision**: Make qlib features **opt-in** with per-account toggles.

**Rationale**:
- Some users prefer "pure LLM" mode (no technical indicators)
- Allows A/B testing
- Graceful rollback if issues arise

**Implementation**:
- Database: `account_settings.use_qlib_features` (boolean)
- Frontend: Checkbox in SettingsDialog
- Backend: Check flag before calling `QlibFeatureEngine`

---

## Testing Strategy

### Phase 1 Testing

**Unit Tests**:
- [ ] `QlibFeatureEngine.calculate_features()` with mock data
- [ ] Feature format validation (no NaN, correct types)
- [ ] CCXT → qlib data conversion accuracy

**Integration Tests**:
- [ ] End-to-end: Market data → qlib features → LLM prompt → decision
- [ ] Performance benchmark: Feature calculation < 50ms
- [ ] Memory leak test: 1000 feature calculations, no memory growth

**User Acceptance Testing**:
- [ ] 10 beta users run for 1 week
- [ ] Survey: Rate usefulness of indicators (1-5 scale)
- [ ] Collect feedback on specific indicators (which are most valuable?)

---

### Phase 2 Testing

**Backtest Validation**:
- [ ] Known strategy test: Buy-and-hold on historical data (should match simple calculation)
- [ ] Transaction cost accuracy: Verify costs match configuration
- [ ] Partial fill handling: Test with low-liquidity scenarios

**API Tests**:
- [ ] Backtest endpoint returns valid backtest_id
- [ ] Status polling works correctly
- [ ] Results persist to database

**Frontend Tests**:
- [ ] Manual UI walkthrough (happy path)
- [ ] Edge cases: Empty results, backtest failure

---

## Risk Management

### Risk 1: Complexity Creep ⚠️

**Description**: Qlib is massive (30k+ lines). Easy to over-engineer.

**Mitigation**:
- **Wrapper pattern**: Isolate qlib behind `QlibFeatureEngine`, `QlibDataPipeline` classes
- **Feature flags**: Make all qlib features opt-in
- **Documentation**: Maintain "Qlib Integration Guide" for future developers
- **Code review**: Senior developer must approve all qlib PRs

**Likelihood**: HIGH | **Impact**: MEDIUM

---

### Risk 2: Performance Degradation 🐢

**Description**: Qlib's batch processing may slow real-time trading.

**Mitigation**:
- **Early benchmarking**: Measure feature calculation in Week 1 of Phase 1
- **Cache aggressively**: Redis cache with 60s TTL for indicators
- **Async execution**: Run qlib in thread pool (don't block FastAPI event loop)
- **Kill criteria**: Abort if feature calculation > 200ms

**Likelihood**: MEDIUM | **Impact**: HIGH

---

### Risk 3: Data Format Hell 🔥

**Description**: Converting CCXT → qlib format is error-prone.

**Mitigation**:
- **Schema validation**: Unit tests for every conversion
- **Incremental approach**: Start with in-memory (no disk), add .bin later
- **Fallback**: If conversion fails, use simple momentum (existing code)

**Likelihood**: HIGH | **Impact**: MEDIUM

---

### Risk 4: User Confusion 🤔

**Description**: Users may not understand technical indicators or backtesting.

**Mitigation**:
- **Educational content**: Add tooltips explaining RSI, MACD, etc.
- **Opt-in design**: Users must actively enable features (not default)
- **Clear documentation**: Write "Understanding Technical Indicators" guide
- **Support channel**: Discord/Slack for questions

**Likelihood**: MEDIUM | **Impact**: LOW

---

## Success Criteria

### Phase 1 Success

**Quantitative**:
- [ ] LLM strategies with qlib features show 20%+ Sharpe ratio improvement vs baseline
- [ ] Docker image < 1GB
- [ ] Feature calculation < 50ms per symbol
- [ ] No production incidents related to qlib

**Qualitative**:
- [ ] User survey: 80%+ find indicators helpful (4+/5 rating)
- [ ] At least 50% of active users enable qlib features
- [ ] Positive feedback in community (Discord/Reddit)

---

### Phase 2 Success

**Quantitative**:
- [ ] 50+ backtests run per week
- [ ] Backtest completion time < 5 minutes for 6 months of data
- [ ] Transaction cost accuracy within 1% of paper trading

**Qualitative**:
- [ ] Users cite backtest results in strategy descriptions
- [ ] Academic researchers request access for citations
- [ ] Institutional users mention backtesting as key feature

---

## Timeline & Milestones

```
Week 0:  Prerequisites (Hyperliquid Phases 4-8 complete)
Week 1:  Phase 1.1 - Install qlib, benchmark
Week 2:  Phase 1.2 - QlibFeatureEngine implementation
Week 3:  Phase 1.3 - Integration with AIDecisionService
Week 4:  Phase 1.4 - Feature selection UI
Week 5-6: Phase 1.5 - A/B testing and validation
--- CHECKPOINT: Phase 1 Review ---
Week 7:  Phase 2.1 - Historical data pipeline (start)
Week 8:  Phase 2.1 - Data pipeline (complete)
Week 9:  Phase 2.2 - LLM strategy adapter
Week 10: Phase 2.3 - Backtesting API
Week 11: Phase 2.4 - Results UI (start)
Week 12: Phase 2.4 - Results UI (complete)
--- CHECKPOINT: Phase 2 Review ---
Week 13-16: Phase 3 (optional advanced features)
```

**Total Duration**: 12-16 weeks (3-4 months)

---

## Resource Requirements

### Team

- **Backend Engineer**: 3-4 months (primary)
- **DevOps Engineer**: 1 week (Docker optimization, data pipeline)
- **Quant Researcher**: 2 weeks (consult on indicators, validate backtests)
- **Frontend Engineer**: 2 weeks (backtest UI, feature selection)

### Infrastructure

- **Compute**: No change (qlib runs on CPU)
- **Memory**: +1GB RAM for qlib data structures
- **Disk**: +10GB for historical .bin files (backtesting only)
- **Network**: No change

### Budget

**Labor** (assuming $100k/year avg salary):
- Backend: 4 months × $8.3k/month = $33k
- DevOps: 1 week × $2k/week = $2k
- Quant: 2 weeks × $3k/week = $6k
- Frontend: 2 weeks × $2k/week = $4k
- Contingency (20%): $9k

**Total Estimated Cost**: ~$54k

**Infrastructure**: $0 (no new cloud services)

---

## Alternatives Considered

### Alternative 1: TA-Lib Instead of Qlib

**Pros**: Lightweight (10MB), simple API, battle-tested
**Cons**: No backtesting, no portfolio optimization, no ML integration

**Decision**: ⚠️ **Use for Phase 1 ONLY if qlib proves too heavy**. TA-Lib is a fallback option.

---

### Alternative 2: Build Custom Feature Library

**Pros**: Full control, no dependencies, minimal image size
**Cons**: Months of development, no academic credibility

**Decision**: ❌ REJECTED. Reinventing the wheel. Qlib has 40+ indicators out-of-the-box.

---

### Alternative 3: Use Backtrader Instead of Qlib

**Pros**: Python-native, popular in retail trading, good docs
**Cons**: No AI/ML focus, less institutional credibility

**Decision**: ❌ REJECTED. Qlib's AI-oriented design aligns better with Arena's mission.

---

## Maintenance Plan

### Post-Launch Support

**Ongoing Tasks**:
- **Data updates**: Download new OHLCV data monthly for backtesting
- **qlib version upgrades**: Check for new qlib releases quarterly
- **Indicator tuning**: Monitor which indicators users find most valuable
- **Performance monitoring**: Track feature calculation latency in production

**Estimated Effort**: 4-8 hours/month

---

### Documentation Requirements

**For Developers**:
- [ ] "Qlib Integration Architecture" (this document)
- [ ] "Adding New Technical Indicators" guide
- [ ] "Backtesting API Reference"
- [ ] "Troubleshooting Qlib Issues" guide

**For Users**:
- [ ] "Understanding Technical Indicators" (RSI, MACD explanations)
- [ ] "How to Backtest Your Strategy" tutorial
- [ ] "Interpreting Backtest Results" guide
- [ ] FAQ: "When Should I Use Qlib Features?"

---

## Appendix: Qlib Resources

### Official Documentation
- GitHub: https://github.com/microsoft/qlib
- Docs: https://qlib.readthedocs.io/
- Paper: https://arxiv.org/abs/2009.11189

### Community Resources
- Discord: [Link TBD]
- Examples: https://github.com/microsoft/qlib/tree/main/examples
- Tutorial Videos: [Search YouTube for "qlib tutorial"]

### Key Contacts
- Qlib Maintainers: @microsoft/qlib-team (GitHub)
- Internal Champion: [TBD]

---

**End of Document**

**Next Steps**: When Hyperliquid Phases 4-8 complete, review this plan and proceed to Phase 1 implementation.
