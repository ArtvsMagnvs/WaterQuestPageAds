# utils/save_system.py

import json
import logging
from pathlib import Path
from datetime import datetime
import shutil
from typing import Dict, Optional

# Constants
SAVE_FILE = 'game_data.json'
BACKUP_DIR = 'backups'
MAX_BACKUPS = 5

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def save_game_data(data: Dict) -> bool:
    """
    Save game data to file with backup creation.
    
    Args:
        data: Dictionary with game data to save
    
    Returns:
        bool: True if save successful, False otherwise
    """
    try:
        # Create backup directory if it doesn't exist
        Path(BACKUP_DIR).mkdir(exist_ok=True)
        
        # Create backup if save file exists
        if Path(SAVE_FILE).exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f'game_data_backup_{timestamp}.json'
            backup_path = Path(BACKUP_DIR) / backup_name
            shutil.copy2(SAVE_FILE, backup_path)
            
            # Clean up old backups if there are too many
            backup_files = sorted(Path(BACKUP_DIR).glob('game_data_backup_*.json'))
            while len(backup_files) > MAX_BACKUPS:
                backup_files[0].unlink()  # Delete oldest backup
                backup_files = backup_files[1:]
        
        # Validate data before saving
        if not validate_save_data(data):
            logger.error("Invalid data structure, save aborted")
            return False

        # Save new data with pretty formatting
        with open(SAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        logger.info("Game data saved successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error saving game data: {e}")
        return False

def load_game_data() -> Dict:
    """
    Load game data from file with backup recovery.
    
    Returns:
        dict: Loaded game data or empty dict if no save exists
    """
    try:
        save_path = Path(SAVE_FILE)
        if not save_path.exists():
            logger.info("No save file found, starting fresh")
            return {}
            
        # Try to load main save file
        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                if validate_save_data(loaded_data):
                    logger.info("Game data loaded successfully")
                    return loaded_data
                else:
                    logger.error("Invalid save file structure, attempting backup")
                    return load_from_backup()
                
        except json.JSONDecodeError:
            logger.error("Corrupted save file, attempting backup")
            return load_from_backup()
            
    except Exception as e:
        logger.error(f"Error loading game data: {e}")
        return {}

def load_from_backup() -> Dict:
    """
    Attempt to load data from most recent valid backup.
    
    Returns:
        dict: Loaded backup data or empty dict if all backups fail
    """
    try:
        # Get all backup files, sorted by date (newest first)
        backup_files = sorted(
            Path(BACKUP_DIR).glob('game_data_backup_*.json'),
            reverse=True
        )
        
        for backup_file in backup_files:
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    if validate_save_data(loaded_data):
                        logger.info(f"Successfully loaded backup: {backup_file.name}")
                        
                        # Restore the backup as the main save
                        shutil.copy2(backup_file, SAVE_FILE)
                        return loaded_data
            except:
                continue
                
        # If all backups fail, start fresh
        logger.error("All backups corrupted, starting fresh")
        return {}
        
    except Exception as e:
        logger.error(f"Error loading from backup: {e}")
        return {}

def validate_save_data(data: Dict) -> bool:
    """
    Validate the structure and content of save data.
    
    Args:
        data: Dictionary containing game data to validate
        
    Returns:
        bool: True if data is valid, False otherwise
    """
    try:
        # Check if data is a dictionary
        if not isinstance(data, dict):
            return False
            
        # Check each player's data structure
        for user_id, player_data in data.items():
            required_keys = {
                'mascota', 'comida', 'última_alimentación',
                'última_actualización', 'inventario', 'combat_stats'
            }
            
            # Check if all required keys exist
            if not all(key in player_data for key in required_keys):
                return False
                
            # Check mascota structure
            mascota_keys = {
                'hambre', 'energia', 'nivel', 'oro', 'oro_hora'
            }
            if not all(key in player_data['mascota'] for key in mascota_keys):
                return False
                
            # Check combat_stats structure
            combat_keys = {
                'level', 'exp', 'battles_today', 'fire_coral'
            }
            if not all(key in player_data['combat_stats'] for key in combat_keys):
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating save data: {e}")
        return False

def backup_data(data: Dict) -> bool:
    """
    Create manual backup of game data.
    
    Args:
        data: Dictionary containing game data to backup
        
    Returns:
        bool: True if backup successful, False otherwise
    """
    try:
        if not validate_save_data(data):
            logger.error("Invalid data structure, backup aborted")
            return False
            
        Path(BACKUP_DIR).mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'game_data_backup_{timestamp}.json'
        backup_path = Path(BACKUP_DIR) / backup_name
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Manual backup created: {backup_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return False

def get_save_info() -> Dict:
    """
    Get information about current save file and backups.
    
    Returns:
        dict: Information about saves and backups
    """
    try:
        save_path = Path(SAVE_FILE)
        backup_path = Path(BACKUP_DIR)
        
        info = {
            "save_exists": save_path.exists(),
            "save_size": save_path.stat().st_size if save_path.exists() else 0,
            "save_modified": datetime.fromtimestamp(save_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S') if save_path.exists() else None,
            "backups": []
        }
        
        if backup_path.exists():
            backup_files = sorted(backup_path.glob('game_data_backup_*.json'), reverse=True)
            for backup in backup_files:
                info["backups"].append({
                    "name": backup.name,
                    "size": backup.stat().st_size,
                    "modified": datetime.fromtimestamp(backup.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return info
        
    except Exception as e:
        logger.error(f"Error getting save info: {e}")
        return {}
    