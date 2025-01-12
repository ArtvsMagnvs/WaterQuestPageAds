# handlers/shop.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from bot.config.settings import SUCCESS_MESSAGES, ERROR_MESSAGES, logger
from bot.config.shop_items import SHOP_ITEMS, PREMIUM_SHOP_ITEMS, ShopManager
from bot.utils.keyboard import generar_botones
from bot.utils.save_system import save_game_data
from bot.config.premium_settings import PREMIUM_FEATURES

#---------------------------------------------------------------
# Temporarily comment out TON SDK imports

from bot.config.ton_config import TON_CONFIG

#ton_utils = TONUtils()
#transaction_verifier = TransactionVerifier()

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

async def premium_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the premium shop menu with TON prices."""
    try:
        user_id = update.effective_user.id
        if user_id not in context.bot_data.get('players', {}):
            await update.callback_query.message.reply_text(ERROR_MESSAGES["no_game"])
            return

        player = context.bot_data['players'][user_id]

        header_message = (
            "🌟 Tienda Premium 🌟\n\n"
            "Aquí puedes comprar artículos y mejoras especiales con TON.\n"
            "1 TON = 1,000,000,000 nanoTON\n\n"
        )

        keyboard = []
        for item_name, item_data in PREMIUM_SHOP_ITEMS.items():
            item_info = ShopManager.format_premium_item_info(item_data)
            header_message += f"{item_info}\n\n"
            
            button = InlineKeyboardButton(
                f"Comprar {item_data['emoji']} {item_name} ({item_data['price']} TON)",
                callback_data=f"buy_premium_{item_name}"
            )
            keyboard.append([button])

        keyboard.append([InlineKeyboardButton("🏪 Tienda Normal", callback_data="tienda")])
        keyboard.append([InlineKeyboardButton("🏠 Volver al Menú", callback_data="start")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.message.edit_text(
                text=header_message,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text=header_message,
                reply_markup=reply_markup
            )

    except Exception as e:
        logger.error(f"Error in premium_shop: {e}")
        await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])

async def buy_premium_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle premium item purchases using TON."""
    try:
        query = update.callback_query
        user_id = query.from_user.id
        item_name = query.data.split('_')[2]

        player = context.bot_data['players'].get(user_id)
        if not player:
            await query.message.reply_text(ERROR_MESSAGES["no_game"])
            return

        item = PREMIUM_SHOP_ITEMS.get(item_name)
        if not item:
            await query.message.reply_text("Item not found in premium shop.")
            return

        # Generate a unique payment address for this transaction
#------------------------------------------------------------------------------------------------
        #payment_address = await ton_utils.generate_payment_address(user_id, item_name)
#------------------------------------------------------------------------------------------------
        # Create a payment link
        #payment_amount = item['price'] * 1_000_000_000  # Convert TON to nanoTON
        #payment_link = f"ton://transfer/{payment_address}?amount={payment_amount}"
#------------------------------------------------------------------------------------------------
        # Send payment instructions to the user
        #payment_message = (
        #    f"Para comprar {item['emoji']} {item_name}, por favor sigue estos pasos:\n\n"
        #    f"1. Haz clic en este enlace para abrir tu billetera TON: {payment_link}\n"
        #    f"2. Confirma el pago de {item['price']} TON\n"
        #    "3. Una vez realizado el pago, haz clic en 'Verificar Pago'\n\n"
        #    "El artículo se añadirá a tu cuenta una vez que se confirme el pago."
        #)

        verify_button = InlineKeyboardButton("Verificar Pago", callback_data=f"verify_payment_{item_name}")
        cancel_button = InlineKeyboardButton("Cancelar", callback_data="premium_shop")
        reply_markup = InlineKeyboardMarkup([[verify_button], [cancel_button]])

        #await query.message.reply_text(payment_message, reply_markup=reply_markup)
