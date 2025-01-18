# handlers/pet.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import time
import logging
from datetime import datetime
from database.db.game_db import get_all_players, get_player, save_player, Session
from telegram import Update

from bot.config.settings import (
    SUCCESS_MESSAGES,
    ERROR_MESSAGES,
    logger,
    IMAGE_PATHS,
    HUNGER_LOSS_RATE,
    ENERGY_GAIN_RATE,
    MAX_ENERGY,
    MAX_HUNGER
)
from bot.utils.keyboard import generar_botones
from bot.utils.save_system import save_game_data
from bot.config.premium_settings import PREMIUM_FEATURES
from sqlalchemy import func

logger = logging.getLogger(__name__)

async def actualizar_estados(player):
    """Update pet's hunger, energy, and gold based on time passed."""
    try:
        tiempo_actual = time.time()
        mascota = player["mascota"]
        tiempo_transcurrido = tiempo_actual - player["última_actualización"]
        minutos_pasados = tiempo_transcurrido // 60

        if minutos_pasados > 0:
            # Update gold generation (with premium multiplier)
            is_premium = player.get('premium_features', {}).get('premium_status', False)
            multiplier = 1.5 if is_premium else 1.0
            oro_generado = int((mascota["oro_hora"] * minutos_pasados) * multiplier)
            mascota["oro"] += oro_generado

            # Update hunger and energy
            mascota["hambre"] = max(0, mascota["hambre"] - int(minutos_pasados * HUNGER_LOSS_RATE))
            mascota["energia"] = min(MAX_ENERGY, mascota["energia"] + int(minutos_pasados * ENERGY_GAIN_RATE))
            
            # Auto-collector feature for premium users
            if player.get('premium_features', {}).get('auto_collector', False):
                # Calculate how many times we can collect based on available energy
                max_collections = mascota["energia"]  # Each collection costs 1 energy
                if max_collections > 0:
                    # Perform collections
                    food_collected = min(max_collections, int(minutos_pasados / 60))  # Collect every hour
                    if food_collected > 0:
                        player["comida"] += food_collected
                        mascota["energia"] -= food_collected
                        logger.info(f"Auto-collector added {food_collected} food for user {id}")

            player["última_actualización"] = tiempo_actual
            return True
    except Exception as e:
        logger.error(f"Error updating states: {e}")
    return False

