import shutil
import subprocess
import os
import glob
import logging

class FigletManager:
    """Gestor de fuentes Figlet adaptado de Figlet_Fonts/figlet_tui.py"""
    
    def __init__(self):
        self.figlet_path = shutil.which("figlet")
        
        # Detectar directorio de fuentes
        prefix = os.environ.get("PREFIX", "/usr")
        self.fonts_dir = os.path.join(prefix, "share", "figlet")
    
    def is_available(self) -> bool:
        return self.figlet_path is not None

    def get_fonts(self) -> list[str]:
        """Devuelve una lista ordenada de nombres de fuentes disponibles."""
        if not os.path.exists(self.fonts_dir):
            logging.warning(f"Directorio de fuentes figlet no encontrado: {self.fonts_dir}")
            return ["standard"]
        
        patron = os.path.join(self.fonts_dir, "*.flf")
        archivos = glob.glob(patron)
        nombres = [os.path.splitext(os.path.basename(f))[0] for f in archivos]
        return sorted(nombres, key=str.lower) if nombres else ["standard"]

    def render(self, text: str, font: str, width: int = 80, center: bool = True) -> str:
        """Renderiza el texto usando figlet."""
        if not text or not self.is_available():
            return text
        
        # Validar fuente
        safe_font = font if font in self.get_fonts() else "standard"
        
        try:
            cmd = [self.figlet_path, "-f", safe_font, "-w", str(width)]
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
            logging.error(f"Error renderizando figlet: {e}")
            return f"Error renderizando: {text}"

    def generate_safe_command(self, text: str, font: str) -> str:
        """Genera un comando de shell seguro para .zshrc."""
        import shlex
        
        # 1. Validar fuente (Allowlist)
        available_fonts = self.get_fonts()
        safe_font = font if font in available_fonts else "standard"
        
        # 2. Sanitizar texto usando shlex.quote para escapar caracteres peligrosos
        safe_text = shlex.quote(text)
        
        return f'figlet -f "{safe_font}" -c {safe_text} | lolcat'
