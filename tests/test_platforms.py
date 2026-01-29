from unittest.mock import patch
from omega_zsh.platforms.termux import TermuxPlatform
from omega_zsh.platforms.debian import DebianPlatform

# Helper para mockear Popen context manager
class MockPopen:
    def __init__(self, *args, **kwargs):
        self.stdout = []
        self.returncode = 0
    def wait(self):
        return 0
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass

def test_termux_install_command():
    """Verifica que Termux construye el comando 'pkg install'"""
    plat = TermuxPlatform()
    
    with patch("subprocess.Popen", side_effect=MockPopen) as mock_popen:
        plat.install_package("git")
        
        # Verificar argumentos de la llamada
        call_args = mock_popen.call_args[0][0]
        assert call_args[0] == "pkg"
        assert call_args[1] == "install"
        assert "git" in call_args

def test_debian_install_command_apt():
    """Verifica que Debian usa 'apt-get' por defecto"""
    plat = DebianPlatform(use_nala=False)
    
    with patch("subprocess.Popen", side_effect=MockPopen) as mock_popen:
        plat.install_package("curl")
        
        call_args = mock_popen.call_args[0][0]
        # sudo apt-get install -y curl
        assert "apt-get" in call_args
        assert "install" in call_args
        assert "curl" in call_args

def test_debian_install_command_nala():
    """Verifica que Debian usa 'nala' si se especifica"""
    plat = DebianPlatform(use_nala=True)
    
    with patch("subprocess.Popen", side_effect=MockPopen) as mock_popen:
        plat.install_package("wget")
        
        call_args = mock_popen.call_args[0][0]
        assert "nala" in call_args
        assert "install" in call_args