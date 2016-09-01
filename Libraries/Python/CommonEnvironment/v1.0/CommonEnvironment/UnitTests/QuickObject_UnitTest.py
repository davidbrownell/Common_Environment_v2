# Placeholder unit test

import os
import sys
import unittest

from CommonEnvironment import Package

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

with Package.NameInfo(__package__) as ni:
    __package__ = ni.created

    from ..QuickObject import *

    __package__ = ni.original

# ----------------------------------------------------------------------
class Test(unittest.TestCase):
    pass

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass

