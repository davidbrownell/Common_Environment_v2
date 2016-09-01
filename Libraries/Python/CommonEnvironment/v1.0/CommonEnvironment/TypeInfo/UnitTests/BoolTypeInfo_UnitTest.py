# ---------------------------------------------------------------------------
# |  
# |  BoolTypeInfo_UnitTest.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/29/2015 02:48:37 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Unit test for BoolTypeInfo.py
"""

import os
import re
import sys
import unittest

from CommonEnvironment import Package

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

with Package.NameInfo(__package__) as ni:
    __package__ = ni.created

    from ..BoolTypeInfo import *

    __package__ = ni.original

# ---------------------------------------------------------------------------
class FundamentalBool(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = BoolTypeInfo()

    # ---------------------------------------------------------------------------
    def test_Validate(self):
        self._type_info.Validate(True)
        self.assertRaises(Exception, lambda: self._type_info.Validate("wrong type"))

    # ---------------------------------------------------------------------------
    def test_ToString(self):
        self.assertEqual(self._type_info.ItemToString(True), "true")
        self.assertEqual(self._type_info.ItemToString(False), "false")
        
    # ---------------------------------------------------------------------------
    def test_FromString(self):
        self.assertEqual(self._type_info.ItemFromString("True"), True)
        self.assertEqual(self._type_info.ItemFromString("False"), False)
        self.assertEqual(self._type_info.ItemFromString("true"), True)
        self.assertEqual(self._type_info.ItemFromString("false"), False)
        self.assertEqual(self._type_info.ItemFromString("yes"), True)

    # ---------------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(self._type_info.PythonDefinitionString, r'BoolTypeInfo(arity=Arity(min=1, max_or_none=1))')
        
    # ---------------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(self._type_info.ConstraintsDesc, "")
        
    # ---------------------------------------------------------------------------
    def test_PythonItemRegularExpressionString(self):
        self.assertEqual(self._type_info.PythonItemRegularExpressionString, "(true|t|yes|y|1|false|f|no|n|0)")
        
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
