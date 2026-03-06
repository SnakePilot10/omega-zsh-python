from unittest.mock import MagicMock, patch

import pytest
from rich.text import Text

from omega_zsh.ui.screens import ThemeSelectScreen


@pytest.fixture
def mock_theme():
    theme = MagicMock()
    theme.id = "test_theme"
    theme.path = "/path/to/theme.zsh-theme"
    theme.origin = "test_origin"
    return theme


@patch("subprocess.run")
@patch("shutil.which")
@patch("os.path.exists")
def test_update_preview_success(mock_exists, mock_which, mock_run, mock_theme):
    # Setup
    mock_exists.return_value = True  # zsh exists
    mock_which.return_value = "/bin/zsh"

    # Mock subprocess result
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "\x1b[32m➜\x1b[0m \x1b[36m~\x1b[0m "  # Green Arrow, Cyan Tilde
    mock_run.return_value = mock_result

    screen = ThemeSelectScreen([mock_theme], "test_theme")

    # Mock components
    mock_static = MagicMock()
    mock_list_view = MagicMock()
    mock_list_view.index = 0

    def side_effect_query(selector):
        if selector == "#theme-preview-box":
            return mock_static
        if selector == "ListView":
            return mock_list_view
        return MagicMock()

    screen.query_one = MagicMock(side_effect=side_effect_query)

    # Execute
    screen.update_preview(None)

    # Assert
    mock_run.assert_called_once()
    # Check that update was called on the static widget
    assert mock_static.update.call_count >= 1

    # Retrieve the last argument passed to update
    last_call_args = mock_static.update.call_args[0]
    assert isinstance(last_call_args[0], Text)
    # Verify content roughly matches (Rich parses ANSI, so the plain text should be "➜ ~ ")
    assert "➜" in last_call_args[0].plain


@patch("subprocess.run")
def test_update_preview_no_path(mock_run, mock_theme):
    mock_theme.path = None
    screen = ThemeSelectScreen([mock_theme], "test_theme")

    # Mock components
    mock_static = MagicMock()
    mock_list_view = MagicMock()
    mock_list_view.index = 0

    def side_effect_query(selector):
        if selector == "#theme-preview-box":
            return mock_static
        if selector == "ListView":
            return mock_list_view
        return MagicMock()

    screen.query_one = MagicMock(side_effect=side_effect_query)

    screen.update_preview(None)

    mock_run.assert_not_called()
    mock_static.update.assert_called()
    args, _ = mock_static.update.call_args
    assert "Preview not available" in args[0].plain
