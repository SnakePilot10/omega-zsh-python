

from unittest.mock import MagicMock, patch, PropertyMock
from omega_zsh.ui.app import OmegaApp
from textual.widgets import TabbedContent

def test_action_switch_tab_navigation():
    with patch("omega_zsh.ui.app.OmegaApp.screen_stack", new_callable=PropertyMock) as mock_stack:
        app = OmegaApp()
        
        # Simulate stack with 2 screens
        stack_list = [MagicMock(), MagicMock()]
        mock_stack.return_value = stack_list
        
        # Mock pop_screen to simulate closing modal
        def pop_side_effect():
            if len(stack_list) > 1:
                stack_list.pop()
        
        app.pop_screen = MagicMock(side_effect=pop_side_effect)
        
        # Mock query_one
        mock_tabs = MagicMock(spec=TabbedContent)
        app.query_one = MagicMock(return_value=mock_tabs)
        
        # Execute
        app.action_switch_tab("dash")
        
        # Assert
        # 1. Should have popped the modal (stack size reduced)
        assert len(stack_list) == 1
        # 2. Should have set active tab
        assert mock_tabs.active == "dash"
