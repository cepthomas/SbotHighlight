import sys
import os
import unittest
from unittest.mock import MagicMock

# Set up the sublime emulation environment.
import emu_sublime_api as emu

# Import the code under test.
import sbot_highlight
import sbot_common as sc


#-----------------------------------------------------------------------------------
class TestHighlight(unittest.TestCase):

    def setUp(self):
        mock_settings = {
            "highlight_scopes": ["region.redish", "region.yellowish", "region.greenish", "region.cyanish", "region.bluish", "region.purplish"],
        }
        sublime.load_settings = MagicMock(return_value=mock_settings)

    def tearDown(self):
        pass

    def test_simple(self):
        window = sublime.Window(900)
        view = sublime.View(901)

        view.window = MagicMock(return_value=window)
        view.file_name = MagicMock(return_value='file123.abc')

        # Do the test.
        hl_vals = sbot_highlight._get_hl_vals(view, True)
        self.assertIsNotNone(hl_vals)

