
import pytest
from unittest.mock import MagicMock, patch
from omega_zsh.ui.screens import HeaderSelectScreen
from textual.app import App
from rich.text import Text

class MockApp(App):
    def __init__(self):
        super().__init__()
        self.header_text = "TestHeader"
        self.header_font = "TestFont"

@pytest.mark.asyncio
@patch("omega_zsh.ui.screens.shutil.which")
@patch("omega_zsh.ui.screens.subprocess.run")
async def test_header_preview_fastfetch(mock_run, mock_which):
    # Setup
    mock_which.return_value = "/usr/bin/fastfetch"
    
    # Mock subprocess output
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "\x1b[34mFastfetch Output\x1b[0m"
    mock_run.return_value = mock_result
    
    app = MockApp()
    async with app.run_test() as pilot:
        screen = HeaderSelectScreen("fastfetch")
        app.push_screen(screen)
        
        # Mock query_one to return a mock Static widget
        # Note: In a real run_test, widgets are real. We might want to let it run real update
        # but mock subprocess.
        # But here we want to intercept the update call to verify text.
        
        # We can't easily mock query_one on a live widget in run_test.
        # So we inspect the widget after update.
        
        # Manually trigger update_preview (it's called on mount anyway)
        # screen.update_preview() 
        # Wait for events
        await pilot.pause()
        
        preview_area = screen.query_one("#header-preview-area")
        # Check content
        # In this version of Textual, we might need to use render() or assume mock executed.
        # Let's inspect the renderable via private attribute if needed, or just rely on mock_run
        # verifying the command was executed is the most important part of "live preview logic".
        
        mock_run.assert_called()
        assert mock_run.call_args[0][0][0] == "fastfetch"

@pytest.mark.asyncio
@patch("omega_zsh.ui.screens.shutil.which")
@patch("omega_zsh.ui.screens.subprocess.run")
async def test_header_preview_cow(mock_run, mock_which):
    # Setup: fortune and cowsay exist
    mock_which.side_effect = lambda x: "/bin/" + x
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Moo"
    mock_run.return_value = mock_result
    
    app = MockApp()
    async with app.run_test() as pilot:
        screen = HeaderSelectScreen("cow")
        app.push_screen(screen)
        
        await pilot.pause()
        
        mock_run.assert_called()
        cmd = mock_run.call_args[0][0]
        # Should use shell since it's a pipe
        assert cmd[0] == "sh" 
        assert "cowsay" in cmd[2]
