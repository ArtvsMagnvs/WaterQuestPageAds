import os

# Configuración de los anuncios
AD_CONFIG = {
    # No necesitamos una API key específica para Monetag, ya que solo usamos el data-zone
    'cooldown': 5,  # 5 segundos entre clics (ajustable)
    
    # No hay límites en los anuncios diarios
    'daily_limit': None,  # Sin límite de anuncios diarios
    
    # ID de la unidad de anuncios (Monetag usa solo el 'data-zone' como identificador)
    'ad_unit_id': os.getenv('MONETAG_ZONE_ID', 'YOUR_DEFAULT_MONETAG_ZONE_ID'),  # Usamos MONETAG_ZONE_ID desde el env
    
    # Límite de intentos para cargar anuncios si falla
    'retry_limit': 5,  # Intentos para recargar si el anuncio falla
    
    # Recompensas basadas en el número de anuncios visualizados
    'ad_rewards': {
        'watch': {
            'energy': 25,  # Recompensa de energía por ver un anuncio
            'quick_combat': 1  # Recompensa de combate rápido
        },
        'milestones': {
            # Recompensas por hitos alcanzados al ver anuncios
            3: {
                'miniboss_attempts': 1  # +1 intento de MiniBoss por 3 anuncios
            },
            5: {
                'miniboss_attempts': 2,  # +2 intentos de MiniBoss por 5 anuncios
                'gold_gen': 1.01  # Aumento del 1% en la generación de oro por 5 anuncios
            },
            10: {
                'miniboss_attempts': 3,  # +3 intentos de MiniBoss por 10 anuncios
                'destiny_fragment': 1  # +1 Fragmento del Destino por 10 anuncios
            }
        }
    }
}

