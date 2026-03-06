import asyncio
import unittest
from unittest.mock import MagicMock, patch

from textual.app import App

from omega_zsh.ui.screens import HeaderSelectScreen


class MockApp(App):
    def __init__(self):
        super().__init__()
        self.header_text = "TestHeader"
        self.header_font = "TestFont"


class TestHeaderPreview(unittest.IsolatedAsyncioTestCase):
    async def test_header_preview_fastfetch(self):
        call_log = []
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Fastfetch Output"

        def fake_run(*args, **kwargs):
            call_log.append(args)
            return mock_result

        with (
            patch("omega_zsh.ui.screens.shutil.which", return_value="/usr/bin/fastfetch"),
            patch("omega_zsh.ui.screens.subprocess.run", side_effect=fake_run),
        ):
            app = MockApp()
            async with app.run_test():
                screen = HeaderSelectScreen("fastfetch", "Test", "slant")
                await app.push_screen(screen)
                # Forzar actualización manual ya que el timer/on_mount puede ser asíncrono
                screen.update_header_preview()
                await asyncio.sleep(0.1)

            assert any("fastfetch" in str(call[0]) for call in call_log)

    async def test_header_preview_figlet(self):
        """Prueba la previsualización de Figlet."""
        with patch("omega_zsh.ui.screens.FigletManager") as mock_figlet_class:
            mock_figlet = mock_figlet_class.return_value
            mock_figlet.get_fonts.return_value = ["slant"]
            mock_figlet.render.return_value = "Rendered Figlet"

            app = MockApp()
            async with app.run_test():
                screen = HeaderSelectScreen("figlet", "Test", "slant")
                await app.push_screen(screen)
                screen.update_header_preview()
                await asyncio.sleep(0.1)

            mock_figlet.render.assert_called_with("Test", "slant")
            preview_area = screen.query_one("#header-preview-area")
            assert "Rendered Figlet" in str(preview_area.renderable)
