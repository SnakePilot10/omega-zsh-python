import unittest
import asyncio
from unittest.mock import MagicMock, patch
from omega_zsh.ui.screens import HeaderSelectScreen
from textual.app import App


class MockApp(App):
    def __init__(self):
        super().__init__()
        self.header_text = "TestHeader"
        self.header_font = "TestFont"


class TestHeaderPreview(unittest.IsolatedAsyncioTestCase):
    async def test_header_preview_fastfetch(self):
        call_log = []
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Fastfetch Output"

        def fake_run(*args, **kwargs):
            call_log.append(args)
            return mock_result

        with patch("omega_zsh.ui.screens.shutil.which", return_value="/usr/bin/fastfetch"), \
             patch("omega_zsh.ui.screens.subprocess.run", side_effect=fake_run):
            
            app = MockApp()
            async with app.run_test():
                screen = HeaderSelectScreen("fastfetch")
                app.push_screen(screen)
                await asyncio.sleep(0.5)
                
            if not call_log:
                 raise AssertionError("subprocess.run was not called (captured via side_effect)")
            
            assert call_log[0][0][0] == "fastfetch"

    async def test_header_preview_cow(self):
        call_log = []
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Moo"

        def fake_run(*args, **kwargs):
            call_log.append(args)
            return mock_result

        # Setup: fortune and cowsay exist
        with patch("omega_zsh.ui.screens.shutil.which", side_effect=lambda x: "/bin/" + x), \
             patch("omega_zsh.ui.screens.subprocess.run", side_effect=fake_run):

            app = MockApp()
            async with app.run_test():
                screen = HeaderSelectScreen("cow")
                app.push_screen(screen)
                await asyncio.sleep(0.5)

            if not call_log:
                 raise AssertionError("subprocess.run was not called (captured via side_effect)")
            
            cmd = call_log[0][0]
            # Should use shell since it's a pipe
            assert cmd[0] == "sh"
            assert "cowsay" in cmd[2]
