
import json
import os
from pathlib import Path

# Ruta al archivo JSON de assets
ASSETS_PATH = Path(__file__).parent.parent / "assets" / "plugins.json"

_CACHED_PLUGINS = None

def _load_plugins():
    global _CACHED_PLUGINS
    if _CACHED_PLUGINS is not None:
        return _CACHED_PLUGINS
    
    if ASSETS_PATH.exists():
        try:
            with open(ASSETS_PATH, 'r', encoding='utf-8') as f:
                _CACHED_PLUGINS = json.load(f)
        except Exception:
            _CACHED_PLUGINS = {}
    else:
        _CACHED_PLUGINS = {}
    
    return _CACHED_PLUGINS

def get_description(plugin_name):
    """Obtiene la descripción amigable desde el JSON centralizado."""
    db = _load_plugins()
    return db.get(plugin_name, "Plugin de Oh My Zsh (sin descripción documentada en la base de datos).")

def get_all_documented_plugins():
    """Devuelve la lista de nombres de todos los plugins documentados."""
    return list(_load_plugins().keys())