#------------------------------------------------------------------------------------------------
    except Exception as e:
        logger.error(f"Error in buy_premium_item: {e}")
        await query.message.reply_text(ERROR_MESSAGES["generic_error"])

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.config.settings import SUCCESS_MESSAGES, ERROR_MESSAGES, logger
from bot.config.shop_items import PREMIUM_SHOP_ITEMS
from bot.utils.save_system import save_game_data

# async def verify_premium_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Verify the payment for a premium item."""
#     try:
#         query = update.callback_query
#         user_id = query.from_user.id
#         item_name = query.data.split('_')[2]
#
#         player = context.bot_data['players'].get(user_id)
#         if not player:
#             await query.message.reply_text(ERROR_MESSAGES["no_game"])
#             return
#
#         item = PREMIUM_SHOP_ITEMS.get(item_name)
#         if not item:
#             await query.message.reply_text("Item not found in premium shop.")
#             return
#
#         # Verify the transaction
#         payment_address = await ton_utils.get_payment_address(user_id, item_name)
#         expected_amount = item['price'] * 1_000_000_000  # Convert TON to nanoTON
#         is_paid = await transaction_verifier.verify_payment(payment_address, expected_amount)
#
#         if is_paid:
#             # Update player's premium features
#             if 'premium_features' not in player:
#                 player['premium_features'] = {}
#             player['premium_features'][item_name] = True
#             save_game_data(context.bot_data['players'])
#
#             await query.message.reply_text(f"✅ Pago confirmado. Has adquirido {item['emoji']} {item_name}!")
#         else:
#             await query.message.reply_text("❌ No se ha detectado el pago. Por favor, intenta de nuevo más tarde o contacta con soporte si crees que es un error.")
#
#     except Exception as e:
#         logger.error(f"Error in verify_premium_payment: {e}")
#         await query.message.reply_text(ERROR_MESSAGES["generic_error"])

async def premium_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the premium shop menu with free items for testing."""
    try:
        user_id = update.effective_user.id
        if user_id not in context.bot_data.get('players', {}):
            await update.callback_query.message.reply_text(ERROR_MESSAGES["no_game"])
            return

        player = context.bot_data['players'][user_id]

        header_message = (
            "🌟 Tienda Premium (Modo de Prueba) 🌟\n\n"
            "Aquí puedes obtener artículos y mejoras especiales de forma gratuita para probar.\n\n"
        )

        keyboard = []
        for item_name, item_data in PREMIUM_SHOP_ITEMS.items():
            button = InlineKeyboardButton(
                f"Obtener {item_data['emoji']} {item_name}",
                callback_data=f"get_premium_{item_name}"
            )
            keyboard.append([button])

        keyboard.append([InlineKeyboardButton("🏪 Tienda Normal", callback_data="tienda")])
        keyboard.append([InlineKeyboardButton("🏠 Volver al Menú", callback_data="start")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.message.edit_text(
                text=header_message,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text=header_message,
                reply_markup=reply_markup
            )

    except Exception as e:
        logger.error(f"Error in premium_shop: {e}")
        await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])

async def get_premium_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle free premium item acquisition for testing."""
    try:
        query = update.callback_query
        user_id = query.from_user.id
        item_name = query.data.split('_')[2]

        player = context.bot_data['players'].get(user_id)
        if not player:
            await query.message.reply_text(ERROR_MESSAGES["no_game"])
            return

        item = PREMIUM_SHOP_ITEMS.get(item_name)
        if not item:
            await query.message.reply_text("Item not found in premium shop.")
            return

        # Update player's premium features
        if 'premium_features' not in player:
            player['premium_features'] = {}
        player['premium_features'][item_name] = True
        save_game_data(context.bot_data['players'])

        await query.message.reply_text(f"✅ Has obtenido {item['emoji']} {item_name} de forma gratuita para pruebas!")

    except Exception as e:
        logger.error(f"Error in get_premium_item: {e}")
        await query.message.reply_text(ERROR_MESSAGES["generic_error"])