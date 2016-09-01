# ---------------------------------------------------------------------------
# |  
# |  FloatTypeInfo_UnitTest.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/29/2015 02:37:15 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Unit test for FloatTypeInfo.py
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

    from ..FloatTypeInfo import *

    __package__ = ni.original

# ---------------------------------------------------------------------------
class FundamentalFloat(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = FloatTypeInfo(10, 20)

    # ---------------------------------------------------------------------------
    def test_Invalid(self):
        self.assertRaises(Exception, lambda: FloatTypeInfo(20, 10))

    # ---------------------------------------------------------------------------
    def test_Validate(self):
        self._type_info.Validate(10)
        self._type_info.Validate(20.0)
        self._type_info.Validate(15.5)
        self.assertRaises(Exception, lambda: self._type_info.Validate(5))       # Below min
        self.assertRaises(Exception, lambda: self._type_info.Validate(25.2))    # Above max
        self.assertRaises(Exception, lambda: self._type_info.Validate("foo"))   # Wrong type

    # ---------------------------------------------------------------------------
    def test_ToString(self):
        self.assertEqual(self._type_info.ItemToString(15.2), "15.2")
        self.assertRaises(Exception, lambda: self._type_info.ItemToString(5.0))     # Below min
        self.assertRaises(Exception, lambda: self._type_info.ItemToString("foo"))   # Wrong type

    # ---------------------------------------------------------------------------
    def test_FromString(self):
        self.assertEqual(self._type_info.ItemFromString("15.0"), 15.0)
        self.assertRaises(Exception, lambda: self._type_info.ItemFromString("5"))   # Below min
        self.assertRaises(Exception, lambda: self._type_info.ItemFromString("foo")) # Wrong type

    # ---------------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(self._type_info.PythonDefinitionString, r'FloatTypeInfo(arity=Arity(min=1, max_or_none=1), min=10.0, max=20.0)')
        
    # ---------------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(self._type_info.ConstraintsDesc, r"Value must be >= 10.0, be <= 20.0")
        
    # ---------------------------------------------------------------------------
    def test_PythonItemRegularExpressionString(self):
        self.assertEqual(self._type_info.PythonItemRegularExpressionString, r"[0-9]{2}\.[0-9]+")
        
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
