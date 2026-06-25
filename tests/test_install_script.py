import subprocess
from pathlib import Path


INSTALL_SH = Path(__file__).parent.parent / "install.sh"


def test_install_script_syntax_ok():
    result = subprocess.run(["bash", "-n", str(INSTALL_SH)], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr


def test_install_script_requires_explicit_apply_and_theme_sync_flags():
    content = INSTALL_SH.read_text(encoding="utf-8")

    assert "APPLY_CONFIG=false" in content
    assert "SYNC_THEMES=false" in content
    assert "--apply-config" in content
    assert "--sync-themes" in content
    assert 'if [ "$APPLY_CONFIG" = true ]; then' in content
    assert 'if [ "$SYNC_THEMES" = true ]; then' in content
    assert ".zshrc no modificado" in content
    assert "Temas Omega no sincronizados" in content


def test_install_script_uses_core_apply_not_ui_for_theme_sync():
    content = INSTALL_SH.read_text(encoding="utf-8")

    assert "from omega_zsh.core.apply import link_omega_themes" in content
    assert "from omega_zsh.ui.app import link_omega_themes" not in content
