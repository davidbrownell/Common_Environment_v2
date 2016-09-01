# ---------------------------------------------------------------------------
# |  
# |  StringTypeInfo_UnitTest.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/28/2015 03:32:36 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Unit test for StringTypeInfo.py
"""

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

    from ..StringTypeInfo import *
    
    __package__ = ni.original

# ---------------------------------------------------------------------------
class FundamentalString(unittest.TestCase):
    
    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._empty_type_info = StringTypeInfo(min_length=0)
        cls._type_info = StringTypeInfo(validation_expression=r"\d{1,5}")

    # ---------------------------------------------------------------------------
    def test_Validate(self):
        
        self._type_info.Validate("123")
        self.assertRaises(Exception, lambda: _self._type_info.Validate("abcd"))     # Not valid
        self.assertRaises(Exception, lambda: _self._type_info.Validate(""))         # Too short
        self.assertRaises(Exception, lambda: _self._type_info.Validate("123456"))   # Too long

        self._empty_type_info.Validate("123")
        self._empty_type_info.Validate("abcd")
        self._empty_type_info.Validate("")
        self._empty_type_info.Validate("123456")

        self.assertRaises(Exception, lambda: self._empty_type_info.Validate(10))    # Wrong type

    # ---------------------------------------------------------------------------
    def test_ToString(self):
        self.assertEqual(self._empty_type_info.ItemToString("foo"), "foo")
        self.assertRaises(Exception, lambda: _type_info.ItemToString("abc"))        # Not valid

    # ---------------------------------------------------------------------------
    def test_FromString(self):
        self.assertEqual(self._empty_type_info.ItemFromString("foo"), "foo")
        self.assertRaises(Exception, lambda: _type_info.ItemFromString("abc"))          # Not valid

    # ---------------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(self._empty_type_info.PythonDefinitionString, "StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=0)")
        self.assertEqual(self._type_info.PythonDefinitionString, r'StringTypeInfo(arity=Arity(min=1, max_or_none=1), validation_expression=r"\d{1,5}")')
        
    # ---------------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(self._empty_type_info.ConstraintsDesc, "")
        self.assertEqual(self._type_info.ConstraintsDesc, r"Value must match the regular expression '\d{1,5}'")
        
    # ---------------------------------------------------------------------------
    def test_PythonItemRegularExpressionString(self):
        self.assertEqual(self._empty_type_info.PythonItemRegularExpressionString, ".*")
        self.assertEqual(self._type_info.PythonItemRegularExpressionString, r"\d{1,5}")
        
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
