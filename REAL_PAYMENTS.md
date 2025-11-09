# Real Payments Guide 💰

**node3 Agent now sends REAL SOL payments!** This guide explains how the payment system works and how to test it.

## What's Real?

✅ **Real Solana wallets** - Agent and marketplace have actual Solana keypairs  
✅ **Real blockchain transactions** - Payments are recorded on Solana devnet  
✅ **Real SOL** - You earn actual SOL (devnet SOL for testing)  
✅ **Verifiable on-chain** - All transactions viewable on Solana Explorer  

## How It Works

### 1. Wallet Creation
- Agent creates wallet: `wallet.json`
- Marketplace creates wallet: `marketplace_wallet.json`
- Both are real Solana Ed25519 keypairs

### 2. Job Flow with Payments
```
1. Agent accepts job → Sends wallet address to marketplace
2. Agent completes job → Reports completion
3. Marketplace verifies → Sends SOL payment on-chain
4. Agent receives → Real SOL in wallet (verifiable)
```

### 3. On-Chain Transaction
Every payment creates a real Solana transaction:
- From: Marketplace wallet
- To: Agent wallet
- Amount: Job reward (e.g., 0.001 SOL)
- Memo: Job ID
- Status: Confirmed on blockchain

## Quick Start

### Test Payments (5 minutes)

```bash
# 1. Test the payment system
python test_real_payments.py
```

This will:
- Create wallets for marketplace and agent
- Fund marketplace from devnet faucet
- Send a test payment
- Verify it on-chain

### Run with Real Payments

```bash
# Terminal 1: Start marketplace
python mock_marketplace.py

# Terminal 2: Fund marketplace (one-time)
curl -X POST http://127.0.0.1:8000/api/marketplace/fund

# Terminal 3: Start agent
python main.py

# Watch the magic happen!
# - Agent accepts jobs
# - Completes them
# - Receives REAL SOL payments
# - View transactions in logs
```

## Viewing Your Earnings

### 1. Check Balance (Dashboard)
Open http://localhost:8080 - balance updates in real-time

### 2. Check on Blockchain
```bash
# Get your wallet address from dashboard or logs
# Visit: https://explorer.solana.com/address/YOUR_ADDRESS?cluster=devnet
```

### 3. Via API
```bash
curl http://127.0.0.1:8080/api/status
```

## Devnet vs Mainnet

### Current: Devnet (Testing)
- **RPC**: `https://api.devnet.solana.com`
- **SOL**: Free testnet tokens
- **Purpose**: Testing and development
- **Get SOL**: https://faucet.solana.com

### Future: Mainnet (Production)
To switch to real money (mainnet-beta):
```bash
# In .env file:
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
```

⚠️ **WARNING**: Mainnet uses REAL money! Only switch when ready for production.

## Payment Verification

Every payment includes:
- **Transaction Signature** - Unique identifier
- **Amount** - Exact SOL sent
- **Timestamp** - When payment was made
- **Block** - Blockchain block number

View any transaction:
```
https://explorer.solana.com/tx/SIGNATURE?cluster=devnet
```

## API Endpoints

### Marketplace

```bash
# Get marketplace info
GET /api/marketplace/info

# Response:
{
  "wallet_address": "5Kq7...",
  "balance": 1.5,
  "payments_processed": 10,
  "total_paid": 0.01
}

# Fund marketplace (devnet only)
POST /api/marketplace/fund

# Get payment history
GET /api/payments/history
```

### Agent

```bash
# Get agent status (includes balance)
GET http://localhost:8080/api/status

# Response:
{
  "wallet_address": "7Xm9...",
  "balance": 0.005,
  "active_jobs": 1,
  "completed_jobs": 5
}
```

## Wallet Security

### Testnet (Current)
- ✅ Fine to commit wallet files (devnet only!)
- ✅ No real money at risk
- ✅ Can regenerate anytime

### Mainnet (Production)
- ⚠️ **NEVER** commit wallet files
- ⚠️ Add to `.gitignore`
- ⚠️ Back up securely
- ⚠️ Use hardware wallet if possible

## Troubleshooting

### "Payment failed"
**Cause**: Marketplace has insufficient funds

**Fix**:
```bash
curl -X POST http://127.0.0.1:8000/api/marketplace/fund
```

### "Wallet not initialized"
**Cause**: Payment module startup failed

**Fix**: Check logs for errors, ensure Solana RPC is accessible

### "Transaction timeout"
**Cause**: Network congestion or RPC issues

**Fix**: Wait 30 seconds and check balance - transaction may still process

## Cost Analysis

### Transaction Fees
- **Typical fee**: ~0.000005 SOL ($0.0001 at $20/SOL)
- **Who pays**: Marketplace (sender)
- **Impact**: Negligible for devnet testing

### Example Earnings
```
Job 1: 0.001 SOL (completed)
Job 2: 0.0005 SOL (completed)
Job 3: 0.002 SOL (completed)
---------------------------------
Total: 0.0035 SOL

At $20/SOL = $0.07 USD
```

## Next Steps

### Phase 1: Testing (NOW) ✅
- Run on devnet
- Test payment flow
- Verify on-chain
- **Status**: LIVE

### Phase 2: Beta (Week 2)
- Invite beta testers
- Monitor payment success rate
- Gather feedback

### Phase 3: Production (Month 2)
- Switch to mainnet
- Real SOL payments
- Scale to multiple agents

## Resources

- **Solana Explorer (Devnet)**: https://explorer.solana.com/?cluster=devnet
- **Devnet Faucet**: https://faucet.solana.com
- **Solana Docs**: https://docs.solana.com
- **node3 Docs**: Coming soon!

---

**Ready to earn real SOL?** 🚀

```bash
python test_real_payments.py
python mock_marketplace.py
python main.py
```

Watch those payments roll in! 💸

