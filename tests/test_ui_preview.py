from unittest.mock import MagicMock, patch
from omega_zsh.ui.screens import ThemeSelectScreen
from textual.widgets import ListView


def make_theme(stem="test_theme", path="/path/to/theme.zsh-theme"):
    t = MagicMock()
    t.id = stem
    t.path = path
    t.desc = "test_origin"
    return t


@patch("subprocess.run")
@patch("shutil.which")
@patch("os.path.exists")
def test_update_preview_success(mock_exists, mock_which, mock_run):
    mock_exists.return_value = True
    mock_which.return_value = "/bin/zsh"
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "\x1b[32m➜\x1b[0m \x1b[36m~\x1b[0m "
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    theme = make_theme()
    screen = ThemeSelectScreen([theme], "test_theme")

    mock_static = MagicMock()
    mock_list_view = MagicMock()
    mock_list_view.index = 0

    def query(selector):
        if selector is ListView or selector == ListView:
            return mock_list_view
        return mock_static

    screen.query_one = MagicMock(side_effect=query)
    screen.update_preview(None)
    assert mock_static.update.called


@patch("subprocess.run")
def test_update_preview_no_path(mock_run):
    theme = make_theme(path=None)
    screen = ThemeSelectScreen([theme], "test_theme")

    mock_static = MagicMock()
    mock_list_view = MagicMock()
    mock_list_view.index = 0

    def query(selector):
        if selector is ListView or selector == ListView:
            return mock_list_view
        return mock_static

    screen.query_one = MagicMock(side_effect=query)
    screen.update_preview(None)
    mock_run.assert_not_called()
    assert mock_static.update.called
