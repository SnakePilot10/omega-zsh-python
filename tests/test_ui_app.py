from unittest.mock import MagicMock, patch
from omega_zsh.ui.app import OmegaApp
from omega_zsh.core.constants import ThemeDef
from pathlib import Path


def test_get_all_themes_discovery():
    # Parcheamos SystemContext y StateManager para el arranque de la app
    with patch("omega_zsh.ui.app.SystemContext"), \
         patch("omega_zsh.ui.app.StateManager"):
        
        app = OmegaApp()
        app.context = MagicMock()

        # 1. Preparar Mocks de archivos
        t1 = MagicMock(); t1.stem = "omega_theme"; t1.name = "omega_theme.zsh-theme"
        t2 = MagicMock(); t2.stem = "robbyrussell"; t2.name = "robbyrussell.zsh-theme"
        t3 = MagicMock(); t3.stem = "my_custom"; t3.name = "my_custom.zsh-theme"

        # 2. Configurar assets_dir (Temas Omega)
        omega_dir_mock = MagicMock()
        omega_dir_mock.exists.return_value = True
        omega_dir_mock.glob.return_value = [t1]
        app.context.assets_dir = MagicMock()
        app.context.assets_dir.__truediv__.return_value = omega_dir_mock

        # 3. Configurar omz_dir (Temas OMZ y Custom)
        omz_dir_mock = MagicMock()
        app.context.omz_dir = omz_dir_mock
        
        omz_themes_mock = MagicMock()
        omz_themes_mock.exists.return_value = True
        omz_themes_mock.glob.return_value = [t2]
        
        custom_base_mock = MagicMock()
        custom_themes_mock = MagicMock()
        custom_themes_mock.exists.return_value = True
        custom_themes_mock.glob.return_value = [t3]
        custom_base_mock.__truediv__.return_value = custom_themes_mock

        def omz_div_effect(x):
            if x == "themes": return omz_themes_mock
            if x == "custom": return custom_base_mock
            return MagicMock()
        
        omz_dir_mock.__truediv__.side_effect = omz_div_effect

        # 4. Parchear Path para que devuelva nuestros mocks cuando se convierta a str
        # El código hace: Path(str(self.context.assets_dir / "themes"))
        original_path = Path
        def path_mock_factory(x):
            if x == str(omega_dir_mock): return omega_dir_mock
            if x == str(omz_themes_mock): return omz_themes_mock
            if x == str(custom_themes_mock): return custom_themes_mock
            return original_path(x)

        with patch("omega_zsh.ui.app.Path", side_effect=path_mock_factory):
            themes = app._get_all_themes()
            ids = [t.id for t in themes]
            
            # Verificaciones
            assert "omega_theme" in ids
            assert "robbyrussell" in ids
            assert "my_custom" in ids
