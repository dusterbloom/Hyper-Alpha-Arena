# Next Session: Phase 4 - Hyperliquid Live Order Submission

**Copy and paste this entire prompt into your next Claude Code session:**

---

## Context & Current Status

I'm continuing the Hyper Alpha Arena project - an AI trading competition platform. We've just completed **Phase 3: KISS Wallet Integration** (wallet credential storage with AES-256-GCM encryption). The current branch is `feature/hyperliquid-phase3-auth` with 4 commits ready.

**What's Complete:**
- ✅ Phase 1: Enhanced paper trading with realistic slippage simulation
- ✅ Phase 2: Live trading database schema (trading_mode, exchange fields)
- ✅ Phase 3A: Backend wallet storage (encrypted private keys, validation, API endpoints, 6 tests passing)
- ✅ Phase 3B: Frontend wallet UI (input forms with security UX)

**Current Branch Status:**
- Branch: `feature/hyperliquid-phase3-auth`
- Commits: 5 total (629683b, 99202d4, fb9e580, ea5f90e, df13fe3)
- Tests: All passing ✅
- Ready to merge or continue to Phase 4

## Your First Actions

**IMPORTANT**: Before writing any code, do these 3 steps in order:

### Step 1: Load Context (Required)
Read these files IN THIS ORDER to understand what's been done:

1. **First**: `/dev/active/hyperliquid-integration/PHASE3-COMPLETE.md`
   - This has the complete Phase 3 implementation details
   - Security checklist, test results, file changes
   - Known issues and recommendations

2. **Second**: `/CLAUDE.md` (lines 313-383)
   - Jump directly to the "KISS Wallet Integration (Phase 3)" section
   - Read the Phase 3 documentation
   - Read the "Planned but Not Implemented" section (Phase 4 details)

3. **Third**: `/backend/utils/encryption.py`
   - Understand how private key encryption works
   - You'll need to decrypt keys for signing in Phase 4

### Step 2: Verify Current State (Required)
Run these commands to verify everything works:

```bash
# Verify backend tests pass
cd backend
uv run pytest tests/test_wallet_storage.py -v

# Check recent commits
git log --oneline -5

# Verify encryption key exists
ls -la backend/.env | grep ENCRYPTION_KEY || echo "Key not in .env yet (will be auto-generated on first use)"

# Check branch status
git status
```

Expected results:
- 6 tests passing ✅
- Clean working tree (no uncommitted changes)
- Branch: `feature/hyperliquid-phase3-auth`

### Step 3: Confirm Direction
Ask me: **"Phase 3 is complete. Would you like to: (A) Merge/push this branch and start fresh, or (B) Continue directly to Phase 4 on this branch?"**

**Do NOT start Phase 4 implementation until I respond.**

---

## Phase 4 Overview (If I say proceed)

### Goal
Implement live order submission to Hyperliquid exchange using wallet signatures.

### Architecture
```
AI Decision → Order Executor → Wallet Signer → Hyperliquid API → Exchange
                   ↓                                    ↓
              Update DB                         Store exchange_order_id
```

### Key Technical Challenges
1. **Signature Format**: Hyperliquid requires specific EIP-712 typed data signatures
2. **Nonce Management**: Each order needs a unique nonce to prevent replay attacks
3. **Order Lifecycle**: Track order states (pending → open → filled/rejected)
4. **Error Handling**: Network failures, insufficient balance, invalid signatures
5. **Testnet First**: Must use testnet initially, then add mainnet toggle

---

## Phase 4A: Transaction Signing (Part 1)

### What to Build

**New File**: `/backend/services/wallet_signer.py`

**Requirements:**
1. Class: `WalletSigner`
2. Method: `sign_order(account_id: int, order_data: dict) -> str`
   - Load encrypted private key from database (account.wallet_private_key_encrypted)
   - Decrypt using `decrypt_private_key()` from utils/encryption.py
   - Format order data for Hyperliquid (EIP-712 typed data)
   - Sign with eth-account library
   - Return hex signature string

**Key Implementation Details:**
```python
from eth_account import Account
from eth_account.messages import encode_typed_data
from utils.encryption import decrypt_private_key

class WalletSigner:
    def sign_order(self, account_id: int, order_data: dict) -> str:
        # 1. Load account from database
        # 2. Get encrypted private key
        # 3. Decrypt: decrypted_key = decrypt_private_key(encrypted)
        # 4. Create eth_account: account = Account.from_key("0x" + decrypted_key)
        # 5. Format typed data for Hyperliquid
        # 6. Sign: signed = account.sign_typed_data(typed_data)
        # 7. Return signature as hex string
        pass
```

