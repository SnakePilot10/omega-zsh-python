from unittest.mock import MagicMock, patch

from omega_zsh.ui.screens import ProblemsScreen


def test_problems_screen_renders_only_non_ok_checks():
    screen = ProblemsScreen()
    report = {
        "overall": "warning",
        "checks": [
            {"id": "zsh", "severity": "ok", "message": "zsh disponible", "detail": "/bin/zsh"},
            {
                "id": "oh-my-zsh",
                "severity": "error",
                "message": "directorio Oh My Zsh no existe",
                "detail": "/tmp/home/.oh-my-zsh",
            },
        ],
    }

    lines = screen._render_report(report)

    rendered = "\n".join(lines)
    assert "overall: warning" in rendered
    assert "oh-my-zsh" in rendered
    assert "zsh disponible" not in rendered


def test_problems_screen_runs_read_only_doctor():
    screen = ProblemsScreen()
    screen._write_log = MagicMock()
    screen._notify = MagicMock()

    with patch("omega_zsh.ui.screens.SystemContext"), \
         patch("omega_zsh.ui.screens.run_doctor") as mock_doctor:
        mock_doctor.return_value = {"overall": "ok", "checks": []}

        screen._run_doctor()

        mock_doctor.assert_called_once()
        screen._notify.assert_called_with("Doctor complete: ok", severity=None)


def test_problems_screen_runs_explicit_doctor_fix():
    screen = ProblemsScreen()
    screen._write_log = MagicMock()
    screen._notify = MagicMock()

    with patch("omega_zsh.ui.screens.SystemContext"), \
         patch("omega_zsh.ui.screens.run_doctor_fix") as mock_fix:
        mock_fix.return_value = {
            "fixes": [{"id": "manifest", "status": "fixed", "message": "ok", "detail": "x"}],
            "report": {"overall": "warning", "checks": []},
        }

        screen._run_doctor_fix()

        mock_fix.assert_called_once()
        screen._notify.assert_called_with("Doctor fix complete: warning", severity=None)
