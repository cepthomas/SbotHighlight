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
class TestHighlight(unittest.TestCase):  # TODOT more tests

    def setUp(self):
        mock_settings = {
            "highlight_scopes": ["region.redish", "region.yellowish", "region.greenish", "region.cyanish", "region.bluish", "region.purplish"],
        }
        emu.set_settings(mock_settings)

    def tearDown(self):
        pass

    #------------------------------------------------------------
    def test_simple(self):
        window = emu.Window(900)
        view = emu.View(901)

        view._window = window
        view._file_name = 'file123.abc'

        # Do the test.
        hl_vals = sbot_highlight._get_hl_vals(view, True)
        self.assertIsNotNone(hl_vals)

