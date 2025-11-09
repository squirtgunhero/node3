#!/usr/bin/env python3
"""
Test Real Payments End-to-End
==============================

This script tests the complete payment flow:
1. Start marketplace with wallet
2. Fund marketplace wallet (devnet)
3. Start agent with wallet
4. Accept and complete a job
5. Verify real SOL payment was received
"""

import asyncio
import time
from payment_module import PaymentModule
from loguru import logger

async def test_payments():
    """Test end-to-end payment flow"""
    
    print("\n" + "="*60)
    print("REAL PAYMENT TEST - node3 Agent")
    print("="*60 + "\n")
    
    # Step 1: Initialize marketplace wallet
    print("1️⃣  Initializing marketplace wallet...")
    marketplace_wallet = PaymentModule(
        rpc_url="https://api.devnet.solana.com",
        wallet_path="./marketplace_wallet.json"
    )
    await marketplace_wallet.initialize()
    
    marketplace_address = marketplace_wallet.get_wallet_address()
    marketplace_balance = await marketplace_wallet.get_balance()
    
    print(f"   Marketplace: {marketplace_address}")
    print(f"   Balance: {marketplace_balance} SOL\n")
    
    # Step 2: Initialize agent wallet
    print("2️⃣  Initializing agent wallet...")
    agent_wallet = PaymentModule(
        rpc_url="https://api.devnet.solana.com",
        wallet_path="./wallet.json"
    )
    await agent_wallet.initialize()
    
    agent_address = agent_wallet.get_wallet_address()
    agent_balance_before = await agent_wallet.get_balance()
    
    print(f"   Agent: {agent_address}")
    print(f"   Balance: {agent_balance_before} SOL\n")
    
    # Step 3: Fund marketplace if needed
    if marketplace_balance < 0.1:
        print("3️⃣  Funding marketplace from devnet faucet...")
        print("   (This may take 30-60 seconds)")
        success = await marketplace_wallet.request_airdrop(2.0)
        if success:
            marketplace_balance = await marketplace_wallet.get_balance()
            print(f"   ✅ Marketplace funded: {marketplace_balance} SOL\n")
        else:
            print("   ❌ Airdrop failed")
            print("   Manually fund at: https://faucet.solana.com")
            print(f"   Address: {marketplace_address}\n")
            return False
    else:
        print(f"3️⃣  Marketplace has sufficient funds ({marketplace_balance} SOL)\n")
    
    # Step 4: Send test payment
    payment_amount = 0.001  # 0.001 SOL
    print(f"4️⃣  Sending payment: {payment_amount} SOL")
    print(f"   From: {marketplace_address[:20]}...")
    print(f"   To: {agent_address[:20]}...")
    
    signature = await marketplace_wallet.send_payment(
        to_address=agent_address,
        amount_sol=payment_amount,
        memo="Test job payment"
    )
    
    if not signature:
        print("   ❌ Payment failed!\n")
        return False
    
    print(f"   ✅ Payment sent!")
    print(f"   Transaction: {signature}\n")
    
    # Step 5: Verify payment received
    print("5️⃣  Verifying payment received...")
    print("   (Waiting for confirmation...)")
    
    # Wait a few seconds for confirmation
    await asyncio.sleep(5)
    
    agent_balance_after = await agent_wallet.get_balance()
    received_amount = agent_balance_after - agent_balance_before
    
    print(f"   Balance before: {agent_balance_before} SOL")
    print(f"   Balance after: {agent_balance_after} SOL")
    print(f"   Received: {received_amount} SOL\n")
    
    if received_amount >= payment_amount * 0.95:  # Allow for fees
        print("✅ SUCCESS! Payment verified on blockchain")
        print(f"   View on Solana Explorer:")
        print(f"   https://explorer.solana.com/tx/{signature}?cluster=devnet\n")
        return True
    else:
        print("❌ Payment not received")
        print("   May still be processing - check explorer:")
        print(f"   https://explorer.solana.com/tx/{signature}?cluster=devnet\n")
        return False
    
    # Cleanup
    await marketplace_wallet.close()
    await agent_wallet.close()

if __name__ == "__main__":
    try:
        result = asyncio.run(test_payments())
        
        if result:
            print("="*60)
            print("🎉 REAL PAYMENTS WORKING! 🎉")
            print("="*60)
            print("\nNext steps:")
            print("  1. Run: python mock_marketplace.py")
            print("  2. Run: python main.py")
            print("  3. Complete a job and watch real SOL payments!")
            print()
        else:
            print("="*60)
            print("Payment test incomplete")
            print("="*60)
            
    except KeyboardInterrupt:
        print("\n\nTest cancelled")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

