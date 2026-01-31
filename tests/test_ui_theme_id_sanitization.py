from unittest.mock import MagicMock, patch
from omega_zsh.ui.screens import ThemeSelectScreen
from omega_zsh.core.constants import ThemeDef
from textual.widgets import RadioButton


@patch("omega_zsh.ui.screens.Horizontal")
@patch("omega_zsh.ui.screens.Vertical")
@patch("omega_zsh.ui.screens.RadioSet")
def test_theme_select_screen_sanitization(mock_rs, mock_v, mock_h):
    # Setup mocks to act as context managers
    for m in [mock_h, mock_v, mock_rs]:
        m.return_value.__enter__.return_value = MagicMock()
        m.return_value.__exit__.return_value = None

    # Setup
    themes = [
        ThemeDef(id="standard", path="/path/to/standard", desc="Standard"),
        ThemeDef(id="wezm+", path="/path/to/wezm", desc="Plus Theme"),
        ThemeDef(id="my_theme", path="/path/to/my_theme", desc="Underscore"),
    ]
    current_theme = "standard"

    screen = ThemeSelectScreen(themes, current_theme)

    # Act: Generate widgets via compose
    widgets = list(screen.compose())

    # Extract RadioButtons
    radio_buttons = [w for w in widgets if isinstance(w, RadioButton)]

    # Debug info
    print(f"Found RadioButtons with IDs: {[rb.id for rb in radio_buttons]}")

    # Verification
    # Map label text to ID
    rb_map = {rb.label.plain: rb.id for rb in radio_buttons}

    # Debug print
    print(f"Radio Buttons Map: {rb_map}")

    # 1. Standard
    # "standard" -> "Standard"
    assert rb_map["Standard"] == "t-standard"

    # 2. Invalid char (+)
    # "wezm+" -> clean: "wezm+" -> replace _,- with space -> "wezm+" -> title() -> "Wezm+"
    # Wait, strictly following logic:
    # clean_name = theme.id.replace('_', ' ').replace('-', ' ').strip()
    # "wezm+" -> "wezm+"
    # title() -> "Wezm+"
    assert rb_map["Wezm+"] == "t-wezm-"

    # 3. Underscore
    # "my_theme" -> "my theme" -> "My Theme"
    assert rb_map["My Theme"] == "t-my-theme"
