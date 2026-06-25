import json

import pytest

from omega_zsh.core.state import AppState, StateManager, normalize_app_state


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
        header_font="block",
    )
    manager.save(state)

    expected_file = tmp_path / "state.json"
    assert expected_file.exists()

    data = json.loads(expected_file.read_text())
    assert data["selected_plugins"] == ["git", "python"]
    assert data["allowed_custom_plugins"] == []
    assert data["header_text"] == "TEST"
    assert not expected_file.with_suffix(".tmp").exists()


def test_load_existing_state(manager, tmp_path):
    """Prueba cargar un estado existente"""
    state_file = tmp_path / "state.json"
    initial_data = {
        "selected_plugins": ["docker"],
        "selected_theme": "agnoster",
        "selected_root_theme": "blue",
        "selected_header": "none",
        "header_text": "A",
        "header_font": "B",
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


def test_import_from_zshrc_normaliza_plugins(manager, tmp_path):
    zshrc = tmp_path / ".zshrc"
    zshrc.write_text('plugins=(git git zoxide  EZA "" 123)\n', encoding="utf-8")
    manager.zshrc_path = zshrc

    loaded = manager.load()

    assert loaded.selected_plugins == ["git", "zoxide", "eza", "123"]


def test_load_state_normaliza_tipos_invalidos(manager, tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text(
        json.dumps(
            {
                "selected_plugins": ["git", 123, "", " zoxide "],
                "selected_theme": None,
                "selected_root_theme": "",
                "selected_header": "invalid",
                "header_text": 42,
                "header_font": " slant ",
                "unknown_field": "ignored",
            }
        ),
        encoding="utf-8",
    )

    loaded = manager.load()

    assert loaded.selected_plugins == ["git", "zoxide"]
    assert loaded.selected_theme == "robbyrussell"
    assert loaded.selected_root_theme == "root_p10k_red"
    assert loaded.selected_header == "fastfetch"
    assert loaded.header_text == "Omega"
    assert loaded.header_font == "slant"


def test_load_state_normaliza_allowed_custom_plugins(manager, tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text(
        json.dumps(
            {
                "selected_plugins": ["git", "Mi-Custom", "mi-custom"],
                "allowed_custom_plugins": [" Mi-Custom ", "mi-custom", 123],
                "selected_header": "none",
            }
        ),
        encoding="utf-8",
    )

    loaded = manager.load()

    assert loaded.selected_plugins == ["git", "mi-custom"]
    assert loaded.allowed_custom_plugins == ["mi-custom"]


def test_load_state_json_no_dict_usa_defaults(manager, tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps(["git", "zoxide"]), encoding="utf-8")

    loaded = manager.load()

    assert isinstance(loaded, AppState)
    assert loaded.selected_plugins == []
    assert loaded.selected_theme == "robbyrussell"


def test_normalize_app_state_acepta_plugin_string():
    state = normalize_app_state({"selected_plugins": " Git ", "selected_header": "none"})

    assert state.selected_plugins == ["git"]
    assert state.selected_header == "none"


def test_normalize_app_state_deduplica_plugins_preservando_orden():
    state = normalize_app_state(
        {
            "selected_plugins": [
                " Git ",
                "zoxide",
                "git",
                "",
                "  EZA  ",
                123,
                "zoxide",
            ]
        }
    )

    assert state.selected_plugins == ["git", "zoxide", "eza"]


def test_normalize_app_state_header_tipo_invalido_no_revienta():
    state = normalize_app_state({"selected_header": ["fastfetch"]})

    assert state.selected_header == "fastfetch"


def test_normalize_app_state_header_limpia_espacios():
    state = normalize_app_state({"selected_header": " none "})

    assert state.selected_header == "none"


def test_save_state_normaliza_antes_de_escribir(manager, tmp_path):
    state = AppState(selected_plugins="git", selected_header="invalid")

    manager.save(state)

    data = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert data["selected_plugins"] == ["git"]
    assert data["selected_header"] == "fastfetch"
