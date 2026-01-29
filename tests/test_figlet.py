import pytest

from omega_zsh.core.figlet import FigletManager

@pytest.fixture
def figlet_manager():
    return FigletManager()

def test_figlet_available(figlet_manager):
    # This might be false in CI/minimal envs, but should be true in Termux if installed
    # We just check it returns a boolean
    assert isinstance(figlet_manager.is_available(), bool)

def test_get_fonts(figlet_manager):
    fonts = figlet_manager.get_fonts()
    assert isinstance(fonts, list)
    assert len(fonts) > 0 or "standard" in fonts
    assert "standard" in fonts if not fonts else True

def test_render(figlet_manager):
    output = figlet_manager.render("Test", "standard")
    assert isinstance(output, str)
    assert len(output) > 0

def test_generate_safe_command(figlet_manager):
    cmd = figlet_manager.generate_safe_command("Hello World", "standard")
    assert "figlet" in cmd
    assert "lolcat" in cmd
    # Check for quoting
    assert "'Hello World'" in cmd or "'Hello World'" in cmd
