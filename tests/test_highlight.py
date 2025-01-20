import sys
import os
import unittest
from unittest.mock import MagicMock

# Set up the sublime emulation environment.
import emu_sublime_api as emu

# Import the code under test.
import sbot_highlight
# import sbot_common as sc


#-----------------------------------------------------------------------------------
class TestHighlight(unittest.TestCase):  # TEST more tests

    def setUp(self):
        mock_settings = {
            "highlight_scopes": ["region.redish", "region.yellowish", "region.greenish", "region.cyanish", "region.bluish", "region.purplish"],
        }
        emu.set_settings(mock_settings)

    def tearDown(self):
        pass

    #------------------------------------------------------------
    def test_simple(self):
        pass

