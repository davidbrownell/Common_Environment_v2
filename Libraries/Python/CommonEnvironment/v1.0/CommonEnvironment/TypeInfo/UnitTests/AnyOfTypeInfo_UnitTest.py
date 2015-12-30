# ---------------------------------------------------------------------------
# |  
# |  AnyOfTypeInfo_UnitTest.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/29/2015 05:04:41 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Unit test for AnyOfTypeInfo.py
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
from ..AnyOfTypeInfo import *
from ..FundamentalTypes import *
__package__ = None

# ---------------------------------------------------------------------------
class AnyOfTest(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = AnyOfTypeInfo( [ StringTypeInfo(max_length=5),
                                          IntTypeInfo(min=1, max=5),
                                        ],
                                      )

    # ---------------------------------------------------------------------------
    def test_All(self):
        self._type_info.Validate("foo")
        self._type_info.Validate(4)
        self.assertRaises(Exception, lambda: self._type_info.Validate(10.0))    # Wrong type
        self.assertRaises(Exception, lambda: self._type_info.Validate("too long"))
        self.assertRaises(Exception, lambda: self._type_info.Validate(10))      # Too large

    # ---------------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(self._type_info.PythonDefinitionString, r'AnyOfTypeInfo(arity=Arity(min=1, max_or_none=1), type_info_list=[ StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=1, max_length=5), IntTypeInfo(arity=Arity(min=1, max_or_none=1), min=1, max=5) ])')
        
    # ---------------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(self._type_info.ConstraintsDesc, "Value where: String: Value must have more than 1 character, have less than 5 characters / Integer: Value must be >= 1, be <= 5")
        
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
