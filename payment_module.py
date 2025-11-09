# payment_module.py

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders.system_program import TransferParams, transfer
from solders.message import MessageV0
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TxOpts
from typing import Optional, List, Dict
from loguru import logger
import os
import json
import asyncio

class PaymentModule:
    """Handle Solana wallet and payments"""
    
    def __init__(self, 
                 rpc_url: str = "https://api.devnet.solana.com",
                 wallet_path: str = "./wallet.json"):
        self.rpc_url = rpc_url
        self.wallet_path = wallet_path
        self.client = AsyncClient(rpc_url)
        self.keypair: Optional[Keypair] = None
        self.pubkey: Optional[Pubkey] = None
        
    async def initialize(self):
        """Initialize or load wallet"""
        if os.path.exists(self.wallet_path):
            # Load existing wallet
            await self.load_wallet()
        else:
            # Create new wallet
            await self.create_wallet()
            
    async def create_wallet(self):
        """Create a new Solana wallet"""
        try:
            # Generate new keypair
            self.keypair = Keypair()
            self.pubkey = self.keypair.pubkey()
            
            # Save to file
            wallet_data = {
                'public_key': str(self.pubkey),
                'secret_key': list(bytes(self.keypair))
            }
            
            with open(self.wallet_path, 'w') as f:
                json.dump(wallet_data, f)
                
            logger.info(f"New wallet created: {self.pubkey}")
            logger.warning(f"IMPORTANT: Back up your wallet file: {self.wallet_path}")
            
        except Exception as e:
            logger.error(f"Failed to create wallet: {e}")
            raise
            
    async def load_wallet(self):
        """Load existing wallet from file"""
        try:
            with open(self.wallet_path, 'r') as f:
                wallet_data = json.load(f)
                
            # Recreate keypair from secret key
            secret_key_bytes = bytes(wallet_data['secret_key'])
            self.keypair = Keypair.from_bytes(secret_key_bytes)
            self.pubkey = self.keypair.pubkey()
            
            logger.info(f"Wallet loaded: {self.pubkey}")
            
        except Exception as e:
            logger.error(f"Failed to load wallet: {e}")
            raise
            
    async def get_balance(self) -> float:
        """Get wallet balance in SOL"""
        try:
            response = await self.client.get_balance(self.pubkey, commitment=Confirmed)
            balance_lamports = response.value
            balance_sol = balance_lamports / 1e9  # Convert lamports to SOL
            
            logger.info(f"Balance: {balance_sol} SOL")
            return balance_sol
            
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0.0
            
    async def get_recent_transactions(self, limit: int = 10) -> List[Dict]:
        """Get recent transactions for this wallet"""
        try:
            response = await self.client.get_signatures_for_address(
                self.pubkey,
                limit=limit
            )
            
            transactions = []
            for tx in response.value:
                transactions.append({
                    'signature': str(tx.signature),
                    'slot': tx.slot,
                    'block_time': tx.block_time,
                    'confirmation_status': tx.confirmation_status
                })
                
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to get transactions: {e}")
            return []
            
    async def wait_for_payment(self, expected_amount: float, timeout: int = 300) -> bool:
        """
        Wait for an incoming payment
        
        Args:
            expected_amount: Expected payment amount in SOL
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if payment received, False otherwise
        """
        import asyncio
        start_time = asyncio.get_event_loop().time()
        initial_balance = await self.get_balance()
        
        logger.info(f"Waiting for payment of {expected_amount} SOL...")
        
        while True:
            current_time = asyncio.get_event_loop().time()
            if current_time - start_time > timeout:
                logger.warning(f"Payment timeout after {timeout}s")
                return False
                
            current_balance = await self.get_balance()
            
            if current_balance >= initial_balance + expected_amount:
                logger.info(f"Payment received: {current_balance - initial_balance} SOL")
                return True
                
            await asyncio.sleep(5)  # Check every 5 seconds
            
    def get_wallet_address(self) -> str:
        """Get wallet public address as string"""
        return str(self.pubkey)
    
    async def send_payment(self, to_address: str, amount_sol: float, memo: str = "") -> Optional[str]:
        """
        Send SOL to another address
        
        Args:
            to_address: Recipient's wallet address
            amount_sol: Amount to send in SOL
            memo: Optional transaction memo
            
        Returns:
            Transaction signature if successful, None otherwise
        """
        try:
            # Convert SOL to lamports (1 SOL = 1 billion lamports)
            amount_lamports = int(amount_sol * 1e9)
            
            # Create recipient pubkey
            to_pubkey = Pubkey.from_string(to_address)
            
            logger.info(f"Sending {amount_sol} SOL ({amount_lamports} lamports) to {to_address}")
            
            # Create transfer instruction
            transfer_ix = transfer(
                TransferParams(
                    from_pubkey=self.pubkey,
                    to_pubkey=to_pubkey,
                    lamports=amount_lamports
                )
            )
            
            # Get recent blockhash
            recent_blockhash_resp = await self.client.get_latest_blockhash(commitment=Confirmed)
            recent_blockhash = recent_blockhash_resp.value.blockhash
            
            # Create message
            message = MessageV0.try_compile(
                payer=self.pubkey,
                instructions=[transfer_ix],
                address_lookup_table_accounts=[],
                recent_blockhash=recent_blockhash,
            )
            
            # Create and sign transaction
            tx = VersionedTransaction(message, [self.keypair])
            
            # Send transaction
            opts = TxOpts(skip_preflight=False, preflight_commitment=Confirmed)
            response = await self.client.send_transaction(tx, opts)
            signature = str(response.value)
            
            logger.info(f"Payment sent! Signature: {signature}")
            
            # Wait for confirmation
            await self._wait_for_confirmation(signature)
            
            return signature
            
        except Exception as e:
            logger.error(f"Failed to send payment: {e}")
            return None
    
    async def _wait_for_confirmation(self, signature: str, max_retries: int = 30):
        """Wait for transaction confirmation"""
        for i in range(max_retries):
            try:
                response = await self.client.get_signature_statuses([signature])
                if response.value and response.value[0]:
                    status = response.value[0]
                    if status.confirmation_status:
                        logger.info(f"Transaction confirmed: {signature}")
                        return True
                        
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.warning(f"Error checking confirmation: {e}")
                await asyncio.sleep(2)
        
        logger.warning(f"Transaction confirmation timeout: {signature}")
        return False
    
    async def request_airdrop(self, amount_sol: float = 1.0) -> bool:
        """
        Request SOL airdrop from devnet faucet (devnet only!)
        
        Args:
            amount_sol: Amount to request (max 2 SOL per request on devnet)
            
        Returns:
            True if successful
        """
        try:
            if "devnet" not in self.rpc_url and "testnet" not in self.rpc_url:
                logger.error("Airdrop only available on devnet/testnet")
                return False
            
            amount_lamports = int(amount_sol * 1e9)
            logger.info(f"Requesting airdrop of {amount_sol} SOL...")
            
            response = await self.client.request_airdrop(self.pubkey, amount_lamports)
            
            # Check if response has an error
            if hasattr(response, 'value') and response.value:
                signature = str(response.value)
            else:
                logger.error(f"Airdrop request failed: {response}")
                logger.warning("Devnet faucet may be rate limited or unavailable")
                logger.warning(f"Manual funding: https://faucet.solana.com")
                logger.warning(f"Address: {self.pubkey}")
                return False
            
            logger.info(f"Airdrop requested: {signature}")
            
            # Wait for confirmation
            await self._wait_for_confirmation(signature)
            
            new_balance = await self.get_balance()
            logger.info(f"Airdrop successful! New balance: {new_balance} SOL")
            
            return True
            
        except Exception as e:
            logger.error(f"Airdrop failed: {e}")
            logger.warning("You can manually fund the wallet at: https://faucet.solana.com")
            logger.warning(f"Wallet address: {self.pubkey}")
            return False
    
    async def get_transaction_details(self, signature: str) -> Optional[Dict]:
        """Get details of a specific transaction"""
        try:
            response = await self.client.get_transaction(
                signature,
                encoding="json",
                commitment=Confirmed,
                max_supported_transaction_version=0
            )
            
            if response.value:
                tx = response.value
                return {
                    'signature': signature,
                    'slot': tx.slot,
                    'block_time': tx.block_time,
                    'fee': tx.transaction.meta.fee if tx.transaction.meta else 0,
                    'status': 'success' if not tx.transaction.meta.err else 'failed'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get transaction details: {e}")
            return None
        
    async def close(self):
        """Close the RPC client"""
        await self.client.close()

