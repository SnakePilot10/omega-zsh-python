import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from omega_zsh.core import bootstrap
from omega_zsh.platforms.arch import ArchPlatform
from omega_zsh.platforms.debian import DebianPlatform
from omega_zsh.platforms.termux import TermuxPlatform

INSTALL_SH = Path(__file__).parent.parent / "install.sh"


def _ctx(tmp_path, package_manager_type="apt", is_termux=False):
    home = tmp_path / "home"
    return SimpleNamespace(
        home=home,
        omega_dir=home / ".omega-zsh",
        assets_dir=tmp_path / "assets",
        omz_dir=home / ".oh-my-zsh",
        package_manager_type=package_manager_type,
        is_termux=is_termux,
    )


def test_make_platform_selects_package_manager_specific_platform(tmp_path):
    assert isinstance(bootstrap.make_platform(_ctx(tmp_path, "apt")), DebianPlatform)
    assert isinstance(bootstrap.make_platform(_ctx(tmp_path, "nala")), DebianPlatform)
    assert isinstance(bootstrap.make_platform(_ctx(tmp_path, "pacman")), ArchPlatform)
    assert isinstance(
        bootstrap.make_platform(_ctx(tmp_path, "pkg", is_termux=True)), TermuxPlatform
    )


def test_make_platform_rejects_unsupported_package_manager(tmp_path):
    try:
        bootstrap.make_platform(_ctx(tmp_path, "dnf"))
    except RuntimeError as exc:
        assert "Package manager no soportado: dnf" in str(exc)
    else:
        raise AssertionError("unsupported package manager did not fail")


def test_bootstrap_ensures_omz_before_installing_plugins(monkeypatch, tmp_path):
    ctx = _ctx(tmp_path)
    state = SimpleNamespace(selected_plugins=["zsh-autosuggestions"])
    installer = MagicMock()
    installer.ensure_omz.return_value = True
    installer.install_all_result.return_value = SimpleNamespace(ok=True)

    monkeypatch.setattr(sys, "argv", ["bootstrap", "--unattended"])
    monkeypatch.setattr(bootstrap, "detect_os", lambda: "debian")
    monkeypatch.setattr(bootstrap, "install_core_packages", lambda os_id: None)
    monkeypatch.setattr(bootstrap, "setup_venv", lambda project_dir: tmp_path / ".venv")
    monkeypatch.setattr(bootstrap.subprocess, "run", MagicMock())
    monkeypatch.setattr(bootstrap, "SystemContext", lambda: ctx)
    monkeypatch.setattr(bootstrap, "PluginInstaller", MagicMock(return_value=installer))
    monkeypatch.setattr(
        bootstrap, "StateManager", MagicMock(return_value=SimpleNamespace(load=lambda: state))
    )

    bootstrap.main()

    installer.ensure_omz.assert_called_once()
    installer.install_all_result.assert_called_once_with(
        state.selected_plugins, installer.ensure_omz.call_args[0][0]
    )
    call_names = [call[0] for call in installer.mock_calls]
    assert call_names.index("ensure_omz") < call_names.index("install_all_result")


def test_bootstrap_aborts_when_ensure_omz_fails(monkeypatch, tmp_path):
    ctx = _ctx(tmp_path)
    state = SimpleNamespace(selected_plugins=["zsh-autosuggestions"])
    installer = MagicMock()
    installer.ensure_omz.return_value = False

    monkeypatch.setattr(sys, "argv", ["bootstrap", "--unattended"])
    monkeypatch.setattr(bootstrap, "detect_os", lambda: "debian")
    monkeypatch.setattr(bootstrap, "install_core_packages", lambda os_id: None)
    monkeypatch.setattr(bootstrap, "setup_venv", lambda project_dir: tmp_path / ".venv")
    monkeypatch.setattr(bootstrap.subprocess, "run", MagicMock())
    monkeypatch.setattr(bootstrap, "SystemContext", lambda: ctx)
    monkeypatch.setattr(bootstrap, "PluginInstaller", MagicMock(return_value=installer))
    monkeypatch.setattr(
        bootstrap, "StateManager", MagicMock(return_value=SimpleNamespace(load=lambda: state))
    )

    with pytest.raises(SystemExit) as exc:
        bootstrap.main()

    assert exc.value.code == 1
    installer.ensure_omz.assert_called_once()
    installer.install_all_result.assert_not_called()


def test_bootstrap_sync_themes_and_apply_config(monkeypatch, tmp_path):
    ctx = _ctx(tmp_path)
    state = SimpleNamespace(selected_plugins=[])
    installer = MagicMock()
    installer.ensure_omz.return_value = True
    installer.install_all_result.return_value = SimpleNamespace(ok=True)
    link_omega_themes = MagicMock(return_value=[])
    apply_config = MagicMock(return_value=SimpleNamespace(ok=True, message="ok"))

    monkeypatch.setattr(
        sys, "argv", ["bootstrap", "--unattended", "--sync-themes", "--apply-config"]
    )
    monkeypatch.setattr(bootstrap, "detect_os", lambda: "debian")
    monkeypatch.setattr(bootstrap, "install_core_packages", lambda os_id: None)
    monkeypatch.setattr(bootstrap, "setup_venv", lambda project_dir: tmp_path / ".venv")
    monkeypatch.setattr(bootstrap.subprocess, "run", MagicMock())
    monkeypatch.setattr(bootstrap, "SystemContext", lambda: ctx)
    monkeypatch.setattr(bootstrap, "PluginInstaller", MagicMock(return_value=installer))
    monkeypatch.setattr(
        bootstrap, "StateManager", MagicMock(return_value=SimpleNamespace(load=lambda: state))
    )
    monkeypatch.setattr(bootstrap, "link_omega_themes", link_omega_themes)
    monkeypatch.setattr(bootstrap, "apply_config", apply_config)

    bootstrap.main()

    link_omega_themes.assert_called_once()
    assert link_omega_themes.call_args[0][0] == ctx.assets_dir
    assert link_omega_themes.call_args[0][1] == ctx.omz_dir
    apply_config.assert_called_once_with(ctx, state)


def test_install_script_syntax_ok():
    result = subprocess.run(["bash", "-n", str(INSTALL_SH)], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr


def test_install_script_delegates_flags_to_bootstrap():
    result = subprocess.run(
        ["bash", str(INSTALL_SH), "--apply-config", "--separation-smoke"],
        env={"HOME": "/tmp", "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "APPLY_CONFIG=true" in result.stdout
    assert "SYNC_THEMES=false" in result.stdout


def test_install_script_separation_smoke_does_not_write_shell_files(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    result = subprocess.run(
        ["bash", str(INSTALL_SH), "--unattended", "--separation-smoke"],
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "APPLY_CONFIG=false" in result.stdout
    assert "SYNC_THEMES=false" in result.stdout
    assert not (home / ".zshrc").exists()
    assert not (home / ".oh-my-zsh" / "custom" / "themes").exists()
    assert not (home / ".config" / "omega-zsh").exists()
