# utils/keyboard.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional, Dict

def generar_botones(player: Optional[dict] = None) -> InlineKeyboardMarkup:
    """Generate main game menu buttons."""
    botones = []
    
    # Basic buttons always present
    botones.append([InlineKeyboardButton("🎮 Iniciar Juego 🎮", callback_data="start")])
    botones.append([InlineKeyboardButton("🎁 Recompensa Diaria 🎁", callback_data="daily_reward")])
    botones.append([InlineKeyboardButton("🌾 Recolectar Comida 🌾", callback_data="recolectar")])
    botones.append([InlineKeyboardButton("🍖 Alimentar Mascota 🍖", callback_data="alimentar")])
    botones.append([InlineKeyboardButton("📊 Ver Estado 📊", callback_data="estado")])
    botones.append([InlineKeyboardButton("🏪 Ir a la Tienda 🏪", callback_data="tienda")])
    botones.append([InlineKeyboardButton("🎁 Bonus Gratis (Ads)", callback_data="ads_menu")])
    
    # Combat buttons
    botones.append([InlineKeyboardButton("⚔️ Combate Rápido ⚔️", callback_data="combate")])
    botones.append([InlineKeyboardButton("🗺️ MiniBoss 🗺️", callback_data="miniboss")])
    
    # Premium shop and Portal buttons
    botones.append([InlineKeyboardButton("💎 Tienda Premium 💎", callback_data="premium_shop")])
    botones.append([InlineKeyboardButton("🌊 Portal de las Mareas 🌊", callback_data="portal")])

    # USDT Contests & USDT Mining
    botones.append([InlineKeyboardButton("🏆 Concurso Semanal USDT", callback_data="weekly_contest")])

    
    # If player data is provided, add conditional buttons
    if player:
        # Add prestige button if max level
        if player['mascota']['nivel'] >= 100:
            botones.append([InlineKeyboardButton("✨ Realizar Prestige ✨", callback_data="do_prestige")])
    
    # Special content buttons (always available)
    botones.append([InlineKeyboardButton("📜 WaterQuest 📜", callback_data="waterquest_menu")])

    return InlineKeyboardMarkup(botones)

def create_shop_keyboard(items: List[dict], player_gold: int) -> InlineKeyboardMarkup:
    """Generate shop menu buttons."""
    keyboard = []
    
    for item in items:
        if player_gold >= item['costo']:
            emoji = item['emoji']
            keyboard.append([InlineKeyboardButton(
                f"Comprar {emoji} {item['nombre']} ({item['costo']} oro)",
                callback_data=f"comprar_{item['nombre']}"
            )])
    
    # Add navigation buttons
    keyboard.append([
        InlineKeyboardButton("💎 Tienda Premium", callback_data="premium_shop"),
        InlineKeyboardButton("🏠 Volver", callback_data="start")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_premium_shop_keyboard(items: dict) -> InlineKeyboardMarkup:
    """Generate premium shop menu buttons."""
    keyboard = []
    
    for item_id, item in items.items():
        keyboard.append([InlineKeyboardButton(
            f"Comprar {item['name']} ({item['price']} TON)",
            callback_data=f"premium_buy_{item_id}"
        )])
    
    keyboard.append([
        InlineKeyboardButton("🏪 Tienda Normal", callback_data="tienda"),
        InlineKeyboardButton("🏠 Volver", callback_data="start")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_miniboss_keyboard(stage: int) -> InlineKeyboardMarkup:
    """Generate MiniBoss battle buttons."""
    keyboard = []
    
    if stage < 5:  # Not final boss
        keyboard.append([InlineKeyboardButton("⚔️ Siguiente Combate", callback_data="siguiente_miniboss")])
        keyboard.append([InlineKeyboardButton("🏃 Retirarse", callback_data="retirarse_miniboss")])
    else:
        keyboard.append([InlineKeyboardButton("🏠 Volver al Menú", callback_data="start")])
    
    return InlineKeyboardMarkup(keyboard)

def create_confirmation_keyboard(
    confirm_data: str,
    cancel_data: str = "start",
    confirm_text: str = "✅ Confirmar",
    cancel_text: str = "❌ Cancelar"
) -> InlineKeyboardMarkup:
    """Generate confirmation buttons."""
    keyboard = [[
        InlineKeyboardButton(confirm_text, callback_data=confirm_data),
        InlineKeyboardButton(cancel_text, callback_data=cancel_data)
    ]]
    return InlineKeyboardMarkup(keyboard)

def create_combat_keyboard(battles_left: int) -> InlineKeyboardMarkup:
    """Generate combat result buttons."""
    keyboard = []
    
    if battles_left > 0:
        keyboard.append([InlineKeyboardButton("⚔️ Otro Combate", callback_data="combate")])
    
    keyboard.append([InlineKeyboardButton("🏠 Volver", callback_data="start")])
    
    return InlineKeyboardMarkup(keyboard)

def create_portal_keyboard(tickets: int) -> InlineKeyboardMarkup:
    """Generate Portal of Tides buttons."""
    keyboard = []
    
    if tickets > 0:
        keyboard.append([InlineKeyboardButton("🌊 Abrir Portal (1 Fragmento)", callback_data="portal_spin_1")])
        if tickets >= 10:
            keyboard.append([InlineKeyboardButton("🌟 10 Aperturas (Raro+ garantizado)", callback_data="portal_spin_10")])
    
    keyboard.append([InlineKeyboardButton("🏠 Volver", callback_data="start")])
    
    return InlineKeyboardMarkup(keyboard)

def create_waterquest_menu_keyboard() -> InlineKeyboardMarkup:
    """Generate WaterQuest menu buttons."""
    keyboard = []
    
    # Available quests
    keyboard.append([
        InlineKeyboardButton("📜 La Voz del Abismo", callback_data="start_voice_of_abyss")
    ])
    
    # Navigation
    keyboard.append([InlineKeyboardButton("🏠 Volver al Menú", callback_data="start")])
    
    return InlineKeyboardMarkup(keyboard)

def create_waterquest_dialogue_keyboard(responses: List[Dict]) -> InlineKeyboardMarkup:
    """Generate dialogue choice buttons for WaterQuest."""
    keyboard = []
    
    for response in responses:
        keyboard.append([
            InlineKeyboardButton(
                response["text"],
                callback_data=f"quest_choice_{response['id']}"
            )
        ])
    
    return InlineKeyboardMarkup(keyboard)

def create_menu_keyboard(current_menu: str = "main") -> InlineKeyboardMarkup:
    """Generate navigation menu buttons."""
    menus = {
        "main": [
            [InlineKeyboardButton("🎮 Jugar", callback_data="start")],
            [InlineKeyboardButton("📊 Estadísticas", callback_data="stats")],
            [InlineKeyboardButton("❓ Ayuda", callback_data="help")]
        ],
        "stats": [
            [InlineKeyboardButton("👥 Mi Perfil", callback_data="profile")],
            [InlineKeyboardButton("🏆 Ranking", callback_data="ranking")],
            [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")]
        ],
        "help": [
            [InlineKeyboardButton("📖 Guía", callback_data="guide")],
            [InlineKeyboardButton("💬 Soporte", callback_data="support")],
            [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")]
        ]
    }
    
    return InlineKeyboardMarkup(menus.get(current_menu, menus["main"]))