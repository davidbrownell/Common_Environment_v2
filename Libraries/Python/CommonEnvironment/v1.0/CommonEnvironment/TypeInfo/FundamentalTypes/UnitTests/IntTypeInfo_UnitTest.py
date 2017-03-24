# ----------------------------------------------------------------------
# |  
# |  IntTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-06 17:31:15
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-17.
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
    
    from ..IntTypeInfo import *
    from ... import ValidationException

    __package__ = ni.original

# ----------------------------------------------------------------------
class UnitTest(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    def test_Construct(self):
        # ----------------------------------------------------------------------
        def Impl(min, max, bytes, expected_min, expected_max):
            ti = IntTypeInfo(min, max, bytes)
            
            self.assertEqual(ti.Bytes, bytes)
            self.assertEqual(ti.Min, expected_min)
            self.assertEqual(ti.Max, expected_max)

        # ----------------------------------------------------------------------
        
        Impl(None, None, None, None, None)
        Impl(0, None, None, 0, None)
        Impl(None, 10, None, None, 10)
        Impl(0, 10, None, 0, 10)

        Impl(None, None, 1, -128, 127)
        Impl(0, None, 1, 0, 255)

        Impl(None, None, 2, -32768, 32767)
        Impl(0, None, 2, 0, 65535)

        Impl(None, None, 4, -2147483648, 2147483647)
        Impl(0, None, 4, 0, 4294967295)

        Impl(None, None, 8, -9223372036854775809, 9223372036854775808)
        Impl(0, None, 8, 0, 18446744073709551615)

    # ----------------------------------------------------------------------
    def test_ConstructErrors(self):
        self.assertRaises(Exception, lambda: IntTypeInfo(10, 0))
        self.assertRaises(Exception, lambda: IntTypeInfo(bytes=5))
        self.assertRaises(Exception, lambda: IntTypeInfo(bytes=1, min=-200))
        self.assertRaises(Exception, lambda: IntTypeInfo(bytes=1, max=200))

    # ----------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(IntTypeInfo().ConstraintsDesc, '')
        self.assertEqual(IntTypeInfo(min=0).ConstraintsDesc, "Value must be >= 0")
        self.assertEqual(IntTypeInfo(max=10).ConstraintsDesc, "Value must be <= 10")
        self.assertEqual(IntTypeInfo(min=0, max=10).ConstraintsDesc, "Value must be >= 0, be <= 10")

    # ----------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(IntTypeInfo().PythonDefinitionString, "IntTypeInfo(arity=Arity(min=1, max_or_none=1))")
        self.assertEqual(IntTypeInfo(min=0).PythonDefinitionString, "IntTypeInfo(arity=Arity(min=1, max_or_none=1), min=0)")
        self.assertEqual(IntTypeInfo(max=10).PythonDefinitionString, "IntTypeInfo(arity=Arity(min=1, max_or_none=1), max=10)")
        self.assertEqual(IntTypeInfo(min=0, max=10).PythonDefinitionString, "IntTypeInfo(arity=Arity(min=1, max_or_none=1), min=0, max=10)")
        self.assertEqual(IntTypeInfo(bytes=1).PythonDefinitionString, "IntTypeInfo(arity=Arity(min=1, max_or_none=1), bytes=1)")
        self.assertEqual(IntTypeInfo(bytes=1, min=2).PythonDefinitionString, "IntTypeInfo(arity=Arity(min=1, max_or_none=1), min=2, max=255, bytes=1)")
        self.assertEqual(IntTypeInfo(bytes=2).PythonDefinitionString, "IntTypeInfo(arity=Arity(min=1, max_or_none=1), bytes=2)")
        self.assertEqual(IntTypeInfo(bytes=4).PythonDefinitionString, "IntTypeInfo(arity=Arity(min=1, max_or_none=1), bytes=4)")
        self.assertEqual(IntTypeInfo(bytes=8).PythonDefinitionString, "IntTypeInfo(arity=Arity(min=1, max_or_none=1), bytes=8)")

    # ----------------------------------------------------------------------
    def test_ValidateItem(self):
        ti = IntTypeInfo(min=0, max=10)

        ti.ValidateItem(0)
        ti.ValidateItem(5)
        ti.ValidateItem(10)

        self.assertRaises(ValidationException, lambda: ti.ValidateItem(-1))
        self.assertRaises(ValidationException, lambda: ti.ValidateItem(1000))

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
