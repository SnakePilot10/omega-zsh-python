from unittest.mock import MagicMock, patch

from omega_zsh.ui.screens import HeaderSelectScreen


def run_header_preview(screen: HeaderSelectScreen) -> None:
    HeaderSelectScreen.update_header_preview.__wrapped__(screen)


def test_fastfetch_lanza_subproceso_correcto():
    """Verifica que el preview de fastfetch llama al binario con --pipe."""
    screen = HeaderSelectScreen("fastfetch", "Test", "slant")
    preview = MagicMock()
    screen.get_selected = MagicMock(return_value=("fastfetch", "Test", "slant"))
    screen.query_one = MagicMock(return_value=preview)

    with patch("omega_zsh.ui.screens.shutil.which", return_value="/usr/bin/fastfetch"):
        with patch("omega_zsh.ui.screens.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="System Info", stderr="")

            run_header_preview(screen)

            mock_run.assert_called_once()
            cmd_args = mock_run.call_args[0][0]
            assert "/usr/bin/fastfetch" in cmd_args
            assert "--pipe" in cmd_args
            assert preview.update.called


def test_figlet_llama_render_con_texto_y_fuente():
    """Verifica que figlet.render() recibe exactamente el texto y fuente del usuario."""
    with patch("omega_zsh.ui.screens.FigletManager") as mock_fig:
        mock_fig.return_value.get_fonts.return_value = ["ANSI Shadow"]
        mock_fig.return_value.render.return_value = "██████"
        screen = HeaderSelectScreen("figlet", "S23", "ANSI Shadow")
        preview = MagicMock()
        screen.get_selected = MagicMock(return_value=("figlet", "S23", "ANSI Shadow"))
        screen.query_one = MagicMock(return_value=preview)

        run_header_preview(screen)

        mock_fig.return_value.render.assert_called_once_with("S23", "ANSI Shadow")
        assert preview.update.called


def test_none_no_lanza_subproceso():
    """Verifica que header=none no lanza ningún subproceso."""
    screen = HeaderSelectScreen("none", "", "slant")
    preview = MagicMock()
    screen.get_selected = MagicMock(return_value=("none", "", "slant"))
    screen.query_one = MagicMock(return_value=preview)

    with patch("omega_zsh.ui.screens.subprocess.run") as mock_run:
        run_header_preview(screen)

        mock_run.assert_not_called()
        assert preview.update.called
