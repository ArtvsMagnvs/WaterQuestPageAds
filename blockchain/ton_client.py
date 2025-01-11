# blockchain/ton_client.py
from typing import Optional
import logging
from tonsdk.client import TonClient, TonClientException
from tonsdk.utils import Address
from tonsdk.contract import Contract
from bot.config.ton_config import TON_CONFIG

logger = logging.getLogger(__name__)

class TONClient:
    def __init__(self, network: str = "testnet"):
        if network not in ["testnet", "mainnet"]:
            raise ValueError("Network must be either 'testnet' or 'mainnet'")
            
        self.network = network
        self.endpoint = TON_CONFIG["networks"][network]["endpoint"]
        self.api_key = TON_CONFIG["networks"][network]["api_key"]
        self.contract_address = TON_CONFIG["contract"][network]["address"]
        self.owner_wallet = TON_CONFIG["wallet"][network]["address"]
        self.owner_key = TON_CONFIG["wallet"][network]["private_key"]
        self.client = None
        self.contract = None


    async def init_connection(self):
        try:
            # Use the endpoint and api_key from initialization
            self.client = TonClient(
                endpoint=self.endpoint,  # Use self.endpoint instead of network_config
                api_key=self.api_key     # Use self.api_key directly
            )
            
            # Initialize contract with network-specific address
            self.contract = Contract(
                address=Address(self.contract_address),
                client=self.client
            )
            
            # Verify owner wallet connection
            owner_balance = await self.get_balance(self.owner_wallet)
            if owner_balance is None:
                raise TonClientException("Failed to verify owner wallet")

            await self.client.get_balance(self.contract_address)
            logger.info(f"Successfully connected to TON {self.network}")
            return True
        except TonClientException as e:
            logger.error(f"Failed to initialize TON connection: {e}")
            return False
    
    

    async def send_transaction(self, address: str, amount: float):
        try:
            # Convert amount to nanotons (1 TON = 10^9 nanotons)
            amount_nanotons = int(amount * 1e9)
            
            # Create and sign transaction using owner wallet
            transaction = {
                "from": self.owner_wallet,
                "to": address,
                "value": amount_nanotons,
                "bounce": False,
                "private_key": self.owner_key
            }
            
            # Send transaction
            result = await self.client.send_transaction(transaction)
            
            logger.info(f"Transaction sent on {self.network}: {result['transaction_id']}")
            return result['transaction_id']
        except TonClientException as e:
            logger.error(f"Transaction failed on {self.network}: {e}")
            return None

    async def interact_with_contract(self, method: str, params: dict):
        try:
            # Add network-specific parameters
            params["network"] = self.network
            
            # Call contract method
            result = await self.contract.call_method(
                method_name=method,
                input_params=params,
                private_key=self.owner_key
            )
            
            if result.success:
                logger.info(f"Contract interaction successful on {self.network}: {method}")
                return result.decoded_output
            else:
                logger.error(f"Contract call failed on {self.network}: {result.error}")
                return None
        except TonClientException as e:
            logger.error(f"Contract interaction failed on {self.network}: {e}")
            return None

    async def verify_payment(self, transaction_id: str) -> bool:
        try:
            # Get transaction details with network context
            tx = await self.client.get_transaction(transaction_id)
            
            if tx and tx['status'] == 'completed':
                logger.info(f"Payment verified on {self.network}: {transaction_id}")
                return True
            
            logger.warning(f"Payment not verified on {self.network}: {transaction_id}")
            return False
        except TonClientException as e:
            logger.error(f"Payment verification failed on {self.network}: {e}")
            return False

    async def get_balance(self, address: str) -> Optional[float]:
        try:
            balance = await self.client.get_balance(address)
            return float(balance) / 1e9  # Convert from nanotons to TON
        except TonClientException as e:
            logger.error(f"Failed to get balance on {self.network}: {e}")
            return None

    def switch_network(self, network: str):
        """Switch between testnet and mainnet"""
        if network not in ["testnet", "mainnet"]:
            raise ValueError("Network must be either 'testnet' or 'mainnet'")
        
        self.__init__(network)
        logger.info(f"Switched to {network}")
