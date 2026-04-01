
import pytest


@pytest.fixture(autouse=True)
def patch_textual_work(monkeypatch):
    """
    Parchea el decorador @work de Textual para que se comporte como una
    función normal durante los tests, evitando el error NoActiveAppError.
    """
    def mock_work(exclusive=False, thread=False):
        def decorator(func):
            return func
        return decorator
    
    monkeypatch.setattr("textual.work", mock_work)
