# ----------------------------------------------------------------------
# |  
# |  DictTypeInfo_UnitTest.py
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
    
    from .. import ValidationException
    from ..DictTypeInfo import *
    from ..FundamentalTypes import *
    
    __package__ = ni.original

# ----------------------------------------------------------------------
class UnitTest(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    @classmethod
    def setUp(cls):
        cls._ti = DictTypeInfo( { "foo" : StringTypeInfo(min_length=3),
                                  "bar" : IntTypeInfo(min=10),
                                },
                                require_exact_match=False,
                              )

        cls._ti_exact = DictTypeInfo( { "foo" : StringTypeInfo(min_length=3),
                                        "bar" : IntTypeInfo(min=10),
                                      },
                                      require_exact_match=True,
                                    )

    # ----------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(self._ti.ConstraintsDesc, "Value must contain the attributes 'foo', 'bar'")

    # ----------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(self._ti.PythonDefinitionString, 'DictTypeInfo(arity=Arity(min=1, max_or_none=1), items={ "foo" : StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=3), "bar" : IntTypeInfo(arity=Arity(min=1, max_or_none=1), min=10) }, require_exact_match=False)')

    # ----------------------------------------------------------------------
    def test_IsValidItem(self):
        d = { "foo" : "foo",
              "bar" : 100,
            }

        self.assertTrue(self._ti.IsValidItem(d))
        self.assertTrue(self._ti_exact.IsValidItem(d))

        d["baz"] = 1000

        self.assertTrue(self._ti.IsValidItem(d))
        self.assertTrue(self._ti_exact.IsValidItem(d) == False)

        del d["bar"]

        d["foo"] = "f"
        self.assertRaises(ValidationException, lambda: self._ti.ValidateItem(d))
        d["foo"] = "foo"

        d["bar"] = 1
        self.assertRaises(ValidationException, lambda: self._ti.ValidateItem(d))
        d["bar"] = 10

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
