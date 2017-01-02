# ----------------------------------------------------------------------
# |  
# |  FloatTypeInfo_UnitTest.py
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
    
    from ..FloatTypeInfo import *
    from ... import ValidationException

    __package__ = ni.original

# ----------------------------------------------------------------------
class UnitTest(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    @classmethod
    def setUp(cls):
        cls._ti = FloatTypeInfo()
        cls._ti_min = FloatTypeInfo(min=0)
        cls._ti_max = FloatTypeInfo(max=10)
        cls._ti_min_max = FloatTypeInfo(min=0, max=10)

    # ----------------------------------------------------------------------
    def test_ConstructErrors(self):
        self.assertRaises(Exception, lambda: FloatTypeInfo(min=10000, max=0))

    # ----------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(self._ti.ConstraintsDesc, '')
        self.assertEqual(self._ti_min.ConstraintsDesc, "Value must be >= 0.0")
        self.assertEqual(self._ti_max.ConstraintsDesc, "Value must be <= 10.0")
        self.assertEqual(self._ti_min_max.ConstraintsDesc, "Value must be >= 0.0, be <= 10.0")

    # ----------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(self._ti.PythonDefinitionString, "FloatTypeInfo(arity=Arity(min=1, max_or_none=1))")
        self.assertEqual(self._ti_min.PythonDefinitionString, "FloatTypeInfo(arity=Arity(min=1, max_or_none=1), min=0.0)")
        self.assertEqual(self._ti_max.PythonDefinitionString, "FloatTypeInfo(arity=Arity(min=1, max_or_none=1), max=10.0)")
        self.assertEqual(self._ti_min_max.PythonDefinitionString, "FloatTypeInfo(arity=Arity(min=1, max_or_none=1), min=0.0, max=10.0)")

    # ----------------------------------------------------------------------
    def test_ValidateItem(self):
        self._ti.ValidateItem(5.0)
        
        self._ti_min.ValidateItem(5.0)
        self.assertRaises(ValidationException, lambda: self._ti_min.ValidateItem(-1.0))

        self._ti_max.ValidateItem(5.0)
        self.assertRaises(ValidationException, lambda: self._ti_max.ValidateItem(1000.0))

        self._ti_min_max.ValidateItem(5.0)
        self.assertRaises(ValidationException, lambda: self._ti_min_max.ValidateItem(-1.0))
        self.assertRaises(ValidationException, lambda: self._ti_min_max.ValidateItem(1000.0))

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