**Hyperliquid Order Format:**
- Refer to: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/signing
- Key fields: symbol, isBuy, limitPx (price), sz (size), reduceOnly, orderType
- Must include: timestamp, nonce (prevent replay)

**Testing Strategy:**
1. Create test in `/backend/tests/test_wallet_signer.py`
2. Use a known test private key
3. Sign a test order
4. Verify signature format matches Hyperliquid requirements
5. Test with Hyperliquid testnet API (just signature validation, no actual order)

### Error Handling
- Missing private key → Raise clear error: "No wallet configured for this account"
- Decryption failure → Raise: "Unable to decrypt private key"
- Invalid private key format → Raise: "Invalid private key"

### Security Checks
- ⚠️ NEVER log the decrypted private key
- ⚠️ Keep private key in memory as briefly as possible
- ⚠️ Use testnet_enabled flag from database to determine endpoint

---

## Phase 4B: Order Submission (Part 2)

**Modify File**: `/backend/services/order_executor.py`

Add new method: `submit_to_exchange(order_id: int) -> dict`

**Flow:**
1. Load order from database
2. Check account.trading_mode == "LIVE"
3. If PAPER mode → use existing paper trading logic
4. If LIVE mode → call Hyperliquid API
5. Use WalletSigner to get signature
6. Submit order to Hyperliquid
7. Store exchange_order_id in database
8. Update order status based on response

**Hyperliquid SDK Usage:**
```python
from hyperliquid.api import API

# Initialize
api = API(testnet=account.testnet_enabled == "true")

# Submit order
result = api.place_order(
    signature=signature,
    order_data=order_data,
    wallet_address=account.wallet_address
)

# result contains: exchange_order_id, status, filled_qty, etc.
```

**Error Scenarios to Handle:**
- Insufficient balance
- Invalid symbol
- Price out of bounds
- Rate limiting (429 status)
- Network timeout
- Invalid signature

**Database Updates:**
```python
order.exchange_order_id = result['order_id']
order.exchange = 'HYPERLIQUID'
order.status = result['status']  # 'open', 'filled', 'rejected'
if result.get('filled_qty'):
    order.actual_fill_price = result['avg_fill_price']
db.commit()
```

---

## Phase 4C: Order Status Polling (Part 3)

**New File**: `/backend/services/order_tracker.py`

**Background Task**: Poll Hyperliquid every 5 seconds for order updates

**Requirements:**
1. Query all orders with status = 'PENDING' or 'OPEN' and exchange_order_id != NULL
2. For each order, query Hyperliquid API for status
3. Update local database with latest status, fill data
4. Handle partial fills
5. Mark order as 'FILLED' or 'REJECTED' when complete

**Integration Point**: Start this service in `main.py` on app startup (like market_stream)

---

## Critical Requirements for All Phase 4 Work

### 1. Testnet Only (Initially)
- Use `account.testnet_enabled` flag from database
- Hyperliquid testnet URL: `https://api.hyperliquid-testnet.xyz`
- Get testnet funds: https://app.hyperliquid-testnet.xyz

### 2. Safety Checks
```python
# Before submitting ANY order to Hyperliquid:
if account.trading_mode != "LIVE":
    raise ValueError("Account not in LIVE mode")
if not account.wallet_address:
    raise ValueError("No wallet address configured")
if not account.wallet_private_key_encrypted:
    raise ValueError("No wallet private key configured")
if order.quantity * order.price > 10000:  # Safety limit
    raise ValueError("Order size too large (>$10k limit)")
```

### 3. Testing Strategy
- Write unit tests for signature generation
- Write integration tests with testnet
- Test error scenarios (insufficient balance, network timeout, invalid signature)
- Manual testing with real testnet wallet before any mainnet consideration

### 4. Logging
- Log ALL Hyperliquid API calls (for debugging)
- Log order submissions (symbol, side, quantity, price)
- Log responses (order ID, status, fill data)
- NEVER log decrypted private keys

---

## Available Resources

### Dependencies Already Installed
- `eth-account==0.14.0` - For wallet signing
- `hyperliquid-python-sdk==0.2.7` - For API interaction
- `cryptography==44.0.0` - For decryption

### Existing Code to Reference
- `/backend/utils/encryption.py` - Decryption functions
- `/backend/services/order_executor.py` - Current paper trading logic
- `/backend/database/models.py` - Order and Account models
- `/backend/services/paper_trading_engine.py` - Paper trading simulation (for reference)

