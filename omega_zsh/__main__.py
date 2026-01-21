#!/usr/bin/env python3
import sys
import logging
import traceback
from pathlib import Path

# --- CONFIGURACIÓN DE LOGGING ---
# Requisito: Enviar errores a archivo, Nivel INFO, Formato con Timestamp
LOG_FILE = Path(__file__).parent / "omega_crash.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w' # 'w' para reiniciar el log en cada ejecución y no llenarlo de basura antigua
)

def handle_exception(exc_type, exc_value, exc_traceback):
    """Captura global de excepciones no manejadas."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # Registrar el error completo en el archivo
    logging.critical("Excepción No Controlada (Crash):", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Mostrar también en stderr para feedback visual inmediato
    sys.__stderr__.write("\n[FATAL ERROR] Se ha generado un reporte en omega_crash.log\n")
    sys.__stderr__.write("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))

# Enganchar el manejador global
sys.excepthook = handle_exception

def main():
    logging.info("=== Iniciando Sesión de Omega-ZSH ===")
    
    try:
        # Importación diferida dentro del try/except para capturar errores de dependencia
        logging.info("Cargando módulos de UI...")
        from omega_zsh.ui.app import OmegaApp
        
        logging.info("Inicializando aplicación...")
        app = OmegaApp()
        
        logging.info("Lanzando Loop Principal (TUI)...")
        app.run()
        
        logging.info("Aplicación cerrada correctamente.")
        
    except ImportError as e:
        logging.critical(f"Error de Dependencia: {e}", exc_info=True)
        print(f"Error crítico: Faltan dependencias. Revisa omega_crash.log. ({e})")
        sys.exit(1)
    except Exception as e:
        logging.critical(f"Error en Runtime: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
