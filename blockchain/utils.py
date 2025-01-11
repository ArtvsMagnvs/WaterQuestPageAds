from typing import Dict, Any
from bot.config import NETWORK_CONFIG, CONTRACT_CONFIG

def get_network_params(network: str = 'testnet') -> Dict[str, Any]:
    """Get network configuration parameters"""
    return {
        'endpoint': NETWORK_CONFIG[network]['endpoint'],
        'api_key': NETWORK_CONFIG[network]['api_key'],
        'contract_address': CONTRACT_CONFIG[network]['address'],
        'owner_wallet': CONTRACT_CONFIG[network]['owner_wallet']
    }