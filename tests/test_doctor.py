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
    (omega_dir / "manifest.json").write_text(json.dumps({"files": {}}), encoding="utf-8")
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
    assert _check(report, "ZSH")["detail"] == f"$ZSH={omz}"
    assert _check(report, ".zshrc")["status"] == "ok"
    assert _check(report, "manifest")["status"] == "ok"
    assert _check(report, "binary-tools")["status"] == "missing"
    assert "zoxide" in _check(report, "binary-tools")["detail"]
    assert "instalar:" in _check(report, "binary-tools")["detail"]
    assert "zsh-autosuggestions" in _check(report, "external-plugins")["detail"]
    assert (
        "https://github.com/zsh-users/zsh-autosuggestions.git"
        in _check(report, "external-plugins")["detail"]
    )
    assert _check(report, "theme")["status"] == "missing"


def test_doctor_read_only_does_not_create_logs(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    context = SystemContext(home=home, env={})
    monkeypatch.setattr("omega_zsh.core.doctor.which", lambda command: None)

    run_doctor(context)

    assert not (context.omega_dir / "logs").exists()


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


def test_doctor_reports_bad_zsh_env_path(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    missing_omz = home / "custom-omz"
    context = SystemContext(home=home, env={"ZSH": str(missing_omz)})
    monkeypatch.setattr("omega_zsh.core.doctor.which", lambda command: None)

    report = run_doctor(context)

    zsh_check = _check(report, "ZSH")
    omz_check = _check(report, "oh-my-zsh")
    assert zsh_check["status"] == "warning"
    assert zsh_check["message"] == "$ZSH apunta a ruta inexistente"
    assert str(missing_omz) in zsh_check["detail"]
    assert omz_check["message"] == "directorio Oh My Zsh no existe"


def test_doctor_reports_missing_omz_with_termux_hint(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    context = SystemContext(home=home, env={"PREFIX": "/data/data/com.termux/files/usr"})
    monkeypatch.setattr("omega_zsh.core.doctor.which", lambda command: None)

    report = run_doctor(context)

    omz_check = _check(report, "oh-my-zsh")
    assert omz_check["status"] == "missing"
    assert omz_check["message"] == "directorio Oh My Zsh no existe"
    assert "pkg install zsh git curl" in omz_check["detail"]
    assert str(home / ".oh-my-zsh") in omz_check["detail"]


def test_doctor_reports_missing_omz_script_inside_existing_dir(tmp_path, monkeypatch):
    home = tmp_path / "home"
    omz = home / ".oh-my-zsh"
    omz.mkdir(parents=True)
    context = SystemContext(home=home, env={})
    monkeypatch.setattr("omega_zsh.core.doctor.which", lambda command: None)

    report = run_doctor(context)

    omz_check = _check(report, "oh-my-zsh")
    assert omz_check["status"] == "missing"
    assert omz_check["message"] == "oh-my-zsh.sh no encontrado"
    assert str(omz / "oh-my-zsh.sh") in omz_check["detail"]


def test_doctor_binary_tools_accept_known_command_aliases(tmp_path, monkeypatch):
    home = tmp_path / "home"
    omega_dir = home / ".omega-zsh"
    omega_dir.mkdir(parents=True)
    (omega_dir / "state.json").write_text(
        json.dumps({"selected_plugins": ["ripgrep", "fd"], "selected_header": "none"}),
        encoding="utf-8",
    )
    context = SystemContext(home=home, env={})

    def fake_which(command):
        return f"/usr/bin/{command}" if command in {"rg", "fdfind"} else None

    monkeypatch.setattr("omega_zsh.core.doctor.which", fake_which)

    report = run_doctor(context)

    assert _check(report, "binary-tools")["status"] == "ok"


def test_doctor_reports_actionable_missing_binary_details(tmp_path, monkeypatch):
    home = tmp_path / "home"
    omega_dir = home / ".omega-zsh"
    omega_dir.mkdir(parents=True)
    (omega_dir / "state.json").write_text(
        json.dumps({"selected_plugins": ["fd"], "selected_header": "none"}),
        encoding="utf-8",
    )
    context = SystemContext(home=home, env={})
    monkeypatch.setattr("omega_zsh.core.doctor.which", lambda command: None)

    report = run_doctor(context)

    tool_check = _check(report, "binary-tools")
    assert tool_check["status"] == "missing"
    assert "fd (comando: fd/fdfind" in tool_check["detail"]
    assert "paquete: fd" in tool_check["detail"]
    assert "instalar:" in tool_check["detail"]


def test_doctor_reports_unsupported_binary_tools(tmp_path, monkeypatch):
    home = tmp_path / "home"
    omega_dir = home / ".omega-zsh"
    omega_dir.mkdir(parents=True)
    (omega_dir / "state.json").write_text(
        json.dumps({"selected_plugins": ["lolcat"], "selected_header": "none"}),
        encoding="utf-8",
    )
    context = SystemContext(home=home, env={})
    context.package_manager_type = "pacman"
    monkeypatch.setattr("omega_zsh.core.doctor.which", lambda command: None)

    report = run_doctor(context)

    unsupported_check = _check(report, "unsupported-binary-tools")
    assert unsupported_check["status"] == "warning"
    assert unsupported_check["detail"] == "lolcat"
    assert _check(report, "binary-tools")["status"] == "ok"


def test_doctor_reports_actionable_missing_external_plugin_details(tmp_path, monkeypatch):
    home = tmp_path / "home"
    omega_dir = home / ".omega-zsh"
    omega_dir.mkdir(parents=True)
    (omega_dir / "state.json").write_text(
        json.dumps({"selected_plugins": ["fzf-tab"], "selected_header": "none"}),
        encoding="utf-8",
    )
    context = SystemContext(home=home, env={"ZSH": str(home / ".oh-my-zsh")})
    monkeypatch.setattr("omega_zsh.core.doctor.which", lambda command: None)

    report = run_doctor(context)

    plugin_check = _check(report, "external-plugins")
    assert plugin_check["status"] == "missing"
    assert str(home / ".oh-my-zsh" / "custom" / "plugins" / "fzf-tab") in plugin_check["detail"]
    assert "https://github.com/Aloxaf/fzf-tab.git" in plugin_check["detail"]


def test_doctor_reports_unknown_selected_ids(tmp_path, monkeypatch):
    home = tmp_path / "home"
    omega_dir = home / ".omega-zsh"
    omega_dir.mkdir(parents=True)
    (omega_dir / "state.json").write_text(
        json.dumps({"selected_plugins": ["git", "typo-plugin"], "selected_header": "none"}),
        encoding="utf-8",
    )
    context = SystemContext(home=home, env={})
    monkeypatch.setattr("omega_zsh.core.doctor.which", lambda command: None)

    report = run_doctor(context)

    unknown_check = _check(report, "unknown-selected-ids")
    assert unknown_check["status"] == "warning"
    assert unknown_check["detail"] == "typo-plugin"


def test_doctor_reports_allowed_custom_plugin_status(tmp_path, monkeypatch):
    home = tmp_path / "home"
    omega_dir = home / ".omega-zsh"
    omega_dir.mkdir(parents=True)
    omz = home / ".oh-my-zsh"
    custom_plugin = omz / "custom" / "plugins" / "mi-plugin"
    custom_plugin.mkdir(parents=True)
    (omz / "oh-my-zsh.sh").write_text("# omz\n", encoding="utf-8")
    (omega_dir / "state.json").write_text(
        json.dumps(
            {
                "selected_plugins": ["git", "mi-plugin"],
                "allowed_custom_plugins": ["mi-plugin"],
                "selected_header": "none",
            }
        ),
        encoding="utf-8",
    )
    context = SystemContext(home=home, env={"ZSH": str(omz)})
    monkeypatch.setattr("omega_zsh.core.doctor.which", lambda command: None)

    report = run_doctor(context)

    assert _check(report, "unknown-selected-ids")["status"] == "ok"
    custom_check = _check(report, "custom-plugins")
    assert custom_check["status"] == "ok"
    assert custom_check["detail"] == "mi-plugin"


def test_doctor_warns_when_allowed_custom_plugin_is_missing(tmp_path, monkeypatch):
    home = tmp_path / "home"
    omega_dir = home / ".omega-zsh"
    omega_dir.mkdir(parents=True)
    (omega_dir / "state.json").write_text(
        json.dumps(
            {
                "selected_plugins": ["mi-plugin"],
                "allowed_custom_plugins": ["mi-plugin"],
                "selected_header": "none",
            }
        ),
        encoding="utf-8",
    )
    context = SystemContext(home=home, env={})
    monkeypatch.setattr("omega_zsh.core.doctor.which", lambda command: None)

    report = run_doctor(context)

    custom_check = _check(report, "custom-plugins")
    assert custom_check["status"] == "warning"
    assert custom_check["detail"] == "mi-plugin"


def test_doctor_reports_corrupt_manifest_without_rewriting(tmp_path, monkeypatch):
    home = tmp_path / "home"
    omega_dir = home / ".omega-zsh"
    omega_dir.mkdir(parents=True)
    manifest = omega_dir / "manifest.json"
    manifest.write_text("{ invalid json", encoding="utf-8")
    context = SystemContext(home=home, env={})
    monkeypatch.setattr("omega_zsh.core.doctor.which", lambda command: None)

    report = run_doctor(context)

    manifest_check = _check(report, "manifest")
    assert manifest_check["status"] == "warning"
    assert manifest_check["message"] == "manifest corrupto"
    assert manifest.read_text(encoding="utf-8") == "{ invalid json"


def test_doctor_reports_invalid_manifest_schema_without_rewriting(tmp_path, monkeypatch):
    home = tmp_path / "home"
    omega_dir = home / ".omega-zsh"
    omega_dir.mkdir(parents=True)
    manifest = omega_dir / "manifest.json"
    manifest.write_text(json.dumps({"files": []}), encoding="utf-8")
    context = SystemContext(home=home, env={})
    monkeypatch.setattr("omega_zsh.core.doctor.which", lambda command: None)

    report = run_doctor(context)

    manifest_check = _check(report, "manifest")
    assert manifest_check["status"] == "warning"
    assert manifest_check["message"] == "manifest schema inválido"
    assert json.loads(manifest.read_text(encoding="utf-8"))["files"] == []


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
    assert (context.omega_dir / "logs" / "doctor-fix.log").exists()


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


def test_doctor_fix_restores_latest_valid_zshrc_backup_before_minimal_file(tmp_path, monkeypatch):
    home = tmp_path / "home"
    backup_dir = home / ".omega-backups"
    backup_dir.mkdir(parents=True)
    backup = backup_dir / ".zshrc.20260624-120000.bak"
    backup.write_text("# restored config\n", encoding="utf-8")
    context = SystemContext(home=home, env={})
    monkeypatch.setattr("omega_zsh.core.doctor.which", lambda command: None)

    result = run_doctor_fix(context)

    zshrc_fix = _check({"checks": result["fixes"]}, "zshrc")
    assert zshrc_fix["status"] == "fixed"
    assert zshrc_fix["message"] == ".zshrc restaurado desde backup válido"
    assert context.zshrc_path.read_text(encoding="utf-8") == "# restored config\n"
