# handlers/miniboss.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import random
import logging
from datetime import datetime
from bot.config.settings import (
    SUCCESS_MESSAGES, 
    ERROR_MESSAGES, 
    logger,
    COMBAT_LEVEL_REQUIREMENT,
    MIN_MINIBOSS_GOLD,
    calculate_miniboss_probabilities
)
from bot.utils.keyboard import generar_botones
from bot.utils.save_system import save_game_data
from bot.config.premium_settings import PREMIUM_FEATURES
from bot.handlers.ads import retry_combat_ad
from database.db.game_db import get_player, save_player
from bot.utils.save_system import initialize_new_player

# Store active miniboss battles
miniboss_estado = {}

# MiniBoss attempts limits
MAX_MINIBOSS_ATTEMPTS = 3  # Regular users
MAX_PREMIUM_MINIBOSS_ATTEMPTS = 10  # Premium users

def inicializar_miniboss(user_id):
    """Initialize a new miniboss battle sequence."""
    return {
        "enemigo_actual": 1,
        "recompensas": {
            "oro": 0,
            "coral": 0,
            "exp": 0
        }
    }

def check_miniboss_attempts(player) -> bool:
    """Check if player has attempts remaining."""
    # Initialize miniboss data if not exists
    if 'miniboss_stats' not in player:
        player['miniboss_stats'] = {
            'attempts_today': 0,
            'last_attempt_date': None
        }
    # Reset attempts if it's a new day
    current_date = str(datetime.now().date())
    if player['miniboss_stats']['last_attempt_date'] != current_date:
        player['miniboss_stats']['attempts_today'] = 0
        player['miniboss_stats']['last_attempt_date'] = current_date
    # Get max attempts based on premium status
    max_attempts = MAX_PREMIUM_MINIBOSS_ATTEMPTS if player.get('premium_features', {}).get('premium_status', False) else MAX_MINIBOSS_ATTEMPTS
    return player['miniboss_stats']['attempts_today'] < max_attempts

def get_attempts_remaining(player) -> int:
    """Get remaining attempts for the day."""
    if 'miniboss_stats' not in player:
        return MAX_PREMIUM_MINIBOSS_ATTEMPTS if player.get('premium_features', {}).get('premium_status', False) else MAX_MINIBOSS_ATTEMPTS
    max_attempts = MAX_PREMIUM_MINIBOSS_ATTEMPTS if player.get('premium_features', {}).get('premium_status', False) else MAX_MINIBOSS_ATTEMPTS
    return max_attempts - player['miniboss_stats']['attempts_today']

def calcular_recompensas(nivel_enemigo, is_premium=False):
    """Calculate rewards for current miniboss enemy."""
    base_rewards = {
        1: {  # First enemy
            "oro": (0, 500),
            "coral": (1, 3),
            "exp": 20
        },
        2: {  # Second enemy
            "oro": (500, 1500),
            "coral": (3, 5),
            "exp": 100
        },
        3: {  # Third enemy
            "oro": (2000, 5000),
            "coral": (5, 15),
            "exp": 250
        },
        4: {  # Fourth enemy
            "oro": (5000, 10000),
            "coral": (15, 30),
            "exp": 500
        },
        5: {  # Boss
            "oro": (10000, 50000),
            "coral": (50, 100),
            "exp": 1000
        }
    }
    rewards = base_rewards[nivel_enemigo]
    oro = random.randint(*rewards["oro"])
    coral = random.randint(*rewards["coral"])
    exp = int(rewards["exp"] * (1.1 ** nivel_enemigo))
    # Premium users get 1.5x rewards
    if is_premium:
        oro = int(oro * 1.5)
        coral = int(coral * 1.5)
        exp = int(exp * 1.5)
    return {
        "oro": oro,
        "coral": coral,
        "exp": exp
    }

