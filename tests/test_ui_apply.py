from unittest.mock import MagicMock, patch

import pytest

from omega_zsh.core.state import AppState
from omega_zsh.ui.app import OmegaApp


@pytest.fixture
def mock_app():
    with patch("omega_zsh.ui.app.SystemContext"), \
         patch("omega_zsh.ui.app.StateManager"):
        app = OmegaApp()
        app.context = MagicMock()
        app.context.omz_dir = MagicMock()
        app.context.project_root = MagicMock()
        app.context.omega_dir = MagicMock()
        app.context.zshrc_path = MagicMock()
        app.context.home = MagicMock()
        app.context.home.__truediv__ = lambda s, x: MagicMock()
        app.context.is_termux = False
        app.state_manager = MagicMock()
        app.state = AppState(
            selected_plugins=["zsh-autosuggestions", "zoxide", "eza", "EZA"],
            selected_theme="bira_elegante",
            selected_root_theme="root_p10k_red",
            selected_header="none",
            header_text="Omega",
            header_font="slant",
        )
        app.notify = MagicMock()
        app.exit = MagicMock()
        # query_one siempre falla → usa estado guardado (caso más común)
        app.query_one = MagicMock(side_effect=Exception("no widget"))
        return app


def test_apply_action_delegates_to_core_orchestrator(mock_app):
    with patch("omega_zsh.ui.app.apply_config") as mock_apply:
        mock_apply.return_value.ok = True
        mock_apply.return_value.message = "Configuración actualizada con éxito."

        mock_app.action_apply_changes()

        mock_apply.assert_called_once_with(mock_app.context, mock_app.state)
        mock_app.notify.assert_called_with("Configuración actualizada con éxito.")


def test_header_cmd_figlet(mock_app):
    """Verifica que selected_header=figlet genera el comando correcto."""
    from omega_zsh.core.apply import build_config_context

    mock_app.state.selected_header = "figlet"
    mock_app.state.header_text = "S23"
    mock_app.state.header_font = "ANSI Shadow"

    with patch("omega_zsh.core.apply.FigletManager") as mock_figlet:
        mock_figlet.return_value.generate_safe_command.return_value = "figlet -f 'ANSI Shadow' S23"
        context_data = build_config_context(mock_app.context, mock_app.state)
        assert context_data["header_cmd"] == "figlet -f 'ANSI Shadow' S23"
        mock_figlet.return_value.generate_safe_command.assert_called_with("S23", "ANSI Shadow")


def test_header_cmd_fastfetch(mock_app):
    """Verifica que selected_header=fastfetch genera el comando correcto."""
    from omega_zsh.core.apply import build_config_context

    mock_app.state.selected_header = "fastfetch"
    context_data = build_config_context(mock_app.context, mock_app.state)
    assert context_data["header_cmd"] == "(( $+commands[fastfetch] )) && fastfetch"


def test_header_cmd_none(mock_app):
    """Verifica que selected_header=none no genera comando."""
    from omega_zsh.core.apply import build_config_context

    mock_app.state.selected_header = "none"
    context_data = build_config_context(mock_app.context, mock_app.state)
    assert context_data["header_cmd"] == ""


def test_apply_success_no_cierra_app(mock_app):
    """Verifica que tras generar .zshrc exitosamente la app NO se cierra (Mejora UX)."""
    with patch("omega_zsh.ui.app.apply_config") as mock_apply:
        mock_apply.return_value.ok = True
        mock_apply.return_value.message = "Configuración actualizada con éxito."
        mock_app.action_apply_changes()
        mock_app.exit.assert_not_called()
        mock_app.notify.assert_called_with("Configuración actualizada con éxito.")


def test_apply_failure_notifica_error(mock_app):
    """Verifica que si apply_config falla, se notifica con severity=error."""
    with patch("omega_zsh.ui.app.apply_config") as mock_apply:
        mock_apply.return_value.ok = False
        mock_apply.return_value.message = "Error al aplicar: disk full"
        mock_app.action_apply_changes()

        mock_app.notify.assert_called_once()
        call_kwargs = mock_app.notify.call_args[1]
        assert call_kwargs.get("severity") == "error"
        mock_app.exit.assert_not_called()
