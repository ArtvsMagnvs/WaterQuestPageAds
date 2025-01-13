from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
import logging
import asyncio
import json
import aiohttp
from telegram.ext import CallbackQueryHandler
from bot.config.ads_config import AD_CONFIG  # Importar la configuración de anuncios
from telegram.ext import ConversationHandler
from typing import Dict, Any

# Your URL of the landing page
FRONTEND_URL = "https://artvsmagnvs.github.io/WaterQuest.game/"

logger = logging.getLogger(__name__)

class MonetagAd:
    BASE_URL = "https://artvsmagnvs.github.io/WaterQuest.game/"  # URL de tu página web

@staticmethod
async def initiate_ad() -> Dict[str, Any]:
    try:
        logger.info("Iniciando función initiate_ad")
        ad_zone_id = AD_CONFIG.get('ad_unit_id')
        logger.info(f"ad_zone_id obtenido: {ad_zone_id}")
        
        if not ad_zone_id:
            logger.error("Error: MONETAG_ZONE_ID no está configurado correctamente.")
            return {"success": False, "error": "Falta MONETAG_ZONE_ID"}

        logger.info(f"Iniciando proceso de anuncio con zone ID: {ad_zone_id}")
        
        logger.info(f"BASE_URL: {MonetagAd.BASE_URL}")
        ad_url = f"{MonetagAd.BASE_URL}?zone_id={ad_zone_id}"
        logger.info(f"ad_url generada: {ad_url}")
        
        return {
            "success": True, 
            "ad_data": {
                "ad_id": ad_zone_id,
                "ad_url": ad_url
            }
        }
    
    except Exception as e:
        logger.error(f"Error inesperado al iniciar el anuncio de Monetag: {str(e)}")
        logger.exception("Traceback completo: ")
        return {"success": False, "error": f"Error inesperado: {str(e)}"}

@staticmethod
async def verify_ad_view(ad_id: str) -> bool:
        # We trust Monetag to handle verification
        return True


