# Qlib Integration Tasks
**Implementation Checklist (Markdown Task Format)**

**Status**: Planning (not started)
**Prerequisites**: Hyperliquid Phases 4-8 complete
**Estimated Start**: Week 9+

---

## PREREQUISITES (Must Complete First)

- [ ] **Hyperliquid Phase 4**: Live Order Submission (7-10 hours)
  - [ ] Phase 4A: Transaction Signing (wallet_signer.py)
  - [ ] Phase 4B: Order Submission (order_executor.py modifications)
  - [ ] Phase 4C: Order Status Polling (order_tracker.py)
- [ ] **Hyperliquid Phase 5**: Account Synchronization (6-9 hours)
- [ ] **Hyperliquid Phase 6**: Risk Management (6-9 hours)
- [ ] **Hyperliquid Phase 7**: WebSocket Streaming (9-12 hours)
- [ ] **Hyperliquid Phase 8**: Frontend Integration (6-9 hours)
- [ ] **Hyperliquid Phase 9**: Testing & Validation (1-2 weeks)
- [ ] **Hyperliquid Phase 10**: Production Readiness (1 week)

**Checkpoint**: All Hyperliquid phases complete, system stable in production
**Estimated Completion**: Week 8-9
**Decision Gate**: User approval required to start qlib Phase 1

---

## PHASE 1: FEATURE ENGINEERING PILOT (Weeks 10-12)

**Duration**: 2-3 weeks
**Risk**: LOW
**Priority**: ⭐⭐⭐⭐⭐

### Task 1.1: Install Qlib and Dependencies (2-4 hours)

- [ ] Add qlib to `backend/pyproject.toml` dependencies
  ```bash
  cd backend
  uv add pyqlib lightgbm torch-cpu
  ```
- [ ] Install dependencies and verify imports
  ```bash
  uv sync
  uv run python -c "import qlib; print(qlib.__version__)"
  ```
- [ ] Build Docker image and check size
  ```bash
  docker build -t arena-backend .
  docker images | grep arena-backend  # Must be < 1GB
  ```
- [ ] Document dependency versions in CLAUDE.md
- [ ] Test that existing tests still pass
  ```bash
  uv run pytest tests/ -v
  ```

**Acceptance Criteria**:
- [ ] qlib imports successfully
- [ ] Docker image < 1GB total size
- [ ] All existing tests pass (no regressions)
- [ ] Documentation updated

**Rollback Plan**: If image > 1.2GB, remove qlib and use TA-Lib instead

---

### Task 1.2: Create QlibFeatureEngine Wrapper (4-6 hours)

- [ ] Create new file: `backend/services/qlib_feature_engine.py`
- [ ] Implement `QlibFeatureEngine` class with methods:
  - [ ] `__init__()` - Initialize qlib configuration
  - [ ] `_define_indicators()` - Define qlib expressions for indicators
  - [ ] `convert_ccxt_to_qlib()` - Convert CCXT DataFrame to qlib format
  - [ ] `calculate_features()` - Calculate all indicators for a symbol
  - [ ] `format_for_prompt()` - Format features as human-readable text
  - [ ] `_interpret_rsi()` - Helper for RSI interpretation
  - [ ] `_interpret_macd()` - Helper for MACD interpretation
  - [ ] `_interpret_bollinger()` - Helper for Bollinger Bands interpretation
  - [ ] `_interpret_volume()` - Helper for volume interpretation
- [ ] Implement 5 core indicators:
  - [ ] RSI (14-period) - Relative Strength Index
  - [ ] MACD - Moving Average Convergence Divergence
  - [ ] Bollinger Bands (20-period, 2σ)
  - [ ] ATR (14-period) - Average True Range
  - [ ] Volume Surge (20-period average)
- [ ] Add support/resistance calculation (20-period high/low)
- [ ] Add error handling (graceful degradation if indicator fails)
- [ ] Add logging for feature calculation time

**Acceptance Criteria**:
- [ ] Class instantiates without errors
- [ ] All 5 indicators calculate successfully with mock data
- [ ] `format_for_prompt()` generates readable text
- [ ] Error handling prevents crashes on bad data
- [ ] Calculation time logged to system logs

---

### Task 1.3: Unit Tests for QlibFeatureEngine (2-3 hours)

