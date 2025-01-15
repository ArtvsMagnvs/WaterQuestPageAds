# handlers/shop.py

# Standard library imports
import logging

# Third-party imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session

# Local imports
from database.db.game_db import Session, get_player, save_player, update_player, get_all_players
from bot.config.settings import SUCCESS_MESSAGES, ERROR_MESSAGES, logger
from bot.config.shop_items import SHOP_ITEMS, PREMIUM_SHOP_ITEMS, ShopManager
from bot.config.premium_settings import PREMIUM_FEATURES
from bot.config.ton_config import TON_CONFIG
from bot.utils.keyboard import generar_botones


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
        session = Session()
        try:
            player = get_player(session, user_id)
            if not player:
                if update.callback_query:
                    await update.callback_query.message.reply_text(ERROR_MESSAGES["no_game"])
                else:
                    await update.message.reply_text(ERROR_MESSAGES["no_game"])
                return

            if not player.mascota or 'oro' not in player.mascota:
                logger.error(f"Invalid or missing player data for user_id: {user_id}")
                if update.callback_query:
                    await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])
                else:
                    await update.message.reply_text(ERROR_MESSAGES["generic_error"])
                return

            # Header message with complete item descriptions and production rates
            header_message = (
                f"🏪 Bienvenido a la Tienda\n"
                f"💰 Tu oro: {player.mascota['oro']}\n\n"
                "Artículos disponibles:\n\n"
            )

            # Add descriptions and production rates to header message
            for base_item in SHOP_ITEMS:
                current_level = player.inventario.get(base_item['nombre'], 0) + 1
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
                    current_level = player.inventario.get(base_item['nombre'], 0) + 1
                    item = ShopManager.calculate_item_stats(base_item, current_level)
                    
                    # Create button text with only name, level and price
                    can_afford = player.mascota['oro'] >= item['costo']
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

        finally:
            session.close()

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

            current_level = player.inventario.get(item_name, 0) + 1
            item = ShopManager.calculate_item_stats(base_item, current_level)

            # Check if player has enough gold
            if mascota['oro'] >= item['costo']:
                # Process purchase
                mascota['oro'] -= item['costo']
                player.inventario[item_name] = current_level
                mascota['oro_hora'] += item['oro_hora']

                # Save game data
                save_player(player)

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

        finally:
            session.close()

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

async def comprar_fragmentos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Permite comprar fragmentos de destino con oro"""
    user_id = update.effective_user.id
    
    session = Session()
    try:
        player = get_player(session, user_id)
        if not player:
            await update.callback_query.message.reply_text("❌ No se encontró tu perfil de jugador.")
            return

        # Determinar cuántos fragmentos de destino puede comprar el jugador
        fragmentos_precio = 5  # Ejemplo: 5 oro por 1 fragmento de destino
        cantidad = 1  # En este caso compran 1 fragmento por transacción

        if player.mascota['oro'] < fragmentos_precio:
            await update.callback_query.message.reply_text("❌ No tienes suficiente oro para comprar Fragmentos de Destino.")
            return

        # Deduce el oro y agrega los fragmentos (tickets)
        player.mascota['oro'] -= fragmentos_precio
        player.fragmento_del_destino += cantidad  # Aumentar los fragmentos disponibles

        # Guardar los datos
        session.commit()

        # Mensaje de confirmación
        await update.callback_query.message.reply_text(f"✅ Has comprado {cantidad} Fragmento de Destino.")

    except Exception as e:
        logger.error(f"Error in comprar_fragmentos: {e}")
        await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])
    finally:
        session.close()

async def premium_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the premium shop menu with TON prices."""
    try:
        user_id = update.effective_user.id
        
        session = Session()
        try:
            player = get_player(session, user_id)
            
            if not player:
                await update.callback_query.message.reply_text(ERROR_MESSAGES["no_game"])
                return

            header_message = (
                "🌟 Tienda Premium 🌟\n\n"
                "Aquí puedes comprar artículos y mejoras especiales con TON.\n"
                "1 TON = 1,000,000,000 nanoTON\n\n"
            )

            keyboard = []
            for item_name, item_data in PREMIUM_SHOP_ITEMS.items():
                # Mostrar el nombre y la descripción en formato Fragmentos del Destino
                item_display_name = item_data["name"]
                item_description = item_data["description"]
                item_price = item_data["price"]
                
                # Añadir al mensaje de la tienda
                header_message += (
                    f"{item_display_name}\n"
                    f"{item_description}\n"
                    f"💰 Precio: {item_price} TON\n\n"
                )

                # Crear botón para comprar
                button = InlineKeyboardButton(
                    f"Comprar {item_display_name} ({item_price} TON)",
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

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error in premium_shop: {e}")
        await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])

async def buy_premium_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle premium item purchases using TON."""
    try:
        query = update.callback_query
        user_id = query.from_user.id
        item_name = query.data.split('_')[2]

        session = Session()
        try:
            player = get_player(session, user_id)
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
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error in buy_premium_item: {e}")
        await query.message.reply_text(ERROR_MESSAGES["generic_error"])

async def premium_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the premium shop menu with free items for testing."""
    try:
        user_id = update.effective_user.id
        session = Session()
        try:
            player = get_player(session, user_id)
            if not player:
                await update.callback_query.message.reply_text(ERROR_MESSAGES["no_game"])
                return

            header_message = (
                "🌟 Tienda Premium (Modo de Prueba) 🌟\n\n"
                "Aquí puedes obtener artículos y mejoras especiales de forma gratuita para probar.\n\n"
            )

            keyboard = []
            for item_name, item_data in PREMIUM_SHOP_ITEMS.items():
                emoji = item_data.get('emoji', '🎁')
                display_name = item_data.get('display_name', item_name)
                button = InlineKeyboardButton(
                    f"Obtener {emoji} {display_name}",
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

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error in premium_shop: {e}")
        await update.callback_query.message.reply_text(ERROR_MESSAGES["generic_error"])

async def get_premium_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        user_id = query.from_user.id
        item_name = query.data.split('_')[2]

        session = Session()
        try:
            player = get_player(session, user_id)
            if not player:
                await query.message.reply_text(ERROR_MESSAGES["no_game"])
                return

            item = PREMIUM_SHOP_ITEMS.get(item_name)
            if not item:
                await query.message.reply_text("Item no encontrado en la tienda premium.")
                return

            # Procesar compra de tickets (Fragmentos del Destino)
            if "tickets" in item_name:
                amount = item.get("amount", 0)
                player.premium_features['tickets'] = player.premium_features.get('tickets', 0) + amount
                update_player(session, player)

                await query.message.reply_text(
                    f"✅ Has comprado {amount} {item['name']} con éxito."
                )
            else:
                # Otros ítems, como suscripciones premium
                player.premium_features[item_name] = True
                update_player(session, player)
                await query.message.reply_text(
                    f"✅ Has obtenido {item['name']} con éxito."
                )

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error in get_premium_item: {e}")
        await query.message.reply_text(ERROR_MESSAGES["generic_error"])
