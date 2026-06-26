from unittest.mock import MagicMock, patch

from omega_zsh.core.recovery import RecoveryResult
from omega_zsh.ui.screens import RecoveryScreen


def test_recovery_screen_uses_core_restore_action():
    screen = RecoveryScreen()
    screen._write_log = MagicMock()
    screen._notify = MagicMock()

    with patch("omega_zsh.ui.screens.SystemContext"), \
         patch("omega_zsh.ui.screens.restore_latest_zshrc_backup") as mock_restore:
        mock_restore.return_value = RecoveryResult(
            ok=True,
            action="restore-zshrc",
            changed=["/tmp/home/.zshrc"],
            messages=["Restored .zshrc"],
        )

        screen._run_recovery("restore-zshrc")

        mock_restore.assert_called_once()
        screen._notify.assert_called_with("Restored .zshrc")


def test_recovery_screen_reports_core_errors():
    screen = RecoveryScreen()
    screen._write_log = MagicMock()
    screen._notify = MagicMock()

    with patch("omega_zsh.ui.screens.SystemContext"), \
         patch("omega_zsh.ui.screens.restore_latest_zshrc_backup") as mock_restore:
        mock_restore.return_value = RecoveryResult(
            ok=False,
            action="restore-zshrc",
            errors=["No valid .zshrc backup found."],
        )

        screen._run_recovery("restore-zshrc")

        screen._notify.assert_called_with("No valid .zshrc backup found.", severity="error")


def test_recovery_screen_restores_selected_backup(tmp_path):
    selected = tmp_path / ".zshrc.20260625-120000.bak"
    screen = RecoveryScreen()
    screen._write_log = MagicMock()
    screen._notify = MagicMock()
    screen._selected_backup = MagicMock(return_value=selected)

    with patch("omega_zsh.ui.screens.SystemContext"), \
         patch("omega_zsh.ui.screens.restore_zshrc_backup") as mock_restore:
        mock_restore.return_value = RecoveryResult(
            ok=True,
            action="restore-zshrc",
            changed=["/tmp/home/.zshrc"],
            messages=["Restored selected backup"],
        )

        screen._run_recovery("restore-zshrc")

        mock_restore.assert_called_once()
        assert mock_restore.call_args.args[0] == selected
        screen._notify.assert_called_with("Restored selected backup")
