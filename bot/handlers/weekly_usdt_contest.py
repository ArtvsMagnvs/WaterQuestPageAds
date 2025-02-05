#weekly_usdt_contest.py

import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from bot.config.settings import logger
from bot.utils.save_system import save_game_data

# Contest Configuration
CONTEST_CONFIG = {
    "start_day": 0,  # Monday
    "start_hour": 17,  # 17:00 CET
    "duration_days": 7,
    "max_daily_ads": 10,
    "max_weekly_ads": 70,
    "daily_bonus_threshold": 10,
    "daily_bonus_tickets": 5,
    "weekly_bonus_threshold": 70,
    "weekly_bonus_tickets": 50,
    "min_ads_for_entry": 1,
    "prizes": [
        {"amount": 20, "count": 1},
        {"amount": 10, "count": 2},
        {"amount": 5, "count": 3},
        {"amount": 3, "count": 4},
        {"amount": 1, "count": 10}
    ]
}

# Test Mode Configuration
TEST_MODE = False
TEST_CONTEST_DURATION = timedelta(minutes=1)


async def weekly_contest_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the weekly contest menu."""
    user_id = update.effective_user.id
    contest_data = context.bot_data.get("weekly_contest", {})
    player_data = context.bot_data["players"].get(str(user_id), {})
    player_contest_data = player_data.get("contest_data", {"tickets": 0})

    if not contest_data or datetime.now() > contest_data.get("end_time", datetime.now()):
        message = "No hay un concurso activo en este momento. ¡Espera al próximo concurso semanal!"
    else:
        time_left = contest_data["end_time"] - datetime.now()
        message = (
            f"🏆 Concurso Semanal USDT\n\n"
            f"Tiempo restante: {time_left.days} días, {time_left.seconds // 3600} horas\n"
            f"Tus boletos: {player_contest_data['tickets']}\n\n"
            f"¡Mira anuncios para ganar más boletos!"
        )

    keyboard = [
        [InlineKeyboardButton("Ver Anuncio", callback_data="view_ad")],
        [InlineKeyboardButton("🏠 Volver", callback_data="start")]
    ]

    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def start_weekly_contest(context: ContextTypes.DEFAULT_TYPE):
    """Start the weekly contest."""
    contest_data = {
        "start_time": datetime.now(),
        "end_time": datetime.now() + (TEST_CONTEST_DURATION if TEST_MODE else timedelta(days=CONTEST_CONFIG["duration_days"])),
        "participants": {}
    }
    context.bot_data["weekly_contest"] = contest_data
    
    # Schedule the end of the contest
    context.job_queue.run_once(end_weekly_contest, TEST_CONTEST_DURATION if TEST_MODE else timedelta(days=CONTEST_CONFIG["duration_days"]))
    
    # Notify all users
    for user_id in context.bot_data["players"]:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="🎉 ¡El concurso semanal ha comenzado! Mira anuncios para ganar boletos y participar en el sorteo de 100 USDT.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Ver Anuncio", callback_data="view_ad")]])
            )
        except Exception as e:
            logger.error(f"Error notifying user {user_id}: {e}")

async def end_weekly_contest(context: ContextTypes.DEFAULT_TYPE):
    """End the weekly contest and distribute prizes."""
    contest_data = context.bot_data.get("weekly_contest", {})
    participants = contest_data.get("participants", {})
    
    if not participants:
        logger.warning("No participants in the weekly contest.")
        return
    
    winners = select_winners(participants)
    
    for user_id, prize in winners.items():
        player = context.bot_data["players"].get(str(user_id))
        if player:
            player["balance"] = player.get("balance", 0) + prize
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎊 ¡Felicidades! Has ganado {prize} USDT en el concurso semanal."
            )
    
    # Notify non-winners
    for user_id in participants:
        if user_id not in winners:
            await context.bot.send_message(
                chat_id=user_id,
                text="El concurso semanal ha terminado. ¡Gracias por participar! Mejor suerte la próxima vez."
            )
    
    # Save game data
    save_game_data(context.bot_data["players"])
    
    # Reset contest data
    context.bot_data["weekly_contest"] = {}
    
    # Schedule the next contest
    next_contest_time = get_next_contest_start_time()
    context.job_queue.run_once(start_weekly_contest, next_contest_time - datetime.now())

def select_winners(participants):
    """Select winners based on their tickets."""
    all_tickets = []
    for user_id, tickets in participants.items():
        all_tickets.extend([user_id] * tickets)
    
    winners = {}
    for prize in CONTEST_CONFIG["prizes"]:
        for _ in range(prize["count"]):
            if all_tickets:
                winner = random.choice(all_tickets)
                winners[winner] = winners.get(winner, 0) + prize["amount"]
                all_tickets = [t for t in all_tickets if t != winner]
    
    return winners

def get_next_contest_start_time():
    """Get the start time for the next contest."""
    now = datetime.now()
    days_ahead = CONTEST_CONFIG["start_day"] - now.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    next_contest = now.replace(hour=CONTEST_CONFIG["start_hour"], minute=0, second=0, microsecond=0) + timedelta(days=days_ahead)
    return next_contest

async def view_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ad viewing and update contest tickets."""
    user_id = update.effective_user.id
    contest_data = context.bot_data.get("weekly_contest", {})
    
    if not contest_data or datetime.now() > contest_data.get("end_time", datetime.now()):
        await update.callback_query.answer("No hay un concurso activo en este momento.")
        return
    
    player = context.bot_data["players"].get(str(user_id))
    if not player:
        await update.callback_query.answer("Debes iniciar el juego primero con /start.")
        return
    
    # Simulate ad viewing
    if TEST_MODE:
        await update.callback_query.answer("Anuncio simulado visto con éxito.")
    else:
        # Here you would integrate with your actual ad viewing system
        # For now, we'll just simulate it
        await update.callback_query.answer("Anuncio visto con éxito.")
    
    # Update player's contest data
    player_contest_data = player.setdefault("contest_data", {"daily_ads": 0, "weekly_ads": 0, "tickets": 0})
    player_contest_data["daily_ads"] += 1
    player_contest_data["weekly_ads"] += 1
    player_contest_data["tickets"] += 1
    
    # Apply bonuses
    if player_contest_data["daily_ads"] == CONTEST_CONFIG["daily_bonus_threshold"]:
        player_contest_data["tickets"] += CONTEST_CONFIG["daily_bonus_tickets"]
    if player_contest_data["weekly_ads"] == CONTEST_CONFIG["weekly_bonus_threshold"]:
        player_contest_data["tickets"] += CONTEST_CONFIG["weekly_bonus_tickets"]
    
    # Update contest participants
    contest_data["participants"][user_id] = player_contest_data["tickets"]
    
    await update.callback_query.edit_message_text(
        f"Anuncio visto. Tienes {player_contest_data['tickets']} boletos para el concurso semanal.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Ver Otro Anuncio", callback_data="view_ad")]])
    )

def setup_weekly_contest(application):
    """Set up the weekly contest handlers and initial job."""
    application.add_handler(CallbackQueryHandler(view_ad, pattern="^view_ad$"))
    
    # Schedule the first contest
    next_contest_time = get_next_contest_start_time()
    application.job_queue.run_once(start_weekly_contest, next_contest_time - datetime.now())

# Test command to force start a contest
async def force_start_contest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if TEST_MODE:
        await start_weekly_contest(context)
        await update.message.reply_text("Concurso de prueba iniciado.")
    else:
        await update.message.reply_text("El modo de prueba no está activado.")

def add_test_commands(application):
    if TEST_MODE:
        application.add_handler(CommandHandler("force_start_contest", force_start_contest))