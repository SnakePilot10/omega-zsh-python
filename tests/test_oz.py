from pathlib import Path
from unittest.mock import patch
from omega_zsh.cli.oz_tool import get_active_plugins, inspect_plugin


def test_get_active_plugins_empty(tmp_path):
    """Verifica que devuelve lista vacía si no hay .zshrc"""
    with patch("omega_zsh.cli.oz_tool.ZSHRC", tmp_path / "nonexistent"):
        plugins = get_active_plugins()
        assert plugins == []


def test_get_active_plugins_parse(tmp_path):
    """Verifica que extrae plugins correctamente del .zshrc"""
    zshrc = tmp_path / ".zshrc"
    zshrc.write_text("plugins=(git python docker\n  zsh-autosuggestions)")

    with patch("omega_zsh.cli.oz_tool.ZSHRC", zshrc):
        plugins = get_active_plugins()
        assert "git" in plugins
        assert "python" in plugins
        assert "zsh-autosuggestions" in plugins
        assert len(plugins) == 4


def test_inspect_plugin_not_found():
    """Verifica el comportamiento cuando un plugin no existe"""
    with (
        patch("omega_zsh.cli.oz_tool.CUSTOM_PLUGINS", Path("/tmp/fake")),
        patch("omega_zsh.cli.oz_tool.STANDARD_PLUGINS", Path("/tmp/fake2")),
    ):
        info = inspect_plugin("non-existent-plugin")
        assert info["found"] is False


def test_inspect_plugin_parsing(tmp_path):
    """Verifica que extrae alias y funciones del código del plugin"""
    plugin_dir = tmp_path / "myplugin"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "myplugin.plugin.zsh"
    plugin_file.write_text(
        "\nalias gst='git status'\nalias gp='git push'\nfunction myfunc() { echo 1 }\nother_func() { echo 2 }\n    "
    )

    # Simulamos que lo encuentra en CUSTOM_PLUGINS
    with (
        patch("omega_zsh.cli.oz_tool.CUSTOM_PLUGINS", tmp_path),
        patch("omega_zsh.cli.oz_tool.STANDARD_PLUGINS", Path("/tmp/nowhere")),
    ):
        info = inspect_plugin("myplugin")
        assert info["found"] is True
        assert "gst" in info["aliases"]
        assert "gp" in info["aliases"]
        assert "myfunc" in info["functions"]
        assert "other_func" in info["functions"]
