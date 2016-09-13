# ----------------------------------------------------------------------
# |  
# |  ListTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-06 17:31:15
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016.
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
    
    from .. import ValidationException
    from ..ListTypeInfo import *
    from ..FundamentalTypes import *

    __package__ = ni.original

# ----------------------------------------------------------------------
class UnitTest(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    @classmethod
    def setUp(cls):
        cls._ti = ListTypeInfo( StringTypeInfo(min_length=2, arity="(3)"),
                                arity="(2)",
                              )

    # ----------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(self._ti.ConstraintsDesc, "List of 'String' items where: Value must have more than 2 characters")

    # ----------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(self._ti.PythonDefinitionString, "ListTypeInfo(arity=Arity(min=2, max_or_none=2), element_type_info=StringTypeInfo(arity=Arity(min=3, max_or_none=3), min_length=2))")

    # ----------------------------------------------------------------------
    def test_Standard(self):
        l = [ [ "abc", "def", "ghi", ], [ "012", "345", "678", ], ]

        self.assertTrue(self._ti.IsValid(l))

        l.append([ "xxx", "yyy", "zzz", ])
        self.assertRaises(ValidationException, lambda: self._ti.Validate(l))
        l.pop()

        l[0].append("xxx")
        self.assertRaises(ValidationException, lambda: self._ti.Validate(l))
        l[0].pop()

        l[0][0] = "1"
        self.assertRaises(ValidationException, lambda: self._ti.Validate(l))
        l[0][0] = "abc"

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
