# main.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes,
    CallbackContext
)



from database import Session, get_all_players, get_player
from bot.handlers.base import initialize_new_player
from database.models.player_model import Player

from filelock import FileLock, Timeout


from bot.config.settings import SUCCESS_MESSAGES, ERROR_MESSAGES, logger
from bot.handlers.daily import setup_daily_handlers, check_daily_reset, check_weekly_tickets

from datetime import time
import zoneinfo
import logging
import asyncio
import pytz
from datetime import datetime
from bot.handlers.base import initialize_combat_stats
from bot.handlers.ads import register_handlers
from bot.handlers.shop import premium_shop, get_premium_item, comprar_fragmentos

from database.app import app

# Import configurations and save system
from bot.config.settings import (
    TOKEN, 
    SUCCESS_MESSAGES, 
    ERROR_MESSAGES, 
    logger
)
from bot.config.premium_settings import PREMIUM_FEATURES
from bot.utils.save_system import save_game_data, load_game_data, backup_data
from bot.utils.keyboard import (
    generar_botones,
#    create_waterquest_menu_keyboard,
#    create_waterquest_dialogue_keyboard
)


#----------------------------------------------------------
# Temporarily comment out TON SDK imports
class TonClientException(Exception):
    pass
TonClientError = TonClientException

# Comment out TON initialization
# ton_client = initialize_ton_client()
# wallet_manager = initialize_wallet_manager()
#----------------------------------------------------------

# Import all handlers
from bot.handlers import (
    start, button, error_handler,
    help_command, stats_command,
    recolectar, alimentar, estado,
    quick_combat, view_combat_stats,
    miniboss_handler, siguiente_miniboss, retirarse_miniboss, 
    claim_daily_reward, check_daily_reset, check_weekly_tickets,
    tienda, comprar,
    check_premium_expiry, 
    portal_menu, spin_portal
)

from bot.handlers.miniboss import retry_miniboss_battle

from bot.handlers.ads import (
    ads_menu,
    process_ad_watch,
    retry_combat_ad
)

logging.basicConfig(level=logging.DEBUG)

from telegram.ext import Application


def setup_daily_handlers(application: Application):
    """Set up daily reward related handlers and jobs."""
    # Add job to check daily resets at midnight UTC
    application.job_queue.run_daily(
        check_daily_reset,
        time=time(hour=0, minute=0),
        days=(0, 1, 2, 3, 4, 5, 6)
    )
    
    # Add job to check weekly tickets distribution
    application.job_queue.run_daily(
        check_weekly_tickets,
        time=time(hour=0, minute=0),
        days=(0,)  # This is correct for Monday in v20.0+
    )

    # Add handler for the /daily command
    application.add_handler(CommandHandler("daily", claim_daily_reward))

from database.db.game_db import get_player, create_player, Session
from bot.utils.keyboard import generar_botones
from bot.config.settings import SUCCESS_MESSAGES, ERROR_MESSAGES, logger

from database.db.game_db import get_player, create_player, Session
from bot.utils.keyboard import generar_botones
from bot.config.settings import SUCCESS_MESSAGES, ERROR_MESSAGES, logger

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        nombre = update.effective_user.first_name

        session = Session()
        try:
            # Check if player exists in the database
            player = get_player(session, user_id)

            if not player:
                # Initialize new player
                logger.info(f"Creating new player for user_id: {user_id}, nombre: {nombre}")
                player = create_player(session, user_id, nombre)
                session.commit()
                logger.info(f"New player created with ID: {player.id}")
                message = SUCCESS_MESSAGES["welcome"]
            else:
                message = "¡Bienvenido de nuevo! Usa los botones para jugar."

            # Convert player to dictionary for button generation
            player_dict = player.to_dict()  # Assuming Player model has a to_dict method

            # Generate buttons based on player data
            reply_markup = generar_botones(player_dict)

            if update.callback_query and update.callback_query.message:
                await update.callback_query.message.edit_text(
                    message,
                    reply_markup=reply_markup
                )
            elif update.message:
                await update.message.reply_text(
                    message,
                    reply_markup=reply_markup
                )

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error in start command: {str(e)}", exc_info=True)
        if update.callback_query and update.callback_query.message:
            await update.callback_query.message.edit_text(ERROR_MESSAGES["generic_error"])
        elif update.message:
            await update.message.reply_text(ERROR_MESSAGES["generic_error"])



