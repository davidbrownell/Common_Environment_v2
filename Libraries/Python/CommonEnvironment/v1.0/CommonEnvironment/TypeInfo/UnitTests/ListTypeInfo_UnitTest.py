# ---------------------------------------------------------------------------
# |  
# |  ListTypeInfo_UnitTest.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/29/2015 04:58:18 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Unit test for ListTypeInfo.py
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

    from ..ListTypeInfo import *
    from ..FundamentalTypes import *

    __package__ = ni.original

# ---------------------------------------------------------------------------
class ListTest(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = ListTypeInfo( StringTypeInfo(arity='+'),
                                       arity='*',
                                     )

    # ---------------------------------------------------------------------------
    def test_All(self):
        self._type_info.Validate([ [ "1", "2", "3", ], [ "4", "5", ], [ "6", ], ])
        self._type_info.Validate([])
        self.assertRaises(Exception, lambda: self._type_info.Validate([ [ "1", "2", "3", ], [], [ "4", "5", ], ]))

    # ---------------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(self._type_info.PythonDefinitionString, r'ListTypeInfo(arity=Arity(min=0, max_or_none=None), element_type_info=StringTypeInfo(arity=Arity(min=1, max_or_none=None), min_length=1))')
        
    # ---------------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(self._type_info.ConstraintsDesc, "List of items where: Value must have more than 1 character")
        
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
