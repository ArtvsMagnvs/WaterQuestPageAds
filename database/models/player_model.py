from sqlalchemy import Column, Integer, String, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import DateTime
from datetime import datetime


Base = declarative_base()

class Player(Base):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    nombre = Column(String, nullable=False)
    nivel = Column(Integer, default=1)
    nivel_combate = Column(Integer, default=1)
    oro_por_minuto = Column(Float, default=1.0)
    inventario = Column(JSON, default={})
    fire_coral = Column(Integer, default=0)
    comida = Column(Integer, default=0)
    fragmento_del_destino = Column(Integer, default=0)
    watershard = Column(Integer, default=0)
    ultima_alimentacion = Column(DateTime, default=datetime.utcnow)
    ultima_actualizacion = Column(DateTime, default=datetime.utcnow)

    mascota = Column(JSON, default={
        "hambre": 100,
        "energia": 100,
        "nivel": 1,
        "oro": 0,
        "oro_hora": 1,
    })

    combat_stats = Column(JSON, default={
        "level": 1,
        "hp": 100,
        "atk": 10,
        "mp": 50,
        "def_p": 5,
        "def_m": 5,
        "agi": 10,
        "sta": 100,
        "exp": 0,
        "exp_to_next_level": 100
    })

    premium_features = Column(JSON, default={
        "premium_status": False,
        "premium_status_expires": 0,
        "tickets": 0,
        "daily_bonus": False
    })

    daily_reward = Column(JSON, default={
        "last_claim": 0,
        "streak": 0,
        "last_weekly_tickets": 0
    })

    miniboss_stats = Column(JSON, default={
        "attempts_today": 0,
        "last_attempt_date": None
    })

    def __init__(self, user_id, nombre):
        self.user_id = user_id
        self.nombre = nombre
        self.nivel = 1
        self.nivel_combate = 1
        self.oro_por_minuto = 1.0
        self.inventario = {}
        self.fire_coral = 0
        self.comida = 0
        self.fragmento_del_destino = 0
        self.watershard = 0
        self.ultima_alimentacion = datetime.utcnow()
        self.ultima_actualizacion = datetime.utcnow()
        self.mascota = {
            "hambre": 100,
            "energia": 100,
            "nivel": 1,
            "oro": 0,
            "oro_hora": 1,
            "fire_coral": 0,
        }
        self.combat_stats = {
            "level": 1,
            "hp": 100,
            "atk": 10,
            "mp": 50,
            "def_p": 5,
            "def_m": 5,
            "agi": 10,
            "sta": 100,
            "exp": 0,
            "exp_to_next_level": 100
        }
        self.premium_features = {
            "premium_status": False,
            "premium_status_expires": 0,
            "tickets": 0,
            "daily_bonus": False
        }
        self.daily_reward = {
            "last_claim": 0,
            "streak": 0,
            "last_weekly_tickets": 0
        }
        self.miniboss_stats = {
            "attempts_today": 0,
            "last_attempt_date": None
        }

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}




    @staticmethod
    def initialize_new_player():
        """Initialize data for a new player."""
        return {
            "mascota": {
                "hambre": 100,
                "energia": 100,
                "nivel": 1,
                "oro": 0,
                "oro_hora": 1,
                "fire_coral": 0,
            },
            "comida": 0,
            "ultima_alimentacion": datetime.now().timestamp(),
            "ultima_actualizacion": datetime.now().timestamp(),
            "inventario": {},
            "combat_stats": {"nivel": 0, "vida": 100, "ataque": 10},
            "daily_reward": {
                "last_claim": 0,
                "streak": 1,
                "last_weekly_tickets": 0
            },
            "premium_features": {
                "premium_status": False,
                "premium_status_expires": 0,
                "tickets": 0,
            },
            "watershard": 0,
            "miniboss_stats": {
                "attempts_today": 0,
                "last_attempt_date": None
            },
        }

    @classmethod
    def create_new_player(cls, nombre):
        """Create a new player instance."""
        new_player_data = cls.initialize_new_player()
        return cls(
            nombre=nombre,
            nivel=1,
            nivel_combate=0,
            oro_por_minuto=1,
            inventario={},
            fire_coral=new_player_data['fire_coral'],
            mascota=new_player_data['mascota'],
            comida=new_player_data['comida'],
            ultima_alimentacion=new_player_data['ultima_alimentacion'],  # Changed from 'última_alimentación'
            ultima_actualizacion=new_player_data['ultima_actualizacion'],
            combat_stats=new_player_data['combat_stats'],
            daily_reward=new_player_data['daily_reward'],
            premium_features=new_player_data['premium_features'],
            watershard=new_player_data['watershard'],
            miniboss_stats=new_player_data['miniboss_stats']
        )

    def to_dict(self):
        """Convert player object to dictionary."""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'nivel': self.nivel,
            'nivel_combate': self.nivel_combate,
            'oro_por_minuto': self.oro_por_minuto,
            'inventario': self.inventario,
            'mascota': self.mascota,
            'comida': self.comida,
            'ultima_alimentacion': self.ultima_alimentacion,
            'ultima_actualizacion': self.ultima_actualizacion,
            'combat_stats': self.combat_stats,
            'daily_reward': self.daily_reward,
            'premium_features': self.premium_features,
            'watershard': self.watershard,
            'miniboss_stats': self.miniboss_stats,
            'fire_coral': self.fire_coral  # Add this line
        }

    @classmethod
    def from_dict(cls, data):
        """Create a player object from a dictionary."""
        return cls(**data)
