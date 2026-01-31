import shutil
import subprocess
import os
import glob
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Input, ListView, ListItem, Label, Static
from textual import on

# --- CAPA DE LÓGICA (BACKEND) ---


class FigletManager:
    """Encargada de la lógica de negocio: gestión de fuentes y renderizado."""

    def __init__(self):
        self.figlet_path = shutil.which("figlet")
        if not self.figlet_path:
            raise FileNotFoundError(
                "No se encontró el ejecutable 'figlet'. Instálalo con 'pkg install figlet'"
            )

        # Detectar directorio de fuentes
        prefix = os.environ.get("PREFIX", "/usr")
        self.fonts_dir = os.path.join(prefix, "share", "figlet")

    def get_fonts(self) -> list[str]:
        """Devuelve una lista ordenada de nombres de fuentes disponibles."""
        if not os.path.exists(self.fonts_dir):
            return []

        patron = os.path.join(self.fonts_dir, "*.flf")
        archivos = glob.glob(patron)
        nombres = [os.path.splitext(os.path.basename(f))[0] for f in archivos]
        return sorted(nombres, key=str.lower)

    def render(self, text: str, font: str, width: int = 80) -> str:
        """
        Renderiza el texto usando figlet.
        Args:
            width: Ancho máximo disponible en caracteres para forzar el salto de línea.
        """
        if not text:
            return ""
        try:
            # -w: Ancho máximo (width)
            # -c: Centrar el texto (center)
            result = subprocess.run(
                [self.figlet_path, "-f", font, "-w", str(width), "-c", text],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return "Error al renderizar."
        except Exception as e:
            return f"Error inesperado: {e}"


# --- CAPA DE INTERFAZ (FRONTEND) ---


class FigletApp(App):
    """Aplicación TUI para visualizar fuentes Figlet."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #input-container {
        height: 3;
        dock: top;
        margin: 1;
    }

    #main-container {
        layout: horizontal;
        height: 1fr;
    }

    #sidebar {
        width: 30%;
        height: 100%;
        border: solid green;
        background: $surface;
    }

    ListView {
        height: 100%;
    }

    #preview-area {
        width: 70%;
        height: 100%;
        border: solid $accent;
        padding: 1;
        overflow: auto; /* Scroll si aún así es muy grande */
    }

    #art-output {
        color: $text;
        width: 100%;
    }
    """

    TITLE = "Termux Figlet Viewer"
    SUB_TITLE = "Snake's Studio"

    def __init__(self):
        super().__init__()
        self.manager = FigletManager()
        self.fuentes_reales = self.manager.get_fonts()

        # Mapeado seguro para evitar errores con nombres de fuentes raros
        self.mapa_fuentes = {}
        self.items_lista = []

        for idx, nombre_real in enumerate(self.fuentes_reales):
            id_seguro = f"font_id_{idx}"
            self.mapa_fuentes[id_seguro] = nombre_real
            self.items_lista.append(ListItem(Label(nombre_real), id=id_seguro))

        self.current_font = "standard"
        if self.fuentes_reales:
            self.current_font = self.fuentes_reales[0]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Input(placeholder="Escribe aquí...", id="text-input", value="Termux Ninja"),
            id="input-container",
        )
        yield Container(
            Container(ListView(*self.items_lista, id="font-list"), id="sidebar"),
            Container(Static("", id="art-output"), id="preview-area"),
            id="main-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        if self.items_lista:
            self.query_one("#font-list").index = 0
        # Forzamos una actualización inicial tras un breve delay para que Textual calcule tamaños
        self.call_after_refresh(self.update_preview)

    @on(Input.Changed)
    def on_input_changed(self, event: Input.Changed) -> None:
        self.update_preview()

    @on(ListView.Selected)
    def on_font_selected(self, event: ListView.Selected) -> None:
        id_seleccionado = event.item.id
        nombre_real = self.mapa_fuentes.get(id_seleccionado)
        if nombre_real:
            self.current_font = nombre_real
            self.update_preview()

    def on_resize(self, event) -> None:
        """Si giras la pantalla o cambias el tamaño, se recalcula."""
        self.update_preview()

    def update_preview(self) -> None:
        contenedor = self.query_one("#preview-area")

        # Obtenemos el ancho real del contenedor en la pantalla
        # Si es 0 (aún no cargó), usamos 40 como fallback seguro para móvil
        ancho_disponible = contenedor.size.width if contenedor.size.width > 0 else 40

        # Restamos un pequeño margen para bordes (padding)
        ancho_seguro = max(10, ancho_disponible - 4)

        texto = self.query_one("#text-input").value

        # Renderizamos pasando el ancho detectado
        arte = self.manager.render(texto, self.current_font, width=ancho_seguro)

        self.query_one("#art-output").update(arte)


if __name__ == "__main__":
    app = FigletApp()
    app.run()
