# Placeholder unit test

import os
import sys
import unittest

from CommonEnvironment.CallOnExit import CallOnExit

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, ".."))
with CallOnExit(lambda: sys.path.pop(0)):
    from Decorator import *

# ----------------------------------------------------------------------
class Test(unittest.TestCase):
    
    @AsFunc("Foo")
    class MyClass(object):
        @staticmethod
        def Foo():
            return "Bar"

        def __init__(self, value):
            self.value = value

        def Another(self):
            return "Another: {}".format(self.value)

    # ----------------------------------------------------------------------
    def test_Standard(self):
        self.assertEquals(Test.MyClass(), "Bar")
        self.assertEqual(Test.MyClass(Test.MyClass.StandardInit, 100).Another(), "Another: 100")

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass

