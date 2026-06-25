from unittest.mock import MagicMock

import pytest

from omega_zsh.core.constants import EXTERNAL_URLS
from omega_zsh.core.installer import PluginInstaller
from omega_zsh.platforms.base import BasePlatform


class MockPlatform(BasePlatform):
    def install_package(self, package, on_progress=None):
        pass

    def update_repos(self):
        pass

    def get_essential_tools(self):
        return ["git"]


@pytest.fixture
def installer(tmp_path):
    platform = MockPlatform()
    return PluginInstaller(platform, home_dir=tmp_path)


def test_ensure_omz_clones(installer):
    """Prueba que si no existe OMZ, intenta clonarlo"""
    # Mockeamos _git_clone para no llamar a git real
    installer._git_clone = MagicMock()

    # Callback dummy
    def cb(x):
        pass

    installer.ensure_omz(cb)

    installer._git_clone.assert_called_once()
    args = installer._git_clone.call_args[0]
    assert "ohmyzsh" in args[0]
    assert ".oh-my-zsh" in str(args[1])


def test_install_plugin_external(installer):
    """Prueba la instalación de un plugin externo (Git)"""
    # Usamos un plugin real de la lista de constantes
    plugin_id = "zsh-autosuggestions"
    # Aseguramos que esté en EXTERNAL_URLS para que la lógica lo detecte
    EXTERNAL_URLS[plugin_id] = "https://github.com/foo/bar.git"

    installer._git_clone = MagicMock()

    def cb(x):
        pass

    installer.install_all([plugin_id], cb)

    installer._git_clone.assert_called()
    args = installer._git_clone.call_args[0]
    assert args[0] == "https://github.com/foo/bar.git"
    assert plugin_id in str(args[1])


def test_install_plugin_binary(installer):
    """Prueba la instalación de un plugin binario (e.g., fzf)"""
    plugin_id = "fzf"

    installer.platform.install_package = MagicMock()

    def cb(x):
        pass

    installer.install_all([plugin_id], cb)

    installer.platform.install_package.assert_called_with(plugin_id, on_progress=cb)


def test_install_binary_uses_catalog_package_name_for_platform(tmp_path):
    platform = MockPlatform()
    platform.pkg_mgr = "apt-get"
    platform.install_package = MagicMock(return_value=True)
    installer = PluginInstaller(platform, home_dir=tmp_path)

    assert installer.install_binary("fd")

    args, kwargs = platform.install_package.call_args
    assert args[0] == "fd-find"
    assert callable(kwargs["on_progress"])


def test_install_binary_uses_catalog_fortune_package_on_debian(tmp_path):
    platform = MockPlatform()
    platform.pkg_mgr = "apt-get"
    platform.install_package = MagicMock(return_value=True)
    installer = PluginInstaller(platform, home_dir=tmp_path)

    assert installer.install_binary("fortune")

    args, kwargs = platform.install_package.call_args
    assert args[0] == "fortune-mod"
    assert callable(kwargs["on_progress"])


def test_install_all_result_reports_installed_skipped_and_failed(tmp_path):
    platform = MockPlatform()
    platform.pkg_mgr = "apt-get"
    platform.install_package = MagicMock(side_effect=lambda package, on_progress=None: package != "fd-find")
    installer = PluginInstaller(platform, home_dir=tmp_path)
    messages = []

    result = installer.install_all_result(["zoxide", "fd", "git", "typo-plugin"], messages.append)

    assert not result.ok
    assert result.installed == ["zoxide"]
    assert result.failed == ["fd"]
    assert result.skipped == ["git", "typo-plugin"]
    assert "ID desconocido omitido: typo-plugin" in messages


def test_install_all_keeps_bool_compatibility(tmp_path):
    platform = MockPlatform()
    platform.pkg_mgr = "apt-get"
    platform.install_package = MagicMock(return_value=True)
    installer = PluginInstaller(platform, home_dir=tmp_path)

    assert installer.install_all(["zoxide"], lambda message: None)
