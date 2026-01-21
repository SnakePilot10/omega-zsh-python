import shutil
import subprocess
import os
import glob
import logging
import shlex
from pathlib import Path
from typing import Dict, List

class FigletManager:
    """Gestor de fuentes Figlet con soporte para fuentes del sistema y locales."""
    
    def __init__(self):
        self.figlet_path = shutil.which("figlet")
        
        # 1. Fuentes del Sistema
        prefix = os.environ.get("PREFIX", "/usr")
        self.system_fonts_dir = Path(prefix) / "share" / "figlet"
        
        # 2. Fuentes Locales (Project Root / assets / fonts)
        # src/core/figlet.py -> src/core -> src -> root
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.local_fonts_dir = self.project_root / "assets" / "fonts"
        
        # Cache de fuentes: { "nombre_fuente": "ruta_absoluta" }
        self._font_cache: Dict[str, str] = {}
        self._refresh_cache()
    
    def is_available(self) -> bool:
        return self.figlet_path is not None

    def _refresh_cache(self):
        """Escanea directorios y reconstruye el cache de fuentes."""
        self._font_cache.clear()
        
        # Helper para escanear directorios
        def scan_dir(directory: Path):
            if not directory.exists():
                return
            for font_file in directory.glob("*.flf"):
                font_name = font_file.stem
                # Las fuentes locales tienen prioridad (sobreescriben) si hay colisión
                # o viceversa dependiendo del orden. Aquí: Local > Sistema
                self._font_cache[font_name] = str(font_file.absolute())

        # Escanear sistema primero
        scan_dir(self.system_fonts_dir)
        # Escanear locales después (sobrescriben)
        scan_dir(self.local_fonts_dir)

    def get_fonts(self) -> List[str]:
        """Devuelve una lista ordenada de nombres de fuentes disponibles."""
        if not self._font_cache:
            self._refresh_cache()
        
        fonts = list(self._font_cache.keys())
        return sorted(fonts, key=str.lower) if fonts else ["standard"]

    def _resolve_font_path(self, font_name: str) -> str:
        """Devuelve la ruta completa si es local/sistema, o el nombre si es fallback."""
        return self._font_cache.get(font_name, "standard")

    def render(self, text: str, font: str, width: int = 80, center: bool = True) -> str:
        """Renderiza el texto usando figlet."""
        if not text or not self.is_available():
            return text
        
        # Obtener ruta segura
        font_path = self._resolve_font_path(font)
        
        try:
            cmd = [self.figlet_path, "-f", font_path, "-w", str(width)]
            if center:
                cmd.append("-c")
            cmd.append(text)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except Exception as e:
            logging.error(f"Error renderizando figlet con fuente '{font}': {e}")
            return f"Error renderizando: {text}"

    def generate_safe_command(self, text: str, font: str) -> str:
        """Genera un comando de shell seguro para .zshrc."""
        
        # 1. Resolver ruta absoluta de la fuente
        # Esto es crítico para que funcione desde cualquier directorio en zsh
        font_path = self._resolve_font_path(font)
        
        # 2. Sanitizar texto
        safe_text = shlex.quote(text)
        safe_font = shlex.quote(font_path)
        
        return f'figlet -f {safe_font} -c {safe_text} | lolcat'