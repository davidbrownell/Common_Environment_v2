# ---------------------------------------------------------------------------
# |  
# |  GuidTypeInfo_UnitTest.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/29/2015 02:59:51 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Unit test for GuidTypeInfo.py
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
from ..GuidTypeInfo import *
__package__ = None

# ---------------------------------------------------------------------------
class FundamentalGuid(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = GuidTypeInfo()

    # ---------------------------------------------------------------------------
    def test_Validate(self):
        self._type_info.Validate(self._type_info.Create())
        self.assertRaises(Exception, lambda: self._type_info.Validate("wrong type"))

    # ---------------------------------------------------------------------------
    def test_StringConversion(self):
        guid = self._type_info.Create()
        self.assertEqual(guid, self._type_info.ItemFromString(self._type_info.ItemToString(guid)))

    # ---------------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(self._type_info.PythonDefinitionString, r'GuidTypeInfo(arity=Arity(min=1, max_or_none=1))')
        
    # ---------------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(self._type_info.ConstraintsDesc, "")
        
    # ---------------------------------------------------------------------------
    def test_PythonItemRegularExpressionString(self):
        self.assertEqual(self._type_info.PythonItemRegularExpressionString, r"(\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\})|([0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12})|(\{[0-9A-Fa-f]{32}\})|([0-9A-Fa-f]{32})")
        
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
