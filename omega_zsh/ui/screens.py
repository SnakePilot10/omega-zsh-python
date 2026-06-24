import os
import re
import shutil
import subprocess
from pathlib import Path

from rich.text import Text
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button,
    Input,
    Label,
    ListItem,
    ListView,
    Log,
    RadioButton,
    RadioSet,
    SelectionList,
    Static,
)
from textual.widgets.selection_list import Selection

from ..core.context import SystemContext
from ..core.figlet import FigletManager
from ..core.recovery import cleanup_shell_files, nuclear_fix_shell, recovery_dry_run, restore_latest_zshrc_backup


NAV_HINT = "[dim]Tabs: [bold]1-5[/] / [bold]D P T H R[/] · Apply: [bold]A[/] · Exit: [bold]Q[/][/dim]"


class DashboardScreen(Static):
    """Pantalla principal con estética Neon Retro Informativa."""

    def compose(self) -> ComposeResult:
        self.context = SystemContext()
        stats = self._get_stats()

        header_art = Text.from_markup(
            "[bold #ff006e]OMEGA[/][bold #00f5ff] ZSH[/]\n"
            "[italic #00ff9f]Elite Terminal Experience[/]"
        )

        yield Static(header_art, id="dashboard-title")

        telemetry = (
            f"[bold #00f5ff]SISTEMA:[/] [white]{stats['os']}[/]\n"
            f"[bold #ff006e]MEMORIA:[/] [white]{stats['mem_usage']}[/]\n"
            f"[bold #00ff9f]DISCO:[/]   [white]{stats['disk_usage']}[/]\n"
            f"[bold yellow]UPTIME:[/]  [white]{stats['uptime']}[/]"
        )
        yield Static(
            f"[bold #ff006e]◄ STATUS OMEGA ►[/]\n{telemetry}",
            id="dashboard-telemetry"
        )

        help_text = (
            "• [bold #00ff9f]A[/]: Apply config only\n"
            "• [bold #00ff9f]D/P/T/H/R[/]: Dashboard, Plugins, Themes, Headers, Recovery\n"
            "• [bold #00ff9f]1-5[/]: Same tab navigation\n"
            "• [bold #00ff9f]Q[/]: Exit"
        )
        yield Static(
            f"[bold #ff006e]◄ SHORTCUTS ►[/]\n{help_text}",
            id="dashboard-shortcuts"
        )

    def _get_stats(self):
        """Obtiene estadísticas del sistema sin depender de psutil."""
        try:
            mem_p = "N/A"
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo", encoding="utf-8") as f:
                    lines = f.readlines()
                mem = {}
                for line in lines:
                    parts = line.split(":")
                    if len(parts) == 2:
                        mem[parts[0].strip()] = int(parts[1].split()[0].strip())
                total = mem.get("MemTotal", 1)
                free = mem.get("MemFree", 0)
                used = total - free
                mem_p = f"{int((used / total) * 100)}%"

            disk_p = "N/A"
            try:
                st = os.statvfs("/")
                total = st.f_blocks * st.f_frsize
                free = st.f_bavail * st.f_frsize
                used = total - free
                disk_p = f"{int((used / total) * 100)}%"
            except Exception:
                pass

            uptime_str = "N/A"
            if os.path.exists("/proc/uptime"):
                with open("/proc/uptime", "r", encoding="utf-8") as f:
                    uptime_seconds = float(f.readline().split()[0])
                    hours, remainder = divmod(int(uptime_seconds), 3600)
                    minutes, _ = divmod(remainder, 60)
                    uptime_str = f"{hours}h {minutes}m"

            return {
                "os": "Android/Termux" if os.path.exists("/data/data/com.termux") else "Linux",
                "mem_usage": mem_p,
                "disk_usage": disk_p,
                "uptime": uptime_str,
            }
        except Exception:
            return {"os": "Unknown", "mem_usage": "N/A", "disk_usage": "N/A", "uptime": "N/A"}


class RecoveryScreen(Vertical):
    """Pantalla para ejecutar recuperación shell con backups."""

    def compose(self) -> ComposeResult:
        yield Label("[bold #ff006e]RECOVERY / NUCLEAR FIX[/]")
        yield Label(NAV_HINT, id="recovery-nav-hint")
        yield Static(
            "[bold #00f5ff]Modo seguro:[/] prueba primero con Dry Run.\n"
            "[bold yellow]Nuclear Fix:[/] respalda y reconstruye .zshrc, .bashrc y .profile.\n"
            "[bold green]Restore Backup:[/] restaura el último .zshrc válido encontrado.\n"
            "[dim]Los respaldos de recovery viven en ~/.omega-zsh-recovery[/]",
            id="recovery-help",
        )
        with Horizontal(id="recovery-actions"):
            yield Button("Dry Run", variant="primary", id="btn-recovery-dry-run")
            yield Button("Cleanup", variant="warning", id="btn-recovery-uninstall")
            yield Button("Nuclear Fix", variant="error", id="btn-recovery-nuclear")
            yield Button("Restore Backup", variant="success", id="btn-recovery-restore")
        yield Log(id="recovery-log")

    def _write_log(self, message: str) -> None:
        def write() -> None:
            self.query_one("#recovery-log", Log).write(message)

        try:
            self.app.call_from_thread(write)
        except RuntimeError:
            write()

    def _notify(self, message: str, severity: str | None = None) -> None:
        def notify() -> None:
            if severity:
                self.app.notify(message, severity=severity)
            else:
                self.app.notify(message)

        try:
            self.app.call_from_thread(notify)
        except RuntimeError:
            notify()

    def _run_recovery(self, action: str) -> None:
        context = SystemContext()
        self._write_log(f"$ omega recovery {action}\n")
        try:
            if action == "dry-run":
                result = recovery_dry_run(context)
            elif action == "cleanup":
                result = cleanup_shell_files(context)
            elif action == "nuclear-fix":
                result = nuclear_fix_shell(context)
            elif action == "restore-zshrc":
                result = restore_latest_zshrc_backup(context)
            else:
                raise ValueError(f"Unknown recovery action: {action}")

            for message in result.messages:
                self._write_log(f"[i] {message}\n")
            for backup in result.backups:
                self._write_log(f"[backup] {backup}\n")
            for changed in result.changed:
                self._write_log(f"[changed] {changed}\n")
            for warning in result.warnings:
                self._write_log(f"[warning] {warning}\n")
            for error in result.errors:
                self._write_log(f"[error] {error}\n")

            if result.ok:
                self._notify(result.summary)
            else:
                self._notify(result.summary, severity="error")
        except Exception as e:
            self._write_log(f"[ERROR] {e}\n")
            self._notify(f"Recovery error: {e}", severity="error")

    @on(Button.Pressed, "#btn-recovery-dry-run")
    @work(exclusive=True, thread=True)
    def run_dry_run(self) -> None:
        self._run_recovery("dry-run")

    @on(Button.Pressed, "#btn-recovery-uninstall")
    @work(exclusive=True, thread=True)
    def run_cleanup(self) -> None:
        self._run_recovery("cleanup")

    @on(Button.Pressed, "#btn-recovery-nuclear")
    @work(exclusive=True, thread=True)
    def run_nuclear_fix(self) -> None:
        self._run_recovery("nuclear-fix")

    @on(Button.Pressed, "#btn-recovery-restore")
    @work(exclusive=True, thread=True)
    def run_restore_backup(self) -> None:
        self._run_recovery("restore-zshrc")


class PluginSelectScreen(Vertical):
    """Interfaz para activar/desactivar plugins y herramientas binarias."""

    def __init__(self, all_plugins, bin_plugins, selected_plugins):
        super().__init__()
        self.all_plugins = all_plugins
        self.bin_plugins = bin_plugins
        self.selected_plugins = selected_plugins

    def compose(self) -> ComposeResult:
        yield Label("[bold #ff006e]SELECCIÓN DE PLUGINS Y BINARIOS[/]")
        yield Label(NAV_HINT, id="plugin-nav-hint")
        yield Label("[dim]Usa [bold]Espacio[/] para marcar/desmarcar[/]", id="plugin-hint")

        options = []
        seen_ids = set()

        for p in self.all_plugins:
            if p.id not in seen_ids:
                options.append(Selection(p.id, p.id, p.id in self.selected_plugins))
                seen_ids.add(p.id)

        for p in self.bin_plugins:
            pid = p if isinstance(p, str) else p.id
            if pid not in seen_ids:
                options.append(Selection(f"📦 {pid}", pid, pid in self.selected_plugins))
                seen_ids.add(pid)

        yield SelectionList(*options, id="plugin-list")

    def get_selected(self) -> list[str]:
        return self.query_one(SelectionList).selected


class ThemeSelectScreen(Horizontal):
    """Interfaz dividida para elegir temas con previsualización en vivo."""

    def __init__(self, all_themes, selected_theme):
        super().__init__()
        self.all_themes = all_themes
        self.selected_theme = selected_theme

    def compose(self) -> ComposeResult:
        with Vertical(id="theme-list-container"):
            yield Label("[bold #ff006e]TEMAS DISPONIBLES[/]")
            yield Label(NAV_HINT, id="theme-nav-hint")
            items = []
            selected_index = 0
            for i, t in enumerate(self.all_themes):
                items.append(ListItem(Label(f"{t.id} [dim]({t.desc})[/]"), id=f"t-{i}"))
                if t.id == self.selected_theme:
                    selected_index = i

            lv = ListView(*items, id="theme-list")
            lv.index = selected_index
            yield lv

        with Vertical(id="theme-preview-container"):
            yield Label("[bold #00f5ff]PREVISUALIZACIÓN[/]")
            yield Static("Select a theme to see preview...", id="preview-area")

    def get_selected(self) -> str:
        idx = self.query_one(ListView).index
        if idx is not None and idx < len(self.all_themes):
            return self.all_themes[idx].id
        return self.selected_theme

    @on(ListView.Highlighted)
    @work(exclusive=True, thread=True)
    def update_preview(self, event: ListView.Highlighted) -> None:
        idx = self.query_one(ListView).index
        if idx is None:
            return

        theme = self.all_themes[idx]
        preview_box = self.query_one("#preview-area")

        if not theme.path or not os.path.exists(theme.path):
            preview_box.update(Text("Preview not available (No path found)", style="red"))
            return

        preview_box.update(Text("Rendering...", style="yellow"))

        zsh_bin = shutil.which("zsh")
        if not zsh_bin:
            preview_box.update(Text("Error: Zsh binary not found.", style="bold red"))
            return

        try:
            omz_dir = os.environ.get('ZSH', str(Path.home() / '.oh-my-zsh'))
            omz_lib = f'{omz_dir}/lib'
            cmd = (
                f'[[ -f ~/.cargo/env ]] && source ~/.cargo/env 2>/dev/null; export ZSH="{omz_dir}" && '
                f'fpath=("{omz_dir}/functions" "{omz_dir}/completions" $fpath) && '
                f'autoload -U colors && colors && '
                f'autoload -Uz vcs_info && '
                f'autoload -U compinit && '
                f'for _f in {omz_lib}/git.zsh {omz_lib}/theme-and-appearance.zsh'
                f' {omz_lib}/functions.zsh; do [[ -f $_f ]] && source $_f; done && '
                f'source {theme.path} && '
                f'print -P "$PROMPT" && print -P "$RPROMPT"'
            )
            result = subprocess.run([zsh_bin, "-c", cmd], capture_output=True, text=True, timeout=1.5)
            if result.stdout.strip():
                try:
                    preview_box.update(Text.from_ansi(result.stdout))
                except Exception as e:
                    preview_box.update(Text(f"Error parsing ANSI: {e}", style="red"))
            elif result.stderr:
                preview_box.update(Text(f"Preview Error:\n{result.stderr}", style="dim red"))
            else:
                preview_box.update(Text("Preview vacío (tema sin PROMPT definido)", style="dim"))
        except subprocess.TimeoutExpired:
            preview_box.update(Text("Preview timed out (Theme too slow?)", style="orange"))
        except Exception as e:
            preview_box.update(Text(f"Execution Error: {e}", style="red"))

    def _sanitize_id(self, text: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_-]", "_", text)


class HeaderSelectScreen(Vertical):
    """Configuración estética del Banner de bienvenida."""

    def __init__(self, selected_header, header_text, selected_font):
        super().__init__()
        self.selected_header = selected_header
        self.header_text = header_text
        self.selected_font = selected_font
        self.figlet = FigletManager()

    def compose(self) -> ComposeResult:
        yield Label("[bold #ff006e]CONFIGURACIÓN DE HEADER[/]")
        yield Label(NAV_HINT, id="header-nav-hint")

        with Horizontal(id="header-config-row"):
            with Vertical(id="header-type-col"):
                yield Label("Tipo:")
                yield RadioSet(
                    RadioButton("None", id="h-none", value=(self.selected_header == "none")),
                    RadioButton("Fastfetch", id="h-ff", value=(self.selected_header == "fastfetch")),
                    RadioButton("Figlet", id="h-fig", value=(self.selected_header == "figlet")),
                    RadioButton("Cowsay", id="h-cow", value=(self.selected_header == "cowsay")),
                    id="header-type-set",
                )

            with Vertical(id="header-text-col"):
                yield Label("Texto / Fuentes (solo Figlet):")
                yield Input(value=self.header_text, placeholder="Banner Text", id="header-input")
                fonts = self.figlet.get_fonts()
                selected_idx = 0
                items = []
                for i, f in enumerate(fonts):
                    items.append(ListItem(Label(f), id=f"font-{i}"))
                    if f == self.selected_font:
                        selected_idx = i

                lv = ListView(*items, id="font-list")
                lv.index = selected_idx
                yield lv

        yield Label("[bold #00f5ff]PREVIEW:[/]")
        yield Static("", id="preview-area")

    def get_selected(self) -> tuple[str, str, str]:
        h_set = self.query_one("#header-type-set")
        btn = h_set.pressed_button
        if btn is None:
            h_type = self.selected_header
        elif btn.id == "h-ff":
            h_type = "fastfetch"
        elif btn.id == "h-fig":
            h_type = "figlet"
        elif btn.id == "h-cow":
            h_type = "cowsay"
        else:
            h_type = "none"

        text = self.query_one("#header-input").value
        idx = self.query_one("#font-list").index
        fonts = self.figlet.get_fonts()
        font = fonts[idx] if idx is not None else self.selected_font

        return h_type, text, font

    @on(RadioSet.Changed)
    @on(Input.Changed)
    @on(ListView.Highlighted)
    @work(exclusive=True, thread=True)
    def update_header_preview(self) -> None:
        h_type, text, font = self.get_selected()
        preview_area = self.query_one("#preview-area")

        if h_type == "none":
            preview_area.update(Text("No header selected", style="dim"))
            return

        if h_type == "figlet":
            preview_area.update(Text(self.figlet.render(text, font)))
            return

        if h_type == "cowsay":
            import shutil as _shutil
            cow_bin = _shutil.which("cowsay")
            if not cow_bin:
                preview_area.update(Text("cowsay no encontrado. Instala con: pkg install cowsay", style="red"))
                return
            try:
                import subprocess as _sp
                result = _sp.run([cow_bin, text or "Omega ZSH"], capture_output=True, text=True, timeout=2.0)
                if result.returncode == 0:
                    preview_area.update(Text(result.stdout))
                else:
                    preview_area.update(Text(f"Error: {result.stderr}", style="red"))
            except Exception as e:
                preview_area.update(Text(f"Error: {e}", style="red"))
            return

        if h_type == "fastfetch":
            preview_area.update(Text("Rendering live preview...", style="yellow"))
            ff_bin = shutil.which("fastfetch")
            if not ff_bin:
                preview_area.update(Text("Fastfetch not found. Please install it first.", style="red"))
                return

            try:
                result = subprocess.run([ff_bin, "--pipe"], capture_output=True, text=True, timeout=2.0)
                if result.returncode == 0:
                    try:
                        preview_area.update(Text.from_ansi(result.stdout))
                    except Exception as e:
                        preview_area.update(Text(f"ANSI Parse Error: {e}", style="red"))
                else:
                    err = result.stderr or "Check if fastfetch is working."
                    preview_area.update(Text(f"Command execution failed:\n{err}", style="dim red"))
            except subprocess.TimeoutExpired:
                preview_area.update(Text("Preview timed out (Command took too long)", style="orange"))
            except Exception as e:
                preview_area.update(Text(f"Preview Error: {e}", style="red"))
