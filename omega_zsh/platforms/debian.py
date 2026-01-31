from typing import List, Callable, Optional
import os
from .base import BasePlatform


class DebianPlatform(BasePlatform):
    def __init__(self, use_nala: bool = False):
        self.pkg_mgr = "nala" if use_nala else "apt-get"
        self.has_sudo = os.getuid() != 0  # Si no es root, asumimos que necesita sudo

    def _get_base_cmd(self, action: str) -> List[str]:
        cmd = []
        if self.has_sudo:
            cmd.append("sudo")
        cmd.extend([self.pkg_mgr, action])
        if self.pkg_mgr == "apt-get":
            cmd.append("-y")
        return cmd

    def update_repos(self) -> bool:
        cmd = self._get_base_cmd("update")
        return self._run_command(cmd)

    def install_package(
        self, package_name: str, on_progress: Optional[Callable[[str], None]] = None
    ) -> bool:
        resolved_name = package_name
        # Mapeos específicos de Debian
        if package_name == "fd":
            resolved_name = "fd-find"
        elif package_name == "bat":
            resolved_name = "bat"

        cmd = self._get_base_cmd("install")
        cmd.append(resolved_name)
        return self._run_command(cmd, on_progress)

    def get_essential_tools(self) -> List[str]:
        return [
            "zsh",
            "git",
            "curl",
            "wget",
            "build-essential",
            "fzf",
            "bat",
            "eza",
            "fastfetch",
            "figlet",
            "fortune-mod",
            "cowsay",
            "lolcat",
        ]
