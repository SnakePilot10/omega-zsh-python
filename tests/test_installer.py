import pytest
from unittest.mock import MagicMock
from omega_zsh.core.installer import PluginInstaller
from omega_zsh.platforms.base import BasePlatform
from omega_zsh.core.constants import BIN_PLUGINS, EXTERNAL_URLS

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
    # Aseguramos que sea binario
    if plugin_id not in BIN_PLUGINS:
        BIN_PLUGINS.append(plugin_id)
        
    installer.platform.install_package = MagicMock()
    def cb(x):
        pass
    
    installer.install_all([plugin_id], cb)
    
    installer.platform.install_package.assert_called_with(plugin_id, on_progress=cb)
