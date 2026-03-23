import pytest
from unittest.mock import MagicMock, patch, call, ANY
from omega_zsh.ui.app import OmegaApp
from omega_zsh.core.state import AppState


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
            selected_plugins=["zsh-autosuggestions", "zoxide", "eza"],
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


def test_context_data_claves_correctas(mock_app):
    """Verifica que context_data tiene las claves exactas que el template Jinja2 espera.
    Este test habría detectado el bug donde se pasaba 'theme' en vez de 'user_theme'."""
    with patch("omega_zsh.ui.app.ConfigGenerator") as mock_gen_class, \
         patch("omega_zsh.ui.app.FigletManager"), \
         patch("omega_zsh.ui.app.BIN_PLUGINS", ["zoxide", "eza"]):
        mock_gen = mock_gen_class.return_value
        mock_gen.generate_zshrc.return_value = True
        mock_app.action_apply_changes()

        _, call_kwargs = mock_gen.generate_zshrc.call_args
        context_data = mock_gen.generate_zshrc.call_args[0][1]

        # Claves que el template .zshrc.j2 requiere
        assert "omz_dir" in context_data,      "Falta omz_dir — ZSH no puede sourcer oh-my-zsh.sh"
        assert "user_theme" in context_data,   "Falta user_theme — bug histórico: se usaba 'theme'"
        assert "root_theme" in context_data,   "Falta root_theme"
        assert "plugins" in context_data,      "Falta plugins"
        assert "header_cmd" in context_data,   "Falta header_cmd"
        assert "is_termux" in context_data,    "Falta is_termux"
        assert "active_tools" in context_data, "Falta active_tools"
        assert "personal_zsh" in context_data, "Falta personal_zsh"
        assert "custom_zsh" in context_data,   "Falta custom_zsh"

        # Clave que NO debe existir (bug anterior)
        assert "theme" not in context_data, "Bug: se usa 'theme' en vez de 'user_theme'"
        assert "omega_dir" not in context_data, "omega_dir no es una clave del template"


def test_plugins_separados_omz_vs_binarios(mock_app):
    """Verifica que los binarios NO van en plugins=() del .zshrc.
    Este test habría detectado el bug donde yazi, fd, etc. aparecían como plugins OMZ."""
    with patch("omega_zsh.ui.app.ConfigGenerator") as mock_gen_class, \
         patch("omega_zsh.ui.app.FigletManager"), \
         patch("omega_zsh.ui.app.BIN_PLUGINS", ["zoxide", "eza"]):
        mock_gen = mock_gen_class.return_value
        mock_gen.generate_zshrc.return_value = True
        mock_app.action_apply_changes()

        context_data = mock_gen.generate_zshrc.call_args[0][1]
        omz_plugins = context_data["plugins"]
        active_tools = context_data["active_tools"]

        # zsh-autosuggestions es plugin OMZ → debe ir en plugins
        assert "zsh-autosuggestions" in omz_plugins

        # zoxide y eza son binarios → NO deben ir en plugins
        assert "zoxide" not in omz_plugins, "Bug: binario zoxide en plugins OMZ"
        assert "eza" not in omz_plugins,    "Bug: binario eza en plugins OMZ"

        # Los binarios deben ir en active_tools
        assert "zoxide" in active_tools
        assert "eza" in active_tools


def test_header_cmd_figlet(mock_app):
    """Verifica que selected_header=figlet genera el comando correcto."""
    mock_app.state.selected_header = "figlet"
    mock_app.state.header_text = "S23"
    mock_app.state.header_font = "ANSI Shadow"

    with patch("omega_zsh.ui.app.ConfigGenerator") as mock_gen_class, \
         patch("omega_zsh.ui.app.FigletManager") as mock_figlet, \
         patch("omega_zsh.ui.app.BIN_PLUGINS", []):
        mock_figlet.return_value.generate_safe_command.return_value = "figlet -f 'ANSI Shadow' S23"
        mock_gen = mock_gen_class.return_value
        mock_gen.generate_zshrc.return_value = True
        mock_app.action_apply_changes()

        context_data = mock_gen.generate_zshrc.call_args[0][1]
        assert context_data["header_cmd"] == "figlet -f 'ANSI Shadow' S23"
        mock_figlet.return_value.generate_safe_command.assert_called_with("S23", "ANSI Shadow")


def test_header_cmd_fastfetch(mock_app):
    """Verifica que selected_header=fastfetch genera el comando correcto."""
    mock_app.state.selected_header = "fastfetch"

    with patch("omega_zsh.ui.app.ConfigGenerator") as mock_gen_class, \
         patch("omega_zsh.ui.app.FigletManager"), \
         patch("omega_zsh.ui.app.BIN_PLUGINS", []):
        mock_gen = mock_gen_class.return_value
        mock_gen.generate_zshrc.return_value = True
        mock_app.action_apply_changes()

        context_data = mock_gen.generate_zshrc.call_args[0][1]
        assert context_data["header_cmd"] == "fastfetch"


def test_header_cmd_none(mock_app):
    """Verifica que selected_header=none no genera comando."""
    mock_app.state.selected_header = "none"

    with patch("omega_zsh.ui.app.ConfigGenerator") as mock_gen_class, \
         patch("omega_zsh.ui.app.FigletManager"), \
         patch("omega_zsh.ui.app.BIN_PLUGINS", []):
        mock_gen = mock_gen_class.return_value
        mock_gen.generate_zshrc.return_value = True
        mock_app.action_apply_changes()

        context_data = mock_gen.generate_zshrc.call_args[0][1]
        assert context_data["header_cmd"] == ""


def test_apply_success_cierra_app(mock_app):
    """Verifica que tras generar .zshrc exitosamente la app se cierra."""
    with patch("omega_zsh.ui.app.ConfigGenerator") as mock_gen_class, \
         patch("omega_zsh.ui.app.FigletManager"), \
         patch("omega_zsh.ui.app.BIN_PLUGINS", []):
        mock_gen = mock_gen_class.return_value
        mock_gen.generate_zshrc.return_value = True
        mock_app.action_apply_changes()
        mock_app.exit.assert_called_once()


def test_apply_failure_notifica_error(mock_app):
    """Verifica que si generate_zshrc falla, se notifica con severity=error."""
    with patch("omega_zsh.ui.app.ConfigGenerator") as mock_gen_class, \
         patch("omega_zsh.ui.app.FigletManager"), \
         patch("omega_zsh.ui.app.BIN_PLUGINS", []):
        mock_gen = mock_gen_class.return_value
        mock_gen.generate_zshrc.side_effect = Exception("disk full")
        mock_app.action_apply_changes()

        mock_app.notify.assert_called_once()
        call_kwargs = mock_app.notify.call_args[1]
        assert call_kwargs.get("severity") == "error"
        mock_app.exit.assert_not_called()
