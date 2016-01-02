# ---------------------------------------------------------------------------
# |  
# |  IntTypeInfo_UnitTest.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/29/2015 02:30:42 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Unit test for IntTypeInfo.py
"""

import os
import sys
import unittest

from CommonEnvironment import Package

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

__package__ = Package.CreateName(__package__, __name__, __file__)
from ..IntTypeInfo import *
__package__ = None

# ---------------------------------------------------------------------------
class FundamentalInt(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = IntTypeInfo(10, 20)

    # ---------------------------------------------------------------------------
    def test_Invalid(self):
        self.assertRaises(Exception, lambda: IntTypeInfo(20, 10))

    # ---------------------------------------------------------------------------
    def test_Validate(self):
        self._type_info.Validate(10)
        self._type_info.Validate(20)
        self._type_info.Validate(15)
        self.assertRaises(Exception, lambda: self._type_info.Validate(5))       # Below min
        self.assertRaises(Exception, lambda: self._type_info.Validate(25))      # Above max
        self.assertRaises(Exception, lambda: self._type_info.Validate("foo"))   # Wrong type

    # ---------------------------------------------------------------------------
    def test_ToString(self):
        self.assertEqual(self._type_info.ItemToString(15), "15")
        self.assertRaises(Exception, lambda: self._type_info.ItemToString(5))       # Below min
        self.assertRaises(Exception, lambda: self._type_info.ItemToString("foo"))   # Wrong type

    # ---------------------------------------------------------------------------
    def test_FromString(self):
        self.assertEqual(self._type_info.ItemFromString("15"), 15)
        self.assertRaises(Exception, lambda: self._type_info.ItemFromString("5"))   # Below min
        self.assertRaises(Exception, lambda: self._type_info.ItemFromString("foo")) # Wrong type

    # ---------------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(self._type_info.PythonDefinitionString, r'IntTypeInfo(arity=Arity(min=1, max_or_none=1), min=10, max=20)')
        
    # ---------------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(self._type_info.ConstraintsDesc, r"Value must be >= 10, be <= 20")
        
    # ---------------------------------------------------------------------------
    def test_PythonItemRegularExpressionStrings(self):
        self.assertEqual(self._type_info.PythonItemRegularExpressionStrings, r"[0-9]{2}")
        
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
