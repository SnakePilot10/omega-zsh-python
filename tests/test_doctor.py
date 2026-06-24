import json

from omega_zsh.core.context import SystemContext
from omega_zsh.core.doctor import run_doctor, run_doctor_fix


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


def test_doctor_fix_creates_only_low_risk_missing_files(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    context = SystemContext(home=home, env={})
    monkeypatch.setattr("omega_zsh.core.doctor.which", lambda command: None)

    result = run_doctor_fix(context)
    fix_status = {fix["id"]: fix["status"] for fix in result["fixes"]}

    assert fix_status["omega-dir"] == "fixed"
    assert fix_status["manifest"] == "fixed"
    assert fix_status["zshrc"] == "fixed"
    assert context.omega_dir.is_dir()
    assert json.loads((context.omega_dir / "manifest.json").read_text(encoding="utf-8"))["files"]
    assert context.zshrc_path.read_text(encoding="utf-8").startswith(
        "# Created by Omega-ZSH doctor --fix"
    )
    assert _check(result["report"], ".zshrc")["status"] == "ok"


def test_doctor_fix_preserves_existing_zshrc(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    zshrc = home / ".zshrc"
    zshrc.write_text("# user config\n", encoding="utf-8")
    context = SystemContext(home=home, env={})
    monkeypatch.setattr("omega_zsh.core.doctor.which", lambda command: None)

    result = run_doctor_fix(context)

    assert zshrc.read_text(encoding="utf-8") == "# user config\n"
    assert _check({"checks": result["fixes"]}, "zshrc")["status"] == "skipped"


def test_doctor_fix_backs_up_corrupt_manifest_before_repair(tmp_path, monkeypatch):
    home = tmp_path / "home"
    omega_dir = home / ".omega-zsh"
    omega_dir.mkdir(parents=True)
    manifest = omega_dir / "manifest.json"
    manifest.write_text("{ invalid json", encoding="utf-8")
    context = SystemContext(home=home, env={})
    monkeypatch.setattr("omega_zsh.core.doctor.which", lambda command: None)

    result = run_doctor_fix(context)

    assert _check({"checks": result["fixes"]}, "manifest")["status"] == "fixed"
    assert json.loads(manifest.read_text(encoding="utf-8"))["files"]
    backups = list((omega_dir / "backups").glob("manifest.json.*.bak"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "{ invalid json"


def test_doctor_fix_does_not_create_zshrc_without_manifest_ready(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    (home / ".omega-zsh").write_text("not a directory", encoding="utf-8")
    context = SystemContext(home=home, env={})
    monkeypatch.setattr("omega_zsh.core.doctor.which", lambda command: None)

    result = run_doctor_fix(context)

    assert _check({"checks": result["fixes"]}, "omega-dir")["status"] == "failed"
    assert _check({"checks": result["fixes"]}, "zshrc")["status"] == "skipped"
    assert not context.zshrc_path.exists()
