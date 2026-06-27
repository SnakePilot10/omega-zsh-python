import pytest

from omega_zsh.core.figlet import FigletManager


@pytest.fixture
def figlet_manager():
    return FigletManager()


def test_figlet_available(figlet_manager):
    assert isinstance(figlet_manager.is_available(), bool)


def test_get_fonts(figlet_manager):
    fonts = figlet_manager.get_fonts()
    assert isinstance(fonts, list)
    assert len(fonts) > 0 or "standard" in fonts


def test_render(figlet_manager):
    output = figlet_manager.render("Test", "standard")
    assert isinstance(output, str)
    assert len(output) > 0


def test_generate_safe_command_with_lolcat(figlet_manager):
    cmd = figlet_manager.generate_safe_command("Hello World", "standard")
    assert "$+commands[figlet]" in cmd
    assert "$+commands[lolcat]" in cmd
    assert "| lolcat" in cmd


def test_generate_safe_command_without_lolcat(figlet_manager):
    cmd = figlet_manager.generate_safe_command("Hello World", "standard")
    assert "|| figlet" in cmd
    assert "Hello World" in cmd
