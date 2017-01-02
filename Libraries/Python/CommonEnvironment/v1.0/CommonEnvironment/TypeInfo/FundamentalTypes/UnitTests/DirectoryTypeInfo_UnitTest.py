# ----------------------------------------------------------------------
# |  
# |  DirectoryTypeInfo_UnitTest.py
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
    
    from ..DirectoryTypeInfo import *
    from ... import ValidationException

    __package__ = ni.original

# ----------------------------------------------------------------------
class UnitTest(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    @classmethod
    def setUp(cls):
        cls._ti = DirectoryTypeInfo()
        cls._ti_not_exists = DirectoryTypeInfo(False)

    # ----------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(self._ti.ConstraintsDesc, "Value must be a valid directory")
        self.assertEqual(self._ti_not_exists.ConstraintsDesc, '')

    # ----------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(self._ti.PythonDefinitionString, "DirectoryTypeInfo(arity=Arity(min=1, max_or_none=1), ensure_exists=True)")
        self.assertEqual(self._ti_not_exists.PythonDefinitionString, "DirectoryTypeInfo(arity=Arity(min=1, max_or_none=1), ensure_exists=False)")

    # ----------------------------------------------------------------------
    def test_ValidateItem(self):
        self._ti.ValidateItem(_script_dir)
        self._ti_not_exists.ValidateItem(_script_dir)

        invalid_dir = os.path.join(_script_dir, "DoesNotExist")

        self.assertRaises(ValidationException, lambda: self._ti.ValidateItem(invalid_dir))
        self._ti_not_exists.ValidateItem(invalid_dir)

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
