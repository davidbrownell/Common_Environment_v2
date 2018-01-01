# ----------------------------------------------------------------------
# |  
# |  CustomTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-06 17:31:15
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-18.
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
    
    from ..CustomTypeInfo import *

    __package__ = ni.original

# ----------------------------------------------------------------------
class UnitTest(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    @classmethod
    def setUp(cls):
        cls._ti = CustomTypeInfo( lambda item: isinstance(item, str),
                                  lambda item: None if item == "test" else "invalid",
                                  "Constraints Desc",
                                )

    # ----------------------------------------------------------------------
    def test_ExpectedType(self):
        self.assertTrue(self._ti.IsExpectedType("a string"))
        self.assertTrue(self._ti.IsExpectedType(10) == False)

    # ----------------------------------------------------------------------
    def test_IsValidItem(self):
        self.assertTrue(self._ti.IsValidItem("test"))
        self.assertTrue(self._ti.IsValidItem("different test") == False)
        self.assertTrue(self._ti.IsValidItem(10) == False)

    # ----------------------------------------------------------------------
    def test_Desc(self):
        self.assertEqual(self._ti.ConstraintsDesc, "Constraints Desc")

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