async def recolectar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle food collection."""
    try:
        user_id = update.effective_user.id
        session = Session()
        try:
            player = get_player(session, user_id)
            if not player:
                if update.callback_query:
                    await update.callback_query.message.reply_text(ERROR_MESSAGES["no_game"])
                else:
                    await update.message.reply_text(ERROR_MESSAGES["no_game"])
                return

            await actualizar_estados(player)
            mascota = player.mascota

            if mascota["energia"] > 0:
                player.comida += 10
                mascota["energia"] -= 10
                save_player(session, player)

                # Send collection message with image
                with open(IMAGE_PATHS['recolectar'], 'rb') as img_file:
                    if update.message:
                        await update.message.reply_photo(
                            photo=img_file,
                            caption=SUCCESS_MESSAGES["food_collected"].format(player.comida),
                            reply_markup=generar_botones()
                        )
                    elif update.callback_query:
                        await update.callback_query.message.reply_photo(
                            photo=img_file,
                            caption=SUCCESS_MESSAGES["food_collected"].format(player.comida),
                            reply_markup=generar_botones()
                        )
            else:
                if update.message:
                    await update.message.reply_text(ERROR_MESSAGES["no_energy"], reply_markup=generar_botones())
                elif update.callback_query:
                    await update.callback_query.message.reply_text(ERROR_MESSAGES["no_energy"], reply_markup=generar_botones())

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error in recolectar: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])
        else:
            await update.message.reply_text(ERROR_MESSAGES["generic_error"])

async def alimentar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pet feeding."""
    try:
        user_id = update.effective_user.id
        session = Session()
        try:
            player = get_player(session, user_id)
            if not player:
                if update.callback_query:
                    await update.callback_query.message.reply_text(ERROR_MESSAGES["no_game"])
                else:
                    await update.message.reply_text(ERROR_MESSAGES["no_game"])
                return

            mascota = player.mascota

            comida_necesaria = mascota.nivel * 5
            if player.comida >= comida_necesaria:
                # Process feeding
                player.comida -= comida_necesaria
                mascota.hambre = min(MAX_HUNGER, mascota.hambre + 10)
                mascota.nivel += 1
                
                # Calculate new gold production (with premium multiplier)
                is_premium = player.premium_features.get('premium_status', False)
                base_production = 2 ** (mascota.nivel - 1)
                mascota.oro_hora = base_production * (1.5 if is_premium else 1.0)
                
                save_player(player)

                # Send feeding message with image
                with open(IMAGE_PATHS['alimentar'], 'rb') as img_file:
                    if update.message:
                        await update.message.reply_photo(
                            photo=img_file,
                            caption=SUCCESS_MESSAGES["pet_fed"].format(
                                mascota.nivel,
                                mascota.oro_hora,
                                mascota.hambre
                            ),
                            reply_markup=generar_botones()
                        )
                    elif update.callback_query:
                        await update.callback_query.message.reply_photo(
                            photo=img_file,
                            caption=SUCCESS_MESSAGES["pet_fed"].format(
                                mascota.nivel,
                                mascota.oro_hora,
                                mascota.hambre
                            ),
                            reply_markup=generar_botones()
                        )
            else:
                mensaje = f"¡Necesitas {comida_necesaria} comidas para subir de nivel! Tienes {player.comida} comidas."
                if update.message:
                    await update.message.reply_text(mensaje, reply_markup=generar_botones())
                elif update.callback_query:
                    await update.callback_query.message.reply_text(mensaje, reply_markup=generar_botones())

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error in alimentar: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])
        else:
            await update.message.reply_text(ERROR_MESSAGES["generic_error"])

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display pet and player status."""
    try:
        user_id = update.effective_user.id
        session = Session()
        try:
            player = get_player(session, user_id)
            if not player:
                if update.callback_query:
                    await update.callback_query.message.reply_text(ERROR_MESSAGES["no_game"])
                else:
                    await update.message.reply_text(ERROR_MESSAGES["no_game"])
                return

            await actualizar_estados(player)
            
            mascota = player.mascota
            comida = player.comida
            combat_stats = player.combat_stats

            # Create status message
            estado_mensaje = (
                f"🍖 Hambre: {mascota.hambre}\n"
                f"⚡ Energía: {mascota.energia}\n"
                f"📊 Nivel: {mascota.nivel}\n"
                f"💰 Oro: {mascota.oro}\n"
                f"⏱️ Producción de Oro/Minuto: {mascota.oro_hora}\n"
                f"🌾 Comida: {comida}\n"
                f"\n📊 Estadísticas de Combate:\n"
                f"🎖️ Nivel de Combate: {combat_stats.level}\n"
                f"🌺 Coral de Fuego: {combat_stats.fire_coral}\n"
                f"⚔️ Batallas hoy: {combat_stats.battles_today}/20"
            )

            # Add premium status if active
            if player.premium_features.get('premium_status', False):
                premium_expires = datetime.fromtimestamp(
                    player.premium_features['premium_status_expires']
                ).strftime('%Y-%m-%d')
                estado_mensaje += f"\n\n👑 Premium Status activo hasta: {premium_expires}"

            # Add auto-collector status if active
            if player.premium_features.get('auto_collector', False):
                auto_collector_expires = datetime.fromtimestamp(
                    player.premium_features['auto_collector_expires']
                ).strftime('%Y-%m-%d')
                estado_mensaje += f"\n🤖 Auto-Collector activo hasta: {auto_collector_expires}"

            # Send status message with image
            with open(IMAGE_PATHS['estado'], 'rb') as img_file:
                if update.message:
                    await update.message.reply_photo(
                        photo=img_file,
                        caption=estado_mensaje,
                        reply_markup=generar_botones()
                    )
                elif update.callback_query:
                    await update.callback_query.message.reply_photo(
                        photo=img_file,
                        caption=estado_mensaje,
                        reply_markup=generar_botones()
                    )

            save_player(player)

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error in estado: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])
        else:
            await update.message.reply_text(ERROR_MESSAGES["generic_error"])

async def check_premium_expiry(context: ContextTypes.DEFAULT_TYPE):
    """Background task to check and update premium feature expiration."""
    try:
        current_time = time.time()
        session = Session()
        try:
            players = get_all_players()
            
            for player in players:
                premium_features = player.premium_features
                
                # Check Premium Status expiry
                if premium_features.get('premium_status', False):
                    if current_time > premium_features.get('premium_status_expires', 0):
                        premium_features['premium_status'] = False
                
                # Check Auto-collector expiry
                if premium_features.get('auto_collector', False):
                    if current_time > premium_features.get('auto_collector_expires', 0):
                        premium_features['auto_collector'] = False
                
                # Save changes for each player
                save_player(player)
            
        finally:
            session.close()
        
    except Exception as e:
        logger.error(f"Error in premium expiry check: {e}")

def setup_pet_handlers(application):
    """Set up pet-related handlers and jobs."""
    # Add job to check premium features expiry every hour
    application.job_queue.run_repeating(
        check_premium_expiry,
        interval=3600,  # 1 hour
        first=10  # Start 10 seconds after bot startup
    )