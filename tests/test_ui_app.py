from unittest.mock import MagicMock, patch
from omega_zsh.ui.app import OmegaApp


def test_get_all_themes_discovery():
    with patch("omega_zsh.ui.app.SystemContext"), \
         patch("omega_zsh.ui.app.StateManager"):
        app = OmegaApp()
        app.context = MagicMock()

        t1 = MagicMock(); t1.stem = "omega_theme"
        omega_dir = MagicMock(); omega_dir.exists.return_value = True
        omega_dir.glob.return_value = [t1]

        t2 = MagicMock(); t2.stem = "robbyrussell"
        omz_themes_dir = MagicMock(); omz_themes_dir.exists.return_value = True
        omz_themes_dir.glob.return_value = [t2]

        t3 = MagicMock(); t3.stem = "my_custom"
        custom_dir = MagicMock(); custom_dir.exists.return_value = True
        custom_dir.glob.return_value = [t3]

        custom_mock = MagicMock()
        custom_mock.__truediv__ = MagicMock(return_value=custom_dir)

        def omz_div(x):
            if x == "themes": return omz_themes_dir
            if x == "custom": return custom_mock
            return MagicMock()

        app.context.omz_dir.__truediv__ = MagicMock(side_effect=omz_div)
        app.context.project_root.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = omega_dir

        themes = app._get_all_themes()
        ids = [t.id for t in themes]
        assert "omega_theme" in ids
        assert "robbyrussell" in ids
        assert "my_custom" in ids
