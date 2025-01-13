from bot.config.premium_settings import PREMIUM_FEATURES
from telegram.ext import ContextTypes
import time

async def distribute_weekly_tickets(context: ContextTypes.DEFAULT_TYPE):
    """Distribute weekly tickets to premium users"""
    current_time = time.time()
    for user_id, player in context.bot_data.get('players', {}).items():
        premium_features = player.get('premium_features', {})
        if premium_features.get('premium_status', False):
            # Reset and add new tickets
            premium_features['tickets'] = PREMIUM_FEATURES['weekly_tickets']
            premium_features['last_ticket_distribution'] = current_time
            
            # Debug: Mostrar el número de tickets asignados
            print(f"User {user_id} ahora tiene {premium_features['tickets']} tickets.")

