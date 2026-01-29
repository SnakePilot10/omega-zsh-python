
import pytest
from unittest.mock import MagicMock
from omega_zsh.ui.app import OmegaApp

@pytest.fixture
def mock_app():
    app = OmegaApp()
    app.context = MagicMock()
    app.state_manager = MagicMock()
    app.generator = MagicMock()
    app.notify = MagicMock()
    app.selected_plugins = ["git", "z"]
    app.selected_theme = "robbyrussell"
    app.selected_root_theme = "red"
    app.selected_header = "fastfetch"
    app.header_text = "Omega"
    app.header_font = "slant"
    return app

def test_action_apply_changes_success(mock_app):
    # Setup mocks
    mock_app.context.home = MagicMock()
    mock_app.generator.generate_zshrc.return_value = True
    
    # Execute
    mock_app.action_apply_changes()
    
    # Assert
    # 1. State saved
    mock_app.state_manager.save.assert_called()
    
    # 2. Generator called
    mock_app.generator.generate_personal_config.assert_called()
    mock_app.generator.generate_zshrc.assert_called()
    mock_app.generator.create_default_custom_zsh.assert_called()
    
    # 3. Notification success
    mock_app.notify.assert_called_with("¡Cambios Aplicados! Ejecuta 'source ~/.zshrc'", title="Éxito", severity="information", timeout=5)

def test_action_apply_changes_failure(mock_app):
    # Setup generator failure
    mock_app.generator.generate_zshrc.return_value = False
    
    # Execute
    mock_app.action_apply_changes()
    
    # Assert
    mock_app.notify.assert_called_with("Error generando .zshrc", title="Error", severity="error")
