import sys
import os
import unittest
from unittest.mock import MagicMock

# Add path to code under test.
cut_path = os.path.join(os.path.dirname(__file__), '..')
if cut_path not in sys.path:
      sys.path.insert(0, cut_path)

# Now import the sublime emulation.
import emu_sublime
import emu_sublime_plugin
sys.modules["sublime"] = emu_sublime
sys.modules["sublime_plugin"] = emu_sublime_plugin

# Now import the code under test.
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

