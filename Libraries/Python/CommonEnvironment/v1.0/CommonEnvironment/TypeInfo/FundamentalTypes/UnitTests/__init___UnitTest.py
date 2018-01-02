# ----------------------------------------------------------------------
# |  
# |  __init___UnitTest.py
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
    
    from .. import *

    __package__ = ni.original

# ----------------------------------------------------------------------
class MyVisitor(Visitor):
    # ----------------------------------------------------------------------
    @staticmethod
    def OnBool(type_info, *args, **kwargs):
        return 1

    # ----------------------------------------------------------------------
    @staticmethod
    def OnDateTime(type_info, *args, **kwargs):
        return 2

    # ----------------------------------------------------------------------
    @staticmethod
    def OnDate(type_info, *args, **kwargs):
        return 3

    # ----------------------------------------------------------------------
    @staticmethod
    def OnDirectory(type_info, *args, **kwargs):
        return 4

    # ----------------------------------------------------------------------
    @staticmethod
    def OnDuration(type_info, *args, **kwargs):
        return 5

    # ----------------------------------------------------------------------
    @staticmethod
    def OnEnum(type_info, *args, **kwargs):
        return 6

    # ----------------------------------------------------------------------
    @staticmethod
    def OnFilename(type_info, *args, **kwargs):
        return 7

    # ----------------------------------------------------------------------
    @staticmethod
    def OnFloat(type_info, *args, **kwargs):
        return 8

    # ----------------------------------------------------------------------
    @staticmethod
    def OnGuid(type_info, *args, **kwargs):
        return 9

    # ----------------------------------------------------------------------
    @staticmethod
    def OnInt(type_info, *args, **kwargs):
        return 10

    # ----------------------------------------------------------------------
    @staticmethod
    def OnString(type_info, *args, **kwargs):
        return 11

    # ----------------------------------------------------------------------
    @staticmethod
    def OnTime(type_info, *args, **kwargs):
        return 12

# ----------------------------------------------------------------------
class UnitTest(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    def _test_impl(self, visitor):
        self.assertEqual(visitor.Accept(BoolTypeInfo()), 1)
        self.assertEqual(visitor.Accept(DateTimeTypeInfo()), 2)
        self.assertEqual(visitor.Accept(DateTypeInfo()), 3)
        self.assertEqual(visitor.Accept(DirectoryTypeInfo()), 4)
        self.assertEqual(visitor.Accept(DurationTypeInfo()), 5)
        self.assertEqual(visitor.Accept(EnumTypeInfo([ "one", "two", "three", ])), 6)
        self.assertEqual(visitor.Accept(FilenameTypeInfo()), 7)
        self.assertEqual(visitor.Accept(FloatTypeInfo()), 8)
        self.assertEqual(visitor.Accept(GuidTypeInfo()), 9)
        self.assertEqual(visitor.Accept(IntTypeInfo()), 10)
        self.assertEqual(visitor.Accept(StringTypeInfo()), 11)
        self.assertEqual(visitor.Accept(TimeTypeInfo()), 12)

    # ----------------------------------------------------------------------
    def test_Visitor(self):
        self._test_impl(MyVisitor)

    # ----------------------------------------------------------------------
    def test_SimpleVisitor(self):
        self._test_impl(CreateSimpleVisitor( lambda *args, **kwargs: 1,
                                             lambda *args, **kwargs: 2,
                                             lambda *args, **kwargs: 3,
                                             lambda *args, **kwargs: 4,
                                             lambda *args, **kwargs: 5,
                                             lambda *args, **kwargs: 6,
                                             lambda *args, **kwargs: 7,
                                             lambda *args, **kwargs: 8,
                                             lambda *args, **kwargs: 9,
                                             lambda *args, **kwargs: 10,
                                             lambda *args, **kwargs: 11,
                                             lambda *args, **kwargs: 12,
                                           ))

        # Call a method that isn't populated
        CreateSimpleVisitor().Accept(BoolTypeInfo())

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
