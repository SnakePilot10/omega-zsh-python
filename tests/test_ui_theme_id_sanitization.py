from unittest.mock import MagicMock, patch
from omega_zsh.core.constants import ThemeDef
from omega_zsh.ui.screens import ThemeSelectScreen


def test_theme_ids_are_numeric():
    """IDs de ListItem son índices numéricos para evitar BadIdentifier."""
    themes = [
        ThemeDef(id="standard",  path="/p/standard",  desc="Standard"),
        ThemeDef(id="wezm+",     path="/p/wezm",      desc="Plus Theme"),
        ThemeDef(id="my_theme",  path="/p/my_theme",  desc="Underscore"),
    ]
    screen = ThemeSelectScreen(themes, "standard")

    items = []
    class FakeCtx:
        def __enter__(self): return self
        def __exit__(self, *a): pass

    with patch("omega_zsh.ui.screens.Vertical", return_value=FakeCtx()), \
         patch("omega_zsh.ui.screens.ListView") as mock_lv:
        mock_lv.return_value = MagicMock()

        with patch("omega_zsh.ui.screens.ListItem") as mock_li, \
             patch("omega_zsh.ui.screens.Label"):
            mock_li.side_effect = lambda *a, **kw: MagicMock(id=kw.get("id"))
            list(screen.compose())
            ids = [call.kwargs.get("id") for call in mock_li.call_args_list]

    assert "t-0" in ids
    assert "t-1" in ids
    assert "t-2" in ids
    # Verificar que no hay IDs con caracteres inválidos
    for id_ in ids:
        if id_:
            assert "+" not in id_
