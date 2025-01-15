# WaterQuest/__init__.py

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode
from bot.config import config
from bot.handlers import register_handlers
from database.db import Database

"""
WaterQuest - Telegram Bot Game
A pet-raising and combat game with premium features and progression systems.
"""

__version__ = '1.0.0'
__author__ = 'Artvs Magnvs'
__license__ = 'Private'

# Game information
GAME_INFO = {
    'name': 'WaterQuest',
    'version': __version__,
    'description': 'Pet-raising and combat Telegram bot game',
    'commands': {
        'start': 'Iniciar el juego',
        'help': 'Ver comandos y ayuda',
        'stats': 'Ver estadísticas detalladas'
    }
}

# Import main components for easier access
from bot.config.settings import *
from bot.handlers import *
from bot.utils import *

# Define what gets imported with "from WaterQuest import *"
__all__ = [
    'GAME_INFO',
    '__version__',
    '__author__',
    '__license__'
]