- [ ] Create test file: `backend/tests/test_qlib_feature_engine.py`
- [ ] Test indicator calculations:
  - [ ] `test_calculate_rsi()` - Known RSI value from reference data
  - [ ] `test_calculate_macd()` - Known MACD value
  - [ ] `test_calculate_bollinger()` - Known Bollinger values
  - [ ] `test_calculate_atr()` - Known ATR value
  - [ ] `test_volume_surge()` - Known volume ratio
- [ ] Test data conversion:
  - [ ] `test_ccxt_to_qlib_conversion()` - Format correctness
  - [ ] `test_conversion_with_missing_data()` - Handle gaps
- [ ] Test error handling:
  - [ ] `test_insufficient_data()` - Too few rows for calculation
  - [ ] `test_invalid_data()` - NaN/inf values
- [ ] Test prompt formatting:
  - [ ] `test_format_for_prompt()` - Output format validation
- [ ] Performance benchmark:
  - [ ] `test_calculation_performance()` - Must complete in < 50ms

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] Code coverage > 80% for qlib_feature_engine.py
- [ ] Performance benchmark passes (< 50ms)

---

### Task 1.4: Integrate with AI Decision Service (3-4 hours)

- [ ] Modify `backend/services/ai_decision_service.py`:
  - [ ] Add import: `from services.qlib_feature_engine import QlibFeatureEngine`
  - [ ] Initialize engine in `__init__()`: `self.qlib_engine = QlibFeatureEngine()`
  - [ ] Add method `_fetch_historical_ohlcv()` - Get last 200 rows from price_cache
  - [ ] Update `call_ai_for_decision()` to calculate qlib features
  - [ ] Inject feature text into prompt using `{TECHNICAL_INDICATORS}` placeholder
  - [ ] Add feature flag check: `if account.settings.use_qlib_features:`
  - [ ] Log feature calculation time to system logs
- [ ] Update `backend/config/prompt_templates.py`:
  - [ ] Add `{TECHNICAL_INDICATORS}` section to DEFAULT_PROMPT_TEMPLATE
  - [ ] Add `{TECHNICAL_INDICATORS}` section to PRO_PROMPT_TEMPLATE
  - [ ] Add explanatory comment for indicator section
- [ ] Update database schema:
  - [ ] Add `use_qlib_features` column to `accounts` table (boolean, default false)
  - [ ] Create migration script: `backend/database/migrations/005_add_qlib_settings.py`

**Acceptance Criteria**:
- [ ] Feature section appears in AI decision logs when enabled
- [ ] Feature flag works (can enable/disable per account)
- [ ] No errors when features disabled
- [ ] Latency increase < 50ms (measured in system logs)
- [ ] Migration runs successfully on test database

---

### Task 1.5: Add Feature Selection UI (4-5 hours)

- [ ] Modify `frontend/app/components/layout/SettingsDialog.tsx`:
  - [ ] Add "Technical Indicators (Qlib)" section
  - [ ] Add master toggle: "Use qlib-powered technical indicators"
  - [ ] Add checkboxes for individual indicators (future feature):
    - [ ] RSI (14-period)
    - [ ] MACD
    - [ ] Bollinger Bands
    - [ ] ATR (14-period)
    - [ ] Volume Surge
  - [ ] Add tooltip explanations for each indicator
  - [ ] Save preferences via API: `PUT /api/account/{id}`
- [ ] Update TypeScript interfaces in `frontend/app/lib/api.ts`:
  - [ ] Add `use_qlib_features?: boolean` to `AIAccount`
  - [ ] Add `use_qlib_features?: boolean` to `TradingAccountUpdate`
- [ ] Test UI:
  - [ ] Toggle switches work correctly
  - [ ] Preferences persist on page reload
  - [ ] Tooltips display correctly
  - [ ] Responsive on mobile

**Acceptance Criteria**:
- [ ] UI renders without errors
- [ ] Master toggle enables/disables features
- [ ] Preferences save to database via API
- [ ] Tooltips explain each indicator clearly
- [ ] Mobile-responsive design

---

### Task 1.6: Update Prompt Preview with Qlib Features (2-3 hours)

- [ ] Modify `frontend/app/components/prompt/PromptPreviewDialog.tsx`:
  - [ ] Add qlib feature calculation to preview
  - [ ] Show technical indicators section when enabled
  - [ ] Use sample data if real features unavailable
  - [ ] Add loading state while calculating features
