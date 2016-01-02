# ---------------------------------------------------------------------------
# |  
# |  EnumTypeInfo_UnitTest.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/29/2015 01:19:50 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Unit test for EnumTypeInfo.py
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
from ..EnumTypeInfo import *
__package__ = None

# ---------------------------------------------------------------------------
class FundamentalEnum(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = EnumTypeInfo([ "a", "b", "c", ])

    # ---------------------------------------------------------------------------
    def test_Invalid(self):
        self.assertRaises(Exception, lambda: EnumTypeInfo([ "a", "b", ], friendly_values=[ "c", ]))     # Wrong number of args between values and friendly_values

    # ---------------------------------------------------------------------------
    def test_Validate(self):
        self._type_info.Validate("a")
        self.assertRaises(Exception, lambda: self._type_info.Validate("not_here"))  # Invalid value

    # ---------------------------------------------------------------------------
    def test_ToString(self):
        self.assertEqual(self._type_info.ItemToString("a"), "a")
        self.assertRaises(Exception, lambda: self._type_info.ItemToString("invalid"))

    # ---------------------------------------------------------------------------
    def test_FromString(self):
        self.assertEqual(self._type_info.ItemFromString("a"), "a")
        self.assertRaises(Exception, lambda: self._type_info.ItemToString("invalid"))

    # ---------------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(self._type_info.PythonDefinitionString, r'EnumTypeInfo(arity=Arity(min=1, max_or_none=1), values=[ "a", "b", "c" ])')
        
    # ---------------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(self._type_info.ConstraintsDesc, r"Value must be one of 'a', 'b', 'c'")
        
    # ---------------------------------------------------------------------------
    def test_PythonItemRegularExpressionStrings(self):
        self.assertEqual(self._type_info.PythonItemRegularExpressionStrings, r"(a|b|c)")
        
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