### Hyperliquid Documentation
- Main Docs: https://hyperliquid.gitbook.io/
- API Signing: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/signing
- Order Types: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/orders
- Python SDK: https://github.com/hyperliquid-dex/hyperliquid-python-sdk

---

## Success Criteria for Phase 4

### Phase 4A Complete When:
- [ ] WalletSigner class implemented
- [ ] Sign order method works with test private key
- [ ] Signature format matches Hyperliquid requirements
- [ ] Unit tests pass
- [ ] No private keys logged

### Phase 4B Complete When:
- [ ] Order submission to Hyperliquid works (testnet)
- [ ] exchange_order_id stored in database
- [ ] Error handling covers all scenarios
- [ ] Integration tests pass with testnet
- [ ] Manual test with real testnet order succeeds

### Phase 4C Complete When:
- [ ] Order status polling service runs in background
- [ ] Order status updates in database
- [ ] Partial fills handled correctly
- [ ] Service starts/stops cleanly

---

## Development Workflow

### Recommended Order
1. **Phase 4A** (Signing) - 2-3 hours
   - Implement WalletSigner
   - Write unit tests
   - Test signature generation

2. **Phase 4B** (Submission) - 3-4 hours
   - Modify order_executor.py
   - Add Hyperliquid API integration
   - Write integration tests
   - Manual testnet testing

3. **Phase 4C** (Tracking) - 2-3 hours
   - Implement order_tracker.py
   - Add background service
   - Test status updates

### Git Workflow
- Continue on `feature/hyperliquid-phase3-auth` branch, OR
- Create new branch: `feature/hyperliquid-phase4-orders`
- Commit after each sub-phase (4A, 4B, 4C)
- Use conventional commits: `feat(orders):`, `test(signing):`, etc.

### Testing Workflow
```bash
# After Phase 4A
uv run pytest tests/test_wallet_signer.py -v

# After Phase 4B
uv run pytest tests/test_order_submission.py -v

# After Phase 4C
uv run pytest tests/test_order_tracker.py -v

# Run all tests
uv run pytest tests/ -v
```

---

## Common Pitfalls to Avoid

### 1. Signature Format
❌ Don't assume eth-account's default format works
✅ Do verify signature matches Hyperliquid's exact requirements

### 2. Nonce Management
❌ Don't reuse nonces (replay attack vulnerability)
✅ Do generate unique nonce per order (use timestamp + random)

### 3. Private Key Handling
❌ Don't store decrypted key in class attributes
✅ Do decrypt, sign, and immediately discard from memory

### 4. Error Messages
❌ Don't expose technical details to users
✅ Do provide clear, actionable error messages

### 5. Testnet vs Mainnet
❌ Don't hardcode testnet=True
✅ Do use account.testnet_enabled from database

### 6. Order Size Limits
❌ Don't submit orders without size validation
✅ Do implement safety limits (e.g., max $10k per order initially)

---

## Emergency Contacts & Resources

### If Stuck on Signatures
- Read: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/signing
- Check: eth-account documentation for EIP-712 signing
- Reference: Hyperliquid Python SDK examples

### If Stuck on API Integration
- Check: hyperliquid-python-sdk source code
- Test: API endpoints with curl/Postman first
- Verify: Testnet endpoint is reachable

### If Database Issues
- Review: Phase 2 migration (002_add_live_trading_fields.py)
- Verify: exchange_order_id, exchange fields exist in orders table
- Check: account.trading_mode, wallet fields exist

---

## Final Checklist Before Starting

Run this checklist:
- [ ] Read PHASE3-COMPLETE.md thoroughly
- [ ] Read CLAUDE.md Phase 3 section
- [ ] Read /backend/utils/encryption.py
- [ ] Ran pytest and verified 6 tests pass
- [ ] Checked git status (clean working tree)
- [ ] Reviewed Hyperliquid API signing documentation
- [ ] Asked user: merge first or continue to Phase 4?
- [ ] Waited for user's response before writing code

---

## Summary

**What You Know:**
- Phase 3 is complete (wallet storage working)
- All tests passing
- Branch ready to merge or extend

**What You Need to Do:**
1. Load context from documentation files
2. Verify current state
3. Ask user about direction (merge or continue)
4. If continue: Implement Phase 4A (signing) first
5. Test thoroughly before moving to Phase 4B
6. Use testnet exclusively

**What Not to Do:**
- Don't start coding before reading documentation
- Don't skip verification steps
- Don't log private keys
- Don't use mainnet
- Don't assume - ask for clarification

---

**This prompt sets you up for success. Follow the steps in order, and you'll complete Phase 4 smoothly. Good luck!** 🚀
