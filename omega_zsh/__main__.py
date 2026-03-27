#!/usr/bin/env python3
import logging
import sys
import traceback
from pathlib import Path

# --- CONFIGURACIÓN DE LOGGING ---
# Ubicación del log en el home del usuario para asegurar permisos de escritura
LOG_FILE = Path.home() / ".omega-zsh" / "omega_crash.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)



def handle_exception(exc_type, exc_value, exc_traceback):
    """Captura global de excepciones no manejadas."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.critical("Excepción No Controlada:", exc_info=(exc_type, exc_value, exc_traceback))
    sys.__stderr__.write(f"\n[FATAL ERROR] Revisa {LOG_FILE} para detalles.\n")
    sys.__stderr__.write("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))


sys.excepthook = handle_exception



def main():
    # Si hay argumentos (ej: oz stats), delegar a la herramienta CLI oz_tool.py
    if len(sys.argv) > 1:
        logging.info(f"Delegando comando CLI: {sys.argv[1:]}")
        try:
            from omega_zsh.cli.oz_tool import main as cli_main

            cli_main()
            return
        except Exception as e:
            logging.error(f"Error en delegación CLI: {e}", exc_info=True)
            print(f"Error ejecutando comando CLI: {e}")
            sys.exit(1)

    # Si no hay argumentos, lanzar la interfaz visual (TUI)
    logging.info("Iniciando Interfaz Visual (TUI)...")
    try:
        from omega_zsh.ui.app import OmegaApp

        app = OmegaApp()
        app.run()
    except ImportError as e:
        logging.critical(f"Error de Dependencia: {e}", exc_info=True)
        print(f"Error: Faltan dependencias para la UI. ({e})")
        sys.exit(1)
    except Exception as e:
        logging.critical(f"Error en TUI: {e}", exc_info=True)
        print(f"Error al iniciar la interfaz visual. Revisa {LOG_FILE}")
        sys.exit(1)


if __name__ == "__main__":
    main()
