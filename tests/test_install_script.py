import subprocess
from pathlib import Path


INSTALL_SH = Path(__file__).parent.parent / "install.sh"


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
