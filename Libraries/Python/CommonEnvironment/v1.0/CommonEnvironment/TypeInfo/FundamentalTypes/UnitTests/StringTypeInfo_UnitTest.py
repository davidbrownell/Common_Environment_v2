# ----------------------------------------------------------------------
# |  
# |  StringTypeInfo_UnitTest.py
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
    
    from ..StringTypeInfo import *
    from ... import ValidationException

    __package__ = ni.original

# ----------------------------------------------------------------------
class UnitTest(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    @classmethod
    def setUp(cls):
        cls._ti = StringTypeInfo()
        cls._ti_min = StringTypeInfo(min_length=3)
        cls._ti_max = StringTypeInfo(max_length=5)
        cls._ti_ve = StringTypeInfo(r"\d+")

    # ----------------------------------------------------------------------
    def test_ConstructErrors(self):
        self.assertRaises(Exception, lambda: StringTypeInfo("Foo", min_length=10))
        self.assertRaises(Exception, lambda: StringTypeInfo("Foo", max_length=10))
        self.assertRaises(Exception, lambda: StringTypeInfo(min_length=10, max_length=0))

    # ----------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(self._ti.ConstraintsDesc, "Value must have more than 1 character")
        self.assertEqual(self._ti_min.ConstraintsDesc, "Value must have more than 3 characters")
        self.assertEqual(self._ti_max.ConstraintsDesc, "Value must have more than 1 character, have less than 5 characters")
        self.assertEqual(self._ti_ve.ConstraintsDesc, r"Value must match the regular expression '\d+'")

    # ----------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(self._ti.PythonDefinitionString, "StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=1)")
        self.assertEqual(self._ti_min.PythonDefinitionString, "StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=3)")
        self.assertEqual(self._ti_max.PythonDefinitionString, "StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=1, max_length=5)")
        self.assertEqual(self._ti_ve.PythonDefinitionString, 'StringTypeInfo(arity=Arity(min=1, max_or_none=1), validation_expression=r"\d+")')

    # ----------------------------------------------------------------------
    def test_ValidateItem(self):
        self._ti.ValidateItem("Foo")
        self.assertRaises(ValidationException, lambda: self._ti.ValidateItem(''))

        self._ti_min.ValidateItem("Foo")
        self.assertRaises(ValidationException, lambda: self._ti_min.ValidateItem("Yo"))

        self._ti_max.ValidateItem("Foo")
        self.assertRaises(ValidationException, lambda: self._ti_max.ValidateItem("Foolish"))
        self.assertRaises(ValidationException, lambda: self._ti_max.ValidateItem(''))

        self._ti_ve.ValidateItem("12345")
        self.assertRaises(ValidationException, lambda: self._ti_ve.ValidateItem("Foo"))

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
