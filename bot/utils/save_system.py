from database.models.player_model import Player
from database.db.game_db import Session, get_player, save_player, create_player, get_all_players
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import json
import os
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_game_data(data: dict[int, dict]) -> bool:
    """
    Save game data to the database.
    
    Args:
        data: Dictionary with game data to save, keyed by user_id
    
    Returns:
        bool: True if save successful, False otherwise
    """
    try:
        session = Session()
        for user_id, player_data in data.items():
            player = session.query(Player).filter(Player.id == user_id).first()
            if player:
                # Update existing player
                for key, value in player_data.items():
                    setattr(player, key, value)
            else:
                # Create new player
                new_player = Player(**player_data)
                session.add(new_player)
        
        session.commit()
        logger.info("Game data saved successfully to database")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database error saving game data: {e}")
        session.rollback()
        return False
    except Exception as e:
        logger.error(f"Error saving game data: {e}")
        return False
    finally:
        session.close()

def load_game_data() -> dict[int, dict]:
    """
    Load game data from the database.
    
    Returns:
        dict: Loaded game data keyed by user_id
    """
    try:
        players = get_all_players()
        
        game_data = {player.id: player.to_dict() for player in players}
        
        logger.info("Game data loaded successfully from database")
        return game_data
    except SQLAlchemyError as e:
        logger.error(f"Database error loading game data: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error loading game data: {e}")
        return {}

def backup_data():
    """
    Create a backup of all player data.
    """
    players = get_all_players()
    backup_data = [player.to_dict() for player in players]
    
    backup_dir = 'backups'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f'game_data_backup_{timestamp}.json')
    
    with open(backup_file, 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    logger.info(f"Backup created: {backup_file}")
    return backup_file

def restore_from_backup(backup_file):
    """
    Restore game data from a backup file.
    """
    with open(backup_file, 'r') as f:
        backup_data = json.load(f)
    
    session = Session()
    try:
        for player_data in backup_data:
            player_id = player_data['id']
            player = get_player(player_id)
            if player:
                for key, value in player_data.items():
                    setattr(player, key, value)
            else:
                new_player = Player.from_dict(player_data)
                session.add(new_player)
        session.commit()
        logger.info(f"Game data restored from backup: {backup_file}")
    except Exception as e:
        session.rollback()
        logger.error(f"Error restoring from backup: {e}")
        raise
    finally:
        session.close()

def get_save_info():
    """
    Get information about the current save state.
    """
    players = get_all_players()
    total_players = len(players)
    last_save = max(player.ultima_actualizacion for player in players) if players else None
    
    return {
        "total_players": total_players,
        "last_save": datetime.fromtimestamp(last_save).strftime("%Y-%m-%d %H:%M:%S") if last_save else None
    }

def initialize_new_player(player_id, nombre):
    """
    Initialize a new player in the database.
    """
    new_player = create_player(player_id, nombre)
    logger.info(f"New player initialized: {nombre} (ID: {player_id})")
    return new_player.to_dict()