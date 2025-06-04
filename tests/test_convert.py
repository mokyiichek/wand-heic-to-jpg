import os
import tempfile
import unittest
from unittest import mock
from types import ModuleType
import sys

# Provide a dummy 'wand.image' module so convert can be imported without
# requiring the real dependency.
wand = ModuleType('wand')
wand.image = ModuleType('wand.image')
wand.image.Image = mock.MagicMock
sys.modules['wand'] = wand
sys.modules['wand.image'] = wand.image

import convert

class SkipDirsTest(unittest.TestCase):
    def test_skipdirs_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            process_dir = os.path.join(tmpdir, 'process')
            skip_dir = os.path.join(tmpdir, '.sync')
            os.makedirs(process_dir)
            os.makedirs(skip_dir)

            with open(os.path.join(process_dir, 'a.HEIC'), 'w') as f:
                f.write('data')
            with open(os.path.join(skip_dir, 'b.HEIC'), 'w') as f:
                f.write('data')

            with mock.patch('convert.Image') as MockImage:
                convert.check_dir(tmpdir, '.HEIC')

                processed = [call.kwargs.get('filename')
                             for call in MockImage.call_args_list]
                self.assertIn(os.path.join(process_dir, 'a.HEIC'), processed)
                self.assertNotIn(os.path.join(skip_dir, 'b.HEIC'), processed)

if __name__ == '__main__':
    unittest.main()
