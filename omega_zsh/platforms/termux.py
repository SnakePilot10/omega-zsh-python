from shutil import which
from typing import Callable, List, Optional

from .base import BasePlatform


class TermuxPlatform(BasePlatform):
    def __init__(self, use_nala: bool = False):
        self.pkg_mgr = "nala" if use_nala else "pkg"

    def update_repos(self) -> bool:
        return self._run_command([self.pkg_mgr, "upgrade", "-y"])

    def install_package(
        self, package_name: str, on_progress: Optional[Callable[[str], None]] = None
    ) -> bool:
        # Resolvemos nombres específicos de paquetes si es necesario
        resolved_name = package_name
        if package_name == "fd":
            resolved_name = "fd"  # Termux usa fd directamente

        # lolcat en Termux suele instalarse de forma más confiable vía Ruby Gem.
        if package_name == "lolcat":
            if which("gem") is None:
                if not self._run_command([self.pkg_mgr, "install", "-y", "ruby"], on_progress):
                    return False

            return self._run_command(["gem", "install", "lolcat", "--no-document"], on_progress)

        cmd = [self.pkg_mgr, "install", "-y", resolved_name]
        return self._run_command(cmd, on_progress)

    def get_essential_tools(self) -> List[str]:
        return [
            "zsh",
            "git",
            "curl",
            "wget",
            "proot",
            "tsu",
            "fzf",
            "bat",
            "eza",
            "fastfetch",
            "figlet",
            "fortune",
            "cowsay",
        ]
