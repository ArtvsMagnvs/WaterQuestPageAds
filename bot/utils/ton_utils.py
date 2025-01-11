# utils/ton_utils.py

import logging
from typing import Dict, Optional, Tuple
from tonsdk.contract import Contract
from tonsdk.utils import Address
from tonsdk.contract import Contract
from tonsdk.utils import Address
from datetime import datetime

import asyncio
from typing import Tuple
from tonsdk.contract import Contract
from tonsdk.utils import Address

from bot.config.ton_config import TON_CONFIG
from bot.utils.save_system import save_game_data

from typing import Tuple
import logging
from datetime import datetime, timedelta
from tonsdk.contract.token.ft import JettonMinter, JettonWallet
from tonsdk.utils import Address
from tonsdk.provider import ToncenterClient
from tonsdk.client import TonClientException, TonClientException as TonClientError
from blockchain.ton_client import TONClient  # Use custom implementation

#---------------------------------------------------------
# Temporarily comment out TON SDK imports
# from tonsdk.client import TonClientException, TonClientException as TonClientError

# Create dummy classes for development
# Temporary TON SDK mock
class TonClientException(Exception):
    pass

TonClientError = TonClientException

def initialize_ton_client():
    return None

def initialize_wallet_manager():
    return None

def create_payment_link():
    return "payment_disabled"

def check_payment_status():
    return True
#----------------------------------------------------------

logger = logging.getLogger(__name__)

# Import required data
from utils.save_system import load_game_data

# Initialize players_data
players_data = load_game_data()

logger = logging.getLogger(__name__)

class TONUtils:
    def __init__(self, network: str = "testnet"):
        """Initialize TON utilities with network configuration."""
        self.network = network
        self.config = TON_CONFIG["networks"][network]
        self.contract_address = TON_CONFIG["contract"][network]["address"]
        self.wallet_config = TON_CONFIG["wallet"][network]

    async def initialize_ton_client(self, network: str = "testnet"):
        """Initialize TON client with network configuration."""
        try:
            # Get network configuration from TON_CONFIG
            config = TON_CONFIG["networks"][network]
            
            # Initialize TON SDK client with network endpoint and API key
            client = {
                'endpoint': config['endpoint'],
                'api_key': config['api_key']
            }
            
            # Test connection
            if client['endpoint'] and client['api_key']:
                return True
            return False
            
        except Exception as e:
            logger.error(f"TON client initialization failed: {e}")
            return False

