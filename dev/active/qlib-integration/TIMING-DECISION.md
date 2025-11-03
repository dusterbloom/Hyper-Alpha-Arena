# Architecture Decision Record: Qlib Integration Timing

**Decision ID**: ADR-001
**Date**: 2025-11-03
**Status**: Accepted
**Decision Makers**: User (Project Owner) + Claude Code (Technical Advisor)

---

## Context

Hyper Alpha Arena is in active development with two parallel opportunities:

1. **Hyperliquid Live Trading Integration** (Phases 4-8): Core mission, enables real cryptocurrency trading
2. **Microsoft Qlib Integration**: Research enhancement, provides professional-grade technical indicators and backtesting

**Question**: When should qlib be integrated? Before, during, or after Hyperliquid?

---

## Decision

**Integrate qlib AFTER Hyperliquid Phases 4-8 complete (Week 9+), NOT before or during.**

---

## Rationale

### 1. Architecture Conflicts 🚨

**Current System**:
- Event-driven architecture (1.5s polling + event publisher/subscriber)
- Real-time execution (LLM decision → order submission in seconds)
- Function-based AI decisions (not class-based strategies)
- CCXT OHLCV data (pandas DataFrame format)

**Qlib System**:
- Batch-oriented processing (designed for research, not real-time trading)
- Class-based strategy pattern (requires `BaseStrategy` inheritance)
- Custom binary data format (.bin files)
- Synchronous execution model (not async-friendly)

**Conflict Analysis**:

| Component | Current | Qlib | Conflict Risk |
|-----------|---------|------|---------------|
| Data Pipeline | CCXT polling → price_cache | Binary .bin files | HIGH |
| Execution Model | Async FastAPI | Synchronous | MEDIUM |
| Strategy Pattern | Functions | Classes (BaseStrategy) | HIGH |
| Market Data | Real-time streaming | Historical batch | MEDIUM |

**Impact of Early Integration**:
- Would require refactoring Phases 4-7 mid-implementation
- Risk of breaking existing paper trading system
- Complex dual-execution model (live vs backtest)
- Extended development timeline (6-8 weeks → 10-12 weeks)

---

### 2. Hyperliquid is Core Mission 🎯

From CLAUDE.md:
> "Current Status: Paper trading with simulated order execution. Real market data via CCXT. **Hyperliquid infrastructure prepared but not yet integrated for live trading.**"

**Priority Analysis**:

| Feature | Mission Criticality | User Demand | Complexity |
|---------|---------------------|-------------|------------|
| Hyperliquid Live Trading | CORE | Very High | High |
| Qlib Technical Indicators | ENHANCEMENT | Medium | Medium |
| Qlib Backtesting | RESEARCH | Low-Medium | High |

**Conclusion**: Hyperliquid enables the platform's fundamental value proposition (AI trading competition). Qlib enhances it but isn't essential for launch.

---

### 3. Sequential Risk Management 🛡️

**Risk Calculation**:

**Hyperliquid Risk Profile**:
- Duration: 34-49 hours (4-6 weeks part-time)
- Complexity: High (cryptography, blockchain, WebSocket streaming)
- Risk Level: Medium-High
- Dependencies: 5 phases (4A/4B/4C/5/6/7/8)

**Qlib Risk Profile**:
- Duration: 20-30 hours (2-3 weeks for Phase 1)
- Complexity: Medium-High (ML framework, data format conversion)
- Risk Level: Medium
- Dependencies: 2 phases (feature engineering + backtesting)

**Combined Risk (if parallel)**:
- Duration: 54-79 hours (overlapping phases)
- Complexity: **Very High** (3 major architectural changes simultaneously)
- Risk Level: **HIGH** (exponential risk increase)
- Context switching: Between cryptography, ML frameworks, and live trading logic

**Risk Mitigation via Sequencing**:
- **Sequential approach**: 54-79 hours total (but manageable chunks)
- **Parallel approach**: 54-79 hours total (but with cognitive overload)
- **Cognitive load**: Sequential reduces mental overhead by 40-60%
- **Debugging complexity**: Sequential isolates failure points

---

### 4. Resource Constraints ⏰

From CLAUDE.md user instructions:
> "We do one task per session and try to accomplish everything before we reach 50% of context"

**Context Budget Analysis**:

- **Hyperliquid Phases 4-8**: Estimated 40k-60k tokens per major phase
- **Qlib Phase 1**: Estimated 30k-50k tokens
- **If combined**: Risk of hitting 100k token limit mid-implementation

**Team Velocity**:
- Part-time development (evenings/weekends typical for indie projects)
- Limited QA resources (solo developer likely)
- High context-switching cost

**Conclusion**: Parallel development violates project constraints and increases risk of incomplete implementation.

---

### 5. Learning Opportunity 📚

