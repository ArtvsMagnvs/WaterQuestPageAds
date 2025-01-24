from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models.player_model import Base, Player
from bot.utils.game_mechanics import initialize_combat_stats
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration for Railway PostgreSQL
db_url = os.environ.get('DATABASE_URL')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url)
Session = sessionmaker(bind=engine)

from contextlib import contextmanager

@contextmanager
def db_session():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_player(session, user_id):
    player = session.query(Player).filter_by(id=user_id).first()
    if player and not player.combat_stats:
        player.combat_stats = initialize_combat_stats(1)
        session.commit()
    return player

def save_player(player):
    session = Session()
    try:
        session.merge(player)
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def create_player(user_id):
    session = Session()
    try:
        new_player = Player(user_id=user_id)
        session.add(new_player)
        session.commit()
        # Refresh the instance to ensure all attributes are loaded
        session.refresh(new_player)
        return new_player
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating player for user_id {user_id}: {str(e)}")
        raise e
    finally:
        session.close()

def get_all_players():
    session = Session()
    try:
        players = session.query(Player).all()
        return players
    finally:
        session.close()

def update_player(session, user_id, update_data):
    try:
        player = session.query(Player).filter_by(id=user_id).first()
        if player:
            for key, value in update_data.items():
                setattr(player, key, value)
            return player
        else:
            return None
    except Exception as e:
        raise e