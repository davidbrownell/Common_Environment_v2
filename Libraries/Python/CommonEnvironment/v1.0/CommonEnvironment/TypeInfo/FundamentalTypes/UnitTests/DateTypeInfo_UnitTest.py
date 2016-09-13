# ----------------------------------------------------------------------
# |  
# |  DateTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-06 17:31:15
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import sys
import unittest

from CommonEnvironment import Package

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with Package.NameInfo(__package__) as ni:
    __package__ = ni.created
    
    from ..DateTypeInfo import *

    __package__ = ni.original

# ----------------------------------------------------------------------
class UnitTest(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    @classmethod
    def setUp(cls):
        cls._ti = DateTypeInfo()
        cls._now = cls._ti.Create()

    # ----------------------------------------------------------------------
    def test_Standard(self):
        self.assertEqual(self._ti.PythonDefinitionString, "DateTypeInfo(arity=Arity(min=1, max_or_none=1))")

        self._ti.ValidateItem(self._now)

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
