# ----------------------------------------------------------------------
# |  
# |  AnyOfTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-06 17:31:15
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-17.
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
    
    from ..AnyOfTypeInfo import *
    from .. import FundamentalTypes

    __package__ = ni.original

# ----------------------------------------------------------------------
class UnitTest(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    @classmethod
    def setUp(cls):
        cls._ti = AnyOfTypeInfo([ FundamentalTypes.StringTypeInfo(min_length=2),
                                  FundamentalTypes.IntTypeInfo(min=10),
                                ])

    # ----------------------------------------------------------------------
    def test_Desc(self):
        self.assertEqual(self._ti.Desc, "Any of 'String', 'Integer'")

    # ----------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(self._ti.ConstraintsDesc, "Value where: String: Value must have more than 2 characters / Integer: Value must be >= 10")

    # ----------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(self._ti.PythonDefinitionString, "AnyOfTypeInfo(arity=Arity(min=1, max_or_none=1), type_info_list=[ StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=2), IntTypeInfo(arity=Arity(min=1, max_or_none=1), min=10) ])")

    # ----------------------------------------------------------------------
    def test_ExpectedType(self):
        self.assertTrue(self._ti.IsExpectedType("Foo"))
        self.assertTrue(self._ti.IsExpectedType(100))
        self.assertTrue(self._ti.IsExpectedType(1.0) == False)

    # ----------------------------------------------------------------------
    def test_IsValidItem(self):
        self.assertTrue(self._ti.IsValidItem("Foo"))
        self.assertTrue(self._ti.IsValidItem("F") == False)
        
        self.assertTrue(self._ti.IsValidItem(100))
        self.assertTrue(self._ti.IsValidItem(1) == False)

        self.assertTrue(self._ti.IsValidItem(1.0) == False)

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
