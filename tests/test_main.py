import sys
from unittest.mock import patch

from omega_zsh.__main__ import handle_exception, main


def test_main_success():
    """Prueba que main() inicie la app correctamente sin argumentos."""
    with patch("sys.argv", ["omega"]):
        with patch("omega_zsh.ui.app.OmegaApp") as mock_app:
            instance = mock_app.return_value
            main()
            instance.run.assert_called_once()


def test_main_cli_delegation():
    """Prueba que main() delegue a oz_tool si hay argumentos."""
    with patch("sys.argv", ["oz", "stats"]):
        with patch("omega_zsh.cli.oz_tool.main") as mock_cli:
            main()
            mock_cli.assert_called_once()


def test_main_import_error():
    """Prueba el manejo de ImportError en main()."""
    with patch("sys.argv", ["omega"]):
        with patch("omega_zsh.ui.app.OmegaApp", side_effect=ImportError("Missing module")):
            with patch("sys.exit") as mock_exit:
                main()
                mock_exit.assert_called_once_with(1)


def test_main_runtime_error():
    """Prueba el manejo de excepciones generales en main()."""
    with patch("sys.argv", ["omega"]):
        with patch("omega_zsh.ui.app.OmegaApp", side_effect=Exception("Runtime error")):
            with patch("sys.exit") as mock_exit:
                main()
                mock_exit.assert_called_once_with(1)


def test_handle_exception_keyboard_interrupt():
    """Prueba que KeyboardInterrupt sea manejado por el sistema por defecto."""
    with patch("sys.__excepthook__") as mock_hook:
        handle_exception(KeyboardInterrupt, KeyboardInterrupt(), None)
        mock_hook.assert_called_once()


def test_handle_exception_fatal():
    """Prueba que las excepciones fatales se registren en el log."""
    with patch("logging.critical") as mock_log:
        with patch("sys.__stderr__.write") as mock_write:
            handle_exception(ValueError, ValueError("Test Error"), None)
            mock_log.assert_called_once()
            mock_write.assert_called()
