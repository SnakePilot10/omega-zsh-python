import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from omega_zsh.core.generator import ConfigGenerator
from omega_zsh.core.installer import PluginInstaller
from omega_zsh.core.state import StateManager
from omega_zsh.platforms.base import BasePlatform
from omega_zsh.cli.oz_tool import main as oz_main

def test_generator_error_handling(tmp_path):
    """Cubre líneas de error en generator.py."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    
    gen = ConfigGenerator(templates_dir)
    with patch("jinja2.Template.render", side_effect=Exception("Template Error")):
        with patch("jinja2.Environment.get_template") as mock_get:
            mock_tmpl = MagicMock()
            mock_tmpl.render.side_effect = Exception("Template Error")
            mock_get.return_value = mock_tmpl
            
            res = gen.generate_personal_config(tmp_path / "personal.zsh", {"theme": "test"})
            assert res is False

def test_plugin_installer_git_error():
    """Cubre fallos en git clone en installer.py."""
    platform_mock = MagicMock()
    inst = PluginInstaller(platform_mock, Path("/tmp/home"))
    
    with patch("subprocess.Popen", side_effect=Exception("Git Fail")):
        on_progress = MagicMock()
        inst._git_clone("http://url", Path("/tmp/target"), on_progress)
        on_progress.assert_any_call("Error clonando http://url: Git Fail")

def test_state_manager_corrupt_json(tmp_path):
    """Cubre lectura de JSON corrupto en state.py."""
    config_dir = tmp_path / ".config"
    config_dir.mkdir()
    state_file = config_dir / "state.json"
    state_file.write_text("{corrupt json", encoding="utf-8")
    
    zshrc = tmp_path / ".zshrc"
    zshrc.write_text("ZSH_THEME=\"robbyrussell\"", encoding="utf-8")

    sm = StateManager(config_dir)
    sm.zshrc_path = zshrc
    
    state = sm.load()
    assert state.selected_theme == "robbyrussell"

def test_base_platform_abstracts():
    """Cubre la clase base de plataformas."""
    class ConcretePlatform(BasePlatform):
        def get_shell_config_path(self): return Path(".zshrc")
        def install_package(self, pkg, on_progress=None): pass
        def get_essential_tools(self): return []
        def update_repos(self, on_progress=None): pass
    
    plat = ConcretePlatform()
    assert isinstance(plat, BasePlatform)

@patch("subprocess.Popen")
def test_base_platform_run_cmd_internal(mock_popen):
    """Prueba _run_command de la clase base."""
    class ConcretePlatform(BasePlatform):
        def update_repos(self) -> bool: pass
        def install_package(self, package_name: str, on_progress=None) -> bool: pass
        def get_essential_tools(self):
            pass

    plat = ConcretePlatform()
    
    process_mock = MagicMock()
    process_mock.stdout = ["Línea 1\n"]
    process_mock.wait.return_value = 0
    mock_popen.return_value = process_mock
    
    on_progress = MagicMock()
    success = plat._run_command(["ls"], on_progress=on_progress)
    
    assert success is True
    on_progress.assert_called_with("Línea 1")

@patch("sys.argv", ["oz", "--help"])
@patch("omega_zsh.cli.oz_tool.console.print")
def test_oz_tool_help(mock_print):
    """Cubre el punto de entrada de oz_tool."""
    oz_main()
    mock_print.assert_called()