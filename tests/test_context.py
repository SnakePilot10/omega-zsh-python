import pytest
from unittest.mock import patch, MagicMock

from omega_zsh.core.context import SystemContext


@pytest.fixture(autouse=True)
def reset_singleton():
    """Resetea la instancia Singleton de SystemContext antes de cada test."""
    SystemContext._instance = None


def test_singleton_instance():
    ctx1 = SystemContext()
    ctx2 = SystemContext()
    assert ctx1 is ctx2


@patch("platform.system")
@patch("omega_zsh.core.context.shlex.split")
@patch("omega_zsh.core.context.subprocess.check_output")
def test_detect_termux(mock_check, mock_split, mock_platform):
    mock_platform.return_value = "Linux"
    mock_check.return_value = ""

    # Mockeamos os.environ manualmente para evitar efectos secundarios
    env = {"PREFIX": "/data/data/com.termux/files/usr", "ANDROID_ROOT": "/system"}

    with (
        patch.dict("os.environ", env, clear=True),
        patch(
            "shutil.which",
            side_effect=lambda x: "/usr/bin/nala" if x == "nala" else None,
        ),
    ):
        ctx = SystemContext()
        assert ctx.is_termux is True
        assert ctx.is_android is True
        assert ctx.package_manager_type == "nala"


@patch("platform.system")
@patch.dict("os.environ", {}, clear=True)
def test_detect_linux_debian(mock_platform):
    mock_platform.return_value = "Linux"

    # Mocking Path.exists and open for /etc/os-release
    def mock_exists(self):
        return str(self) == "/etc/os-release"

    with (
        patch("pathlib.Path.exists", mock_exists),
        patch(
            "builtins.open",
            MagicMock(
                side_effect=[
                    MagicMock(__enter__=lambda s: ["ID=debian\n", "VERSION_ID=12\n"])
                ]
            ),
        ),
    ):
        with patch(
            "shutil.which", side_effect=lambda x: "/usr/bin/apt" if x == "apt" else None
        ):
            ctx = SystemContext()
            assert ctx.distro_id == "debian"
            assert ctx.package_manager_type == "apt"


@patch("platform.system")
@patch.dict("os.environ", {"ANDROID_ROOT": "/system"}, clear=True)
@patch("omega_zsh.core.context.subprocess.check_output")
def test_detect_android_gsi(mock_check_output, mock_platform):
    mock_platform.return_value = "Linux"

    def side_effect(args, **kwargs):
        if "ro.build.flavor" in args:
            return "aosp_arm64-userdebug"
        return ""

    mock_check_output.side_effect = side_effect

    ctx = SystemContext()
    assert ctx.is_android is True
    assert ctx.is_gsi is True


@patch("platform.system")
def test_detect_arch_linux(mock_platform):
    mock_platform.return_value = "Linux"

    with (
        patch.dict("os.environ", {}, clear=True),
        patch("pathlib.Path.exists", return_value=True),
        patch(
            "builtins.open",
            MagicMock(side_effect=[MagicMock(__enter__=lambda s: ["ID=arch\n"])]),
        ),
    ):
        with patch(
            "shutil.which",
            side_effect=lambda x: "/usr/bin/pacman" if x == "pacman" else None,
        ):
            ctx = SystemContext()
            assert ctx.distro_id == "arch"
            assert ctx.package_manager_type == "pacman"


@patch("platform.system")
def test_detect_fedora(mock_platform):
    mock_platform.return_value = "Linux"
    with (
        patch.dict("os.environ", {}, clear=True),
        patch("pathlib.Path.exists", return_value=True),
        patch(
            "builtins.open",
            MagicMock(side_effect=[MagicMock(__enter__=lambda s: ["ID=fedora\n"])]),
        ),
    ):
        with patch(
            "shutil.which", side_effect=lambda x: "/usr/bin/dnf" if x == "dnf" else None
        ):
            ctx = SystemContext()
            assert ctx.package_manager_type == "dnf"


@patch("platform.system")
def test_detect_fallback(mock_platform):
    mock_platform.return_value = "Linux"
    with (
        patch.dict("os.environ", {}, clear=True),
        patch("pathlib.Path.exists", return_value=False),
    ):
        with patch(
            "shutil.which", side_effect=lambda x: "/usr/bin/apk" if x == "apk" else None
        ):
            ctx = SystemContext()
            assert ctx.package_manager_type == "apk"


def test_repr():
    ctx = SystemContext()
    representation = repr(ctx)
    assert "SystemContext" in representation


@patch("omega_zsh.core.context.subprocess.check_output")
def test_run_cmd_error(mock_check_output):
    mock_check_output.side_effect = Exception("Fail")
    ctx = SystemContext()
    # Forzar ejecución de _run_cmd
    result = ctx._run_cmd("invalid-command")
    assert result == ""
