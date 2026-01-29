import pytest

from pathlib import Path
from omega_zsh.core.generator import ConfigGenerator
import omega_zsh

@pytest.fixture
def temp_home(tmp_path):
    # Create a temporary home directory structure
    home = tmp_path / "home"
    home.mkdir()
    (home / ".oh-my-zsh").mkdir()
    return home

@pytest.fixture
def generator():
    # Estrategia robusta para encontrar templates
    
    # 1. Intentar ruta relativa al repositorio (Desarrollo local / CI checkout)
    repo_root = Path(__file__).parent.parent
    source_templates = repo_root / "omega_zsh" / "assets" / "templates"
    
    if source_templates.exists():
        return ConfigGenerator(source_templates)
        
    # 2. Intentar ruta relativa al paquete instalado (si se instaló en site-packages)
    pkg_root = Path(omega_zsh.__file__).parent
    installed_templates = pkg_root / "assets" / "templates"
    
    if installed_templates.exists():
        return ConfigGenerator(installed_templates)

    # 3. Fallback para debugging
    raise FileNotFoundError(f"No se encontraron templates en {source_templates} ni en {installed_templates}")

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
    assert success, "Fallo al generar .zshrc"
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
    assert success, "Fallo al generar personal.zsh"
    assert output_path.exists()
    content = output_path.read_text()
    assert "export MY_VAR=\"123\"" in content
    assert "alias ll='ls -l'" in content