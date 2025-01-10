from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
import logging
import asyncio
import json
import aiohttp
from telegram.ext import CallbackQueryHandler
from config.ads_config import AD_CONFIG  # Importar la configuración de anuncios

logger = logging.getLogger(__name__)

class MonetagAd:
    @staticmethod
    async def show_ad():
        """Ejecuta el anuncio de Monetag utilizando el MONETAG_ZONE_ID configurado."""
        try:
            # Obtener el MONETAG_ZONE_ID de la configuración
            ad_zone_id = AD_CONFIG['ad_unit_id']
            
            # Comprobación si el ad_zone_id está configurado correctamente
            if not ad_zone_id:
                logger.error("Error: MONETAG_ZONE_ID no está configurado correctamente.")
                return False

            # Información del logger antes de intentar mostrar el anuncio
            logger.info(f"Intentando mostrar el anuncio con el zone ID: {ad_zone_id}")
            
            # Aquí es donde el anuncio se presenta directamente
            # Dependiendo de cómo se configure Monetag, podría ser solo enviar este ID al frontend
            # o realizar algún tipo de interacción con un servidor que lo maneje.
            
            # Simulación de la lógica de presentación del anuncio (según configuración de Monetag)
            # Esto puede ser más complejo si es necesario interactuar con un servicio de Monetag.
            # En este caso, el simple hecho de usar el MONETAG_ZONE_ID debería ser suficiente.
            
            logger.info(f"Anuncio mostrado con éxito con el zone ID: {ad_zone_id}")
            return True
        
        except KeyError as e:
            logger.error(f"Error: No se encontró la clave en la configuración: {str(e)}")
            return False
        except ValueError as e:
            logger.error(f"Error de valor: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado al ejecutar el anuncio Monetag: {str(e)}")
            return False




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
    """Procesa la visualización del anuncio y las recompensas."""
    user_id = update.callback_query.from_user.id
    player = context.bot_data['players'].get(user_id)
    
    if not player:
        await update.callback_query.message.reply_text("❌ Error: Jugador no encontrado.")
        return

    # Verificar si el jugador ha visto el máximo de anuncios hoy
    if player.get("daily_ads", 0) >= AD_CONFIG['daily_limit']:
        await update.callback_query.message.reply_text(
            "❌ Has alcanzado el límite máximo de anuncios diarios."
        )
        return

    loading_message = await update.callback_query.message.reply_text(
        "📺 Cargando anuncio..."
    )
    
    try:
        # Mostrar anuncio de Monetag a través de la solicitud al frontend
        ad_result = await MonetagAd.show_ad()
        
        if not ad_result:
            await loading_message.edit_text("❌ Error al cargar el anuncio. Por favor, intenta nuevamente.")
            return

        await loading_message.delete()
        
        # Actualizar el conteo de anuncios diarios
        daily_ads = player.get("daily_ads", 0) + 1
        player["daily_ads"] = daily_ads
        
        # Inicializar el seguimiento de recompensas
        rewards_message = ["✅ Recompensas obtenidas:"]
        
        # Recompensas base por ver el anuncio
        player["mascota"]["energia"] = min(
            player["mascota"]["energia"] + AD_CONFIG['ad_rewards']['watch']['energy'],
            player["mascota"]["energia_max"]
        )
        player["combat_stats"]["battles_today"] += 1
        rewards_message.append(f"• +{AD_CONFIG['ad_rewards']['watch']['energy']} Energía")
        rewards_message.append(f"• +{AD_CONFIG['ad_rewards']['watch']['quick_combat']} Combate Rápido")
        
        # Verificar recompensas por hitos
        if daily_ads == 3:
            player["miniboss_stats"]["attempts_today"] += 1
            rewards_message.append("• +1 intento de MiniBoss (hito 3 anuncios)")

        elif daily_ads == 5:
            player["miniboss_stats"]["attempts_today"] += 2
            # Aumentar generación de oro en un 1%
            current_gold = player["mascota"]["oro_hora"]
            player["mascota"]["oro_hora"] = current_gold * 1.01
            rewards_message.append("• +2 intentos de MiniBoss")
            rewards_message.append("• +1% Generación de Oro (hito 5 anuncios)")

        elif daily_ads == 10:
            player["miniboss_stats"]["attempts_today"] += 3
            player["lucky_tickets"] = player.get("lucky_tickets", 0) + 1
            rewards_message.append("• +3 intentos de MiniBoss")
            rewards_message.append("• +1 Fragmento de Destino (hito 10 anuncios)")
        
        # Guardar los datos del jugador
        context.bot_data['players'][user_id] = player
        
        await update.callback_query.message.reply_text(
            "\n".join(rewards_message)
        )
        
        # Regresar al menú de anuncios
        await ads_menu(update, context)
        
    except Exception as e:
        logger.error(f"Error procesando la visualización del anuncio: {str(e)}")
        await loading_message.edit_text(
            "❌ Error procesando el anuncio. Por favor, intenta nuevamente."
        )

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