async def send_transaction(self, address: str, amount: float, message: str = "") -> Tuple[bool, str]:
    """
    Send a TON transaction to specified address.
    
    Args:
        address (str): Destination wallet address
        amount (float): Amount in TON to send
        message (str): Optional message to include
    
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # Validate address
        if not Address.validate(address):
            return False, "Invalid wallet address"

        # Convert amount to nanotons
        amount_nanotons = self.format_ton_amount(amount)
        
        # Create wallet instance from private key
        wallet = Contract(
            address=Address(self.wallet_config['address']),
            private_key=self.wallet_config['private_key']
        )

        # Check if wallet has sufficient balance
        balance = await self.get_wallet_balance(self.wallet_config['address'])
        if balance is None or balance < amount:
            return False, "Insufficient wallet balance"

        # Prepare transaction parameters
        seqno = await wallet.get_seqno()
        tx_params = {
            'dest': Address(address),
            'value': amount_nanotons,
            'seqno': seqno,
            'bounce': False,
            'payload': message.encode() if message else None
        }

        # Sign and send transaction
        signed_tx = wallet.create_transfer_message(**tx_params)
        tx_hash = await wallet.send_transaction(signed_tx)

        # Wait for transaction confirmation
        for _ in range(TON_CONFIG['transaction']['max_retries']):
            status = await self.check_transaction_status(tx_hash)
            if status[0]:  # Transaction confirmed
                return True, f"Transaction sent successfully. Hash: {tx_hash}"
            await asyncio.sleep(TON_CONFIG['transaction']['retry_delay'])

        return False, "Transaction timed out"

    except ValueError as ve:
        logger.error(f"Value error in transaction: {ve}")
        return False, f"Invalid transaction parameters: {str(ve)}"
    except ConnectionError as ce:
        logger.error(f"Connection error: {ce}")
        return False, "Network connection error"
    except Exception as e:
        logger.error(f"Transaction failed: {e}")
        return False, f"Transaction failed: {str(e)}"

async def check_transaction_status(tx_hash: str):
    """Check status of a TON transaction."""
    try:
        # Transaction verification logic would go here
        # Using parameters from TON_CONFIG
        timeout = TON_CONFIG['transaction']['timeout']
        max_retries = TON_CONFIG['transaction']['max_retries']
        
        # Placeholder for transaction status check
        return True, "Transaction confirmed"
        
    except Exception as e:
        logger.error(f"Transaction status check failed: {e}")
        return False, str(e)

async def get_wallet_balance(self, address: str) -> Optional[float]:
    """Get TON wallet balance.
    Args:
        address (str): The wallet address to check
    Returns:
        Optional[float]: The wallet balance in TON, or None if check fails
    """
    try:
        if not await self.initialize_ton_client(self.network):
            logger.error("Failed to initialize TON client")
            return None

        config = self.config
        client = TONClient(
            network=self.network,
            endpoint=config['endpoint'],
            api_key=config['api_key']
        )

        # Initialize connection
        await client.init_connection()

        # Get balance using the custom client's method
        balance = await client.get_balance(address)
        
        if balance is None:
            return 0.0

        # Close client connection
        if hasattr(client, 'client') and client.client:
            await client.client.close()
            
        return balance

    except TonClientException as e:  # Use TonClientException instead
        return None
    except ValueError as e:
        logger.error(f"Value error in balance check: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in balance check: {e}")
        return None
    
class TransactionVerifier:
    def __init__(self, network="mainnet"):
        self.provider = ToncenterClient(base_url="https://toncenter.com/api/v2/")
        self.min_confirmations = 24
        self.max_tx_age = timedelta(hours=1)
        self.wallet_address = TON_CONFIG["contract"][network]["owner_wallet"]
        
    async def verify_transaction(self, tx_hash: str) -> Tuple[bool, str]:
        """
        Verify a TON transaction using its hash.
        Args:
            tx_hash (str): The transaction hash to verify
        Returns:
            Tuple[bool, str]: (success status, message)
        """
        try:
            tx_data = await self.provider.get_transactions(
                address=tx_hash,
                limit=1
            )
            
            if not tx_data:
                return False, "Transaction not found"
                
            transaction = tx_data[0]
            
            if transaction.get('status') != 'completed':
                return False, f"Transaction status: {transaction.get('status')}"
                
            amount = float(transaction.get('amount', 0))
            if amount <= 0:
                return False, "Invalid transaction amount"
                
            recipient = transaction.get('destination')
            if not recipient or recipient != self.wallet_address:
                return False, "Invalid recipient address"
                
            confirmations = transaction.get('confirmations', 0)
            if confirmations < self.min_confirmations:
                return False, f"Insufficient confirmations: {confirmations}/{self.min_confirmations}"
                
            timestamp = datetime.fromtimestamp(transaction.get('timestamp', 0))
            if datetime.now() - timestamp > self.max_tx_age:
                return False, "Transaction too old"
                
            tx_comment = transaction.get('comment', '')
            if not self.validate_transaction_comment(tx_comment):
                return False, "Invalid transaction comment"
                
            block_height = transaction.get('block_height', 0)
            if not self.validate_block_height(block_height):
                return False, "Invalid block height"
                
            return True, "Transaction verified successfully"
            
        except Exception as e:
            error_msg = f"Transaction verification failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
    def validate_transaction_comment(self, comment: str) -> bool:
        if not comment:
            return False
        try:
            # Validate comment format (should be: userId:itemId)
            parts = comment.split(':')
            if len(parts) != 2:
                return False
            user_id, item_id = parts
            return user_id.isdigit() and len(item_id) > 0
        except:
            return False
            
    def validate_block_height(self, height: int) -> bool:
        try:
            latest_block = self.provider.get_masterchain_info()
            if not latest_block:
                return False
            return height > 0 and height <= latest_block.get('last', 0)
        except:
            return False

    async def process_premium_purchase(
        self, 
        user_id: int, 
        players, 
        item_id: str,
        tx_hash: str
    ) -> Tuple[bool, str]:
        """Process a premium feature purchase."""
        try:
            # Verify transaction first
            verified, msg = await self.verify_transaction(tx_hash)
            if not verified:
                return False, msg

            player = players_data.get(user_id)
            if not player:
                return False, "Player not found"

            # Initialize premium features if not exists
            if 'premium_features' not in player:
                player['premium_features'] = {
                    'premium_status': False,
                    'premium_status_expires': 0,
                    'lucky_tickets': 0
                }

            # Process different premium items
            if item_id == "premium_status":
                duration = 30 * 24 * 60 * 60  # 30 days in seconds
                current_time = datetime.now().timestamp()
                player['premium_features']['premium_status'] = True
                player['premium_features']['premium_status_expires'] = current_time + duration

            elif item_id.startswith("lucky_ticket"):
                ticket_amounts = {
                    "lucky_ticket_1": 1,
                    "lucky_ticket_5": 5,
                    "lucky_ticket_10": 10
                }
                amount = ticket_amounts.get(item_id, 0)
                player['premium_features']['lucky_tickets'] += amount

            # Save updated player data
            save_game_data(players_data)
            return True, "Purchase processed successfully"

        except Exception as e:
            logger.error(f"Premium purchase processing failed: {e}")
            return False, str(e)

    async def check_wallet_balance(self, address: str) -> Optional[float]:
        """Check TON wallet balance."""
        try:
            # Implementation for balance checking
            return 0.0  # Placeholder
        except Exception as e:
            logger.error(f"Balance check failed: {e}")
            return None

    async def validate_payment(
        self, 
        tx_hash: str, 
        expected_amount: float
    ) -> Tuple[bool, str]:
        """Validate a payment transaction."""
        try:
            # Implementation for payment validation
            return True, "Payment validated successfully"
        except Exception as e:
            logger.error(f"Payment validation failed: {e}")
            return False, str(e)

    def get_premium_prices(self) -> Dict:
        """Get current premium feature prices."""
        return {
            "premium_status": self.wallet_config["premium_price"],
            "tickets": self.wallet_config["tickets"]
        }

    def get_wallet_address(self) -> str:
        """Get the game's wallet address for the current network."""
        return self.wallet_config["address"]

    @staticmethod
    def format_ton_amount(amount: float) -> int:
        """Convert TON amount to nanotons."""
        return int(amount * 1_000_000_000)