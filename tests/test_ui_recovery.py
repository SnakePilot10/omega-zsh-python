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
