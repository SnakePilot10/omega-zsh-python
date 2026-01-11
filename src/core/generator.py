import os
import shutil
import time
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from typing import List, Dict, Any

class ConfigGenerator:
    def __init__(self, templates_dir: Path):
        self.env = Environment(loader=FileSystemLoader(str(templates_dir)))

    def generate_zshrc(self, output_path: Path, context: Dict[str, Any]) -> bool:
        """Genera el archivo .zshrc a partir de la plantilla."""
        try:
            # 1. Crear backup si existe
            if output_path.exists():
                backup_path = output_path.with_suffix(f".bak.{int(time.time())}")
                shutil.copy2(output_path, backup_path)

            # 2. Renderizar plantilla
            template = self.env.get_template(".zshrc.j2")
            content = template.render(context)

            # 3. Escritura atómica
            temp_path = output_path.with_suffix(".tmp")
            with open(temp_path, "w") as f:
                f.write(content)
            
            os.replace(temp_path, output_path)
            return True
        except Exception as e:
            print(f"Error generando .zshrc: {e}")
            return False

    def generate_personal_config(self, output_path: Path, context: Dict[str, Any]) -> bool:
        """Genera el archivo personal.zsh de forma segura."""
        try:
            # Si el archivo ya existe, no lo sobreescribimos por defecto 
            # para proteger los cambios manuales del usuario fuera de la app.
            if output_path.exists():
                return True

            template = self.env.get_template("personal.zsh.j2")
            # Valores por defecto si no vienen en el contexto
            default_ctx = {
                "extra_paths": [],
                "env_vars": {},
                "aliases": {},
                "user": os.getlogin() if hasattr(os, "getlogin") else "user"
            }
            default_ctx.update(context)
            content = template.render(default_ctx)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error generando personal.zsh: {e}")
            return False

    def create_default_custom_zsh(self, path: Path):
        """Crea un archivo custom.zsh inicial si no existe."""
        if path.exists():
            return

        path.parent.mkdir(parents=True, exist_ok=True)
        content = """# --- OMEGA-ZSH USER CUSTOMIZATIONS ---
# Agrega aquí tus alias, funciones y variables personales.
alias zr='source ~/.zshrc'
alias zc='micro ~/.zshrc'

# Ejemplo de función auto-venv
function auto_venv() {
    if [[ -d ".venv" ]]; then
        source .venv/bin/activate
    fi
}
"""
        with open(path, "w") as f:
            f.write(content)
        path.chmod(0o644)
