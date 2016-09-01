# ---------------------------------------------------------------------------
# |  
# |  __init___UnitTest.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/29/2015 05:12:37 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Unit test for __init__.py
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

    from .. import *
    from ..FundamentalTypes import *

    __package__ = ni.original

# ---------------------------------------------------------------------------
class ArityTest(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._zero_or_more = IntTypeInfo(arity='*')
        cls._one_or_more = IntTypeInfo(arity='+')
        cls._fixed = IntTypeInfo(arity="{3}")
        cls._range = IntTypeInfo(arity="{2, 4}")

    # ---------------------------------------------------------------------------
    def test_ZeroOrMore(self):
        self._zero_or_more.Validate([])
        self._zero_or_more.Validate([ 1, 2, 3, ])
        self.assertRaises(Exception, lambda: self._zero_or_more.Validate(1))

    # ---------------------------------------------------------------------------
    def test_OneOrMore(self):
        self._one_or_more.Validate([ 1, ])
        self._one_or_more.ValidateItem(1)
        self._one_or_more.Validate([ 1, 2, 3, ])
        self.assertRaises(Exception, lambda: self._one_or_more.Valudate(1))
        self.assertRaises(Exception, lambda: self._one_or_more.Valudate([]))

    # ---------------------------------------------------------------------------
    def test_Fixed(self):
        self._fixed.Validate([ 1, 2, 3, ])
        self.assertRaises(Exception, lambda: self._fixed.Validate(1))
        self.assertRaises(Exception, lambda: self._fixed.Validate([]))
        self.assertRaises(Exception, lambda: self._fixed.Validate([ 1, 2, ]))
        self.assertRaises(Exception, lambda: self._fixed.Validate([ 1, 2, 3, 4, ]))

    # ---------------------------------------------------------------------------
    def test_Range(self):
        self._range.Validate([ 1, 2, ])
        self._range.Validate([ 1, 2, 3, ])
        self._range.Validate([ 1, 2, 3, 4, ])
        self.assertRaises(Exception, lambda: self._range.Validate(1))
        self.assertRaises(Exception, lambda: self._range.Validate([]))
        self.assertRaises(Exception, lambda: self._range.Validate([ 1, ]))
        self.assertRaises(Exception, lambda: self._range.Validate([ 1, 2, 3, 4, 5, ]))

    # ---------------------------------------------------------------------------
    def test_Postprocess(self):
        self.assertEqual(self._fixed.Postprocess([ 1, 2, 3, ]), [ 1, 2, 3, ])
        
# ---------------------------------------------------------------------------
class FundamentalOptionalArity(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._optional_type_info = StringTypeInfo(arity='?')
        cls._type_info = StringTypeInfo()

    # ---------------------------------------------------------------------------
    def test_Validate(self):
        self._optional_type_info.Validate("value")
        self._optional_type_info.Validate(None)
        self._type_info.Validate("value")
        self.assertRaises(Exception, lambda: self._type_info.Validate(None))

    # ---------------------------------------------------------------------------
    def test_StringConversion(self):
        self.assertEqual(None, self._optional_type_info.FromString(self._optional_type_info.ToString(None)))

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