async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        user_id = query.from_user.id
        
        session = Session()
        try:
            player = get_player(session, user_id)
            
            if player is None:
                logger.warning(f"Player data not found for user_id: {user_id}")
                await query.message.reply_text(ERROR_MESSAGES["player_not_found"])
                return

            try:
                await query.answer()
            except:
                # If the callback_query expired, we continue without error
                pass

            # Route to appropriate handler based on callback_data
            if query.data == "start":
                await start(update, context)
            elif query.data == "recolectar":
                await recolectar(update, context)
            elif query.data == "alimentar":
                await alimentar(update, context)
            elif query.data == "estado":
                await estado(update, context)
            elif query.data == "tienda":
                await tienda(update, context)
            elif query.data == "combate":
                await quick_combat(update, context)
            elif query.data == "miniboss":
                await miniboss_handler(update, context)
            elif query.data == "siguiente_miniboss":
                await siguiente_miniboss(update, context)
            elif query.data == "retirarse_miniboss":
                await retirarse_miniboss(update, context)
            elif query.data.startswith("retry_miniboss_"):
                await retry_miniboss_battle(update, context)
            elif query.data == "daily_reward":
                await claim_daily_reward(update, context)
            elif query.data.startswith("comprar_"):
                item_name = query.data.split("_")[1]
                await comprar(update, context, item_name)
            elif query.data == "portal":
                await portal_menu(update, context)
            elif query.data.startswith("portal_spin_"):
                await spin_portal(update, context)
            elif query.data == "ads_menu":
                await ads_menu(update, context)
            elif query.data == "watch_ad":
                await process_ad_watch(update, context)
            elif query.data.startswith("retry_miniboss_"):
                combat_type = query.data.split("_")[3]  # Extract the combat type
                await retry_combat_ad(update, context, combat_type)
            elif query.data == "premium_shop":
                await premium_shop(update, context)
            elif query.data == "comprar_fragmentos":
                await comprar_fragmentos(update, context)
            else:
                logger.warning(f"Unhandled callback_data: {query.data}")
                await query.message.reply_text(
                    ERROR_MESSAGES["generic_error"],
                    reply_markup=generar_botones(player.__dict__)
                )
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        if update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_text(
                ERROR_MESSAGES["generic_error"],
                reply_markup=generar_botones(player.__dict__ if player else None)
            )
        elif update.message:
            await update.message.reply_text(ERROR_MESSAGES["generic_error"])



logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def save_game_job(context: ContextTypes.DEFAULT_TYPE):
    """Periodic save job."""
    try:
        session = Session()
        players = get_all_players(session)
        
        if players:
            player_data = {player.user_id: player.to_dict() for player in players}
            save_result = save_game_data(player_data)
            
            if save_result:
                logger.info("Auto-save completed successfully")
            else:
                logger.warning("Auto-save completed with warnings")
        else:
            logger.info("No player data to save")
        
    except Exception as e:
        logger.error(f"Error in save game job: {e}")
    finally:
        session.close()

def main():
    """Start the bot."""
    lock = FileLock("bot.lock")
    try:
        with lock.acquire(timeout=1):
            # Create application
            application = Application.builder().token(TOKEN).connect_timeout(30).read_timeout(30).build()

            # Add command handlers
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CommandHandler("help", help_command))
            application.add_handler(CommandHandler("stats", stats_command))
            
            # Add callback query handler
            application.add_handler(CallbackQueryHandler(button))
            
            # Add error handler
            application.add_error_handler(error_handler)

            setup_daily_handlers(application)

            # Add premium items
            application.add_handler(CallbackQueryHandler(get_premium_item, pattern=r'^get_premium_'))

            # Add WaterQuest handlers
            #application.add_handler(CallbackQueryHandler(show_waterquest_menu, pattern=r'^waterquest_menu$'))
            #application.add_handler(CallbackQueryHandler(start_voice_of_abyss_quest, pattern=r'^start_voice_of_abyss$'))
            #application.add_handler(CallbackQueryHandler(process_quest_choice, pattern=r'^quest_choice_'))

            job_time = time(hour=0, minute=0)
            cet = pytz.timezone('Europe/Paris')

            application.job_queue.run_daily(check_daily_reset, time=job_time.replace(tzinfo=cet))

            utc_time = cet.localize(datetime.combine(datetime.now(cet), job_time)).astimezone(pytz.UTC).time()
            application.job_queue.run_daily(check_daily_reset, time=utc_time)

            # Add periodic jobs
            application.job_queue.run_repeating(
                save_game_job,
                interval=300,  # Every 5 minutes
                first=300
            )

            # Add weekly ticket check job
            application.job_queue.run_repeating(
                check_weekly_tickets,
                interval=86400,  # Check daily
                first=10
            )

            # Add premium expiry check
            application.job_queue.run_repeating(
                check_premium_expiry,
                interval=3600,  # Every hour
                first=10
            )

            # Add daily reset check
            application.job_queue.run_repeating(
                check_daily_reset,
                interval=21600,  # Every 6 hours
                first=10
            )
     
            # Start the bot
            print("Bot iniciado...")
            application.run_polling()

            return application  # Return the application for cleanup

    except Timeout:
        print("Another instance of the bot is already running. Exiting.")
        return None
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return None