- [ ] Test preview:
  - [ ] Features display correctly
  - [ ] Preview updates when toggling feature flag
  - [ ] Loading state works

**Acceptance Criteria**:
- [ ] Preview shows qlib features when enabled
- [ ] Sample data used if calculation fails
- [ ] Loading state prevents confusion
- [ ] Preview matches actual prompt sent to LLM

---

### Task 1.7: A/B Testing Setup (1-2 hours)

- [ ] Create 2 identical test accounts in database:
  - [ ] Account A (Experimental): use_qlib_features = true
  - [ ] Account B (Control): use_qlib_features = false
  - [ ] Same model, same prompt template, same initial balance
- [ ] Document test plan:
  - [ ] Duration: 1 week minimum
  - [ ] Minimum trades: 50 per account
  - [ ] Metrics to compare: Sharpe ratio, max drawdown, win rate
- [ ] Create monitoring dashboard (optional):
  - [ ] Track performance metrics in real-time
  - [ ] Visualize feature usage

**Acceptance Criteria**:
- [ ] 2 test accounts created and verified
- [ ] Test plan documented
- [ ] Monitoring setup (at minimum: manual log checking)

---

### Task 1.8: Run A/B Test and Validate (1-2 weeks)

- [ ] Run both accounts for 1 week (or until 50+ trades each)
- [ ] Collect metrics:
  - [ ] Total return (%)
  - [ ] Sharpe ratio
  - [ ] Max drawdown (%)
  - [ ] Win rate (%)
  - [ ] Average profit per trade
  - [ ] Total trades executed
- [ ] User survey (beta testers):
  - [ ] Survey question: "How useful are technical indicators?" (1-5 scale)
  - [ ] Survey question: "Which indicators do you find most valuable?"
  - [ ] Collect qualitative feedback
- [ ] Analyze results:
  - [ ] Compare metrics: Experimental vs Control
  - [ ] Calculate statistical significance (t-test)
  - [ ] Summarize findings in report

**Success Criteria** (all must pass to proceed to Phase 2):
- [ ] Sharpe ratio improvement > 20% (Experimental vs Control)
- [ ] Max drawdown reduction > 15%
- [ ] User satisfaction > 80% (4+ / 5 rating)
- [ ] Docker image remains < 1GB
- [ ] Feature calculation remains < 50ms per symbol
- [ ] No production incidents related to qlib

**Rollback Criteria** (abort if any fail):
- [ ] Performance degrades by >10%
- [ ] Docker image exceeds 1.2GB
- [ ] Feature calculation exceeds 200ms
- [ ] User feedback predominantly negative (<60% satisfaction)

**Decision Gate**: Review results with user, decide whether to proceed to Phase 2

---

## PHASE 2: BACKTESTING INFRASTRUCTURE (Weeks 13-18)

**Duration**: 4-6 weeks
**Risk**: MEDIUM
**Priority**: ⭐⭐⭐⭐

### Task 2.1: Historical Data Pipeline (1-2 weeks)

- [ ] Create new file: `backend/services/qlib_data_pipeline.py`
- [ ] Implement `QlibDataPipeline` class:
  - [ ] `download_historical_data()` - Download OHLCV from CCXT
  - [ ] `convert_to_qlib_format()` - Convert to qlib .bin files
  - [ ] `validate_data()` - Check for gaps, correct timestamps
  - [ ] `get_data_info()` - Return metadata (date range, symbols)
- [ ] Download 6 months of historical data:
  - [ ] BTC/USDT (1-minute candles)
  - [ ] ETH/USDT (1-minute candles)
  - [ ] SOL/USDT (1-minute candles)
- [ ] Convert to qlib format and save to `~/.qlib/crypto_data/`
- [ ] Create data validation script:
  - [ ] Check for missing timestamps
  - [ ] Verify OHLC consistency (high >= low, etc.)
  - [ ] Calculate data completeness percentage
- [ ] Document data pipeline usage:
  - [ ] How to download new symbols
  - [ ] How to update historical data
  - [ ] How to validate data quality

**Acceptance Criteria**:
- [ ] 6 months of data downloaded for BTC, ETH, SOL
- [ ] Data converted to qlib .bin format successfully
- [ ] Validation passes (no gaps, correct timestamps)
- [ ] Total download time < 30 minutes
- [ ] Documentation complete