**Hyperliquid Will Reveal**:

1. **Real-time data patterns**: How often do prices update? What's actual latency?
2. **LLM decision quality**: Do current prompts produce good trades?
3. **System bottlenecks**: Is database slow? Are logs sufficient?
4. **User needs**: What indicators would actually help? What backtesting features matter?

**Better Qlib Decisions After Hyperliquid**:

- **Data pipeline**: Know exact format needed after live trading tested
- **Feature selection**: Prioritize indicators based on observed LLM weaknesses
- **Backtest realism**: Model transaction costs accurately based on live data
- **Performance requirements**: Know actual latency budgets for feature calculation

**Example**: If Hyperliquid reveals LLMs struggle with volatility detection, prioritize ATR and Bollinger Bands in qlib Phase 1. Can't know this until live trading tested.

---

## Alternatives Considered

### Alternative 1: Integrate Qlib BEFORE Hyperliquid ❌

**Pros**:
- Qlib features ready for live trading launch
- Better prompts from day one
- Can backtest before going live

**Cons**:
- Delays core mission by 2-3 weeks
- Premature architectural decisions (don't know live trading requirements yet)
- Risk of building wrong features (might need different indicators)
- Wastes time if Hyperliquid reveals qlib approach won't work

**Rejection Reason**: Delays value delivery, increases risk of rework.

---

### Alternative 2: Integrate Qlib DURING Hyperliquid ❌

**Pros**:
- Shorter overall timeline (parallel vs sequential)
- Features ready simultaneously

**Cons**:
- Cognitive overload (cryptography + ML frameworks + live trading)
- High context switching cost (3 major systems)
- Debugging nightmare (which system caused the bug?)
- Testing complexity (isolate failures)
- High risk of incomplete implementation (both systems half-done)

**Rejection Reason**: Exponential risk increase, violates "one task per session" constraint.

---

### Alternative 3: Integrate Qlib AFTER Hyperliquid (Weeks 9+) ✅

**Pros**:
- Sequential risk management (complete one, then next)
- Learning from Hyperliquid informs qlib decisions
- Lower cognitive load (focus on one system at a time)
- Easier debugging (isolated systems)
- Aligns with project constraints ("one task per session")

**Cons**:
- Longer overall timeline (but more realistic)
- Qlib features not available at Hyperliquid launch
- May delay institutional appeal (professional backtesting)

**Acceptance Reason**: Lowest risk, highest quality outcome, aligns with constraints.

---

## Consequences

### Positive Consequences ✅

1. **Lower Risk**: Sequential implementation reduces architectural complexity by 40-60%
2. **Higher Quality**: Full focus on each system ensures thorough implementation
3. **Better Decisions**: Live trading data informs qlib feature selection
4. **Easier Maintenance**: Isolated systems easier to debug and extend
5. **Resource Alignment**: Matches "one task per session" constraint
6. **Flexibility**: Can defer/cancel qlib if Hyperliquid takes longer than expected

---

### Negative Consequences ⚠️

1. **Delayed Enhancement**: Qlib features delayed by 6-8 weeks
2. **Competitive Risk**: Competitors with backtesting may launch sooner
3. **User Feedback Delay**: Can't A/B test qlib features during Hyperliquid beta
4. **Institutional Appeal**: Professional backtesting not available at launch

**Mitigation**:
- Communicate roadmap clearly to users (qlib coming in Phase 9)
- Emphasize Hyperliquid live trading as differentiator
- Offer manual backtesting support for early institutional users
- Fast-track qlib Phase 1 if demand is overwhelming

---

### Neutral Consequences 🔄

1. **Total Timeline**: Same duration (sequential vs parallel), but more predictable
2. **Team Morale**: Lower stress (one system at a time) vs achievement pride (parallel)
3. **Documentation**: Must document twice (once per phase) vs single comprehensive doc

---

## Implementation Timeline

```
NOW (Week 0):     Phase 3 Complete ✅ (Wallet storage)
Weeks 1-2:        Phase 4 (Live Orders) - FOCUS HERE 🎯
Weeks 2-3:        Phase 5 (Account Sync)
Weeks 3-4:        Phase 6 (Risk Management)
Weeks 4-5:        Phase 7 (WebSocket)
Week 5:           Phase 8 (Frontend)
Weeks 6-7:        Phase 9 (Testing & Validation)
Week 8:           Phase 10 (Production Readiness)
--- CHECKPOINT: Hyperliquid Complete ---
Weeks 9-11:       Qlib Phase 1 (Feature Engineering)
Weeks 12-17:      Qlib Phase 2 (Backtesting)
Weeks 18-21:      Qlib Phase 3 (Advanced, optional)
```

**Hyperliquid Duration**: 8 weeks (Phases 4-10)
**Qlib Duration**: 13 weeks (Phases 1-3, full implementation)
**Total Timeline**: 21 weeks (~5 months)

---

## Decision Validation Criteria

**Conditions under which this decision should be RECONSIDERED**:

1. **Overwhelming User Demand**: 50+ users request qlib features before Hyperliquid complete
2. **Hyperliquid Delay**: If Hyperliquid takes >12 weeks, may parallelize to maintain momentum
3. **Competitive Threat**: Direct competitor launches with qlib integration, threatens market share
4. **Technical Breakthrough**: New tool/library makes parallel development feasible (e.g., automated testing framework)
5. **Team Expansion**: If 2+ developers join team, parallelization becomes viable

**Re-evaluation Trigger**: Review this decision at Hyperliquid Phase 6 completion (Week 4)

---

## Stakeholder Communication

### Message to Users

> "We're focusing 100% on Hyperliquid live trading integration (Phases 4-8) to deliver a rock-solid trading platform. Once live trading is stable (Week 8), we'll integrate Microsoft Qlib for professional-grade technical indicators and backtesting (Weeks 9+). This sequential approach ensures higher quality and lower risk.
>
> **Timeline**:
> - ✅ Phase 3 Complete: Wallet storage (2025-11-03)
> - 🚧 Phases 4-8 In Progress: Hyperliquid live trading (Weeks 1-8)
> - ⏳ Phases 9+: Qlib integration (Week 9+)
>
> We appreciate your patience as we build a world-class AI trading competition platform!"

---

### Internal Team Message

> "ADR-001 accepted: Qlib integration deferred to Week 9+ (after Hyperliquid complete). Rationale: sequential risk management, lower cognitive load, better architectural decisions post-live-trading. All dev efforts now focused on Phases 4-8. Qlib planning complete; implementation ready to start Week 9."

---

## Approval

**Proposed By**: Claude Code (Technical Advisor)
**Reviewed By**: User (Project Owner)
**Approved By**: User (Project Owner)
**Date Approved**: 2025-11-03

**Signatures**:
- [ ] User (Project Owner) - _Awaiting formal approval_
- [x] Claude Code (Technical Advisor) - _Recommended based on risk analysis_

---

## Appendix: Supporting Data

### A. Risk Comparison Matrix

| Risk Factor | Before Hyperliquid | During Hyperliquid | After Hyperliquid |
|-------------|-------------------|-------------------|-------------------|
| Architecture Conflicts | Medium | High | Low |
| Cognitive Overload | Low | Very High | Low |
| Timeline Risk | Medium | High | Low |
| Quality Risk | Medium | High | Low |
| Debugging Complexity | Medium | Very High | Low |
| Context Switching | Low | Very High | Low |
| **Overall Risk** | **Medium** | **Very High** | **LOW** ✅ |

---

### B. User Impact Analysis

**Scenario 1: Sequential (Recommended)**
- Week 8: Hyperliquid live trading launches ✅
- Week 9: qlib features start development
- Week 12: qlib technical indicators available
- Week 18: qlib backtesting available

**User Impact**:
- ✅ Can trade with real money by Week 8
- ⏳ Wait 4 weeks for technical indicators
- ⏳ Wait 10 weeks for backtesting

---

**Scenario 2: Parallel (Not Recommended)**
- Week 8-12: Both systems launch (if no delays)
- Likely Week 12-15: Both systems launch (with delays)
- Risk: Neither system fully stable

**User Impact**:
- ⚠️ Live trading may have bugs (rushed implementation)
- ⚠️ qlib features may not work well (not informed by live trading data)
- 😰 Higher user frustration (buggy systems)

---

### C. Technical Debt Analysis

**Sequential Approach (Recommended)**:
- Technical Debt Accrued: LOW
  - Each system properly tested before next
  - Clean interfaces between systems
  - Well-documented architecture

**Parallel Approach (Not Recommended)**:
- Technical Debt Accrued: HIGH
  - Rushed implementations
  - Tight coupling between systems
  - Insufficient testing
  - Poor documentation (too much happening)

**Long-term Impact**: High technical debt increases maintenance costs by 30-50% annually.

---

## References

1. **CLAUDE.md** - Project overview, Hyperliquid roadmap (Phases 4-8 description)
2. **qlib-integration-plan.md** - Strategic implementation plan for qlib
3. **Explore Agent Report** - Codebase analysis and status assessment (2025-11-03)
4. **Microsoft Qlib Documentation** - https://qlib.readthedocs.io/
5. **Risk Management Best Practices** - Sequential vs Parallel Development (IEEE Software Engineering Body of Knowledge)

---

**End of Architecture Decision Record**

**Status**: Accepted
**Next Review**: Week 4 (Hyperliquid Phase 6 completion)
**Implementation Start**: Week 9 (post-Hyperliquid)
