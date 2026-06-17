# Cómo Contribuir a Omega-ZSH

¡Gracias por tu interés en contribuir a Omega-ZSH! Este proyecto busca crear el gestor de entorno shell definitivo para Linux y Android (Termux).

## 🛠 Configuración del Entorno de Desarrollo

El proyecto utiliza un script de bootstrap (`install.sh`) para automatizar la creación del entorno virtual y la instalación de dependencias.

### Pasos Iniciales

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/SnakePilot10/omega-zsh-python.git
    cd omega-zsh-python
    ```

2.  **Ejecutar el instalador en modo desarrollo:**
    Aunque `install.sh` está pensado para usuarios finales, también configura el entorno necesario.
    ```bash
    ./install.sh
    # O para instalación rápida desatendida:
    ./install.sh -y
    ```
    *Nota: Esto creará una carpeta `.venv` y preparará el sistema.*

3.  **Activar el entorno virtual:**
    ```bash
    source .venv/bin/activate
    ```

4.  **Instalar en modo editable:**
    Esto permite que los cambios en el código se reflejen inmediatamente sin reinstalar.
    ```bash
    pip install -e .
    ```

## 🧪 Ejecución de Pruebas

Utilizamos `pytest` para las pruebas unitarias. Asegúrate de que todas las pruebas pasen antes de enviar un Pull Request.

```bash
# Desde la raíz del proyecto (con venv activado)
pytest
```

## 📂 Estructura del Código

*   **`omega_zsh/core`**: Lógica de negocio (instaladores, generadores de config, estado).
*   **`omega_zsh/ui`**: Interfaz gráfica basada en Textual (TUI).
*   **`omega_zsh/platforms`**: Abstracciones específicas del sistema operativo (Termux, Debian, etc.).
*   **`omega_zsh/cli`**: Herramientas de línea de comandos (`oz`).

## 🐛 Reporte de Errores

Si encuentras un error, por favor abre un issue incluyendo:
*   Tu sistema operativo (Android/Termux, Ubuntu, Arch, etc.).
*   El log de error (puedes encontrarlo en `omega_crash.log` o en la salida de la terminal).
*   Pasos para reproducir el problema.

## 🎨 Estilo de Código

*   Seguimos PEP 8 en la medida de lo posible.
*   Usa *Type Hints* (pistas de tipo) en las firmas de las funciones.
*   Añade *docstrings* a las clases y funciones públicas explicando qué hacen, sus argumentos y retorno.

¡Feliz hacking! 🐍
