# config/shop_items.py

from typing import Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

EXPONENTIAL_GROWTH = 2  # Each level increases cost and benefits by 100%



# Regular shop items
SHOP_ITEMS = [
    {
        "nombre": "Juguete",
        "nivel_base": 1,
        "costo_base": 50,
        "oro_hora_base": 1,
        "descripcion": "Un juguete simple que aumenta la producción de oro",
        "emoji": "🎾"
    },
    {
        "nombre": "Casa",
        "nivel_base": 1,
        "costo_base": 200,
        "oro_hora_base": 5,
        "descripcion": "Una casa pequeña que mejora la producción de oro",
        "emoji": "🏠"
    },
    {
        "nombre": "Almohada de Lujo",
        "nivel_base": 1,
        "costo_base": 500,
        "oro_hora_base": 15,
        "descripcion": "Una almohada cómoda que aumenta significativamente la producción",
        "emoji": "🛏️"
    },
    {
        "nombre": "Comedero Automático",
        "nivel_base": 1,
        "costo_base": 1000,
        "oro_hora_base": 30,
        "descripcion": "Alimentador automático que genera una buena cantidad de oro",
        "emoji": "🍽️"
    },
    {
        "nombre": "Parque de Juegos",
        "nivel_base": 1,
        "costo_base": 5000,
        "oro_hora_base": 100,
        "descripcion": "Un parque completo que genera mucho oro",
        "emoji": "🎪"
    },
    {
        "nombre": "Palacio para Mascotas",
        "nivel_base": 1,
        "costo_base": 20000,
        "oro_hora_base": 500,
        "descripcion": "Un palacio lujoso que genera enormes cantidades de oro",
        "emoji": "🏰"
    }
]

# Premium shop items
PREMIUM_SHOP_ITEMS = {
    "premium_status": {
        "name": "👑 Premium Status",
        "description": (
            "Aumenta todo tu progreso x1.5 por un mes\n"
            "• +10 Combates Rápidos diarios\n"
            "• +4 eventos MiniBoss\n"
            "• Recolecta comida automáticamente cada 4 horas\n"
            "• Recompensas diarias mejoradas\n"
            "• 3 Fragmentos de Destino semanales"
        ),
        "price": 3.0,  # 3 USDT in TON
        "duration": 30 * 24 * 60 * 60,  # 30 days in seconds
        "type": "subscription"
    },
    "fragmento_de_destino_1": {
        "name": "🎫 1 Fragmento de Destino",
        "description": "1 Fragmento de Destino para el Portal de las Mareas",
        "price": 0.25,  # 0.25 USDT in TON
        "amount": 1,
        "type": "consumable"
    },
    "fragmento_de_destino_5": {
        "name": "🎫 5 Fragmentos de Destino",
        "description": "5 Fragmentos de Destino para el Portal de las Mareas",
        "price": 1.0,  # 1 USDT in TON
        "amount": 5,
        "type": "consumable"
    },
    "fragmento_de_destino_10": {
        "name": "🎫 10 Fragmentos de Destino",
        "description": "10 Fragmentos de Destino para el Portal de las Mareas",
        "price": 1.5,  # 1.5 USDT in TON
        "amount": 10,
        "type": "consumable"
    }
}


class ShopManager:
    @staticmethod
    def calculate_item_stats(item: dict, current_level: int) -> dict:
        """Calculate item's current cost and production based on level."""
        costo = int(item["costo_base"] * (EXPONENTIAL_GROWTH ** (current_level - 1)))
        oro_hora = int(item["oro_hora_base"] * (EXPONENTIAL_GROWTH ** (current_level - 1)))
        
        return {
            "nombre": item["nombre"],
            "nivel": current_level,
            "costo": costo,
            "oro_hora": oro_hora,
            "descripcion": item["descripcion"],
            "emoji": item["emoji"]
        }

    @staticmethod
    def get_item_by_name(name: str, current_level: int = 1) -> Optional[dict]:
        """Get a shop item by its name with calculated stats for current level."""
        base_item = next((item for item in SHOP_ITEMS if item["nombre"] == name), None)
        if base_item:
            return ShopManager.calculate_item_stats(base_item, current_level)
        return None

    @staticmethod
    def get_premium_item_by_name(name: str) -> Optional[dict]:
        """Get a premium shop item by its name."""
        return PREMIUM_SHOP_ITEMS.get(name)

    @staticmethod
    def format_item_info(item: dict, current_level: int = 1) -> str:
        """Format item information for display."""
        calculated_item = ShopManager.calculate_item_stats(item, current_level)
        return (
            f"{item['emoji']} {item['nombre']} (Nivel {current_level})\n"
            f"💰 Costo: {calculated_item['costo']} oro\n"
            f"⚡ Producción: {calculated_item['oro_hora']} oro/min\n"
            f"📝 {item['descripcion']}\n"
        )

    @staticmethod
    def format_premium_item_info(item: dict) -> str:
        """Format premium item information for display."""
        return (
            f"{item['name']}\n"
            f"💎 Precio: {item['price']} TON\n"
            f"📝 {item['description']}\n"
        )