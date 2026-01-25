import unittest
from unittest.mock import MagicMock, patch
from omega_zsh.ui.screens import HeaderSelectScreen
from textual.app import App
from rich.text import Text
import shutil

class MockApp(App):
    def __init__(self):
        super().__init__()
        self.header_text = "TestHeader"
        self.header_font = "TestFont"

class TestHeaderPreview(unittest.IsolatedAsyncioTestCase):
    
    @patch("omega_zsh.ui.screens.shutil.which")
    @patch("omega_zsh.ui.screens.subprocess.run")
    async def test_header_preview_fastfetch(self, mock_run, mock_which):
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
            
            # Wait for events to settle (mount, update_preview)
            await pilot.pause()
            
            mock_run.assert_called()
            # Verify the command called
            assert mock_run.call_args[0][0][0] == "fastfetch"

    @patch("omega_zsh.ui.screens.shutil.which")
    @patch("omega_zsh.ui.screens.subprocess.run")
    async def test_header_preview_cow(self, mock_run, mock_which):
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