async def miniboss_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle miniboss battle initiation."""
    try:
        user_id = update.effective_user.id
        session = Session()
        try:
            player = get_player(session, user_id)
            if not player:
                await update.effective_message.reply_text(ERROR_MESSAGES["no_game"])
                return

            # Check combat level requirement
            if player.combat_stats["level"] < COMBAT_LEVEL_REQUIREMENT:
                mensaje = f"⚠️ Necesitas nivel de combate {COMBAT_LEVEL_REQUIREMENT} para acceder al MiniBoss."
                await update.effective_message.reply_text(mensaje, reply_markup=generar_botones(player))
                return

            # Check daily attempts
            if not check_miniboss_attempts(player):
                attempts_max = MAX_PREMIUM_MINIBOSS_ATTEMPTS if player.premium_features.get('premium_status', False) else MAX_MINIBOSS_ATTEMPTS
                mensaje = f"⚠️ Has alcanzado el límite de {attempts_max} intentos diarios de MiniBoss."
                await update.effective_message.reply_text(mensaje, reply_markup=generar_botones(player))
                return

            # Check if player has enough gold
            if player.mascota["oro"] < MIN_MINIBOSS_GOLD:
                mensaje = f"⚠️ Necesitas {MIN_MINIBOSS_GOLD} de oro para iniciar una batalla contra MiniBoss!"
                await update.effective_message.reply_text(mensaje, reply_markup=generar_botones(player))
                return

            # Initialize miniboss battle and increment attempts
            miniboss_estado = inicializar_miniboss(user_id)
            player.mascota["oro"] -= MIN_MINIBOSS_GOLD  # Charge entry fee
            player.miniboss_stats['attempts_today'] += 1
            
            # Update player in database
            update_player(session, player)

            # Start first battle
            await procesar_combate_miniboss(update, context, player, miniboss_estado)

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error in miniboss_handler: {e}")
        await update.effective_message.reply_text(ERROR_MESSAGES["generic_error"])

async def procesar_combate_miniboss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process each miniboss battle stage."""
    try:
        user_id = update.effective_user.id
        session = Session()
        try:
            player = get_player(session, user_id)
            if not player:
                await update.effective_message.reply_text(ERROR_MESSAGES["no_game"])
                return

            estado_actual = player.miniboss_stats
            enemigo_actual = estado_actual["enemigo_actual"]
            
            # Get victory probability based on combat level
            combat_level = player.combat_stats["level"]
            probabilities = calculate_miniboss_probabilities(combat_level)
            victoria = random.random() < probabilities[enemigo_actual]
            
            if victoria:
                # Calculate and add rewards
                is_premium = player.premium_features.get('premium_status', False)
                recompensas = calcular_recompensas(enemigo_actual, is_premium)
                estado_actual["recompensas"]["oro"] += recompensas["oro"]
                estado_actual["recompensas"]["coral"] += recompensas["coral"]
                estado_actual["recompensas"]["exp"] += recompensas["exp"]
                
                if enemigo_actual == 5:  # Victory against final boss
                    await finalizar_miniboss(update, context, player, victoria=True)
                else:
                    # Show current rewards and options
                    mensaje = (
                        f"🗡 ¡Victoria contra el enemigo {enemigo_actual}!\n\n"
                        f"Recompensas acumuladas:\n"
                        f"💰 Oro: {estado_actual['recompensas']['oro']}\n"
                        f"🌺 Coral de Fuego: {estado_actual['recompensas']['coral']}\n"
                        f"💫 EXP: {estado_actual['recompensas']['exp']}\n\n"
                        f"¿Qué deseas hacer?"
                    )
                    keyboard = [
                        [InlineKeyboardButton("⚔️ Siguiente Combate", callback_data="siguiente_miniboss")],
                        [InlineKeyboardButton("🏃 Retirarse (50% recompensas)", callback_data="retirarse_miniboss")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    if update.callback_query:
                        await update.callback_query.message.reply_text(mensaje, reply_markup=reply_markup)
                    else:
                        await update.message.reply_text(mensaje, reply_markup=reply_markup)
            else:
                await finalizar_miniboss(update, context, player, victoria=False)

            # Update player in database
            update_player(session, player)

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error in procesar_combate_miniboss: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])
        else:
            await update.message.reply_text(ERROR_MESSAGES["generic_error"])

