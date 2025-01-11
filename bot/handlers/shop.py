# handlers/shop.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from bot.config.settings import SUCCESS_MESSAGES, ERROR_MESSAGES, logger
from bot.config.shop_items import SHOP_ITEMS, ShopManager
from bot.utils.keyboard import generar_botones
from bot.utils.save_system import save_game_data
from bot.config.premium_settings import PREMIUM_FEATURES

#---------------------------------------------------------------
# Temporarily comment out TON SDK imports
class TonClientException(Exception):
    pass
TonClientError = TonClientException

# Temporary payment processing
async def process_premium_purchase(update, context):
    return True  # Simulates successful purchase
#---------------------------------------------------------------

async def tienda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle shop interface with full-width button layout."""
    try:
        user_id = update.effective_user.id
        if user_id not in context.bot_data.get('players', {}):
            if update.callback_query:
                await update.callback_query.message.reply_text(ERROR_MESSAGES["no_game"])
            else:
                await update.message.reply_text(ERROR_MESSAGES["no_game"])
            return

        player = context.bot_data['players'][user_id]
        if not player or 'mascota' not in player or 'oro' not in player['mascota']:
            logger.error(f"Invalid or missing player data for user_id: {user_id}")
            if update.callback_query:
                await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])
            else:
                await update.message.reply_text(ERROR_MESSAGES["generic_error"])
            return

        # Header message with complete item descriptions and production rates
        header_message = (
            f"🏪 Bienvenido a la Tienda\n"
            f"💰 Tu oro: {player['mascota']['oro']}\n\n"
            "Artículos disponibles:\n\n"
        )

        # Add descriptions and production rates to header message
        for base_item in SHOP_ITEMS:
            current_level = player['inventario'].get(base_item['nombre'], 0) + 1
            item = ShopManager.calculate_item_stats(base_item, current_level)
            header_message += (
                f"{base_item['emoji']} {base_item['nombre']}\n"
                f"📝 {base_item['descripcion']}\n"
                f"🪙 Producción: {item['oro_hora']} oro/hora\n\n"
            )

        if not SHOP_ITEMS:
            logger.error("SHOP_ITEMS is empty.")
            header_message += "❌ No hay artículos disponibles en la tienda.\n"
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Volver al Menú", callback_data="start")]])
        else:
            item_buttons = []
            for base_item in SHOP_ITEMS:
                current_level = player['inventario'].get(base_item['nombre'], 0) + 1
                item = ShopManager.calculate_item_stats(base_item, current_level)
                
                # Create button text with only name, level and price
                can_afford = player['mascota']['oro'] >= item['costo']
                item_text = (
                    f"{base_item['emoji']} {base_item['nombre']}\u2800\u2800\n"
                    f"Nivel {current_level}\u2800\u2800\n"
                    f"💰 Precio: {item['costo']} oro\u2800\u2800"
                )
                
                # Create button with comprar callback
                button = InlineKeyboardButton(
                    text=item_text,
                    callback_data=f"comprar_{base_item['nombre']}"
                )
                
                # Add button in its own row
                item_buttons.append([button])

            # Add navigation button at the bottom
            item_buttons.append([InlineKeyboardButton("🏠 Volver al Menú", callback_data="start")])
            reply_markup = InlineKeyboardMarkup(item_buttons)

        if update.callback_query:
            try:
                await update.callback_query.message.edit_text(
                    text=header_message,
                    reply_markup=reply_markup
                )
            except Exception as edit_error:
                logger.warning(f"Could not edit shop message, sending new one: {edit_error}")
                await update.callback_query.message.reply_text(
                    text=header_message,
                    reply_markup=reply_markup
                )
        else:
            await update.message.reply_text(
                text=header_message,
                reply_markup=reply_markup
            )

    except Exception as e:
        logger.error(f"Error in tienda: {e}")
        try:
            if update.callback_query:
                await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])
            else:
                await update.message.reply_text(ERROR_MESSAGES["generic_error"])
        except Exception as reply_error:
            logger.error(f"Failed to send error message: {reply_error}")

async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE, item_name: str):
    """Handle item purchases."""
    try:
        user_id = update.effective_user.id
        if user_id not in context.bot_data.get('players', {}):
            if update.callback_query:
                await update.callback_query.message.reply_text(ERROR_MESSAGES["no_game"])
            else:
                await update.message.reply_text(ERROR_MESSAGES["no_game"])
            return

        player = context.bot_data['players'][user_id]
        mascota = player['mascota']
        
        # Get base item and calculate current level stats
        base_item = next((item for item in SHOP_ITEMS if item['nombre'] == item_name), None)
        if not base_item:
            if update.callback_query:
                await update.callback_query.message.edit_text(
                    "❌ Artículo no encontrado.",
                    reply_markup=generar_botones()
                )
            else:
                await update.message.reply_text(
                    "❌ Artículo no encontrado.",
                    reply_markup=generar_botones()
                )
            return

        current_level = player['inventario'].get(item_name, 0) + 1
        item = ShopManager.calculate_item_stats(base_item, current_level)

        # Check if player has enough gold
        if mascota['oro'] >= item['costo']:
            # Process purchase
            mascota['oro'] -= item['costo']
            player['inventario'][item_name] = current_level
            mascota['oro_hora'] += item['oro_hora']

            # Save game data
            save_game_data(context.bot_data['players'])

            # Calculate next level stats for display
            next_level = ShopManager.calculate_item_stats(base_item, current_level + 1)

            # Prepare success message
            mensaje = (
                f"✅ ¡Compra exitosa!\n\n"
                f"{item['emoji']} {item_name} nivel {current_level}\n"
                f"💰 Oro restante: {mascota['oro']}\n"
                f"⚡ Producción añadida: +{item['oro_hora']}/min\n"
                f"📈 Producción total: {mascota['oro_hora']}/min\n\n"
                f"Siguiente nivel costará: {next_level['costo']} oro\n"
                f"Y producirá: +{next_level['oro_hora']}/min"
            )

            # Create keyboard for next actions
            keyboard = [
                [InlineKeyboardButton("🏪 Seguir Comprando", callback_data="tienda")],
                [InlineKeyboardButton("📊 Ver Estado", callback_data="estado")],
                [InlineKeyboardButton("🏠 Volver al Menú", callback_data="start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if update.callback_query:
                await update.callback_query.message.edit_text(mensaje, reply_markup=reply_markup)
            else:
                await update.message.reply_text(mensaje, reply_markup=reply_markup)
        else:
            # Not enough gold
            falta_oro = item['costo'] - mascota['oro']
            mensaje = (
                f"❌ No tienes suficiente oro.\n"
                f"Necesitas: {item['costo']} oro\n"
                f"Tienes: {mascota['oro']} oro\n"
                f"Te faltan: {falta_oro} oro"
            )
            
            keyboard = [[InlineKeyboardButton("🔙 Volver a la Tienda", callback_data="tienda")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.message.edit_text(mensaje, reply_markup=reply_markup)
            else:
                await update.message.reply_text(mensaje, reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Error in comprar: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(
                ERROR_MESSAGES["generic_error"],
                reply_markup=generar_botones()
            )
        else:
            await update.message.reply_text(
                ERROR_MESSAGES["generic_error"],
                reply_markup=generar_botones()
            )