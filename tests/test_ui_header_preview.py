import unittest
from unittest.mock import MagicMock, patch
from omega_zsh.ui.screens import HeaderSelectScreen


def make_screen_with_mocks(h_type, text, font, btn_id):
    """Crea HeaderSelectScreen con todos los widgets mockeados."""
    with patch("omega_zsh.ui.screens.FigletManager") as mock_fig:
        mock_fig.return_value.get_fonts.return_value = [font]
        screen = HeaderSelectScreen(h_type, text, font)

    mock_area = MagicMock()
    mock_radioset = MagicMock()
    mock_radioset.pressed_button = MagicMock()
    mock_radioset.pressed_button.id = btn_id
    mock_input = MagicMock()
    mock_input.value = text
    mock_lv = MagicMock()
    mock_lv.index = 0

    def query(sel):
        s = str(sel)
        if "type-set" in s: return mock_radioset
        if "input" in s: return mock_input
        if "font" in s: return mock_lv
        return mock_area

    screen.query_one = MagicMock(side_effect=query)
    return screen, mock_area, mock_fig


class TestHeaderPreview(unittest.IsolatedAsyncioTestCase):
    async def test_fastfetch_lanza_subproceso_correcto(self):
        """Verifica que el preview de fastfetch llama al binario con --pipe."""
        with patch("omega_zsh.ui.screens.FigletManager") as mock_fig, \
             patch("omega_zsh.ui.screens.shutil.which", return_value="/usr/bin/fastfetch"), \
             patch("omega_zsh.ui.screens.subprocess.run") as mock_run:
            mock_fig.return_value.get_fonts.return_value = ["slant"]
            mock_run.return_value = MagicMock(returncode=0, stdout="System Info", stderr="")

            screen = HeaderSelectScreen("fastfetch", "Test", "slant")
            mock_area = MagicMock()
            mock_radioset = MagicMock()
            mock_radioset.pressed_button = MagicMock()
            mock_radioset.pressed_button.id = "h-ff"
            mock_input = MagicMock(); mock_input.value = "Test"
            mock_lv = MagicMock(); mock_lv.index = 0

            def query(sel):
                s = str(sel)
                if "type-set" in s: return mock_radioset
                if "input" in s: return mock_input
                if "font" in s: return mock_lv
                return mock_area

            screen.query_one = MagicMock(side_effect=query)
            screen.update_header_preview()

            mock_run.assert_called_once()
            cmd_args = mock_run.call_args[0][0]
            assert "/usr/bin/fastfetch" in cmd_args
            assert "--pipe" in cmd_args

    async def test_figlet_llama_render_con_texto_y_fuente(self):
        """Verifica que figlet.render() recibe exactamente el texto y fuente del usuario."""
        with patch("omega_zsh.ui.screens.FigletManager") as mock_fig:
            mock_fig.return_value.get_fonts.return_value = ["ANSI Shadow"]
            mock_fig.return_value.render.return_value = "██████"

            screen = HeaderSelectScreen("figlet", "S23", "ANSI Shadow")
            mock_area = MagicMock()
            mock_radioset = MagicMock()
            mock_radioset.pressed_button = MagicMock()
            mock_radioset.pressed_button.id = "h-fig"
            mock_input = MagicMock(); mock_input.value = "S23"
            mock_lv = MagicMock(); mock_lv.index = 0

            def query(sel):
                s = str(sel)
                if "type-set" in s: return mock_radioset
                if "input" in s: return mock_input
                if "font" in s: return mock_lv
                return mock_area

            screen.query_one = MagicMock(side_effect=query)
            screen.update_header_preview()

            mock_fig.return_value.render.assert_called_once_with("S23", "ANSI Shadow")

    async def test_none_no_lanza_subproceso(self):
        """Verifica que header=none no lanza ningún subproceso."""
        with patch("omega_zsh.ui.screens.FigletManager") as mock_fig, \
             patch("omega_zsh.ui.screens.subprocess.run") as mock_run:
            mock_fig.return_value.get_fonts.return_value = ["slant"]

            screen = HeaderSelectScreen("none", "", "slant")
            mock_area = MagicMock()
            mock_radioset = MagicMock()
            mock_radioset.pressed_button = MagicMock()
            mock_radioset.pressed_button.id = "h-none"
            mock_input = MagicMock(); mock_input.value = ""
            mock_lv = MagicMock(); mock_lv.index = 0

            def query(sel):
                s = str(sel)
                if "type-set" in s: return mock_radioset
                if "input" in s: return mock_input
                if "font" in s: return mock_lv
                return mock_area

            screen.query_one = MagicMock(side_effect=query)
            screen.update_header_preview()

            mock_run.assert_not_called()