async def siguiente_miniboss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle progression to next miniboss enemy."""
    try:
        user_id = update.effective_user.id
        estado_actual = miniboss_estado[user_id]
        estado_actual["enemigo_actual"] += 1
        await procesar_combate_miniboss(update, context)
    except Exception as e:
        logger.error(f"Error in siguiente_miniboss: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])
        else:
            await update.message.reply_text(ERROR_MESSAGES["generic_error"])

async def retirarse_miniboss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle early retreat from miniboss battle."""
    try:
        user_id = update.effective_user.id
        estado_actual = miniboss_estado[user_id]
        # Apply 50% penalty to rewards
        estado_actual["recompensas"]["oro"] = int(estado_actual["recompensas"]["oro"] * 0.5)
        estado_actual["recompensas"]["coral"] = int(estado_actual["recompensas"]["coral"] * 0.5)
        estado_actual["recompensas"]["exp"] = int(estado_actual["recompensas"]["exp"] * 0.5)
        await finalizar_miniboss(update, context, victoria=True, retirada=True)
    except Exception as e:
        logger.error(f"Error in retirarse_miniboss: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])
        else:
            await update.message.reply_text(ERROR_MESSAGES["generic_error"])

async def finalizar_miniboss(update: Update, context: ContextTypes.DEFAULT_TYPE, player, victoria: bool, retirada: bool = False):
    """Finalize miniboss battle sequence and award rewards."""
    try:
        user_id = update.effective_user.id
        session = Session()
        try:
            player = get_player(session, user_id)
            if not player:
                await update.effective_message.reply_text(ERROR_MESSAGES["no_game"])
                return

            estado_actual = player.miniboss_stats
            
            if victoria:
                # Apply rewards
                player.gold += estado_actual["recompensas"]["oro"]
                player.fire_coral += estado_actual["recompensas"]["coral"]
                player.exp += estado_actual["recompensas"]["exp"]
                
                # Level up logic
                while player.exp >= exp_needed_for_level(player.level):
                    player.exp -= exp_needed_for_level(player.level)
                    player.level += 1
                    new_stats = initialize_combat_stats(player.level)
                    player.update_combat_stats(new_stats)
                
                mensaje = (
                    f"{'🏃 Te has retirado' if retirada else '🎉 ¡MiniBoss Completado!'}\n\n"
                    f"Recompensas finales:\n"
                    f"💰 Oro: {estado_actual['recompensas']['oro']}\n"
                    f"🌺 Coral de Fuego: {estado_actual['recompensas']['coral']}\n"
                    f"💫 EXP: {estado_actual['recompensas']['exp']}\n\n"
                    f"⚔️ Intentos restantes hoy: {get_attempts_remaining(player)}"
                )
                keyboard = [[InlineKeyboardButton("🏠 Volver al Menú", callback_data="start")]]
            else:
                mensaje = f"❌ ¡Has sido derrotado! No recibes recompensas.\n\n⚔️ Intentos restantes hoy: {get_attempts_remaining(player)}"
                # Store current battle state for retry
                player.last_miniboss_state = {
                    'enemy_level': estado_actual['enemigo_actual'],
                    'accumulated_rewards': estado_actual['recompensas']
                }
                keyboard = [
                    [InlineKeyboardButton("📺 Reintentar (Ver Anuncio)", callback_data=f"retry_miniboss_{estado_actual['enemigo_actual']}")],
                    [InlineKeyboardButton("🏠 Volver al Menú", callback_data="start")]
                ]

            # Clean up miniboss state
            player.miniboss_stats = {}
            
            # Update player in database
            update_player(session, player)

            reply_markup = InlineKeyboardMarkup(keyboard)
            if update.callback_query:
                await update.callback_query.message.reply_text(mensaje, reply_markup=reply_markup)
            else:
                await update.message.reply_text(mensaje, reply_markup=reply_markup)
                
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error in finalizar_miniboss: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])
        else:
            await update.message.reply_text(ERROR_MESSAGES["generic_error"])

from database.db.game_db import Session, get_player, save_player
from bot.handlers.ads import retry_combat_ad

async def retry_miniboss_battle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle miniboss battle retry through ad watching."""
    try:
        user_id = update.effective_user.id
        session = Session()
        try:
            player = get_player(session, user_id)
            if not player or not player.miniboss_stats:
                await update.callback_query.message.reply_text("❌ No hay combate para reintentar.")
                return

            # Show ad and verify completion
            ad_success = await retry_combat_ad(update, context, "MiniBoss")
            if not ad_success:
                return

            # Restore miniboss state
            enemigo_actual = player.miniboss_stats.get('enemigo_actual')
            recompensas = player.miniboss_stats.get('recompensas')
            
            if not enemigo_actual or not recompensas:
                await update.callback_query.message.reply_text("❌ Error al recuperar el estado del combate.")
                return

            # Reset the miniboss battle state
            player.miniboss_stats = {
                "enemigo_actual": enemigo_actual,
                "recompensas": recompensas
            }

            # Decrement the attempts count
            if player.miniboss_stats['attempts_today'] > 0:
                player.miniboss_stats['attempts_today'] -= 1

            # Save the updated player state
            save_player(session, player)

            # Process the combat again
            await procesar_combate_miniboss(update, context)

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error in retry_miniboss_battle: {e}")
        await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])

def exp_needed_for_level(level: int) -> int:
    """Calculate experience needed for next level."""
    return int(100 * (1.5 ** level))

def initialize_combat_stats(level: int) -> dict:
    """Initialize combat stats for a given level."""
    return {
        "level": level,
        "hp": 100 + (level * 10),
        "atk": 10 + (level * 2),
        "mp": 50 + (level * 5),
        "def_p": 5 + (level * 1.5),
        "def_m": 5 + (level * 1.5),
        "agi": 10 + (level * 1),
        "sta": 100 + (level * 5)
    }