# config/settings.py

import os
from pathlib import Path
import logging

# Bot Configuration
TOKEN = os.getenv("BOT_TOKEN")

# Save System Settings
SAVE_FILE = 'game_data.json'
BACKUP_DIR = 'backups'
MAX_BACKUPS = 5


# Time Constants
HORA_EN_SEGUNDOS = 8 * 60 * 60
AUTO_SAVE_INTERVAL = 300  # 5 minutes in seconds

# Image Paths
IMAGES_DIR = Path("bot/images")
IMAGE_PATHS = {
    'estado': IMAGES_DIR / "1.webp",
    'recolectar': IMAGES_DIR / "2.webp",
    'alimentar': IMAGES_DIR / "3.webp"
}

# Game Constants
MAX_BATTLES_PER_DAY = 20
MIN_MINIBOSS_GOLD = 1
COMBAT_LEVEL_REQUIREMENT = 1
PET_LEVEL_REQUIREMENT = 1
MAX_COMBAT_LEVEL = 100

# Combat Constants
BASE_VICTORY_CHANCE = 0.75
EXP_MULTIPLIER = 1.1
GOLD_PER_LEVEL = 0.5

# Pet Constants
HUNGER_LOSS_RATE = 1  # Hunger points lost per minute
ENERGY_GAIN_RATE = 2  # Energy points gained per minute
MAX_ENERGY = 100
MAX_HUNGER = 100
PET_MAX_LEVEL = 100

# Prestige System
PRESTIGE_SETTINGS = {
    "gold_kept_percent": 10,  # Keep 10% of gold on prestige
    "base_gold_growth": 2,    # Base exponential growth per level
    "prestige_multipliers": { # Exponential growth gets faster with each prestige
        0: 1,     # No prestige
        1: 2,     # 2x faster growth
        2: 4,     # 4x faster growth
        3: 8,     # 8x faster growth
        4: 16,    # And so on...
        5: 32,
        # Will continue exponentially (2^prestige_level)
    }
}

def calculate_gold_production(level: int, prestige_level: int, is_premium: bool = False) -> int:
    """
    Calculate gold production per minute based on:
    - Pet level (1-100)
    - Prestige level (exponential multiplier)
    - Premium status (1.5x multiplier if premium)
    """
    base_production = PRESTIGE_SETTINGS["base_gold_growth"] ** (level - 1)
    prestige_multiplier = PRESTIGE_SETTINGS["prestige_multipliers"].get(
        prestige_level, 
        2 ** prestige_level
    )
    production = base_production * prestige_multiplier
    if is_premium:
        production = int(production * 1.5)
    return int(production)

# MiniBoss System
def calculate_miniboss_probabilities(combat_level):
    """
    Calculates MiniBoss success probabilities based on combat level
    Level 1: 45% -> 95% (First enemy)
    Level 1: 35% -> 85% (Second enemy)
    Level 1: 25% -> 75% (Third enemy)
    Level 1: 15% -> 65% (Fourth enemy)
    Level 1: 5% -> 45% (Boss)
    """
    increase_per_level = {
        1: (0.95 - 0.45) / 99,  # From 45% to 95%
        2: (0.85 - 0.35) / 99,  # From 35% to 85%
        3: (0.75 - 0.25) / 99,  # From 25% to 75%
        4: (0.65 - 0.15) / 99,  # From 15% to 65%
        5: (0.45 - 0.05) / 99   # From 5% to 45%
    }

    base_probabilities = {
        1: 0.45,  # First enemy
        2: 0.35,  # Second enemy
        3: 0.25,  # Third enemy
        4: 0.15,  # Fourth enemy
        5: 0.05   # Boss
    }

    current_probabilities = {}
    for enemy_level in range(1, 6):
        probability = base_probabilities[enemy_level] + (increase_per_level[enemy_level] * (min(combat_level, 100) - 1))
        current_probabilities[enemy_level] = round(probability, 3)

    return current_probabilities

