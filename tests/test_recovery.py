from omega_zsh.core.context import SystemContext
from omega_zsh.core.recovery import (
    cleanup_shell_files,
    list_zshrc_backups,
    nuclear_fix_shell,
    recovery_dry_run,
    restore_latest_zshrc_backup,
    restore_zshrc_backup,
)


def test_recovery_restore_latest_valid_zshrc_backup(tmp_path, monkeypatch):
    home = tmp_path / "home"
    backup_dir = home / ".omega-backups"
    backup_dir.mkdir(parents=True)
    backup = backup_dir / ".zshrc.20260624-120000.bak"
    backup.write_text("# restored\n", encoding="utf-8")
    current = home / ".zshrc"
    current.write_text("# broken omega-zsh\n", encoding="utf-8")
    context = SystemContext(home=home, env={})
    monkeypatch.setattr("omega_zsh.core.shell.which", lambda command: None)

    result = restore_latest_zshrc_backup(context)

    assert result.ok
    assert str(current) in result.changed
    assert result.backups
    assert current.read_text(encoding="utf-8") == "# restored\n"


def test_recovery_restore_reports_missing_backup(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    context = SystemContext(home=home, env={})
    monkeypatch.setattr("omega_zsh.core.shell.which", lambda command: None)

    result = restore_latest_zshrc_backup(context)

    assert not result.ok
    assert result.errors == ["No valid .zshrc backup found."]


def test_recovery_lists_valid_zshrc_backups_newest_first(tmp_path, monkeypatch):
    home = tmp_path / "home"
    backup_dir = home / ".omega-backups"
    backup_dir.mkdir(parents=True)
    older = backup_dir / ".zshrc.20260624-120000.bak"
    newer = backup_dir / ".zshrc.20260625-120000.bak"
    bad = backup_dir / ".zshrc.20260626-120000.bak"
    older.write_text("# older\n", encoding="utf-8")
    newer.write_text("# newer\n", encoding="utf-8")
    bad.write_text("# bad\n", encoding="utf-8")
    older.touch()
    newer.touch()
    context = SystemContext(home=home, env={})

    def fake_validate(path):
        return (path != bad, "")

    monkeypatch.setattr("omega_zsh.core.recovery.validate_zsh_syntax", fake_validate)

    backups = list_zshrc_backups(context)

    assert backups == [newer, older]


def test_recovery_restores_selected_zshrc_backup(tmp_path, monkeypatch):
    home = tmp_path / "home"
    backup_dir = home / ".omega-backups"
    backup_dir.mkdir(parents=True)
    selected = backup_dir / ".zshrc.20260625-120000.bak"
    selected.write_text("# selected\n", encoding="utf-8")
    current = home / ".zshrc"
    current.write_text("# current\n", encoding="utf-8")
    context = SystemContext(home=home, env={})
    monkeypatch.setattr("omega_zsh.core.recovery.validate_zsh_syntax", lambda path: (True, ""))

    result = restore_zshrc_backup(selected, context)

    assert result.ok
    assert current.read_text(encoding="utf-8") == "# selected\n"
    assert result.backups


def test_cleanup_shell_files_backs_up_and_removes_omega_lines(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    zshrc = home / ".zshrc"
    zshrc.write_text("keep=1\n# omega-zsh generated\nafter=1\n", encoding="utf-8")
    context = SystemContext(home=home, env={})

    result = cleanup_shell_files(context)

    assert result.ok
    assert str(zshrc) in result.changed
    assert result.backups
    assert zshrc.read_text(encoding="utf-8") == "keep=1\nafter=1\n"


def test_nuclear_fix_backs_up_and_writes_minimal_shell_files(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    (home / ".zshrc").write_text("old\n", encoding="utf-8")
    context = SystemContext(home=home, env={})

    result = nuclear_fix_shell(context)

    assert result.ok
    assert result.backups
    assert "rebuilt by Omega ZSH recovery" in (home / ".zshrc").read_text(encoding="utf-8")
    assert (home / ".bashrc").exists()
    assert (home / ".profile").exists()


def test_recovery_dry_run_does_not_modify_files(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    zshrc = home / ".zshrc"
    zshrc.write_text("# omega-zsh\n", encoding="utf-8")
    context = SystemContext(home=home, env={})

    result = recovery_dry_run(context)

    assert result.ok
    assert "Would remove Omega references" in "\n".join(result.messages)
    assert zshrc.read_text(encoding="utf-8") == "# omega-zsh\n"
    assert not (home / ".omega-zsh-recovery").exists()
