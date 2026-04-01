import unittest
from unittest.mock import MagicMock, patch

from rich.text import Text

from omega_zsh.ui.app import OmegaApp  # Importar la app real para run_test
from omega_zsh.ui.screens import ThemeSelectScreen


class TestThemePreview(unittest.IsolatedAsyncioTestCase):
    async def test_preview_renderiza_ansi_correctamente(self):
        """Verifica que el output ANSI del subproceso se parsea y muestra como Rich Text."""
        with patch("omega_zsh.ui.screens.shutil.which", return_value="/bin/zsh"):
            with patch("omega_zsh.ui.screens.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="\x1b[32m➜\x1b[0m \x1b[36m~\x1b[0m ",
                    stderr=""
                )

                theme = MagicMock(id="test_theme", path="/path/to/theme.zsh-theme", desc="Test Origin")

                async with OmegaApp().run_test(initial_screen=ThemeSelectScreen([theme], "test_theme")) as pilot:
                    screen = pilot.app.screen_stack[0]
                    screen.query_one(ListView).index = 0 # Simular selección

                    await screen.update_preview(MagicMock())

                    mock_run.assert_called_once()
                    update_arg = pilot.app.query_one("#preview-area").renderable
                    assert isinstance(update_arg, Text), "El preview debe ser Rich Text con ANSI parseado"
                    assert "➜" in update_arg.plain

    async def test_preview_no_lanza_subprocess_sin_path(self):
        """Si el tema no tiene path, no se lanza zsh."""
        theme = MagicMock(id="test_theme", path=None, desc="Test Origin")
        with patch("omega_zsh.ui.screens.subprocess.run") as mock_run:
            async with OmegaApp().run_test(initial_screen=ThemeSelectScreen([theme], "test_theme")) as pilot:
                screen = pilot.app.screen_stack[0]
                screen.query_one(ListView).index = 0

                await screen.update_preview(MagicMock())

                mock_run.assert_not_called()
                update_arg = pilot.app.query_one("#preview-area").renderable
                assert "Preview not available" in update_arg.plain


    async def test_preview_muestra_stderr_en_fallo(self):
        """Si zsh retorna error y no hay stdout, muestra el stderr."""
        with patch("omega_zsh.ui.screens.shutil.which", return_value="/bin/zsh"):
            with patch("omega_zsh.ui.screens.os.path.exists", return_value=True):
                with patch("omega_zsh.ui.screens.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=1,
                        stdout="",
                        stderr="command not found: git_prompt_info"
                    )

                    theme = MagicMock(id="test_theme", path="/path/to/theme.zsh-theme", desc="Test Origin")

                    async with OmegaApp().run_test(ThemeSelectScreen([theme], "test_theme")) as pilot:
                        screen = pilot.app.screen_stack[0]
                        screen.query_one(ListView).index = 0

                        await screen.update_preview(MagicMock())

                        update_arg = pilot.app.query_one("#preview-area").renderable
                        assert "git_prompt_info" in update_arg.plain
