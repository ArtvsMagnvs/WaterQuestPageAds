


def exp_needed_for_level(level: int) -> int:
    """Calculate the experience needed for the next level."""
    return int(100 * (1.5 ** level))

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
