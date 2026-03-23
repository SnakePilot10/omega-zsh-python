import unittest
from unittest.mock import MagicMock, patch
from omega_zsh.ui.screens import HeaderSelectScreen


class TestHeaderPreview(unittest.IsolatedAsyncioTestCase):
    async def test_header_preview_fastfetch(self):
        with patch("omega_zsh.ui.screens.FigletManager") as mock_fig, \
             patch("omega_zsh.ui.screens.shutil.which", return_value="/usr/bin/fastfetch"), \
             patch("omega_zsh.ui.screens.subprocess.run") as mock_run:
            mock_fig.return_value.get_fonts.return_value = ["slant"]
            mock_run.return_value = MagicMock(returncode=0, stdout="ff output", stderr="")
            screen = HeaderSelectScreen("fastfetch", "Test", "slant")
            mock_area = MagicMock()
            mock_radioset = MagicMock()
            mock_radioset.pressed_button = MagicMock()
            mock_radioset.pressed_button.id = "h-ff"
            mock_input = MagicMock()
            mock_input.value = "Test"
            mock_lv = MagicMock()
            mock_lv.index = 0

            def query(sel):
                if "type-set" in str(sel): return mock_radioset
                if "input" in str(sel): return mock_input
                if "font" in str(sel): return mock_lv
                return mock_area

            screen.query_one = MagicMock(side_effect=query)
            screen.update_header_preview()
            assert mock_run.called

    async def test_header_preview_figlet(self):
        with patch("omega_zsh.ui.screens.FigletManager") as mock_fig:
            mock_fig.return_value.get_fonts.return_value = ["slant"]
            mock_fig.return_value.render.return_value = "Rendered Figlet"
            screen = HeaderSelectScreen("figlet", "Test", "slant")
            mock_area = MagicMock()
            mock_radioset = MagicMock()
            mock_radioset.pressed_button = MagicMock()
            mock_radioset.pressed_button.id = "h-fig"
            mock_input = MagicMock()
            mock_input.value = "Test"
            mock_lv = MagicMock()
            mock_lv.index = 0

            def query(sel):
                if "type-set" in str(sel): return mock_radioset
                if "input" in str(sel): return mock_input
                if "font" in str(sel): return mock_lv
                return mock_area

            screen.query_one = MagicMock(side_effect=query)
            screen.update_header_preview()
            mock_fig.return_value.render.assert_called_with("Test", "slant")
