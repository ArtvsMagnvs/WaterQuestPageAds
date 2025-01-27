

from database.models.player_model import Player





def initialize_combat_stats(level: int) -> dict:
    """Initialize combat stats for a given level."""
    return {
        "level": level,
        "hp": 100 + (level * 10),
        "atk": 10 + (level * 2),
        "mp": 50 + (level * 5),
        "def_p": 5 + (level * 1.5),
        "def_m": 5 + (level * 1.5),
        "agi": 10 + (level * 1),
        "sta": 100 + (level * 5),
        "exp": 0,
        "exp_to_next_level": exp_needed_for_level(level)
    }

from bot.config.settings import logger

def add_exp(player, exp_gained: int):
    """
    Add experience to the player's combat stats and level up if necessary.
    
    Args:
    player (Player): The player object to update.
    exp_gained (int): The amount of experience to add.

    Returns:
    tuple: (bool, str) - (True if leveled up, message describing the result)
    """
    try:
        combat_stats = player.combat_stats
        combat_stats['exp'] += exp_gained
        leveled_up = False
        level_up_message = ""

        while combat_stats['exp'] >= combat_stats['exp_to_next_level']:
            combat_stats['exp'] -= combat_stats['exp_to_next_level']
            combat_stats['level'] += 1
            player.nivel_combate = combat_stats['level']  # Update player's combat level
            leveled_up = True

            # Update other stats
            combat_stats['hp'] += 10
            combat_stats['atk'] += 2
            combat_stats['mp'] += 5
            combat_stats['def_p'] += 1
            combat_stats['def_m'] += 1
            combat_stats['agi'] += 1
            combat_stats['sta'] += 10

            # Calculate new exp needed for next level
            combat_stats['exp_to_next_level'] = exp_needed_for_level(combat_stats['level'])

            level_up_message += f"¡Has subido al nivel de combate {combat_stats['level']}!\n"
            level_up_message += "Tus estadísticas han aumentado:\n"
            level_up_message += f"HP +10, ATK +2, MP +5, DEF_P +1, DEF_M +1, AGI +1, STA +10\n"

        # Update player's combat stats
        player.combat_stats = combat_stats

        # Prepare return message
        if leveled_up:
            return True, level_up_message
        else:
            return False, f"Has ganado {exp_gained} puntos de experiencia."

    except Exception as e:
        logger.error(f"Error in add_exp function: {e}")
        return False, "Ocurrió un error al añadir experiencia."

def exp_needed_for_level(level: int) -> int:
    """Calculate the experience needed for the next level."""
    return int(100 * (1.5 ** level))


def add_combat_exp(player: Player, exp_gained: int):
    """
    Add combat experience to the player.
    
    Args:
    player (Player): The player object to update.
    exp_gained (int): The amount of experience to add.

    Returns:
    tuple: (bool, str) - (True if leveled up, message describing the result)
    """
    return add_exp(player, exp_gained)