# MiniBoss Rewards
MINIBOSS_REWARDS = {
    1: {  # First enemy
        "oro": (0, 500),
        "coral": (1, 3),
        "exp_multiplier": 2
    },
    2: {  # Second enemy
        "oro": (500, 1500),
        "coral": (3, 5),
        "exp_multiplier": 10
    },
    3: {  # Third enemy
        "oro": (2000, 5000),
        "coral": (5, 15),
        "exp_multiplier": 25
    },
    4: {  # Fourth enemy
        "oro": (5000, 10000),
        "coral": (15, 30),
        "exp_multiplier": 50
    },
    5: {  # Boss
        "oro": (10000, 50000),
        "coral": (50, 100),
        "exp_multiplier": 100
    }
}

def calculate_miniboss_rewards(enemy_level: int, player_level: int, prestige_level: int) -> dict:
    """Calculate MiniBoss rewards with exponential scaling."""
    base_rewards = MINIBOSS_REWARDS[enemy_level]
    
    # Calculate level multiplier (exponential growth)
    level_multiplier = 1.1 ** player_level
    
    # Calculate prestige multiplier (exponential growth)
    prestige_multiplier = 2 ** prestige_level if prestige_level > 0 else 1
    
    # Calculate final rewards
    min_oro, max_oro = base_rewards["oro"]
    min_coral, max_coral = base_rewards["coral"]
    
    return {
        "oro": (
            int(min_oro * level_multiplier * prestige_multiplier),
            int(max_oro * level_multiplier * prestige_multiplier)
        ),
        "coral": (
            int(min_coral * level_multiplier * prestige_multiplier),
            int(max_coral * level_multiplier * prestige_multiplier)
        ),
        "exp_multiplier": base_rewards["exp_multiplier"] * (1.5 ** prestige_level)
    }

RETREAT_PENALTY = 0.5  # 50% penalty on rewards when retreating

# Daily Rewards System
DAILY_REWARDS = {
    "basic": {
        "oro": (100, 500),
        "coral": (1, 3),
        "comida": (10, 20),
        "energia": 100,
        "exp": (50, 100),
        "fragmento_del_destino": (100, 300)
    },
    "premium": {
        "oro": (500, 2000),
        "coral": (3, 8),
        "comida": (30, 50),
        "energia": 100,
        "exp": (100, 250),
        
    },
    "streak_bonuses": {
        3: 1.5,    # 3 days streak = 1.5x rewards
        7: 2.0,    # 7 days streak = 2x rewards
        14: 2.5,   # 14 days streak = 2.5x rewards
        30: 3.0    # 30 days streak = 3x rewards
    },
    "premium_streak_bonuses": {
        3: 2.0,    # 3 days streak = 2x rewards
        7: 3.0,    # 7 days streak = 3x rewards
        14: 4.0,   # 14 days streak = 4x rewards
        30: 5.0    # 30 days streak = 5x rewards
    },
    "cooldown": 24 * 60 * 60,
    "weekly_reset": 7 * 24 * 60 * 60
}

def calculate_daily_rewards(reward_type: str, player_level: int, prestige_level: int) -> dict:
    """Calculate daily rewards with exponential scaling."""
    base_rewards = DAILY_REWARDS[reward_type]
    
    # Calculate level multiplier (exponential growth)
    level_multiplier = 1.1 ** player_level
    
    # Calculate prestige multiplier (exponential growth)
    prestige_multiplier = 2 ** prestige_level if prestige_level > 0 else 1
    
    # Calculate final rewards
    min_oro, max_oro = base_rewards["oro"]
    min_coral, max_coral = base_rewards["coral"]
    min_comida, max_comida = base_rewards["comida"]
    min_exp, max_exp = base_rewards["exp"]
    min_tickets, max_tickets = base_rewards["fragmento_del_destino"]
    
    return {
        "oro": (
            int(min_oro * level_multiplier * prestige_multiplier),
            int(max_oro * level_multiplier * prestige_multiplier)
        ),
        "coral": (
            int(min_coral * level_multiplier * prestige_multiplier),
            int(max_coral * level_multiplier * prestige_multiplier)
        ),
        "comida": (
            int(min_comida * level_multiplier),
            int(max_comida * level_multiplier)
        ),
        "energia": base_rewards["energia"],
        "exp": (
            int(min_exp * level_multiplier * prestige_multiplier),
            int(max_exp * level_multiplier * prestige_multiplier)
        ),
        "fragmento_del_destino": (
            int(min_tickets * prestige_multiplier),
            int(max_tickets * prestige_multiplier)
        )
    }
# Experience Settings
def exp_needed_for_level(level):
    return int(100 * (1.5 ** level))

