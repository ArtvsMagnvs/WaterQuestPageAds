# config/ton_config.py
import os
from dotenv import load_dotenv

# Load environment variables from ton_settings.env
load_dotenv('config/ton_settings.env')

TON_CONFIG = {
    "networks": {
        "testnet": {
            "endpoint": os.getenv('TESTNET_ENDPOINT'),
            "api_key": os.getenv('TESTNET_API_KEY'),
        },
        "mainnet": {
            "endpoint": os.getenv('MAINNET_ENDPOINT'),
            "api_key": os.getenv('MAINNET_API_KEY'),
        }
    },
    "contract": {
        "testnet": {
            "address": os.getenv('TESTNET_CONTRACT_ADDRESS'),
            "owner_wallet": os.getenv('TESTNET_OWNER_WALLET')
        },
        "mainnet": {
            "address": os.getenv('MAINNET_CONTRACT_ADDRESS'),
            "owner_wallet": os.getenv('MAINNET_OWNER_WALLET')
        },
        "min_ton_for_storage": 50000000,  # 0.05 TON
        "premium_price": 3.0,  # 3 USDT in TON
        "tickets": {
            "single": {
                "price": 0.25,  # 0.25 USDT in TON
                "amount": 1
            },
            "five": {
                "price": 1.0,  # 1 USDT in TON
                "amount": 5
            },
            "ten": {
                "price": 1.5,  # 1.5 USDT in TON
                "amount": 10
            }
        }
    },
    "transaction": {
        "timeout": 60,      # seconds
        "max_retries": 3,
        "retry_delay": 5    # seconds
    },
    "premium_features": {
        "duration": 30 * 24 * 60 * 60,  # 30 days in seconds
        "multiplier": 1.5,  # 1.5x rewards
    }
}