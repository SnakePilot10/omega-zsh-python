from typing import Callable, List, Optional

from .base import BasePlatform


class ArchPlatform(BasePlatform):
    def __init__(self):
        self.pkg_mgr = "pacman"

    def update_repos(self) -> bool:
        return self._run_command(["sudo", "pacman", "-Syu", "--noconfirm"])

    def install_package(
        self, package_name: str, on_progress: Optional[Callable[[str], None]] = None
    ) -> bool:
        return self._run_command(
            ["sudo", "pacman", "-S", "--noconfirm", "--needed", package_name],
            on_progress,
        )

    def get_essential_tools(self) -> List[str]:
        return [
            "zsh",
            "git",
            "curl",
            "wget",
            "base-devel",
            "fzf",
            "bat",
            "eza",
            "fastfetch",
            "figlet",
            "fortune-mod",
            "cowsay",
        ]
