import getpass
import logging
import os
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader

from .backup import create_backup, prune_backups, restore_backup
from .manifest import default_manifest_path, record_managed_file
from .shell import validate_zsh_syntax


class ConfigGenerator:
    def __init__(self, templates_dir: Path):
        # Usamos FileSystemLoader con una ruta física real
        self.env = Environment(loader=FileSystemLoader(str(templates_dir)))

    def generate_zshrc(self, output_path: Path, context: Dict[str, Any]) -> bool:
        """Genera el archivo .zshrc a partir de la plantilla."""
        try:
            # 2. Renderizar plantilla
            template = self.env.get_template(".zshrc.j2")
            content = template.render(context)

            # 3. Escritura atómica
            temp_path = output_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)

            valid, message = validate_zsh_syntax(temp_path)
            if not valid:
                temp_path.unlink(missing_ok=True)
                logging.error("Generated .zshrc failed validation: %s", message)
                return False

            backup_dir = output_path.parent / ".omega-backups"
            backup_path = create_backup(output_path, backup_dir)
            try:
                os.replace(temp_path, output_path)
            except Exception:
                temp_path.unlink(missing_ok=True)
                restore_backup(backup_path, output_path)
                raise
            prune_backups(backup_dir, output_path.name)
            manifest_path = default_manifest_path(output_path.parent)
            record_managed_file(manifest_path, output_path, "config", "generated")
            if backup_path:
                record_managed_file(
                    manifest_path,
                    backup_path,
                    "backup",
                    "created",
                    {"source": str(output_path)},
                )
            return True
        except Exception as e:
            logging.error(f"Error generando .zshrc: {e}", exc_info=True)
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
                "user": getpass.getuser(),
            }
            default_ctx.update(context)
            content = template.render(default_ctx)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            logging.error(f"Error generando personal.zsh: {e}", exc_info=True)
            return False

    def create_default_custom_zsh(self, path: Path):
        """Crea un archivo custom.zsh inicial si no existe."""
        if path.exists():
            return

        path.parent.mkdir(parents=True, exist_ok=True)
        content = """# --- OMEGA-ZSH USER CUSTOMIZATIONS ---
# Agrega aquí tus alias, funciones y variables personales.
alias zr='source ~/.zshrc'
alias zc='nano ~/.zshrc'

# Ejemplo de función auto-venv
function auto_venv() {
    if [[ -d ".venv" ]]; then
        source .venv/bin/activate
    fi
}
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        path.chmod(0o644)
