from pathlib import Path
from unittest.mock import MagicMock, patch

from omega_zsh.core.manifest import record_managed_file
from omega_zsh.core.state import AppState
from omega_zsh.ui.app import OmegaApp, link_omega_themes
from omega_zsh.ui.screens import PluginSelectScreen


def test_get_all_themes_discovery():
    # Parcheamos SystemContext y StateManager para el arranque de la app
    with patch("omega_zsh.ui.app.SystemContext"), patch("omega_zsh.ui.app.StateManager"):
        app = OmegaApp()
        app.context = MagicMock()

        # 1. Preparar Mocks de archivos
        t1 = MagicMock()
        t1.stem = "omega_theme"
        t1.name = "omega_theme.zsh-theme"
        t2 = MagicMock()
        t2.stem = "robbyrussell"
        t2.name = "robbyrussell.zsh-theme"
        t3 = MagicMock()
        t3.stem = "my_custom"
        t3.name = "my_custom.zsh-theme"

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
            if x == "themes":
                return omz_themes_mock
            if x == "custom":
                return custom_base_mock
            return MagicMock()

        omz_dir_mock.__truediv__.side_effect = omz_div_effect

        # 4. Parchear Path para que devuelva nuestros mocks cuando se convierta a str
        # El código hace: Path(str(self.context.assets_dir / "themes"))
        original_path = Path

        def path_mock_factory(x):
            if x == str(omega_dir_mock):
                return omega_dir_mock
            if x == str(omz_themes_mock):
                return omz_themes_mock
            if x == str(custom_themes_mock):
                return custom_themes_mock
            return original_path(x)

        with patch("omega_zsh.ui.app.Path", side_effect=path_mock_factory):
            themes = app._get_all_themes()
            ids = [t.id for t in themes]

            # Verificaciones
            assert "omega_theme" in ids
            assert "robbyrussell" in ids
            assert "my_custom" in ids


def test_link_omega_themes_preserva_archivo_ajeno(tmp_path):
    assets = tmp_path / "assets"
    themes = assets / "themes"
    themes.mkdir(parents=True)
    (themes / "same.zsh-theme").write_text("# omega", encoding="utf-8")

    omz = tmp_path / ".oh-my-zsh"
    omz.mkdir()
    (omz / "oh-my-zsh.sh").write_text("# omz", encoding="utf-8")
    foreign = omz / "custom/themes/same.zsh-theme"
    foreign.parent.mkdir(parents=True)
    foreign.write_text("# user", encoding="utf-8")

    link_omega_themes(assets, omz, tmp_path / ".omega-zsh/manifest.json")

    assert foreign.read_text(encoding="utf-8") == "# user"
    assert not foreign.is_symlink()


