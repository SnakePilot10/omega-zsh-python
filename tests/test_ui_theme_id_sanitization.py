from unittest.mock import MagicMock, patch

from omega_zsh.core.constants import ThemeDef
from omega_zsh.ui.screens import ThemeSelectScreen


def test_theme_ids_are_numeric():
    """IDs de ListItem son índices numéricos para evitar BadIdentifier."""
    themes = [
        ThemeDef(id="standard", path="/p/standard", desc="Standard"),
        ThemeDef(id="wezm+", path="/p/wezm", desc="Plus Theme"),
        ThemeDef(id="my_theme", path="/p/my_theme", desc="Underscore"),
    ]
    screen = ThemeSelectScreen(themes, "standard")

    class FakeCtx:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

    with patch("omega_zsh.ui.screens.Vertical", return_value=FakeCtx()), patch(
        "omega_zsh.ui.screens.ListView"
    ) as mock_lv:
        mock_lv.return_value = MagicMock()

        with patch("omega_zsh.ui.screens.ListItem") as mock_li, patch(
            "omega_zsh.ui.screens.Label"
        ):
            mock_li.side_effect = lambda *args, **kwargs: MagicMock(
                id=kwargs.get("id")
            )
            list(screen.compose())
            ids = [call.kwargs.get("id") for call in mock_li.call_args_list]

    assert "t-0" in ids
    assert "t-1" in ids
    assert "t-2" in ids
    for item_id in ids:
        if item_id:
            assert "+" not in item_id
