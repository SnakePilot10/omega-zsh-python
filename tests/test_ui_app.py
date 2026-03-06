from unittest.mock import MagicMock, patch

import pytest

from omega_zsh.ui.app import OmegaApp


@pytest.fixture
def mock_app():
    """Fixture to create a mock OmegaApp instance."""
    with patch("omega_zsh.ui.app.SystemContext"):
        with patch("omega_zsh.ui.app.StateManager"):
            app = OmegaApp()
            # Mock internal components to avoid side effects
            app.context = MagicMock()
            app.state_manager = MagicMock()
            app.push_screen = MagicMock()
            return app


def test_get_all_themes_discovery(mock_app):
    """Test that _get_all_themes discovers and merges themes correctly from multiple sources."""

    # 1. Setup Omega Themes
    mock_omega_dir = MagicMock()
    mock_omega_dir.exists.return_value = True
    theme1 = MagicMock()
    theme1.stem = "omega_theme"
    mock_omega_dir.glob.return_value = [theme1]

    # 2. Setup OMZ Themes
    mock_omz_dir = MagicMock()
    mock_omz_dir.exists.return_value = True
    theme2 = MagicMock()
    theme2.stem = "robbyrussell"
    mock_omz_dir.glob.return_value = [theme2]

    # 3. Setup User Custom Themes
    mock_user_dir = MagicMock()
    mock_user_dir.exists.return_value = True
    theme3 = MagicMock()
    theme3.stem = "my_custom"
    mock_user_dir.glob.return_value = [theme3]

    # Configure the app context paths
    # (self.context.project_root / "omega_zsh" / "assets" / "themes")
    mock_app.context.project_root.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = (
        mock_omega_dir
    )

    # (self.context.omz_dir / "themes")
    mock_app.context.omz_dir.__truediv__.side_effect = (
        lambda x: mock_omz_dir
        if x == "themes"
        else (mock_user_dir if x == "custom/themes" else MagicMock())
    )

    # EXECUTE
    themes = mock_app._get_all_themes()

    # ASSERT
    theme_ids = [t.id for t in themes]
    assert "omega_theme" in theme_ids
    assert "robbyrussell" in theme_ids
    assert "my_custom" in theme_ids
    # We expect 3 themes if they don't overlap
    assert len(themes) >= 3
