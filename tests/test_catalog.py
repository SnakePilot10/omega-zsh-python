from omega_zsh.core.constants import (
    BIN_PLUGINS,
    DB_BINARY_TOOLS,
    DB_PLUGINS,
    DB_ZSH_PLUGINS,
    binary_commands,
    binary_package_name,
    binary_supported,
    is_binary_tool,
    selected_custom_plugin_ids,
    startup_impact,
    unknown_plugin_ids,
    unsupported_binary_tools,
    valid_selected_plugins,
)


def test_catalog_splits_zsh_plugins_from_binary_tools():
    all_ids = {plugin.id for plugin in DB_PLUGINS}
    zsh_ids = {plugin.id for plugin in DB_ZSH_PLUGINS}
    binary_ids = {plugin.id for plugin in DB_BINARY_TOOLS}

    assert "zsh-autosuggestions" in zsh_ids
    assert "zoxide" in binary_ids
    assert zsh_ids.isdisjoint(binary_ids)
    assert zsh_ids | binary_ids == all_ids
    assert set(BIN_PLUGINS).issuperset(binary_ids)


def test_catalog_exposes_binary_detection_commands():
    assert is_binary_tool("fd")
    assert binary_commands("fd") == ["fd", "fdfind"]
    assert binary_commands("ripgrep") == ["rg", "ripgrep"]


def test_catalog_exposes_platform_package_names():
    assert binary_package_name("fd", "apt") == "fd-find"
    assert binary_package_name("fd", "pacman") == "fd"
    assert binary_package_name("fortune", "apt") == "fortune-mod"
    assert binary_package_name("fortune", "nala") == "fortune-mod"
    assert binary_package_name("zoxide", "apt") == "zoxide"


def test_catalog_exposes_platform_support_flags():
    assert binary_supported("lolcat", "apt")
    assert binary_supported("lolcat", "pkg")
    assert not binary_supported("lolcat", "pacman")
    assert unsupported_binary_tools(["lolcat", "zoxide"], "pacman") == ["lolcat"]


def test_catalog_validates_selected_plugin_ids():
    selected = ["git", "zsh-autosuggestions", "fd", "typo-plugin"]

    assert unknown_plugin_ids(selected) == ["typo-plugin"]
    assert valid_selected_plugins(selected) == ["git", "zsh-autosuggestions", "fd"]


def test_catalog_allows_explicit_custom_plugin_ids():
    selected = ["git", "mi-plugin", "typo-plugin"]
    allowed = ["mi-plugin"]

    assert unknown_plugin_ids(selected, allowed) == ["typo-plugin"]
    assert valid_selected_plugins(selected, allowed) == ["git", "mi-plugin"]
    assert selected_custom_plugin_ids(selected, allowed) == ["mi-plugin"]


def test_catalog_exposes_startup_impact_labels():
    assert startup_impact("fastfetch") == "high"
    assert startup_impact("zsh-autosuggestions") == "medium"
    assert startup_impact("zoxide") == "low"
    assert startup_impact("unknown") == "low"
