#!/usr/bin/env python3
"""
Manual Payment Test
===================
Tests payment without relying on airdrop
"""

import asyncio
from payment_module import PaymentModule
from loguru import logger

async def test_manual_payment():
    """Test payment between two wallets (manual funding required)"""
    
    print("\n" + "="*70)
    print("MANUAL PAYMENT TEST - node3 Agent")
    print("="*70 + "\n")
    
    # Initialize wallets
    print("📍 Step 1: Initializing wallets...\n")
    
    marketplace_wallet = PaymentModule(
        rpc_url="https://api.devnet.solana.com",
        wallet_path="./marketplace_wallet.json"
    )
    await marketplace_wallet.initialize()
    
    agent_wallet = PaymentModule(
        rpc_url="https://api.devnet.solana.com",
        wallet_path="./wallet.json"
    )
    await agent_wallet.initialize()
    
    marketplace_address = marketplace_wallet.get_wallet_address()
    agent_address = agent_wallet.get_wallet_address()
    
    print(f"💰 Marketplace Wallet:")
    print(f"   Address: {marketplace_address}")
    marketplace_balance = await marketplace_wallet.get_balance()
    print(f"   Balance: {marketplace_balance} SOL\n")
    
    print(f"💰 Agent Wallet:")
    print(f"   Address: {agent_address}")
    agent_balance = await agent_wallet.get_balance()
    print(f"   Balance: {agent_balance} SOL\n")
    
    # Check if marketplace has funds
    if marketplace_balance < 0.01:
        print("="*70)
        print("⚠️  MARKETPLACE NEEDS FUNDING")
        print("="*70)
        print()
        print("To test payments, fund the marketplace wallet:")
        print()
        print(f"1. Visit: https://faucet.solana.com")
        print(f"2. Paste address: {marketplace_address}")
        print(f"3. Request 2 SOL")
        print(f"4. Wait 30 seconds for confirmation")
        print(f"5. Run this script again")
        print()
        print("="*70)
        await marketplace_wallet.close()
        await agent_wallet.close()
        return False
    
    # Test payment
    print("📍 Step 2: Testing payment transaction...\n")
    payment_amount = 0.001
    
    print(f"Sending {payment_amount} SOL")
    print(f"From: {marketplace_address[:30]}...")
    print(f"To:   {agent_address[:30]}...\n")
    
    agent_balance_before = await agent_wallet.get_balance()
    
    signature = await marketplace_wallet.send_payment(
        to_address=agent_address,
        amount_sol=payment_amount,
        memo="Test payment"
    )
    
    if not signature:
        print("❌ Payment failed!")
        await marketplace_wallet.close()
        await agent_wallet.close()
        return False
    
    print(f"\n✅ Payment sent!")
    print(f"   Transaction: {signature}\n")
    
    # Wait for confirmation
    print("Waiting for blockchain confirmation...")
    await asyncio.sleep(5)
    
    agent_balance_after = await agent_wallet.get_balance()
    received = agent_balance_after - agent_balance_before
    
    print()
    print("="*70)
    print("RESULTS")
    print("="*70)
    print(f"Agent balance before:  {agent_balance_before:.9f} SOL")
    print(f"Agent balance after:   {agent_balance_after:.9f} SOL")
    print(f"Amount received:       {received:.9f} SOL")
    print(f"Expected:              {payment_amount:.9f} SOL")
    print()
    
    if received >= payment_amount * 0.95:  # Allow for fees
        print("✅ SUCCESS! Real payment verified on blockchain!")
        print()
        print("View transaction:")
        print(f"https://explorer.solana.com/tx/{signature}?cluster=devnet")
        print()
        success = True
    else:
        print("⏳ Payment pending - check explorer:")
        print(f"https://explorer.solana.com/tx/{signature}?cluster=devnet")
        print()
        success = False
    
    print("="*70)
    
    await marketplace_wallet.close()
    await agent_wallet.close()
    
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(test_manual_payment())
        
        if result:
            print()
            print("🎉 PAYMENT SYSTEM WORKING!")
            print()
            print("Next: Run the full system:")
            print("  Terminal 1: python mock_marketplace.py")
            print("  Terminal 2: python main.py")
            print()
        
    except KeyboardInterrupt:
        print("\n\nTest cancelled")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

