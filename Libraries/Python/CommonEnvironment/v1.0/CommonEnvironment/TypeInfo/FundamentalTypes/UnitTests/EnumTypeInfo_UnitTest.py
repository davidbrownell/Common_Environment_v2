# ----------------------------------------------------------------------
# |  
# |  EnumTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-06 17:31:15
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-18.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import sys
import unittest

from CommonEnvironment import Package

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with Package.NameInfo(__package__) as ni:
    __package__ = ni.created
    
    from ..EnumTypeInfo import *
    from ... import ValidationException

    __package__ = ni.original

# ----------------------------------------------------------------------
class UnitTest(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    @classmethod
    def setUp(cls):
        cls._ti = EnumTypeInfo([ "one", "two", "three", ])
        cls._ti_friendly = EnumTypeInfo([ "one", "two", "three", ], [ "1", "2", "3", ])

    # ----------------------------------------------------------------------
    def test_ConstructErrors(self):
        self.assertRaises(Exception, lambda: EnumTypeInfo([]))
        self.assertRaises(Exception, lambda: EnumTypeInfo([ "one", ], [ "1", "2", ]))

    # ----------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(self._ti.ConstraintsDesc, 'Value must be one of "one", "two", "three"')
        self.assertEqual(EnumTypeInfo([ "one", ]).ConstraintsDesc, 'Value must be "one"')

    # ----------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(self._ti.PythonDefinitionString, 'EnumTypeInfo(arity=Arity(min=1, max_or_none=1), values=[ "one", "two", "three" ])')
        self.assertEqual(self._ti_friendly.PythonDefinitionString, 'EnumTypeInfo(arity=Arity(min=1, max_or_none=1), values=[ "one", "two", "three" ], friendly_values=[ "1", "2", "3" ])')

    # ----------------------------------------------------------------------
    def test_ValidateItem(self):
        self._ti.ValidateItem("one")
        self.assertRaises(ValidationException, lambda: self._ti.ValidateItem("One"))
        self.assertRaises(ValidationException, lambda: self._ti.ValidateItem("Four"))

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