---

### Task 2.2: LLM Strategy Adapter (1 week)

- [ ] Create new file: `backend/services/qlib_backtest_adapter.py`
- [ ] Implement `LLMTradingStrategy` class (extends qlib `BaseStrategy`):
  - [ ] `__init__()` - Initialize with account_id, model
  - [ ] `generate_trade_decision()` - Called by qlib on each time step
  - [ ] `_fetch_market_context()` - Get price, volume from qlib data
  - [ ] `_call_llm()` - Invoke AIDecisionService
  - [ ] `_convert_decision()` - Arena format → qlib format
- [ ] Handle qlib execution context:
  - [ ] Access current price via qlib APIs
  - [ ] Access current timestamp
  - [ ] Access current portfolio positions
- [ ] Decision format conversion:
  - [ ] Arena "buy" → qlib target weight (e.g., 0.2 = 20% allocation)
  - [ ] Arena "sell" → qlib target weight 0.0 (close position)
  - [ ] Arena "hold" → qlib no change (empty dict)
- [ ] Log all decisions to `ai_decision_log` table (same as live/paper)
- [ ] Add error handling:
  - [ ] LLM API timeout → default to HOLD
  - [ ] Invalid decision format → default to HOLD

**Acceptance Criteria**:
- [ ] Adapter class implements qlib `BaseStrategy` interface correctly
- [ ] Can run LLM decisions in backtest context
- [ ] Decision format conversion works
- [ ] All decisions logged to database
- [ ] Error handling prevents backtest crashes

---

### Task 2.3: Backtesting API Endpoint (1 week)

- [ ] Modify `backend/api/account_routes.py`:
  - [ ] Add endpoint: `POST /api/accounts/{account_id}/backtest`
  - [ ] Add endpoint: `GET /api/backtests/{backtest_id}/status`
  - [ ] Add endpoint: `GET /api/backtests/{backtest_id}/results`
- [ ] Implement backtest request handling:
  - [ ] Validate request body (start_date, end_date, symbols)
  - [ ] Generate backtest_id (UUID)
  - [ ] Create qlib backtest configuration
  - [ ] Queue backtest task (use Celery or Dramatiq)
  - [ ] Return backtest_id immediately (async execution)
- [ ] Implement backtest executor:
  - [ ] Create background task: `run_backtest_task()`
  - [ ] Call qlib `backtest_daily()` with LLMTradingStrategy
  - [ ] Capture results (portfolio metrics, trades)
  - [ ] Store results in database: `backtest_results` table
  - [ ] Update status (running → completed/failed)
- [ ] Create database table: `backtest_results`
  - [ ] Columns: id, account_id, start_date, end_date, status, total_return, sharpe_ratio, max_drawdown, trades_json, created_at
- [ ] Create migration: `backend/database/migrations/006_add_backtest_results.py`
- [ ] Implement results retrieval:
  - [ ] Fetch from database by backtest_id
  - [ ] Return JSON with metrics and trade history

**Acceptance Criteria**:
- [ ] Endpoint accepts valid backtest requests
- [ ] Returns backtest_id immediately (< 1 second)
- [ ] Backtest runs asynchronously in background
- [ ] Status endpoint tracks progress
- [ ] Results persist to database
- [ ] Results endpoint returns complete data

---

### Task 2.4: Background Task Infrastructure (2-3 days)

- [ ] Install Celery or Dramatiq:
  ```bash
  uv add celery redis  # or dramatiq
  ```
- [ ] Create `backend/celery_app.py` (if using Celery):
  - [ ] Configure Celery with Redis broker
  - [ ] Register backtest task
  - [ ] Set task timeout (e.g., 30 minutes)
- [ ] Start Celery worker:
  ```bash
  celery -A celery_app worker --loglevel=info
  ```
- [ ] Update `start_arena.sh` and `start_arena.ps1`:
  - [ ] Start Celery worker alongside backend
  - [ ] Stop Celery worker on shutdown
- [ ] Test task execution:
  - [ ] Submit test backtest
  - [ ] Verify task runs in background
  - [ ] Verify status updates
  - [ ] Verify results persist

