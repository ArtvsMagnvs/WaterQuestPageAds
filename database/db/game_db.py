from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models.player_model import Base, Player
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

def get_player(session, user_id):
    """Retrieve a player from the database."""
    return session.query(Player).filter(Player.id == user_id).first()

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

def update_player(user_id, update_data):
    session = Session()
    try:
        player = session.query(Player).filter_by(id=user_id).first()
        if player:
            for key, value in update_data.items():
                if hasattr(player, key):
                    setattr(player, key, value)
                else:
                    raise AttributeError(f"Player object has no attribute '{key}'")
            session.commit()
            return player
        else:
            return None
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()