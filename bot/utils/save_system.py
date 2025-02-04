#save_system.py

import psycopg2
import logging
from datetime import datetime
from typing import Dict, Optional

# Configuración de la base de datos
import os

DB_CONFIG = {
    "dbname": os.environ.get("PGDATABASE"),
    "user": os.environ.get("PGUSER"),
    "password": os.environ.get("PGPASSWORD"),
    "host": os.environ.get("PGHOST"),
    "port": os.environ.get("PGPORT")
}

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Conectar a la base de datos PostgreSQL."""
    return psycopg2.connect(**DB_CONFIG)

def create_table():
    """Crear la tabla si no existe."""
    query = """
    CREATE TABLE IF NOT EXISTS game_data (
        user_id TEXT PRIMARY KEY,
        mascota_hambre INT,
        mascota_energia INT,
        mascota_nivel INT,
        mascota_oro INT,
        mascota_oro_hora INT,
        comida INT,
        ultima_alimentacion TIMESTAMP,
        ultima_actualizacion TIMESTAMP,
        inventario TEXT,
        combat_level INT,
        combat_exp INT,
        battles_today INT,
        fire_coral INT
    );
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            conn.commit()
    logger.info("Tabla game_data verificada/existente.")

def save_game_data(user_id: str, data: Dict) -> bool:
    """Guarda los datos del usuario en la base de datos."""
    try:
        query = """
        INSERT INTO game_data (
            user_id, mascota_hambre, mascota_energia, mascota_nivel, mascota_oro, mascota_oro_hora,
            comida, ultima_alimentacion, ultima_actualizacion, inventario,
            combat_level, combat_exp, battles_today, fire_coral
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            mascota_hambre = EXCLUDED.mascota_hambre,
            mascota_energia = EXCLUDED.mascota_energia,
            mascota_nivel = EXCLUDED.mascota_nivel,
            mascota_oro = EXCLUDED.mascota_oro,
            mascota_oro_hora = EXCLUDED.mascota_oro_hora,
            comida = EXCLUDED.comida,
            ultima_alimentacion = EXCLUDED.ultima_alimentacion,
            ultima_actualizacion = EXCLUDED.ultima_actualizacion,
            inventario = EXCLUDED.inventario,
            combat_level = EXCLUDED.combat_level,
            combat_exp = EXCLUDED.combat_exp,
            battles_today = EXCLUDED.battles_today,
            fire_coral = EXCLUDED.fire_coral;
        """
        
        values = (
            user_id, data['mascota']['hambre'], data['mascota']['energia'], data['mascota']['nivel'],
            data['mascota']['oro'], data['mascota']['oro_hora'], data['comida'],
            datetime.fromtimestamp(data['última_alimentación']),
            datetime.fromtimestamp(data['última_actualización']),
            str(data['inventario']), data['combat_stats']['level'], data['combat_stats']['exp'],
            data['combat_stats']['battles_today'], data['combat_stats']['fire_coral']
        )
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()
        
        logger.info(f"Datos guardados para {user_id}.")
        return True
    except Exception as e:
        logger.error(f"Error guardando datos para {user_id}: {e}")
        return False

def load_game_data(user_id: str) -> Optional[Dict]:
    """Carga los datos del usuario desde la base de datos."""
    try:
        query = """
        SELECT * FROM game_data WHERE user_id = %s;
        """
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user_id,))
                row = cur.fetchone()
                
                if not row:
                    logger.info(f"No hay datos guardados para {user_id}.")
                    return None
                
                return {
                    "mascota": {
                        "hambre": row[1], "energia": row[2], "nivel": row[3],
                        "oro": row[4], "oro_hora": row[5]
                    },
                    "comida": row[6],
                    "última_alimentación": row[7].timestamp(),
                    "última_actualización": row[8].timestamp(),
                    "inventario": eval(row[9]),
                    "combat_stats": {
                        "level": row[10], "exp": row[11], "battles_today": row[12], "fire_coral": row[13]
                    }
                }
    except Exception as e:
        logger.error(f"Error cargando datos para {user_id}: {e}")
        return None

# Crear la tabla al iniciar
create_table()
    