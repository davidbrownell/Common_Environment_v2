# Placeholder unit test

import os
import sys
import unittest

from CommonEnvironment import Package

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

__package__ = Package.CreateName(__package__, __name__, __file__)
from ..Shell import *
__package__ = None

# ----------------------------------------------------------------------
class Test(unittest.TestCase):
    pass

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass

