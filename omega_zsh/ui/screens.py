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
from ..core.doctor import run_doctor, run_doctor_fix
from ..core.figlet import FigletManager
from ..core.recovery import cleanup_shell_files, nuclear_fix_shell, recovery_dry_run, restore_latest_zshrc_backup
from ..core.recovery import list_zshrc_backups, restore_zshrc_backup
from ..core.system_info import get_system_stats


NAV_HINT = "[dim]Tabs: [bold]1-6[/] / [bold]D X P T H R[/] · Apply: [bold]A[/] · Exit: [bold]Q[/][/dim]"


class FirstRunScreen(Vertical):
    """Safe guided entry point for an empty Omega setup."""

    def __init__(self, omz_found: bool):
        super().__init__()
        self.omz_found = omz_found

    def compose(self) -> ComposeResult:
        omz_status = (
            "[bold green]Oh My Zsh found.[/] You can choose a theme/tools and apply safely."
            if self.omz_found
            else "[bold yellow]Oh My Zsh not found.[/] Install it first, then return to apply."
        )
        yield Label("[bold #ff006e]FIRST RUN SETUP[/]")
        yield Label(
            "[dim]Setup: [bold]S/7[/] · Problems: [bold]X/6[/] · Plugins: [bold]P[/] · "
            "Themes: [bold]T[/] · Apply: [bold]A[/] · Exit: [bold]Q[/][/dim]"
        )
        yield Static(
            "[bold #00f5ff]Recommended path:[/]\n"
            "1. Confirm Oh My Zsh is available.\n"
            "2. Pick a theme if you want one.\n"
            "3. Pick only tools/plugins you actually want.\n"
            "4. Press Apply to write a validated .zshrc with backup protection.\n\n"
            f"{omz_status}\n\n"
            "[dim]This screen does not install packages or modify shell files by itself.[/]",
            id="first-run-help",
        )
        with Horizontal(id="first-run-actions"):
            yield Button("Safe Minimal", variant="primary", id="btn-first-run-minimal")
            yield Button("Apply Minimal", variant="success", id="btn-first-run-apply-minimal")
            yield Button("Choose Tools", id="btn-first-run-plugins")
            yield Button("Choose Theme", id="btn-first-run-themes")
            yield Button("Apply", variant="success", id="btn-first-run-apply")

    @on(Button.Pressed, "#btn-first-run-minimal")
    def use_safe_minimal(self) -> None:
        if hasattr(self.app, "action_first_run_minimal"):
            self.app.action_first_run_minimal()

    @on(Button.Pressed, "#btn-first-run-plugins")
    def choose_tools(self) -> None:
        if hasattr(self.app, "action_switch_tab"):
            self.app.action_switch_tab("tab-plugins")

    @on(Button.Pressed, "#btn-first-run-apply-minimal")
    def apply_safe_minimal(self) -> None:
        if hasattr(self.app, "action_apply_safe_minimal"):
            self.app.action_apply_safe_minimal()

    @on(Button.Pressed, "#btn-first-run-themes")
    def choose_theme(self) -> None:
        if hasattr(self.app, "action_switch_tab"):
            self.app.action_switch_tab("tab-themes")

    @on(Button.Pressed, "#btn-first-run-apply")
    def apply_current(self) -> None:
        if hasattr(self.app, "action_apply_changes"):
            self.app.action_apply_changes()


class DashboardScreen(Static):
    """Pantalla principal con estética Neon Retro Informativa."""

    def compose(self) -> ComposeResult:
        self.context = SystemContext()
        stats = get_system_stats(self.context._env)

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
            "• [bold #00ff9f]D/X/P/T/H/R[/]: Dashboard, Problems, Plugins, Themes, Headers, Recovery\n"
            "• [bold #00ff9f]1-6[/]: Same tab navigation\n"
            "• [bold #00ff9f]Q[/]: Exit"
        )
        yield Static(
            f"[bold #ff006e]◄ SHORTCUTS ►[/]\n{help_text}",
            id="dashboard-shortcuts"
        )


class ProblemsScreen(Vertical):
    """Read-only doctor findings and explicit repair entry points."""

    def __init__(self):
        super().__init__()
        self.fix_armed = False

    def compose(self) -> ComposeResult:
        yield Label("[bold #ff006e]PROBLEMS / DOCTOR FINDINGS[/]")
        yield Label(NAV_HINT, id="problems-nav-hint")
        yield Static(
            "[bold #00f5ff]Doctor is read-only here.[/] Use Doctor Fix only for explicit, "
            "conservative repairs.",
            id="problems-help",
        )
        with Horizontal(id="problems-actions"):
            yield Button("Refresh", variant="primary", id="btn-problems-refresh")
            yield Button("Open Recovery", id="btn-problems-recovery")
            yield Button("Doctor Fix", variant="warning", id="btn-problems-fix")
        yield Log(id="problems-log")

    def on_mount(self) -> None:
        self.refresh_problems()

    def _write_log(self, message: str) -> None:
        def write() -> None:
            self.query_one("#problems-log", Log).write(message)

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

    def _render_report(self, report: dict) -> list[str]:
        lines = [f"overall: {report.get('overall', 'unknown')}"]
        checks = report.get("checks", [])
        problems = [check for check in checks if check.get("severity") != "ok"]
        if not problems:
            return [*lines, "ok: no doctor problems found"]
        for check in problems:
            lines.append(
                f"[{check.get('severity', 'unknown')}] {check.get('id')}: "
                f"{check.get('message')} - {check.get('detail')}"
            )
        return lines

    def _run_doctor(self) -> None:
        self.fix_armed = False
        self._write_log("$ omega doctor\n")
        try:
            report = run_doctor(SystemContext())
            for line in self._render_report(report):
                self._write_log(f"{line}\n")
            severity = "error" if report.get("overall") == "error" else None
            self._notify(f"Doctor complete: {report.get('overall', 'unknown')}", severity=severity)
        except Exception as e:
            self._write_log(f"[ERROR] {e}\n")
            self._notify(f"Doctor error: {e}", severity="error")

    def _run_doctor_fix(self) -> None:
        if not self.fix_armed:
            self.fix_armed = True
            self._write_log("[confirm] Press Doctor Fix again to run conservative repairs.\n")
            self._notify("Press Doctor Fix again to confirm.", severity="warning")
            return
        self.fix_armed = False
        self._write_log("$ omega doctor --fix\n")
        try:
            result = run_doctor_fix(SystemContext())
            for fix in result.get("fixes", []):
                self._write_log(
                    f"[{fix.get('status')}] {fix.get('id')}: "
                    f"{fix.get('message')} - {fix.get('detail')}\n"
                )
            for line in self._render_report(result.get("report", {})):
                self._write_log(f"{line}\n")
            overall = result.get("report", {}).get("overall", "unknown")
            severity = "error" if overall == "error" else None
            self._notify(f"Doctor fix complete: {overall}", severity=severity)
        except Exception as e:
            self._write_log(f"[ERROR] {e}\n")
            self._notify(f"Doctor fix error: {e}", severity="error")

    @on(Button.Pressed, "#btn-problems-refresh")
    @work(exclusive=True, thread=True)
    def refresh_problems(self) -> None:
        self._run_doctor()

    @on(Button.Pressed, "#btn-problems-recovery")
    def open_recovery(self) -> None:
        if hasattr(self.app, "action_switch_tab"):
            self.app.action_switch_tab("tab-recovery")

    @on(Button.Pressed, "#btn-problems-fix")
    @work(exclusive=True, thread=True)
    def run_fix(self) -> None:
        self._run_doctor_fix()

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
            yield Button("Refresh Backups", id="btn-recovery-refresh-backups")
        yield Label("[bold #00f5ff]VALID .zshrc BACKUPS[/]", id="recovery-backups-label")
        yield ListView(id="recovery-backups")
        yield Log(id="recovery-log")

    def on_mount(self) -> None:
        self.refresh_backup_list()

    def refresh_backup_list(self) -> None:
        try:
            context = SystemContext()
            backups = list_zshrc_backups(context)
            items = [ListItem(Label(str(path)), id=f"backup-{i}") for i, path in enumerate(backups)]
            backup_list = self.query_one("#recovery-backups", ListView)
            backup_list.clear()
            backup_list.extend(items)
            self._backup_paths = backups
        except Exception as e:
            self._backup_paths = []
            self._write_log(f"[warning] Could not list backups: {e}\n")

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
                selected_backup = self._selected_backup()
                result = (
                    restore_zshrc_backup(selected_backup, context)
                    if selected_backup
                    else restore_latest_zshrc_backup(context)
                )
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

    @on(Button.Pressed, "#btn-recovery-refresh-backups")
    def run_refresh_backups(self) -> None:
        self.refresh_backup_list()

    def _selected_backup(self) -> Path | None:
        try:
            backup_list = self.query_one("#recovery-backups", ListView)
            index = backup_list.index
            if index is None:
                return None
            paths = getattr(self, "_backup_paths", [])
            return paths[index] if index < len(paths) else None
        except Exception:
            return None


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
