import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
 
# Database configuration for Railway PostgreSQL
db_url = os.environ.get('DATABASE_URL')

if db_url is None:
    raise ValueError("DATABASE_URL environment variable is not set")

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url)
Session = sessionmaker(bind=engine)

def get_player(user_id):
    session = Session()
    try:
        player = session.query(Player).filter_by(id=user_id).first()
        return player
    finally:
        session.close()

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

def create_player(user_id, nombre):
    session = Session()
    try:
        new_player = Player(id=user_id, nombre=nombre)
        session.add(new_player)
        session.commit()
        return new_player
    except:
        session.rollback()
        raise
    finally:
        session.close()

def get_all_players():
    session = Session()
    try:
        players = session.query(Player).all()
        return players
    finally:
        session.close()