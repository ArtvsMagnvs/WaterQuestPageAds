# config/__init__.py

from .settings import *
from .shop_items import *
from .ton_config import TON_CONFIG

__all__ = [
    'TOKEN',
    'GAME_INFO',
    'SHOP_ITEMS',
    'PREMIUM_SHOP_ITEMS',
    'ShopManager'
    'TON_CONFIG'
]