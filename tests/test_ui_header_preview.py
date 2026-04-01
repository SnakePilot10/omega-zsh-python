import unittest
from unittest.mock import MagicMock, patch

from omega_zsh.ui.app import OmegaApp  # Importar la app real para run_test
from omega_zsh.ui.screens import HeaderSelectScreen


class TestHeaderPreview(unittest.IsolatedAsyncioTestCase):
    async def test_fastfetch_lanza_subproceso_correcto(self):
        """Verifica que el preview de fastfetch llama al binario con --pipe."""
        with patch("omega_zsh.ui.screens.shutil.which", return_value="/usr/bin/fastfetch"):
            with patch("omega_zsh.ui.screens.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="System Info", stderr="")

                # Usar App.run_test para simular el ciclo de vida real de la app
                async with OmegaApp().run_test(initial_screen=HeaderSelectScreen("fastfetch", "Test", "slant")) as pilot:
                    screen = pilot.app.screen_stack[0]
                    screen.query_one("#header-type-set").pressed_button.id = "h-ff"
                    screen.query_one("#header-input").value = "Test"
                    screen.query_one("#font-list").index = 0
                    
                    # Llamamos al método que ya está decorado con @work
                    await screen.update_header_preview()

                    mock_run.assert_called_once()
                    cmd_args = mock_run.call_args[0][0]
                    assert "/usr/bin/fastfetch" in cmd_args
                    assert "--pipe" in cmd_args
                    assert "System Info" in pilot.app.query_one("#preview-area").renderable.plain

    async def test_figlet_llama_render_con_texto_y_fuente(self):
        """Verifica que figlet.render() recibe exactamente el texto y fuente del usuario."""
        with patch("omega_zsh.ui.screens.FigletManager") as mock_fig:
            mock_fig.return_value.get_fonts.return_value = ["ANSI Shadow"]
            mock_fig.return_value.render.return_value = "██████"

            async with OmegaApp().run_test(initial_screen=HeaderSelectScreen("figlet", "S23", "ANSI Shadow")) as pilot:
                screen = pilot.app.screen_stack[0]
                screen.query_one("#header-type-set").pressed_button.id = "h-fig"
                screen.query_one("#header-input").value = "S23"
                screen.query_one("#font-list").index = 0

                await screen.update_header_preview()

                mock_fig.return_value.render.assert_called_once_with("S23", "ANSI Shadow")
                assert "██████" in pilot.app.query_one("#preview-area").renderable.plain

    async def test_none_no_lanza_subproceso(self):
        """Verifica que header=none no lanza ningún subproceso."""
        with patch("omega_zsh.ui.screens.subprocess.run") as mock_run:
            async with OmegaApp().run_test(initial_screen=HeaderSelectScreen("none", "", "slant")) as pilot:
                screen = pilot.app.screen_stack[0]
                screen.query_one("#header-type-set").pressed_button.id = "h-none"
                screen.query_one("#header-input").value = ""
                screen.query_one("#font-list").index = 0

                await screen.update_header_preview()

                mock_run.assert_not_called()
                assert "No header selected" in pilot.app.query_one("#preview-area").renderable.plain
