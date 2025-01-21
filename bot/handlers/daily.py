# handlers/daily.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import time
import random
import logging
from datetime import datetime, timedelta
import pytz
from telegram.ext import CommandHandler
from .premium import distribute_weekly_tickets
from bot.config.settings import (
    DAILY_REWARDS,
    SUCCESS_MESSAGES,
    ERROR_MESSAGES,
    logger
)
from bot.utils.keyboard import generar_botones
from bot.utils.save_system import save_game_data
from bot.config.premium_settings import PREMIUM_FEATURES
from database.db.game_db import get_player, Session
from database.models import Player
from sqlalchemy import cast, String

def get_next_midnight_cet():
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if now > midnight:
        midnight += timedelta(days=1)
    return midnight

async def claim_daily_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        
        session = Session()
        try:
            player = get_player(session, user_id)
            
            if not player:
                logger.error(f"Player not found for user_id: {user_id}")
                await send_message(update, ERROR_MESSAGES["no_game"])
                return

            logger.debug(f"Player data: {player.__dict__}")

            current_time = datetime.now()
            last_claim_dt = datetime.fromtimestamp(player.daily_reward.get('last_claim', 0))

            # Check if 24 hours have passed since last claim
            if current_time - last_claim_dt < timedelta(hours=24):
                time_left = timedelta(hours=24) - (current_time - last_claim_dt)
                hours, remainder = divmod(time_left.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                await send_message(update, ERROR_MESSAGES["daily_reward_wait"].format(hours, minutes))
                return

            # Check streak
            yesterday = (current_time - timedelta(days=1)).date()
            if last_claim_dt.date() != yesterday:
                player.daily_reward['streak'] = 1
            else:
                player.daily_reward['streak'] += 1

            # Determine reward type and multipliers
            is_premium = player.premium_features.get('premium_status', False)
            has_daily_bonus = player.premium_features.get('daily_bonus', False)
            reward_type = "premium" if (is_premium or has_daily_bonus) else "basic"
            rewards = DAILY_REWARDS[reward_type]

            # Get appropriate streak bonuses
            streak_bonuses = DAILY_REWARDS['premium_streak_bonuses'] if (is_premium or has_daily_bonus) else DAILY_REWARDS['streak_bonuses']

            # Calculate streak multiplier
            multiplier = 1.0
            for days, bonus in sorted(streak_bonuses.items(), reverse=True):
                if player.daily_reward['streak'] >= days:
                    multiplier = bonus
                    break

            # Calculate rewards
            oro = int(random.randint(*rewards['oro']) * multiplier)
            coral = int(random.randint(*rewards['coral']) * multiplier)
            comida = int(random.randint(*rewards['comida']) * multiplier)
            exp = int(random.randint(*rewards['exp']) * multiplier)
            tickets = int(random.randint(*rewards['fragmento_del_destino']) * multiplier)

            # Update player stats
            player.mascota['oro'] += oro
            if 'fire_coral' not in player.combat_stats:
                player.combat_stats['fire_coral'] = 0
            player.combat_stats['fire_coral'] += coral
            player.comida += comida
            player.mascota['energia'] = rewards['energia']  # Full energy restore
            player.combat_stats['exp'] += exp
            player.fragmento_del_destino = player.fragmento_del_destino + tickets

            # Check for weekly premium tickets
            premium_ticket_message = ""
            if has_daily_bonus:
                last_weekly = player.daily_reward.get('last_weekly_tickets', 0)
                if current_time.timestamp() - last_weekly >= DAILY_REWARDS['weekly_reset']:
                    player.premium_features['tickets'] += 3
                    player.daily_reward['last_weekly_tickets'] = current_time.timestamp()
                    premium_ticket_message = SUCCESS_MESSAGES["weekly_tickets"]

            # Update last claim time
            player.daily_reward['last_claim'] = current_time.timestamp()

            # Save changes to the database
            session.commit()

            # Prepare response message
            message = SUCCESS_MESSAGES["daily_reward"].format(
                oro, coral, comida, exp, tickets,
                "1 día" if player.daily_reward['streak'] == 1 else f"{player.daily_reward['streak']} días"
            )
            if multiplier > 1:
                message += "\n" + SUCCESS_MESSAGES["streak_bonus"].format(multiplier)
            if is_premium or has_daily_bonus:
                message += "\n" + SUCCESS_MESSAGES["daily_reward_premium"].format(
                    premium_ticket_message if premium_ticket_message else ""
                )

            # Add streak progress information
            next_streak_bonus = None
            for days in sorted(streak_bonuses.keys()):
                if days > player.daily_reward['streak']:
                    next_streak_bonus = days
                    break
            if next_streak_bonus:
                days_remaining = next_streak_bonus - player.daily_reward['streak']
                message += f"\n\n🔥 {days_remaining} días más para el siguiente bonus de racha (x{streak_bonuses[next_streak_bonus]})"

            # Create keyboard with return button
            keyboard = [
                [InlineKeyboardButton("📊 Ver Estado", callback_data="estado")],
                [InlineKeyboardButton("🏠 Volver al Menú", callback_data="start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await send_message(update, message, reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Error in claim_daily_reward: {str(e)}", exc_info=True)
            await send_message(update, ERROR_MESSAGES["daily_reward_error"])
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Outer error in claim_daily_reward: {str(e)}", exc_info=True)
        await send_message(update, ERROR_MESSAGES["daily_reward_error"])

async def send_message(update: Update, text: str, reply_markup=None):
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        logger.error("Neither callback_query nor message found in update object")

async def check_daily_reset(context: ContextTypes.DEFAULT_TYPE):
    """Background task to check and reset daily rewards."""
    try:
        cet = pytz.timezone('CET')
        current_time = datetime.now(cet)
        
        session = Session()
        try:
            players = session.query(Player).all()
            
            for player in players:
                if player.daily_reward:
                    last_claim_dt = datetime.fromtimestamp(player.daily_reward['last_claim'], cet)
                    yesterday = (current_time - timedelta(days=1)).date()
                    
                    if last_claim_dt.date() < yesterday:
                        player.daily_reward['streak'] = 1
            
            session.commit()
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error in daily reset check: {e}")

async def check_weekly_tickets(context: ContextTypes.DEFAULT_TYPE):
    """Check and distribute weekly tickets"""
    current_time = datetime.now().timestamp()
    
    session = Session()
    try:
        players = session.query(Player).filter(
            cast(Player.premium_features['premium_status'], String) == 'true'
        ).all()
        
        for player in players:
            premium_features = player.premium_features
            last_distribution = premium_features.get('last_ticket_distribution', 0)
            if current_time - last_distribution >= PREMIUM_FEATURES['weekly_reset']:
                await distribute_weekly_tickets(context, player.id)
                premium_features['last_ticket_distribution'] = current_time
        
        session.commit()
    finally:
        session.close()

def setup_daily_handlers(application):
    """Set up daily reward related handlers and jobs."""
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    
    # Calculate time until next midnight
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if now > midnight:
        midnight += timedelta(days=1)
    
    # Add job to check daily resets at midnight CET
    application.job_queue.run_daily(
        check_daily_reset,
        time=midnight.time(),
        days=(0, 1, 2, 3, 4, 5, 6)
    )
    
    # Add job to check weekly tickets distribution
    application.job_queue.run_daily(
        check_weekly_tickets,
        time=midnight.time(),
        days=(0,)  # This is correct for Monday
    )

    # Add handler for the /daily command
    application.add_handler(CommandHandler("daily", claim_daily_reward))