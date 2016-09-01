# ---------------------------------------------------------------------------
# |  
# |  FilenameTypeInfo_UnitTest.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/29/2015 02:42:05 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Unit test for FilenameTypeInfo.py
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

    from ..FilenameTypeInfo import *

    __package__ = ni.original

# ---------------------------------------------------------------------------
class FundamentalFilename(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._one = FilenameTypeInfo(FilenameTypeInfo.Type_File, ensure_exists=True)
        cls._two = FilenameTypeInfo(FilenameTypeInfo.Type_Directory, ensure_exists=False)
        
    # ---------------------------------------------------------------------------
    def test_Validate(self):
        self._one.Validate(_script_fullpath)
        self.assertRaises(Exception, lambda: self._one.Validate("{}_does_not_exist".format(_script_fullpath)))
        self._two.Validate(_script_dir)
        self._two.Validate("{}_does_not_exist".format(_script_dir))
        self.assertRaises(Exception, lambda: self._one.Validate(15))

    # ---------------------------------------------------------------------------
    def test_ToString(self):
        self.assertEqual(self._one.ItemToString(_script_fullpath), _script_fullpath.replace(os.path.sep, '/'))

    # ---------------------------------------------------------------------------
    def test_FromString(self):
        self.assertEqual(self._one.ItemFromString(_script_fullpath.replace(os.path.sep, '/')), _script_fullpath)
        self.assertEqual(self._one.ItemFromString(_script_fullpath), _script_fullpath)

    # ---------------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(self._one.PythonDefinitionString, r'FilenameTypeInfo(arity=Arity(min=1, max_or_none=1), type=FilenameTypeInfo.Type_File, ensure_exists=True)')
        self.assertEqual(self._two.PythonDefinitionString, r'FilenameTypeInfo(arity=Arity(min=1, max_or_none=1), type=FilenameTypeInfo.Type_Directory, ensure_exists=False)')
        
    # ---------------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(self._one.ConstraintsDesc, "Value must be a valid file name")
        self.assertEqual(self._two.ConstraintsDesc, "")
        
    # ---------------------------------------------------------------------------
    def test_PythonItemRegularExpressionString(self):
        self.assertEqual(self._one.PythonItemRegularExpressionString, ".+")
        self.assertEqual(self._two.PythonItemRegularExpressionString, ".+")
        
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
