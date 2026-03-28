from unittest.mock import MagicMock, patch
from omega_zsh.ui.app import OmegaApp
from omega_zsh.core.constants import ThemeDef


def test_get_all_themes_discovery():
    with patch("omega_zsh.ui.app.SystemContext"), \
         patch("omega_zsh.ui.app.StateManager"):
        app = OmegaApp()
        app.context = MagicMock()

        # Mock de directorios y archivos
        t1 = MagicMock(); t1.stem = "omega_theme"; t1.name = "omega_theme.zsh-theme"
        omega_dir = MagicMock()
        omega_dir.exists.return_value = True
        omega_dir.glob.return_value = [t1]

        t2 = MagicMock(); t2.stem = "robbyrussell"; t2.name = "robbyrussell.zsh-theme"
        omz_themes_dir = MagicMock()
        omz_themes_dir.exists.return_value = True
        omz_themes_dir.glob.return_value = [t2]

        t3 = MagicMock(); t3.stem = "my_custom"; t3.name = "my_custom.zsh-theme"
        custom_dir = MagicMock()
        custom_dir.exists.return_value = True
        custom_dir.glob.return_value = [t3]

        # Configurar el comportamiento de división de rutas (/)
        # Para assets_dir / "themes"
        app.context.assets_dir.__truediv__.return_value = omega_dir
        
        # Para omz_dir / "themes" y omz_dir / "custom" / "themes"
        omz_dir = MagicMock()
        app.context.omz_dir = omz_dir
        
        custom_base = MagicMock()
        
        def omz_div(x):
            if x == "themes": return omz_themes_dir
            if x == "custom": return custom_base
            return MagicMock()
        
        omz_dir.__truediv__.side_effect = omz_div
        custom_base.__truediv__.return_value = custom_dir

        # Parchear Path para que acepte los mocks en el constructor
        from pathlib import Path as RealPath
        def path_side_effect(x):
            if str(x) == str(omega_dir): return omega_dir
            if str(x) == str(omz_themes_dir): return omz_themes_dir
            if str(x) == str(custom_dir): return custom_dir
            return RealPath(x)

        with patch("omega_zsh.ui.app.Path", side_effect=path_side_effect):
            themes = app._get_all_themes()
            ids = [t.id for t in themes]
            assert "omega_theme" in ids
            assert "robbyrussell" in ids
            assert "my_custom" in ids