**Acceptance Criteria**:
- [ ] Celery/Dramatiq installed and configured
- [ ] Worker starts successfully
- [ ] Tasks execute in background
- [ ] Startup scripts updated
- [ ] Integration tests pass

---

### Task 2.5: Backtest Results UI (1-2 weeks)

- [ ] Create new component: `frontend/app/components/backtest/BacktestResultsDialog.tsx`
- [ ] Implement UI features:
  - [ ] Equity curve chart (using lightweight-charts library)
  - [ ] Key metrics table:
    - [ ] Total Return (%)
    - [ ] Sharpe Ratio
    - [ ] Max Drawdown (%)
    - [ ] Win Rate (%)
    - [ ] Total Trades
    - [ ] Average Profit per Trade
  - [ ] Trade history table:
    - [ ] Columns: Timestamp, Symbol, Side, Quantity, Price, P&L
    - [ ] Pagination (show 20 trades per page)
  - [ ] Download HTML report button
- [ ] Add "Backtest" button to SettingsDialog:
  - [ ] Click opens backtest configuration dialog
  - [ ] Date range picker (start/end dates)
  - [ ] Symbol selector (multi-select)
  - [ ] Initial capital input (default: 10,000)
  - [ ] Submit button triggers API call
- [ ] Implement progress indicator:
  - [ ] Show spinner while backtest running
  - [ ] Poll status endpoint every 2 seconds
  - [ ] Show estimated completion time (if available)
- [ ] Handle errors gracefully:
  - [ ] Display error message if backtest fails
  - [ ] Retry button for failed backtests
- [ ] Responsive design:
  - [ ] Mobile-friendly layout
  - [ ] Charts resize correctly

**Acceptance Criteria**:
- [ ] UI renders without errors
- [ ] Can launch backtest from UI
- [ ] Progress indicator works correctly
- [ ] Results display clearly
- [ ] Trade history table functional
- [ ] Download report button works
- [ ] Mobile-responsive

---

### Task 2.6: Backtest Validation and Testing (1 week)

- [ ] Create validation backtest:
  - [ ] Known strategy: Buy-and-hold (should match simple calculation)
  - [ ] Compare qlib result vs manual calculation
  - [ ] Tolerance: < 1% difference
- [ ] Test transaction costs:
  - [ ] Configure 0.05% cost
  - [ ] Verify costs applied correctly
  - [ ] Compare with paper trading costs
- [ ] Test edge cases:
  - [ ] Empty date range (should error)
  - [ ] Future dates (should error)
  - [ ] Single trade scenario
  - [ ] 100+ trade scenario
- [ ] Performance testing:
  - [ ] Backtest 6 months of data
  - [ ] Should complete in < 5 minutes
  - [ ] Monitor memory usage (should not leak)
- [ ] Integration testing:
  - [ ] End-to-end: UI → API → Backtest → Results → UI
  - [ ] Multiple concurrent backtests (should not interfere)

**Acceptance Criteria**:
- [ ] Validation backtest matches expected results
- [ ] Transaction costs accurate within 1%
- [ ] All edge cases handled
- [ ] Performance targets met (< 5 min for 6 months)
- [ ] Integration tests pass

---

## PHASE 3: ADVANCED FEATURES (Weeks 19-22, Optional)

**Duration**: 3-4 weeks
**Risk**: MEDIUM-HIGH
**Priority**: ⭐⭐⭐ (Defer if time-constrained)

### Task 3.1: Portfolio Optimization (Optional)

- [ ] Research qlib `WeightStrategyBase` API
- [ ] Implement portfolio optimizer wrapper
- [ ] Integrate with existing decision flow
- [ ] Add UI toggle for portfolio optimization
- [ ] Test with multi-asset portfolios

**Note**: Defer unless institutional users specifically request this feature.

---

### Task 3.2: Multi-Timeframe Analysis (Optional)

- [ ] Extend QlibFeatureEngine to support multiple timeframes
- [ ] Calculate indicators for 1min, 5min, 1hour simultaneously
- [ ] Update prompt template to show all timeframes
- [ ] Add UI for timeframe selection
- [ ] Test with real trading

**Acceptance Criteria**:
- [ ] Indicators calculated for 3 timeframes
- [ ] Prompt clearly distinguishes timeframes
- [ ] Performance impact < 150ms total
- [ ] UI allows enabling/disabling timeframes