if __name__ == '__main__':
    app = None
    try:
        app = main()
    except KeyboardInterrupt:
        print("\nBot detenido manualmente")
    finally:
        if app:
            try:
                session = Session()
                players = get_all_players(session)
                if players:
                    player_data = {player.user_id: player.to_dict() for player in players}
                    save_result = save_game_data(player_data)
                    if save_result:
                        print("Datos guardados exitosamente.")
                    else:
                        print("Advertencia: Hubo un problema al guardar los datos.")
                    
                    backup_file = backup_data()
                    if backup_file:
                        print(f"Backup creado: {backup_file}")
                    else:
                        print("Advertencia: No se pudo crear el backup.")
                else:
                    print("No hay datos de jugadores para guardar.")
            except Exception as e:
                print(f"Error al guardar los datos: {e}")
            finally:
                session.close()
                print("¡Hasta luego!")




            #---------------------------------------------------------------------------------------
            #---------------------------------------------------------------------------------------

            # WaterQuest Functions
""" async def show_waterquest_menu(update: Update, context: CallbackContext):
#    Display available WaterQuests.
    try:
        user_id = update.effective_user.id
        if user_id not in context.bot_data.get('players', {}):
            await update.callback_query.message.reply_text(ERROR_MESSAGES["no_game"])
            return

        player = context.bot_data['players'][user_id]
        completed_quests = player["waterquest_data"]["completed_quests"]
        
        mensaje = (
            "📜 WaterQuests Disponibles 📜\n\n"
            "Misiones especiales que te llevarán a través del océano seco "
            "en busca de respuestas y poder.\n\n"
            "Misiones disponibles:"
        )
        
        # Lista de quests disponibles
        mensaje += "\n\n📜 La Voz del Abismo\n" \
                  "Una misteriosa voz llama desde las profundidades..."
        
        if "voice_of_abyss" in completed_quests:
            mensaje += "\n✅ Completada"

        # Usar reply_text si no hay mensaje para editar
        if update.callback_query and update.callback_query.message:
            try:
                await update.callback_query.message.edit_text(
                    mensaje,
                    reply_markup=create_waterquest_menu_keyboard()
                )
            except:
                await update.callback_query.message.reply_text(
                    mensaje,
                    reply_markup=create_waterquest_menu_keyboard()
                )
        else:
            await update.message.reply_text(
                mensaje,
                reply_markup=create_waterquest_menu_keyboard()
            )

    except Exception as e:
        logger.error(f"Error in waterquest_menu: {e}")
        if update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_text(
                ERROR_MESSAGES["generic_error"],
                reply_markup=generar_botones(player if 'player' in locals() else None)
            )
        elif update.message:
            await update.message.reply_text(ERROR_MESSAGES["generic_error"])

async def start_voice_of_abyss_quest(update: Update, context: CallbackContext):
#    Start the Voice of Abyss quest.
    try:
        user_id = update.effective_user.id
        if user_id not in context.bot_data.get('players', {}):
            await update.callback_query.message.reply_text(ERROR_MESSAGES["no_game"])
            return

        player = context.bot_data['players'][user_id]
        
        # Initialize quest if not exists
        if 'voice_of_abyss' not in context.bot_data:
            context.bot_data['voice_of_abyss'] = VoiceOfAbyssQuest()

        quest = context.bot_data['voice_of_abyss']
        success, message, data = await quest.start_quest(user_id, player)

        if success:
            # Store quest data
            player["waterquest_data"]["active_quests"]["voice_of_abyss"] = {
                "started_at": datetime.now().timestamp(),
                "current_node": data["node"].id
            }
            save_game_data(context.bot_data['players'])

            await update.callback_query.message.edit_text(
                data["node"].text,
                reply_markup=create_waterquest_dialogue_keyboard(data["node"].responses)
            )
        else:
            await update.callback_query.message.edit_text(
                message,
                reply_markup=generar_botones(player)
            )

    except Exception as e:
        logger.error(f"Error starting Voice of Abyss quest: {e}")
        await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])

async def process_quest_choice(update: Update, context: CallbackContext, choice_id: str):
    #   Process a choice made in a WaterQuest.
    try:
        user_id = update.effective_user.id
        player = context.bot_data['players'][user_id]
        quest = context.bot_data['voice_of_abyss']

        success, message, data = await quest.process_choice(
            user_id,
            choice_id,
            player
        )

        if success:
            # Update quest progress
            player["waterquest_data"]["active_quests"]["voice_of_abyss"]["current_node"] = data["node"].id
            save_game_data(context.bot_data['players'])

            await update.callback_query.message.edit_text(
                data["node"].text,
                reply_markup=create_waterquest_dialogue_keyboard(data["node"].responses)
            )
        else:
            await update.callback_query.message.edit_text(
                message,
                reply_markup=generar_botones(player)
            )

    except Exception as e:
        logger.error(f"Error processing quest choice: {e}")
        await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])"""


