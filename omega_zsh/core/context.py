import os
import platform
import subprocess
import shlex
from pathlib import Path


class SystemContext:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SystemContext, cls).__new__(cls)
            cls._instance._detect()
        return cls._instance

    def _detect(self):
        """Analiza el sistema para determinar el entorno operativo."""
        self.os_type = platform.system().lower()
        self.home = Path.home()
        self.is_android = "ANDROID_ROOT" in os.environ or "ANDROID_DATA" in os.environ
        self.is_termux = "com.termux" in os.environ.get("PREFIX", "")
        self.distro_id = "unknown"
        self.distro_version = ""
        self.is_gsi = False
        self.package_manager_type = "unknown"

        if self.is_android:
            self._detect_android_context()
        elif self.os_type == "linux":
            self._detect_linux_distro()

    def _detect_android_context(self):
        """Detección específica para entornos Android/Termux."""
        self.distro_id = "android"

        # Detectar si es GSI (Generic System Image)
        # Usamos getprop para buscar huellas comunes de GSI
        try:
            # Treble / GSI suelen tener ro.build.flavor o descripciones genéricas
            # Esta es una heurística básica
            build_flavor = self._run_cmd("getprop ro.build.flavor")
            product_name = self._run_cmd("getprop ro.product.name")

            if (
                "aosp" in build_flavor.lower()
                or "gsi" in product_name.lower()
                or "treble" in product_name.lower()
            ):
                self.is_gsi = True
        except Exception:
            pass  # Si falla getprop, asumimos no GSI o no tenemos acceso

        # Determinar gestor de paquetes en Termux
        if self.is_termux:
            if self._command_exists("nala"):
                self.package_manager_type = "nala"
            else:
                self.package_manager_type = "pkg"
        else:
            # Android puro (adb shell) sin Termux environment es raro para esta app,
            # pero asumimos 'toybox' o herramientas limitadas.
            pass

    def _detect_linux_distro(self):
        """Lee /etc/os-release para identificar la distribución Linux."""
        os_release = Path("/etc/os-release")
        if os_release.exists():
            try:
                with open(os_release) as f:
                    data = {}
                    for line in f:
                        if "=" in line:
                            k, v = line.strip().split("=", 1)
                            data[k] = v.strip('"')

                    self.distro_id = data.get("ID", "linux").lower()
                    self.distro_version = data.get("VERSION_ID", "")
            except Exception:
                pass

        # Mapeo de Distro a Gestor de Paquetes
        if self.distro_id in ["debian", "ubuntu", "kali", "pop", "linuxmint", "parrot"]:
            if self._command_exists("nala"):
                self.package_manager_type = "nala"
            else:
                self.package_manager_type = "apt"
        elif self.distro_id in ["arch", "manjaro", "endeavouros"]:
            self.package_manager_type = "pacman"
        elif self.distro_id in ["fedora", "rhel", "centos", "almalinux"]:
            self.package_manager_type = "dnf"
        elif self.distro_id in ["alpine"]:
            self.package_manager_type = "apk"
        elif self.distro_id in ["opensuse", "sles"]:
            self.package_manager_type = "zypper"
        elif self.distro_id in ["void"]:
            self.package_manager_type = "xbps"
        else:
            # Fallback por detección de binario
            if self._command_exists("apt-get"):
                self.package_manager_type = "apt"
            elif self._command_exists("pacman"):
                self.package_manager_type = "pacman"
            elif self._command_exists("dnf"):
                self.package_manager_type = "dnf"
            elif self._command_exists("apk"):
                self.package_manager_type = "apk"

    def _command_exists(self, cmd: str) -> bool:
        """Verifica si un comando existe en el PATH."""
        from shutil import which

        return which(cmd) is not None

    def _run_cmd(self, cmd: str) -> str:
        """Ejecuta un comando shell de forma segura y devuelve stdout limpio."""
        try:
            # Usamos shlex.split para tokenizar el comando correctamente
            # y evitar el uso de shell=True
            args = shlex.split(cmd)
            return subprocess.check_output(args, text=True).strip()
        except Exception:
            return ""

    def __repr__(self):
        return (
            f"<SystemContext os={self.os_type} distro={self.distro_id} "
            f"pkg={self.package_manager_type} termux={self.is_termux} gsi={self.is_gsi}>"
        )
