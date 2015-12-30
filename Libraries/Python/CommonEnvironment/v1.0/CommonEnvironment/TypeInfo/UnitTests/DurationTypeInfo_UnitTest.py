# ---------------------------------------------------------------------------
# |  
# |  DurationTypeInfo_UnitTest.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/29/2015 04:27:42 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Unit test for DurationTypeInfo.py
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
from ..DurationTypeInfo import *
__package__ = None

# ---------------------------------------------------------------------------
class FundamentalDuration(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = DurationTypeInfo()

    # ---------------------------------------------------------------------------
    def test_Validate(self):
        self._type_info.Validate(datetime.timedelta(seconds=0))
        self.assertRaises(Exception, lambda: self._type_info.Validate("wrong type"))
        self.assertRaises(Exception, lambda: self._type_info.Validate(10))

    # ---------------------------------------------------------------------------
    def test_StringConversion(self):
        d = datetime.timedelta(seconds=140)
        self.assertEqual(d, self._type_info.ItemFromString(self._type_info.ItemToString(d)))
        self.assertEqual(datetime.timedelta(seconds=22), self._type_info.ItemFromString("0:22"))
        self.assertEqual(datetime.timedelta(seconds=22, minutes=1), self._type_info.ItemFromString("1:22"))
        self.assertEqual(datetime.timedelta(seconds=22, minutes=1, hours=3), self._type_info.ItemFromString("3:01:22"))

    # ---------------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(self._type_info.PythonDefinitionString, r'DurationTypeInfo(arity=Arity(min=1, max_or_none=1))')
        
    # ---------------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(self._type_info.ConstraintsDesc, "")
        
    # ---------------------------------------------------------------------------
    def test_PythonItemRegularExpressionStrings(self):
        self.assertEqual(self._type_info.PythonItemRegularExpressionStrings, r"([1-9][0-9]*|0)?:[0-5][0-9](:[0-5][0-9](\.[0-9]+)?)?")
        
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
