# ---------------------------------------------------------------------------
# |  
# |  DictTypeInfo_UnitTest.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/29/2015 04:33:12 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Unit test for DictTypeInfo.py
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

    from ..DictTypeInfo import *
    from ..FundamentalTypes import *

    __package__ = ni.original

# ---------------------------------------------------------------------------
class DictTest(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = DictTypeInfo( foo=StringTypeInfo(),
                                       bar=IntTypeInfo(min=10, max=20),
                                       baz=BoolTypeInfo(),
                                     )

    # ---------------------------------------------------------------------------
    def test_Valid(self):
        d = { "foo" : "hello",
              "bar" : 15,
              "baz" : True,
            }

        self._type_info.Validate(d)

    # ---------------------------------------------------------------------------
    def test_Invalid(self):
        self.assertRaises(Exception, lambda: self._type_info.Validate({}))
        self.assertRaises(Exception, lambda: self._type_info.Validate({ "foo" : "valid", "bar" : 15, }))
        self.assertRaises(Exception, lambda: self._type_info.Validate({ "foo" : "valid", "baz" : True, }))
        self.assertRaises(Exception, lambda: self._type_info.Validate({ "bar" : 15, "baz" : True, }))
        self.assertRaises(Exception, lambda: self._type_info.Validate({ "foo" : "", "bar" : 15, "baz" : True, }))
        self.assertRaises(Exception, lambda: self._type_info.Validate({ "foo" : "valid", "bar" : 5, "baz" : True, }))
        self.assertRaises(Exception, lambda: self._type_info.Validate({ "foo" : "valid", "bar" : 15, "baz" : "Trueish", }))

    # ---------------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(self._type_info.PythonDefinitionString, 'DictTypeInfo(arity=Arity(min=1, max_or_none=1), items={ "baz" : BoolTypeInfo(arity=Arity(min=1, max_or_none=1)), "foo" : StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=1), "bar" : IntTypeInfo(arity=Arity(min=1, max_or_none=1), min=10, max=20) })')
        
    # ---------------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(self._type_info.ConstraintsDesc, "Value must contain the attributes 'baz', 'foo', 'bar'")
        
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
