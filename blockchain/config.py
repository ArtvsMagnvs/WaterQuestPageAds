from bot.config.ton_config import TON_CONFIG

# Blockchain network settings
NETWORK_CONFIG = TON_CONFIG['networks']
CONTRACT_CONFIG = TON_CONFIG['contract']
TRANSACTION_CONFIG = TON_CONFIG['transaction']

# Contract deployment settings
MIN_TON_FOR_STORAGE = CONTRACT_CONFIG['min_ton_for_storage']
PREMIUM_PRICE = CONTRACT_CONFIG['premium_price']
TICKET_PRICES = CONTRACT_CONFIG['tickets']
