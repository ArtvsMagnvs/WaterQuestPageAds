# Handlers/register_ads.py
from .ads import register_handlers  # Importa la función que ya has definido en ads.py

def register_ads_handlers(application):
    """Registrar los controladores para anuncios usando la función ya definida en ads.py."""
    
    # Llama a la función que registra los handlers desde ads.py
    register_handlers(application)