def test_link_omega_themes_preserva_symlink_ajeno_con_manifest_corrupto(tmp_path):
    assets = tmp_path / "assets"
    themes = assets / "themes"
    themes.mkdir(parents=True)
    (themes / "same.zsh-theme").write_text("# omega", encoding="utf-8")

    omz = tmp_path / ".oh-my-zsh"
    omz.mkdir()
    (omz / "oh-my-zsh.sh").write_text("# omz", encoding="utf-8")
    foreign_target = tmp_path / "foreign.zsh-theme"
    foreign_target.write_text("# foreign", encoding="utf-8")
    foreign_link = omz / "custom/themes/same.zsh-theme"
    foreign_link.parent.mkdir(parents=True)
    foreign_link.symlink_to(foreign_target)

    manifest = tmp_path / ".omega-zsh/manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text("{broken json", encoding="utf-8")

    link_omega_themes(assets, omz, manifest)

    assert foreign_link.is_symlink()
    assert foreign_link.resolve(strict=False) == foreign_target


def test_link_omega_themes_reemplaza_symlink_propio(tmp_path):
    assets = tmp_path / "assets"
    themes = assets / "themes"
    themes.mkdir(parents=True)
    new_source = themes / "same.zsh-theme"
    new_source.write_text("# omega", encoding="utf-8")

    omz = tmp_path / ".oh-my-zsh"
    omz.mkdir()
    (omz / "oh-my-zsh.sh").write_text("# omz", encoding="utf-8")
    old_source = tmp_path / "old.zsh-theme"
    old_source.write_text("# old", encoding="utf-8")
    owned_link = omz / "custom/themes/same.zsh-theme"
    owned_link.parent.mkdir(parents=True)
    owned_link.symlink_to(old_source)

    manifest = tmp_path / ".omega-zsh/manifest.json"
    record_managed_file(
        manifest,
        owned_link,
        "theme_symlink",
        "created",
        {"source": str(new_source)},
    )

    link_omega_themes(assets, omz, manifest)

    assert owned_link.is_symlink()
    assert owned_link.resolve(strict=False) == new_source


def test_link_omega_themes_omite_omz_inexistente(tmp_path):
    assets = tmp_path / "assets"
    themes = assets / "themes"
    themes.mkdir(parents=True)
    (themes / "same.zsh-theme").write_text("# omega", encoding="utf-8")
    omz = tmp_path / ".oh-my-zsh"

    warnings = link_omega_themes(assets, omz, tmp_path / ".omega-zsh/manifest.json")

    assert "Oh My Zsh no encontrado" in warnings[0]
    assert not (omz / "custom" / "themes").exists()


def test_first_run_detects_empty_setup(tmp_path):
    with patch("omega_zsh.ui.app.SystemContext"), patch("omega_zsh.ui.app.StateManager"):
        app = OmegaApp()
        app.state_manager.config_path = tmp_path / ".omega-zsh" / "state.json"
        app.context.zshrc_path = tmp_path / ".zshrc"

        assert app._detect_first_run() is True


def test_first_run_disabled_when_zshrc_exists(tmp_path):
    zshrc = tmp_path / ".zshrc"
    zshrc.write_text("# user config", encoding="utf-8")

    with patch("omega_zsh.ui.app.SystemContext"), patch("omega_zsh.ui.app.StateManager"):
        app = OmegaApp()
        app.state_manager.config_path = tmp_path / ".omega-zsh" / "state.json"
        app.context.zshrc_path = zshrc

        assert app._detect_first_run() is False


def test_first_run_minimal_saves_state_without_apply():
    with (
        patch("omega_zsh.ui.app.SystemContext"),
        patch("omega_zsh.ui.app.StateManager"),
        patch("omega_zsh.ui.app.apply_config") as mock_apply,
    ):
        app = OmegaApp()
        app.state = AppState(
            selected_plugins=["zoxide", "eza"],
            allowed_custom_plugins=["local-plugin"],
            selected_theme="bira",
            selected_header="fastfetch",
        )
        app.state_manager = MagicMock()
        app.notify = MagicMock()

        app.action_first_run_minimal()

        saved_state = app.state_manager.save.call_args.args[0]
        assert saved_state.selected_plugins == []
        assert saved_state.allowed_custom_plugins == ["local-plugin"]
        assert saved_state.selected_theme == "robbyrussell"
        assert saved_state.selected_header == "none"
        mock_apply.assert_not_called()


def test_plugin_select_status_labels(tmp_path, monkeypatch):
    context = MagicMock()
    context.package_manager_type = "apt"
    context.omz_dir = tmp_path / ".oh-my-zsh"
    (context.omz_dir / "custom" / "plugins" / "zsh-autosuggestions").mkdir(parents=True)
    screen = PluginSelectScreen([], [], [])
    monkeypatch.setattr(
        "omega_zsh.ui.screens.shutil.which", lambda cmd: "/bin/fd" if cmd == "fdfind" else None
    )

    assert "installed" in screen._label_for("zsh-autosuggestions", context)
    assert "impact: medium" in screen._label_for("zsh-autosuggestions", context)
    assert "installed" in screen._label_for("fd", context)
    assert "missing" in screen._label_for("zoxide", context)
    assert "unmanaged" in screen._label_for("git", context)
