import pytest
import json

from omega_zsh.core.state import StateManager, AppState

@pytest.fixture
def state_file(tmp_path):
    return tmp_path / "state.json"

@pytest.fixture
def manager(tmp_path):
    # StateManager espera el directorio base
    return StateManager(tmp_path)

def test_save_state(manager, tmp_path):
    """Prueba guardar un estado nuevo"""
    state = AppState(
        selected_plugins=["git", "python"],
        selected_theme="bira_matrix",
        selected_root_theme="red",
        selected_header="fastfetch",
        header_text="TEST",
        header_font="block"
    )
    manager.save(state)
    
    expected_file = tmp_path / "state.json"
    assert expected_file.exists()
    
    data = json.loads(expected_file.read_text())
    assert data["selected_plugins"] == ["git", "python"]
    assert data["header_text"] == "TEST"

def test_load_existing_state(manager, tmp_path):
    """Prueba cargar un estado existente"""
    state_file = tmp_path / "state.json"
    initial_data = {
        "selected_plugins": ["docker"],
        "selected_theme": "agnoster",
        "selected_root_theme": "blue",
        "selected_header": "none",
        "header_text": "A",
        "header_font": "B"
    }
    state_file.write_text(json.dumps(initial_data))
    
    loaded = manager.load()
    assert loaded.selected_plugins == ["docker"]
    assert loaded.selected_theme == "agnoster"

def test_load_corrupt_state(manager, tmp_path):
    """Prueba cargar un estado corrupto (debe devolver default)"""
    state_file = tmp_path / "state.json"
    state_file.write_text("{ INVALID JSON")
    
    loaded = manager.load()
    # Verifica que devuelve un objeto AppState con valores por defecto (vacíos o None)
    # o lanza excepción si así está diseñado. Según el código, devuelve AppState por defecto.
    assert isinstance(loaded, AppState)
    # Asumiendo que el default de plugins es []
    assert loaded.selected_plugins == []
