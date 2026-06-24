import json

from omega_zsh.core.context import SystemContext
from omega_zsh.core.doctor import run_doctor


def _check(report, check_id):
    return next(check for check in report["checks"] if check["id"] == check_id)


def test_doctor_reports_expected_installation_checks(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    omz = home / ".oh-my-zsh"
    omz.mkdir()
    (omz / "oh-my-zsh.sh").write_text("# omz\n", encoding="utf-8")
    (home / ".zshrc").write_text("plugins=(git)\n", encoding="utf-8")
    omega_dir = home / ".omega-zsh"
    omega_dir.mkdir()
    (omega_dir / "manifest.json").write_text(json.dumps({"files": []}), encoding="utf-8")
    (omega_dir / "state.json").write_text(
        json.dumps(
            {
                "selected_plugins": ["zoxide", "zsh-autosuggestions"],
                "selected_theme": "missing-theme",
                "selected_header": "none",
            }
        ),
        encoding="utf-8",
    )
    context = SystemContext(home=home, env={"ZSH": str(omz)})

    def fake_which(command):
        return f"/usr/bin/{command}" if command in {"zsh", "git"} else None

    monkeypatch.setattr("omega_zsh.core.doctor.which", fake_which)

    report = run_doctor(context)

    assert report["overall"] == "warning"
    assert _check(report, "zsh")["status"] == "ok"
    assert _check(report, "git")["status"] == "ok"
    assert _check(report, "oh-my-zsh")["status"] == "ok"
    assert _check(report, "ZSH")["detail"] == str(omz)
    assert _check(report, ".zshrc")["status"] == "ok"
    assert _check(report, "manifest")["status"] == "ok"
    assert _check(report, "binary-tools")["status"] == "missing"
    assert _check(report, "binary-tools")["detail"] == "zoxide"
    assert _check(report, "external-plugins")["detail"] == "zsh-autosuggestions"
    assert _check(report, "theme")["status"] == "missing"


def test_doctor_accepts_present_external_plugin_and_builtin_theme(tmp_path, monkeypatch):
    home = tmp_path / "home"
    omz = home / ".oh-my-zsh"
    plugin_dir = omz / "custom" / "plugins" / "zsh-autosuggestions"
    plugin_dir.mkdir(parents=True)
    (omz / "oh-my-zsh.sh").write_text("# omz\n", encoding="utf-8")
    omega_dir = home / ".omega-zsh"
    omega_dir.mkdir(parents=True)
    (omega_dir / "state.json").write_text(
        json.dumps(
            {
                "selected_plugins": ["zsh-autosuggestions"],
                "selected_theme": "robbyrussell",
                "selected_header": "none",
            }
        ),
        encoding="utf-8",
    )
    context = SystemContext(home=home, env={"ZSH": str(omz)})

    monkeypatch.setattr("omega_zsh.core.doctor.which", lambda command: f"/bin/{command}")

    report = run_doctor(context)

    assert _check(report, "external-plugins")["status"] == "ok"
    assert _check(report, "theme")["status"] == "ok"
