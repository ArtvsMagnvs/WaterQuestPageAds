# handlers/base.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
import logging
from datetime import datetime

# Import configurations and utilities
from bot.config.settings import SUCCESS_MESSAGES, ERROR_MESSAGES, logger
from bot.utils.keyboard import generar_botones
from bot.utils.save_system import save_game_data

# Import other handlers
from .combat import quick_combat
from .miniboss import miniboss_handler
from .daily import claim_daily_reward
from .shop import tienda, comprar
from .pet import recolectar, alimentar, estado

def initialize_combat_stats(level):
    """Initialize combat stats for a new player."""
    return {
        "level": level,
        "hp": 100 + (level * 10),
        "atk": 10 + (level * 2),
        "mp": 50 + (level * 5),
        "def_p": 5 + (level * 1.5),
        "def_m": 5 + (level * 1.5),
        "agi": 10 + (level * 1),
        "sta": 100 + (level * 5),
        "battles_today": 0,
        "last_battle_date": None,
        "exp": 0,
        "fire_coral": 0
    }

def initialize_new_player():
    """Initialize data for a new player."""
    return {
        "mascota": {
            "hambre": 100,
            "energia": 100,
            "nivel": 1,
            "oro": 0,
            "oro_hora": 1,
        },
        "comida": 0,
        "última_alimentación": datetime.now().timestamp(),
        "última_actualización": datetime.now().timestamp(),
        "inventario": {},
        "combat_stats": initialize_combat_stats(0),
        "daily_reward": {
            "last_claim": 0,
            "streak": 0
        },
        "premium_features": {
            "premium_status": False,
            "premium_status_expires": 0,
            "auto_collector": False,
            "auto_collector_expires": 0,
            "daily_bonus": False,
            "lucky_tickets": 0
        }
    }

async def start(update: Update, context: CallbackContext):
    """Initialize user data and start the game."""
    try:
        user_id = update.effective_user.id
        
        # Get players dictionary from context
        if 'players' not in context.bot_data:
            context.bot_data['players'] = {}
        
        if user_id not in context.bot_data['players']:
            # Initialize new player
            context.bot_data['players'][user_id] = initialize_new_player()
            save_game_data(context.bot_data['players'])
            
            if update.callback_query:
                await update.callback_query.message.reply_text(
                    SUCCESS_MESSAGES["welcome"],
                    reply_markup=generar_botones()
                )
            else:
                await update.message.reply_text(
                    SUCCESS_MESSAGES["welcome"],
                    reply_markup=generar_botones()
                )
        else:
            if update.callback_query:
                await update.callback_query.message.reply_text(
                    "¡Ya tienes una mascota! Usa los botones para jugar.",
                    reply_markup=generar_botones()
                )
            else:
                await update.message.reply_text(
                    "¡Ya tienes una mascota! Usa los botones para jugar.",
                    reply_markup=generar_botones()
                )
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])
        else:
            await update.message.reply_text(ERROR_MESSAGES["generic_error"])

async def button(update: Update, context: CallbackContext):
    """Handle button presses."""
    try:
        query = update.callback_query
        await query.answer()

        # Route to appropriate handler based on callback_data
        handlers = {
            "start": start,
            "recolectar": recolectar,
            "alimentar": alimentar,
            "estado": estado,
            "tienda": tienda,
            "combate": quick_combat,
            "miniboss": miniboss_handler,
            "daily_reward": claim_daily_reward
        }

        if query.data in handlers:
            await handlers[query.data](update, context)
        elif query.data.startswith("comprar_"):
            item_name = query.data.split("_")[1]
            await comprar(update, context, item_name)
        else:
            logger.warning(f"Unhandled callback_data: {query.data}")
            await query.message.reply_text(ERROR_MESSAGES["generic_error"])

    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])
        else:
            await update.message.reply_text(ERROR_MESSAGES["generic_error"])

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Error occurred: {context.error}")
    try:
        if update and update.effective_message:
            if update.callback_query:
                await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])
            else:
                await update.effective_message.reply_text(ERROR_MESSAGES["generic_error"])
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help information."""
    help_text = (
        "🎮 *Comandos del Juego:*\n\n"
        "/start - Iniciar el juego\n"
        "/help - Mostrar esta ayuda\n\n"
        "🐾 *Funciones:*\n"
        "• Alimenta a tu mascota para subir de nivel\n"
        "• Recolecta comida usando energía\n"
        "• Gana oro con el tiempo\n"
        "• Compra mejoras en la tienda\n"
        "• Participa en combates\n"
        "• Enfrenta MiniBosses\n"
        "• Reclama recompensas diarias\n\n"
        "💎 *Premium:*\n"
        "• Status Premium: Progreso x1.5\n"
        "• Auto-Recolector: Comida automática\n"
        "• Bonus Diario: Mejores recompensas\n"
        "• Lucky Tickets: Premios especiales"
    )
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=generar_botones()
        )
    else:
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=generar_botones()
        )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed player statistics."""
    try:
        user_id = update.effective_user.id
        if user_id not in context.bot_data.get('players', {}):
            if update.callback_query:
                await update.callback_query.message.reply_text(ERROR_MESSAGES["no_game"])
            else:
                await update.message.reply_text(ERROR_MESSAGES["no_game"])
            return

        player = context.bot_data['players'][user_id]
        
        stats_text = (
            "📊 *Estadísticas Detalladas:*\n\n"
            f"🐾 *Nivel de Mascota:* {player['mascota']['nivel']}\n"
            f"💰 *Oro Total:* {player['mascota']['oro']}\n"
            f"⚡ *Producción/min:* {player['mascota']['oro_hora']}\n\n"
            f"⚔️ *Nivel de Combate:* {player['combat_stats']['level']}\n"
            f"🌺 *Coral de Fuego:* {player['combat_stats']['fire_coral']}\n"
            f"💫 *EXP:* {player['combat_stats']['exp']}\n\n"
            f"🎯 *Batallas Hoy:* {player['combat_stats']['battles_today']}/20\n"
        )

        # Add premium info if any premium feature is active
        if any(player.get('premium_features', {}).values()):
            stats_text += "\n👑 *Premium Features Activas:*\n"
            if player['premium_features'].get('premium_status'):
                stats_text += "• Status Premium\n"
            if player['premium_features'].get('auto_collector'):
                stats_text += "• Auto-Recolector\n"
            if player['premium_features'].get('daily_bonus'):
                stats_text += "• Bonus Diario\n"
            if player['premium_features'].get('lucky_tickets', 0) > 0:
                stats_text += f"• 🎫 Lucky Tickets: {player['premium_features']['lucky_tickets']}\n"

        if update.callback_query:
            await update.callback_query.message.reply_text(
                stats_text,
                parse_mode='Markdown',
                reply_markup=generar_botones()
            )
        else:
            await update.message.reply_text(
                stats_text,
                parse_mode='Markdown',
                reply_markup=generar_botones()
            )
            
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])
        else:
            await update.message.reply_text(ERROR_MESSAGES["generic_error"])