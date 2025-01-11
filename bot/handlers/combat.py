# handlers/combat.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import random
from datetime import datetime
import logging

from bot.config.settings import (
    SUCCESS_MESSAGES, 
    ERROR_MESSAGES, 
    logger,
    MAX_BATTLES_PER_DAY,
    PET_LEVEL_REQUIREMENT,
    EXP_MULTIPLIER,
    GOLD_PER_LEVEL
)
from bot.utils.keyboard import generar_botones
from bot.utils.save_system import save_game_data
from bot.config.premium_settings import PREMIUM_FEATURES

def calculate_rewards(enemy_level: int, is_premium: bool) -> dict:
    """Calculate rewards for combat victory."""
    base_exp = int(10 * (EXP_MULTIPLIER ** enemy_level))
    base_gold_per_min = max(1, int(enemy_level * GOLD_PER_LEVEL))
    coral_gain = random.randint(1, 3)

    # Premium users get 1.5x rewards
    if is_premium:
        base_exp = int(base_exp * 1.5)
        base_gold_per_min = int(base_gold_per_min * 1.5)
        coral_gain = int(coral_gain * 1.5)

    return {
        "exp": base_exp,
        "gold_per_min": base_gold_per_min,
        "coral": coral_gain
    }

def exp_needed_for_level(level: int) -> int:
    """Calculate experience needed for next level."""
    return int(100 * (1.5 ** level))

async def quick_combat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quick combat encounters."""
    try:
        user_id = update.effective_user.id
        if user_id not in context.bot_data.get('players', {}):
            if update.callback_query:
                await update.callback_query.message.reply_text(ERROR_MESSAGES["no_game"])
            else:
                await update.message.reply_text(ERROR_MESSAGES["no_game"])
            return

        player = context.bot_data['players'][user_id]
        stats = player["combat_stats"]
        
        # Check pet level requirement
        if player["mascota"]["nivel"] < PET_LEVEL_REQUIREMENT:
            message = f"⚠️ Necesitas nivel {PET_LEVEL_REQUIREMENT} de mascota para acceder al Combate Rápido."
            if update.callback_query:
                await update.callback_query.message.reply_text(message, reply_markup=generar_botones())
            else:
                await update.message.reply_text(message, reply_markup=generar_botones())
            return
        
        # Reset battles count if it's a new day
        current_date = datetime.now().date()
        if stats["last_battle_date"] != str(current_date):
            stats["battles_today"] = 0
            stats["last_battle_date"] = str(current_date)

        # Check max battles (considering premium status)
        max_battles = MAX_BATTLES_PER_DAY
        if player.get('premium_features', {}).get('premium_status', False):
            max_battles += 10  # Premium users get 10 extra battles

        if stats["battles_today"] >= max_battles:
            if update.callback_query:
                await update.callback_query.message.reply_text(
                    f"⚠️ Ya has realizado todas tus batallas del día! ({max_battles})",
                    reply_markup=generar_botones()
                )
            else:
                await update.message.reply_text(
                    f"⚠️ Ya has realizado todas tus batallas del día! ({max_battles})",
                    reply_markup=generar_botones()
                )
            return

        # Generate enemy based on player level
        player_level = stats["level"]
        enemy_level = max(0, player_level - 1 + random.randint(0, 2))
        
        # Calculate battle result (base 75% win rate + agility bonus)
        victory_chance = 0.75 + (stats["agi"] / 1000)  # Agility gives small bonus
        victory = random.random() < victory_chance

        if victory:
            # Calculate rewards
            is_premium = player.get('premium_features', {}).get('premium_status', False)
            rewards = calculate_rewards(enemy_level, is_premium)

            # Update stats
            stats["exp"] += rewards["exp"]
            player["mascota"]["oro_hora"] += rewards["gold_per_min"]
            stats["fire_coral"] += rewards["coral"]

            # Level up check
            while stats["exp"] >= exp_needed_for_level(stats["level"]):
                stats["exp"] -= exp_needed_for_level(stats["level"])
                stats["level"] += 1
                
                # Update combat stats on level up
                level = stats["level"]
                stats.update({
                    "hp": 100 + (level * 10),
                    "atk": 10 + (level * 2),
                    "mp": 50 + (level * 5),
                    "def_p": 5 + (level * 1.5),
                    "def_m": 5 + (level * 1.5),
                    "agi": 10 + (level * 1)
                })

            message = (
                f"🗡 ¡Victoria!\n"
                f"💫 EXP ganada: {rewards['exp']}\n"
                f"💰 Oro por minuto +{rewards['gold_per_min']}\n"
                f"🌺 Coral de Fuego +{rewards['coral']}"
            )

            if stats["level"] > player_level:  # If leveled up
                message += f"\n\n🎉 ¡Subiste al nivel {stats['level']}!"
        else:
            message = "❌ ¡Derrota! Mejor suerte la próxima vez."

        # Update battles count
        stats["battles_today"] += 1
        battles_left = max_battles - stats["battles_today"]
        message += f"\n\n⚔️ Batallas restantes hoy: {battles_left}"

        # Save game data
        save_game_data(context.bot_data['players'])

        # Create reply keyboard
        keyboard = [
            [InlineKeyboardButton("⚔️ Otro Combate", callback_data="combate")],
            [InlineKeyboardButton("🏠 Volver", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.message.reply_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Error in quick_combat function: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"], reply_markup=generar_botones())
        else:
            await update.message.reply_text(ERROR_MESSAGES["generic_error"], reply_markup=generar_botones())

async def view_combat_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View detailed combat statistics."""
    try:
        user_id = update.effective_user.id
        if user_id not in context.bot_data.get('players', {}):
            if update.callback_query:
                await update.callback_query.message.reply_text(ERROR_MESSAGES["no_game"])
            else:
                await update.message.reply_text(ERROR_MESSAGES["no_game"])
            return

        stats = context.bot_data['players'][user_id]["combat_stats"]
        
        message = (
            "⚔️ *Estadísticas de Combate*\n\n"
            f"📊 Nivel: {stats['level']}\n"
            f"❤️ HP: {stats['hp']}\n"
            f"⚔️ ATK: {stats['atk']}\n"
            f"🌟 MP: {stats['mp']}\n"
            f"🛡️ DEF Física: {stats['def_p']}\n"
            f"✨ DEF Mágica: {stats['def_m']}\n"
            f"💨 Agilidad: {stats['agi']}\n"
            f"💪 Aguante: {stats['sta']}\n"
            f"🌺 Coral de Fuego: {stats['fire_coral']}\n\n"
            f"📈 EXP: {stats['exp']}/{exp_needed_for_level(stats['level'])}\n"
            f"⚔️ Batallas hoy: {stats['battles_today']}/{MAX_BATTLES_PER_DAY}"
        )

        keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

    except Exception as e:
        logger.error(f"Error in view_combat_stats: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])
        else:
            await update.message.reply_text(ERROR_MESSAGES["generic_error"])