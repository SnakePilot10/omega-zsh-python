import pytest
from unittest.mock import MagicMock, patch
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
        app.context.is_termux = False
        app.state_manager = MagicMock()
        app.state = MagicMock(
            selected_plugins=[],
            selected_theme="robbyrussell",
            selected_root_theme="root_p10k_red",
            selected_header="none",
            header_text="Omega",
            header_font="slant",
        )
        app.notify = MagicMock()
        app.exit = MagicMock()
        return app


def test_action_apply_changes_success(mock_app):
    with patch("omega_zsh.ui.app.ConfigGenerator") as mock_gen_class, \
         patch("omega_zsh.ui.app.FigletManager"), \
         patch("omega_zsh.ui.app.BIN_PLUGINS", []):
        mock_gen = mock_gen_class.return_value
        mock_gen.generate_zshrc.return_value = True
        mock_app.query_one = MagicMock(side_effect=Exception("no widget"))
        mock_app.action_apply_changes()
        mock_gen.generate_zshrc.assert_called_once()
        mock_app.exit.assert_called_once()


def test_action_apply_changes_failure(mock_app):
    with patch("omega_zsh.ui.app.ConfigGenerator") as mock_gen_class, \
         patch("omega_zsh.ui.app.FigletManager"), \
         patch("omega_zsh.ui.app.BIN_PLUGINS", []):
        mock_gen = mock_gen_class.return_value
        # Forzar excepción en el generador para que llegue al except
        mock_gen_class.side_effect = Exception("generator failed")
        mock_app.query_one = MagicMock(side_effect=Exception("no widget"))
        mock_app.action_apply_changes()
        assert mock_app.notify.called