def calculate_exp_gain(enemy_level):
    return int(10 * (1.1 ** enemy_level))

def calculate_gold_per_min(player_level):
    return max(1, int(player_level * GOLD_PER_LEVEL))

# Shop Constants
MAX_ITEM_LEVEL = 10
ITEM_UPGRADE_MULTIPLIER = 3

# Error Messages
ERROR_MESSAGES = {
    "no_game": "¡Primero debes iniciar el juego con /start!",
    "no_energy": "¡Tu mascota no tiene energía! Debes esperar.",
    "no_gold": "No tienes suficiente oro para esta acción.",
    "max_battles": "¡Ya has realizado todas tus batallas del día!",
    "level_requirement": "No cumples con el nivel requerido para esta acción.",
    "generic_error": "Ha ocurrido un error. Por favor, intenta nuevamente.",
    "no_miniboss_gold": "¡Necesitas 50 de oro para iniciar una batalla contra MiniBoss!",
    "daily_reward_wait": "⏰ Debes esperar {} horas y {} minutos para tu próxima recompensa diaria.",
    "daily_reward_error": "❌ Error al reclamar la recompensa diaria. Intenta nuevamente.",
    "prestige_level_required": "⚠️ Necesitas alcanzar el nivel {} para realizar un Prestige.",
    "prestige_error": "❌ Error al realizar el Prestige. Intenta nuevamente.",
    "message_edit_failed": "No se pudo editar el mensaje. Intentando enviar uno nuevo...",
    "message_expired": "El mensaje ha expirado. Por favor, intenta la acción nuevamente.",
    "message_not_found": "No se encontró el mensaje para editar. Intentando enviar uno nuevo..."
}

# Weekly Contest Settings
WEEKLY_CONTEST = {
    "enabled": True,
}

# Success Messages
SUCCESS_MESSAGES = {
    # Basic Game Messages
    "welcome": "¡Bienvenido! Has recibido una mascota. Cuida de ella.",
    "food_collected": "Recolectaste 1 comida. Tienes ahora {} comidas.",
    "pet_fed": "¡Tu mascota subió al nivel {}! Oro por minuto: {}, Hambre: {}",
    "item_purchased": "¡Compraste {}! Ahora tienes {} en tu inventario.",
    
    # Combat Messages
    "miniboss_victory": (
        "🎉 ¡MiniBoss derrotado!\n"
        "Recompensas finales:\n"
        "💰 Oro: {}\n"
        "🌺 Coral de Fuego: {}\n"
        "💫 EXP: {}"
    ),
    
    # Daily Reward Messages
    "daily_reward": (
        "🎁 ¡Recompensa Diaria!\n\n"
        "Recibiste:\n"
        "💰 {} oro\n"
        "🌺 {} coral\n"
        "🍖 {} comida\n"
        "🎫 {} fragmentos_del_destino\n"
        "⚡ Energía restaurada\n"
        "💫 {} exp\n\n"
        "🔥 Racha actual: {} días"
    ),
    "daily_reward_premium": (
        "👑 ¡Bonus Premium!\n"
        "¡Todas las recompensas mejoradas!\n"
        "{}"
    ),
    "weekly_tickets": "🎫 ¡Recibiste 3 y Fragmentos del Destino semanales!",
    "streak_bonus": "✨ ¡Bonus de racha x{}!",
    
    # Prestige Messages
    "prestige_available": (
        "✨ ¡Nivel Máximo Alcanzado!\n\n"
        "Puedes realizar un Prestige para:\n"
        "• Reiniciar al nivel 1\n"
        "• Multiplicador de oro x{}\n"
        "• Mantener el {}% de tu oro actual\n"
        "• Conservar items de tienda y progreso de combate\n\n"
        "¿Deseas realizar el Prestige?"
    ),
    "prestige_complete": (
        "🌟 ¡Prestige Completado!\n"
        "• Nivel de Prestige: {}\n"
        "• Nuevo multiplicador: x{}\n"
        "• Oro conservado: {}\n"
        "¡Tu producción de oro crecerá más rápido que nunca!"
    )
}



# Feature Flags
FEATURES = {
    "auto_save": True,
    "backup_system": True,
    "combat_system": True,
    "miniboss_system": True,
    "shop_system": True,
    "prestige_system": True
}

# Logging Configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)