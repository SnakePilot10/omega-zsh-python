from unittest.mock import MagicMock, patch

from textual.widgets import TabbedContent

from omega_zsh.ui.app import OmegaApp


def test_action_switch_tab_cambia_tab_activo():
    """Verifica que action_switch_tab asigna el tab correcto en TabbedContent."""
    with patch("omega_zsh.ui.app.SystemContext"), \
         patch("omega_zsh.ui.app.StateManager"):
        app = OmegaApp()
        mock_tabs = MagicMock(spec=TabbedContent)
        app.query_one = MagicMock(return_value=mock_tabs)

        app.action_switch_tab("tab-plugins")

        app.query_one.assert_called_once_with(TabbedContent)
        assert mock_tabs.active == "tab-plugins"


def test_action_switch_tab_fallo_silencioso():
    """Verifica que si TabbedContent no existe, no lanza excepción."""
    with patch("omega_zsh.ui.app.SystemContext"), \
         patch("omega_zsh.ui.app.StateManager"):
        app = OmegaApp()
        app.query_one = MagicMock(side_effect=Exception("widget not found"))

        # No debe propagar la excepción
        try:
            app.action_switch_tab("tab-dashboard")
        except Exception:
            assert False, "action_switch_tab no debe propagar excepciones"
