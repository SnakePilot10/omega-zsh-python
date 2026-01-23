import pytest
import shutil
from pathlib import Path
from omega_zsh.core.generator import ConfigGenerator

@pytest.fixture
def temp_home(tmp_path):
    # Create a temporary home directory structure
    home = tmp_path / "home"
    home.mkdir()
    (home / ".oh-my-zsh").mkdir()
    return home

@pytest.fixture
def generator():
    # Templates are in omega_zsh/assets/templates relative to project root
    root = Path(__file__).parent.parent
    templates_dir = root / "omega_zsh" / "assets" / "templates"
    return ConfigGenerator(templates_dir)

def test_generate_zshrc(generator, temp_home):
    output_path = temp_home / ".zshrc"
    context = {
        "version": "1.0",
        "is_termux": True,
        "omz_dir": str(temp_home / ".oh-my-zsh"),
        "user_theme": "robbyrussell",
        "root_theme": "root_p10k_red",
        "plugins": ["git"],
        "active_tools": ["bat"],
        "personal_zsh": str(temp_home / ".omega-zsh/personal.zsh"),
        "custom_zsh": str(temp_home / ".omega-zsh/custom.zsh"),
        "header_cmd": "echo 'Hello'"
    }
    
    success = generator.generate_zshrc(output_path, context)
    assert success
    assert output_path.exists()
    content = output_path.read_text()
    assert "export ZSH" in content
    assert "robbyrussell" in content
    assert "echo 'Hello'" in content

def test_generate_personal_config(generator, temp_home):
    output_path = temp_home / ".omega-zsh" / "personal.zsh"
    context = {
        "extra_paths": ["/tmp"],
        "env_vars": {"MY_VAR": "123"},
        "aliases": {"ll": "ls -l"},
        "user": "testuser"
    }
    
    success = generator.generate_personal_config(output_path, context)
    assert success
    assert output_path.exists()
    content = output_path.read_text()
    assert "export MY_VAR=\"123\"" in content
    assert "alias ll='ls -l'" in content
