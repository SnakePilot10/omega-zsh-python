from unittest.mock import MagicMock, patch
from omega_zsh.ui.app import OmegaApp


def test_action_switch_tab_navigation():
    with patch("omega_zsh.ui.app.SystemContext"), \
         patch("omega_zsh.ui.app.StateManager"):
        app = OmegaApp()
        mock_tabs = MagicMock()
        app.query_one = MagicMock(return_value=mock_tabs)
        app.action_switch_tab("tab-dashboard")
        app.query_one.assert_called_once()
