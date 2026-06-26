import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from .constants import BIN_PLUGINS, DB_PLUGINS, is_binary_tool
from .plugins_db import get_description
from .state import StateManager


@dataclass(frozen=True)
class PluginInspection:
    found: bool
    is_binary: bool
    description: str
    aliases: list[str]
    functions: list[str]
    path: str = ""


def get_ram_usage() -> str:
    try:
        mem = _read_meminfo(Path("/proc/meminfo"))
        total = mem.get("MemTotal", 1)
        free = mem.get("MemFree", 0)
        buffers = mem.get("Buffers", 0)
        cached = mem.get("Cached", 0)
        used = total - free - buffers - cached
        return f"{int((used / total) * 100)}%"
    except Exception:
        return "N/A"


def get_disk_usage(path: str = "/") -> str:
    try:
        st = os.statvfs(path)
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        used = total - free
        return f"{int((used / total) * 100)}%"
    except Exception:
        return "N/A"


def get_uptime() -> str:
    try:
        uptime_seconds = float(Path("/proc/uptime").read_text(encoding="utf-8").split()[0])
        hours, remainder = divmod(int(uptime_seconds), 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours}h {minutes}m"
    except Exception:
        return "N/A"


def get_os_label(env: dict[str, str] | None = None) -> str:
    env = env or os.environ
    if Path("/data/data/com.termux").exists() or "com.termux" in env.get("PREFIX", ""):
        return "Android/Termux"

    os_release = Path("/etc/os-release")
    if os_release.exists():
        try:
            for line in os_release.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
        except Exception:
            pass

    return sys.platform


def get_system_stats(env: dict[str, str] | None = None) -> dict[str, str]:
    return {
        "os": get_os_label(env),
        "mem_usage": get_ram_usage(),
        "disk_usage": get_disk_usage(),
        "uptime": get_uptime(),
    }


def parse_zshrc_plugins(path: Path) -> list[str]:
    if not path.exists():
        return []
    content = path.read_text(errors="ignore")
    match = re.search(r"^plugins=\((.*?)\)", content, re.MULTILINE | re.DOTALL)
    if not match:
        return []
    cleaned = re.sub(r"#.*", "", match.group(1))
    return cleaned.split()


def get_active_items(config_dir: Path, zshrc_path: Path) -> list[str]:
    try:
        return StateManager(config_dir).load().selected_plugins
    except Exception:
        return parse_zshrc_plugins(zshrc_path)


def inspect_plugin(
    plugin_name: str,
    omz_dir: Path,
    custom_plugins: Path | None = None,
    standard_plugins: Path | None = None,
) -> PluginInspection:
    custom_plugins = custom_plugins or omz_dir / "custom" / "plugins"
    standard_plugins = standard_plugins or omz_dir / "plugins"
    paths = [
        custom_plugins / plugin_name / f"{plugin_name}.plugin.zsh",
        standard_plugins / plugin_name / f"{plugin_name}.plugin.zsh",
        custom_plugins / plugin_name / f"{plugin_name}.zsh",
        standard_plugins / plugin_name / f"{plugin_name}.zsh",
    ]
    plugin_path = next((p for p in paths if p.exists()), None)
    description = _description_for(plugin_name)

    if not plugin_path or is_binary_tool(plugin_name):
        return PluginInspection(False, True, description, [], [])

    try:
        content = plugin_path.read_text(errors="ignore")
        aliases = re.findall(r"^alias\s+([\w-]+)=", content, re.MULTILINE)
        functions = re.findall(r"^function\s+([\w-]+)", content, re.MULTILINE)
        functions += re.findall(r"^([\w-]+)\(\)\s*\{", content, re.MULTILINE)
        functions = [func for func in functions if not func.startswith("_")]
    except Exception:
        aliases, functions = [], []

    return PluginInspection(
        True,
        False,
        description,
        sorted(set(aliases)),
        sorted(set(functions)),
        str(plugin_path),
    )


def _read_meminfo(path: Path) -> dict[str, int]:
    mem = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split(":")
        if len(parts) == 2:
            mem[parts[0].strip()] = int(parts[1].split()[0].strip())
    return mem


def _description_for(plugin_name: str) -> str:
    description = get_description(plugin_name)
    if (
        "Sin descripción" not in description
        and description != "Plugin de Oh My Zsh (sin descripción documentada en la base de datos)."
    ):
        return description
    for plugin_def in DB_PLUGINS:
        if plugin_def.id == plugin_name:
            return plugin_def.desc
    if plugin_name in BIN_PLUGINS:
        return description
    return description
