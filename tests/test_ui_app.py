import pytest
from unittest.mock import MagicMock, patch
from omega_zsh.ui.app import OmegaApp


@pytest.fixture
def mock_app():
    """Fixture to create a mock OmegaApp instance."""
    app = OmegaApp()
    # Mock internal components to avoid side effects
    app.context = MagicMock()
    app.state_manager = MagicMock()
    app.push_screen = MagicMock()
    return app


@patch("omega_zsh.ui.app.Path")
def test_action_config_themes_discovery(mock_path, mock_app):
    """Test that action_config_themes discovers and merges themes correctly."""

    # Setup paths
    mock_assets_path = MagicMock()
    mock_omz_themes_path = MagicMock()
    mock_user_custom_path = MagicMock()

    # Configure path existence
    mock_assets_path.exists.return_value = True
    mock_omz_themes_path.exists.return_value = True
    mock_user_custom_path.exists.return_value = True

    # Mock glob results for each path
    # 1. Omega Themes
    theme1 = MagicMock()
    theme1.stem = "omega_theme"
    mock_assets_path.glob.return_value = [theme1]

    # 2. Standard OMZ Themes
    theme2 = MagicMock()
    theme2.stem = "robbyrussell"
    mock_omz_themes_path.glob.return_value = [theme2]

    # 3. User Custom Themes
    theme3 = MagicMock()
    theme3.stem = "my_custom"
    mock_user_custom_path.glob.return_value = [theme3]

    # Mock Path construction to return our mocks
    # This is tricky with pathlib.Path because it's used in many places.
    # We'll rely on side_effect or specific return values based on input if possible,
    # or just simple mocking if the structure allows.

    # Easier approach: Mock the properties on the app instance or context directly if feasible,
    # but here paths are constructed inside the method.
    # Let's inspect how Path is used in the method:
    # custom_themes_path = Path(__file__).parent.parent / "assets/themes"
    # omz_themes_path = self.context.home / ".oh-my-zsh/themes"
    # user_custom_path = self.context.home / ".oh-my-zsh/custom/themes"

    # We can mock the returns of the chains.

    # Mocking Path(__file__).parent.parent / "assets/themes"
    # This chain is long. Let's assume we can mock Path logic or just the result.

    # Let's try to patch the specific glob calls if possible, OR
    # just mock the attributes of mock_app.context.home

    mock_home = mock_app.context.home

    # Setup the chain for OMZ paths
    # home / ".oh-my-zsh/themes"
    mock_home.__truediv__.return_value.__truediv__.return_value = mock_omz_themes_path
    # We need to distinguish between the two paths derived from home.

    def side_effect_home_div(arg):
        if arg == ".oh-my-zsh/themes":
            return mock_omz_themes_path
        if arg == ".oh-my-zsh/custom/themes":
            return mock_user_custom_path
        # Return a generic mock for other cases (like intermediate dirs)
        m = MagicMock()
        # Allow chaining for .oh-my-zsh / themes if it's done step by step
        if arg == ".oh-my-zsh":
            m.__truediv__.side_effect = (
                lambda x: mock_omz_themes_path
                if x == "themes"
                else (mock_user_custom_path if x == "custom/themes" else MagicMock())
            )
            # This is getting complicated because of how Path / works.
        return m

    # Simplify: patch pathlib.Path in the module
    with patch("omega_zsh.ui.app.Path") as MockPathClass:
        # Mock the asset path construction
        mock_asset_path_obj = MagicMock()
        mock_asset_path_obj.exists.return_value = True
        mock_asset_path_obj.glob.return_value = [theme1]

        # When Path(__file__) is called...
        # We need to catch the chain: Path(...) .parent .parent / "assets/themes"
        MockPathClass.return_value.parent.parent.__truediv__.return_value = (
            mock_asset_path_obj
        )

        # Mock context.home logic
        # We need to ensure mock_app.context.home returns an object that behaves like a Path
        # and returns our mocked theme dirs.

        mock_home = MagicMock()
        mock_app.context.home = mock_home

        mock_omz_themes_dir = MagicMock()
        mock_omz_themes_dir.exists.return_value = True
        mock_omz_themes_dir.glob.return_value = [theme2]

        mock_user_custom_dir = MagicMock()
        mock_user_custom_dir.exists.return_value = True
        mock_user_custom_dir.glob.return_value = [theme3]
        mock_user_custom_dir.rglob.return_value = [theme3]

        # Handle: self.context.home / ".oh-my-zsh/themes"
        # and: self.context.home / ".oh-my-zsh/custom/themes"

        def home_div_side_effect(arg):
            if arg == ".oh-my-zsh/themes":
                return mock_omz_themes_dir
            if arg == ".oh-my-zsh/custom/themes":
                return mock_user_custom_dir
            return MagicMock()  # Fallback

        mock_home.__truediv__.side_effect = home_div_side_effect

        # EXECUTE
        mock_app.action_config_themes()

        # ASSERT
        # Check that push_screen was called with a ThemeSelectScreen containing all themes
        mock_app.push_screen.assert_called_once()
        call_args = mock_app.push_screen.call_args
        screen_instance = call_args[0][0]

        # Extract themes passed to screen
        themes = screen_instance.themes
        theme_ids = [t.id for t in themes]

        assert "omega_theme" in theme_ids
        assert "robbyrussell" in theme_ids
        assert "my_custom" in theme_ids
        assert len(themes) == 3