---

### Task 3.3: Risk Management Dashboard (Optional)

- [ ] Create new page: `frontend/app/pages/RiskDashboard.tsx`
- [ ] Implement risk metrics:
  - [ ] Value at Risk (VaR) calculator
  - [ ] Correlation heatmap (crypto assets)
  - [ ] Portfolio volatility decomposition
  - [ ] Tail risk analysis (extreme events)
- [ ] Integrate with qlib risk functions
- [ ] Add real-time updates via WebSocket
- [ ] Mobile-responsive design

**Acceptance Criteria**:
- [ ] Dashboard displays all risk metrics
- [ ] Metrics update in real-time
- [ ] Heatmap visualization works
- [ ] Mobile-friendly layout

---

## POST-IMPLEMENTATION TASKS

### Documentation

- [ ] Write "Qlib Integration Guide" for developers:
  - [ ] Architecture overview
  - [ ] How to add new indicators
  - [ ] How to modify backtest configuration
  - [ ] Troubleshooting common issues
- [ ] Write user documentation:
  - [ ] "Understanding Technical Indicators" (RSI, MACD explanations)
  - [ ] "How to Backtest Your Strategy" tutorial
  - [ ] "Interpreting Backtest Results" guide
  - [ ] FAQ: "When Should I Use Qlib Features?"
- [ ] Update CLAUDE.md:
  - [ ] Mark qlib features as "Production Ready"
  - [ ] Add qlib to tech stack section
  - [ ] Document maintenance tasks

---

### Production Deployment

- [ ] Code review with senior developer
- [ ] Security audit (no data leaks, proper error handling)
- [ ] Performance profiling in production
- [ ] Monitor Docker image size in production
- [ ] Set up alerts for qlib errors
- [ ] Create runbook for qlib issues

---

### Maintenance

- [ ] Schedule monthly data updates (download new historical data)
- [ ] Check for qlib version updates quarterly
- [ ] Monitor feature calculation latency
- [ ] Track which indicators users find most valuable
- [ ] Collect user feedback continuously

---

## ROLLBACK PROCEDURES

### Phase 1 Rollback (If A/B Test Fails)

- [ ] Remove qlib imports from `ai_decision_service.py`
- [ ] Set `use_qlib_features = false` for all accounts in database
- [ ] Remove qlib dependencies from `pyproject.toml`
- [ ] Rebuild Docker image
- [ ] Deploy to production
- [ ] Notify users of feature removal

**Estimated Time**: 2-3 hours

---

### Phase 2 Rollback (If Backtesting Unstable)

- [ ] Disable backtest endpoint (return 503 Service Unavailable)
- [ ] Hide "Backtest" button in frontend UI
- [ ] Keep Phase 1 features (don't remove qlib entirely)
- [ ] Investigate root cause
- [ ] Fix or defer to future release

**Estimated Time**: 1-2 hours

---

## DECISION GATES

### Gate 1: After Hyperliquid Phases 4-8 Complete

**Decision**: Start qlib Phase 1 or defer?

**Criteria**:
- [ ] Hyperliquid live trading stable in production (1+ week)
- [ ] No critical bugs or performance issues
- [ ] User feedback on Hyperliquid positive
- [ ] Team capacity available (not overloaded with support)

**Decision Maker**: User (project owner)

---

### Gate 2: After Phase 1 Complete (A/B Test Results)

**Decision**: Proceed to Phase 2 or rollback?

**Criteria** (all must pass):
- [ ] Sharpe ratio improvement > 20%
- [ ] User satisfaction > 80%
- [ ] No performance degradation
- [ ] Docker image < 1GB
- [ ] Feature calculation < 50ms

**Decision Maker**: User + Technical Lead

---

### Gate 3: After Phase 2 Complete

**Decision**: Proceed to Phase 3 or declare victory?

**Criteria**:
- [ ] Backtesting used by 20%+ of active users
- [ ] Institutional users specifically request advanced features
- [ ] Team has capacity for 3-4 more weeks

**Decision Maker**: User (project owner)

---

**End of Tasks Document**

**Total Estimated Effort**: 12-16 weeks (spread across 3 phases)
**Current Status**: Planning complete, awaiting Hyperliquid completion
**Next Review**: Week 9 (post-Hyperliquid)
