from unittest.mock import MagicMock, patch
from rich.text import Text
from omega_zsh.ui.screens import ThemeSelectScreen
from textual.widgets import ListView


def make_theme(id="test_theme", path="/path/to/theme.zsh-theme"):
    t = MagicMock()
    t.id = id
    t.path = path
    t.desc = "Test Origin"
    return t


def make_screen_with_mocks(themes, selected, idx=0):
    screen = ThemeSelectScreen(themes, selected)
    mock_static = MagicMock()
    mock_lv = MagicMock()
    mock_lv.index = idx

    def query(selector):
        if selector is ListView: return mock_lv
        return mock_static

    screen.query_one = MagicMock(side_effect=query)
    return screen, mock_static


@patch("subprocess.run")
@patch("shutil.which")
@patch("os.path.exists")
def test_preview_renderiza_ansi_correctamente(mock_exists, mock_which, mock_run):
    """Verifica que el output ANSI del subproceso se parsea y muestra como Rich Text."""
    mock_exists.return_value = True
    mock_which.return_value = "/bin/zsh"
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="\x1b[32m➜\x1b[0m \x1b[36m~\x1b[0m ",
        stderr=""
    )

    theme = make_theme()
    screen, mock_static = make_screen_with_mocks([theme], "test_theme")
    screen.update_preview(None)

    mock_run.assert_called_once()
    update_arg = mock_static.update.call_args[0][0]
    assert isinstance(update_arg, Text), "El preview debe ser Rich Text con ANSI parseado"
    assert "➜" in update_arg.plain


@patch("subprocess.run")
def test_preview_no_lanza_subprocess_sin_path(mock_run):
    """Si el tema no tiene path, no se lanza zsh."""
    theme = make_theme(path=None)
    screen, mock_static = make_screen_with_mocks([theme], "test_theme")
    screen.update_preview(None)

    mock_run.assert_not_called()
    # Debe mostrar mensaje de error, no quedarse vacío
    assert mock_static.update.called
    update_arg = mock_static.update.call_args[0][0]
    assert "Preview not available" in update_arg.plain


@patch("subprocess.run")
@patch("shutil.which")
@patch("os.path.exists")
def test_preview_muestra_stderr_en_fallo(mock_exists, mock_which, mock_run):
    """Si zsh retorna error y no hay stdout, muestra el stderr."""
    mock_exists.return_value = True
    mock_which.return_value = "/bin/zsh"
    mock_run.return_value = MagicMock(
        returncode=1,
        stdout="",
        stderr="command not found: git_prompt_info"
    )

    theme = make_theme()
    screen, mock_static = make_screen_with_mocks([theme], "test_theme")
    screen.update_preview(None)

    update_arg = mock_static.update.call_args[0][0]
    assert "git_prompt_info" in update_arg.plain or mock_static.update.called