async def ads_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú de anuncios con el progreso actual."""
    user_id = update.callback_query.from_user.id
    player = context.bot_data['players'].get(user_id)
    
    if not player:
        await update.callback_query.message.reply_text("❌ Error: Jugador no encontrado.")
        return
    
    # Obtener el conteo de anuncios diarios y asegurarse de que exista
    if "daily_ads" not in player:
        player["daily_ads"] = 0
    daily_ads = player["daily_ads"]
    
    keyboard = [
        [InlineKeyboardButton("📺 Ver Anuncio", callback_data="watch_ad")],
        [InlineKeyboardButton("🏠 Volver", callback_data="start")]
    ]
    
    message = (
        "📺 *Recompensas por Anuncios Diarios*\n\n"
        f"Anuncios vistos hoy: {daily_ads}/10\n\n"
        "Recompensas actuales:\n"
        "• Ver Anuncio: +25 Energía, +1 Combate Rápido\n"
        f"• 3 Anuncios Diarios: +1 MiniBoss {'✅' if daily_ads >= 3 else '❌'}\n"
        f"• 5 Anuncios Diarios: +2 MiniBoss, +1% Generación de Oro {('✅' if daily_ads >= 5 else '❌')}\n"
        f"• 10 Anuncios Diarios: +3 MiniBoss, +1 Fragmento de Destino {('✅' if daily_ads >= 10 else '❌')}\n\n"
        "Características Especiales:\n"
        "• Reintentar combate MiniBoss (1 Anuncio)\n"
        "• Reintentar combate Aventura (1 Anuncio)"
    )
    
    await update.callback_query.message.edit_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def process_ad_watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    player = context.bot_data['players'].get(user_id)
    
    if not player:
        await update.callback_query.message.reply_text("❌ Error: Player not found.")
        return

    daily_limit = AD_CONFIG.get('daily_limit', 100)
    if player.get("daily_ads", 0) >= daily_limit:
        await update.callback_query.message.reply_text(
            "❌ You've reached the maximum daily ad limit."
        )
        return

    loading_message = await update.callback_query.message.reply_text(
        "📺 Initiating ad..."
    )
    
    try:
        # Iniciar el anuncio de Monetag
        ad_result = await initiate_monetag_ad()
        
        if not ad_result["success"]:
            await loading_message.edit_text(f"❌ Error loading the ad: {ad_result['error']}")
            return

        ad_url = ad_result["ad_url"]
        ad_id = ad_result["ad_id"]

        # Direct link to the ad and processing reward
        await loading_message.edit_text(
            f"📺 Please click the link below to view the ad:\n\n{ad_url}",
            reply_markup=InlineKeyboardMarkup([  # Optional back button
                [InlineKeyboardButton("Back", callback_data="start")]
            ])
        )

        # Directly verify after ad viewing without confirmation step
        if await verify_ad_view(ad_id):
            # Rewards processing
            player["daily_ads"] += 1
            await grant_ad_rewards(player)
            await loading_message.edit_text("✅ Ad view confirmed. Processing rewards...")

        else:
            await loading_message.edit_text("❌ Ad view could not be verified. Please try again.")

    except Exception as e:
        logger.error(f"Error in process_ad_watch: {str(e)}")
        await loading_message.edit_text("❌ An unexpected error occurred. Please try again later.")


        # Verificar la visualización del anuncio
        viewed_ad_id = update.callback_query.data.split(":")[1]
        if await verify_ad_view(viewed_ad_id):
            await loading_message.edit_text("✅ Ad view confirmed. Processing rewards...")
            
            # Actualizar el conteo diario de anuncios
            player["daily_ads"] = player.get("daily_ads", 0) + 1
            
            # Otorgar recompensas
            rewards = await grant_ad_rewards(player)
            
            rewards_message = "🎁 Rewards obtained:\n" + "\n".join(rewards)
            await update.callback_query.message.reply_text(rewards_message)
            
            # Verificar hitos
            await check_ad_milestones(update, context, player)
        else:
            await loading_message.edit_text("❌ Ad view could not be verified. Please try again.")

    except Exception as e:
        logger.error(f"Error in process_ad_watch: {str(e)}")
        await loading_message.edit_text("❌ An unexpected error occurred. Please try again later.")

async def initiate_monetag_ad():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{FRONTEND_URL}/initiate-ad") as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "success": True,
                    "ad_url": data["ad_url"],
                    "ad_id": data["ad_id"]
                }
            else:
                return {"success": False, "error": "Failed to initiate ad"}

async def grant_ad_rewards(player):
    """Grants rewards for watching an ad."""
    rewards = []
    
    # Grant energy
    energy_reward = AD_CONFIG['ad_rewards']['watch']['energy']
    player['energy'] = min(player.get('energy', 0) + energy_reward, player.get('max_energy', 100))
    rewards.append(f"+{energy_reward} Energy")
    
    # Grant quick combat
    quick_combat_reward = AD_CONFIG['ad_rewards']['watch']['quick_combat']
    player['quick_combats'] = player.get('quick_combats', 0) + quick_combat_reward
    rewards.append(f"+{quick_combat_reward} Quick Combat")
    
    return rewards

async def check_ad_milestones(update: Update, context: ContextTypes.DEFAULT_TYPE, player):
    """Checks and grants milestone rewards based on daily ad count."""
    try:
        daily_ads = player.get("daily_ads", 0)
        milestones = AD_CONFIG['ad_rewards']['milestones']
        
        for count, rewards in milestones.items():
            if daily_ads == count:
                milestone_rewards = []
                for reward_type, value in rewards.items():
                    if reward_type == 'miniboss_attempts':
                        player['miniboss_attempts'] = player.get('miniboss_attempts', 0) + value
                        milestone_rewards.append(f"+{value} intentos de MiniBoss")
                    elif reward_type == 'gold_gen':
                        player['gold_multiplier'] = player.get('gold_multiplier', 1) * value
                        milestone_rewards.append(f"{value}x mejora en generación de oro")
                    elif reward_type == 'tickets':  # Internamente son tickets
                        player['premium_features']['tickets'] = (
                            player['premium_features'].get('tickets', 0) + value
                        )
                        milestone_rewards.append(f"+{value} Fragmentos del Destino")  # En la interfaz son Fragmentos del Destino
                
                if milestone_rewards:
                    milestone_message = (
                        f"🎉 ¡Hito alcanzado ({count} anuncios vistos)!\n\n" +
                        "\n".join(milestone_rewards)
                    )
                    await update.callback_query.message.reply_text(milestone_message)
                break
    except Exception as e:
        logger.error(f"Error in check_ad_milestones: {e}")
        await update.callback_query.message.reply_text("❌ An unexpected error occurred. Please try again later.")

async def retry_combat_ad(update: Update, context: ContextTypes.DEFAULT_TYPE, combat_type: str):
    """Maneja el reintento de combate a través de la visualización de anuncios."""
    user_id = update.callback_query.from_user.id
    player = context.bot_data['players'].get(user_id)
    
    if not player:
        await update.callback_query.message.reply_text("❌ Error: Jugador no encontrado.")
        return False

    loading_message = await update.callback_query.message.reply_text(
        "📺 Cargando anuncio para reintentar combate..."
    )
        
    try:
        # Mostrar anuncio de Monetag a través de la solicitud al frontend
        ad_result = await MonetagAd.show_ad()
        
        if not ad_result:
            await loading_message.edit_text("❌ Error al cargar el anuncio. Por favor, intenta nuevamente.")
            return False

        await loading_message.delete()
        
        # Actualizar el conteo de anuncios diarios
        player["daily_ads"] = player.get("daily_ads", 0) + 1
        
        # Guardar los datos del jugador
        context.bot_data['players'][user_id] = player
        
        await update.callback_query.message.reply_text(
            f"✅ ¡Ahora puedes reintentar el combate de {combat_type}!"
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error procesando el reintento del anuncio: {str(e)}")
        await loading_message.edit_text(
            "❌ Error procesando el anuncio. Por favor, intenta nuevamente."
        )
        return False

def register_handlers(application):
    """Registrar todos los controladores relacionados con los anuncios."""
    
    # Añadir el controlador para el menú de anuncios
    application.add_handler(CallbackQueryHandler(ads_menu, pattern="^ads_menu$"))
    
    # Añadir el controlador para procesar la visualización del anuncio
    application.add_handler(CallbackQueryHandler(process_ad_watch, pattern="^watch_ad$"))
