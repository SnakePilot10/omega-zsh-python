
import pytest
from unittest.mock import MagicMock, patch
from omega_zsh.ui.screens import ThemeSelectScreen
from rich.text import Text

@pytest.fixture
def mock_theme():
    theme = MagicMock()
    theme.id = "test_theme"
    theme.path = "/path/to/theme.zsh-theme"
    return theme

@patch("subprocess.run")
@patch("omega_zsh.ui.screens.os.path.exists")
def test_generate_preview_success(mock_exists, mock_run, mock_theme):
    # Setup
    mock_exists.return_value = True # zsh exists
    
    # Mock subprocess result
    mock_result = MagicMock()
    mock_result.return_code = 0
    mock_result.stdout = "\x1b[32m➜\x1b[0m \x1b[36m~\x1b[0m " # Green Arrow, Cyan Tilde
    mock_result.returncode = 0
    mock_run.return_value = mock_result
    
    screen = ThemeSelectScreen([mock_theme], "test_theme")
    
    # Mock query_one to return a mock Static widget
    mock_static = MagicMock()
    screen.query_one = MagicMock(return_value=mock_static)
    
    # Execute
    screen.generate_preview("test_theme")
    
    # Assert
    mock_run.assert_called_once()
    # Check that update was called on the static widget
    assert mock_static.update.call_count >= 2
    
    # Retrieve the last argument passed to update
    last_call_args = mock_static.update.call_args[0]
    assert isinstance(last_call_args[0], Text)
    # Verify content roughly matches (Rich parses ANSI, so the plain text should be "➜ ~ ")
    assert "➜ ~ " in last_call_args[0].plain

@patch("subprocess.run")
def test_generate_preview_no_path(mock_run, mock_theme):
    mock_theme.path = None
    screen = ThemeSelectScreen([mock_theme], "test_theme")
    mock_static = MagicMock()
    screen.query_one = MagicMock(return_value=mock_static)
    
    screen.generate_preview("test_theme")
    
    mock_run.assert_not_called()
    mock_static.update.assert_called()
    args, _ = mock_static.update.call_args
    assert "Preview not available" in args[0].plain
