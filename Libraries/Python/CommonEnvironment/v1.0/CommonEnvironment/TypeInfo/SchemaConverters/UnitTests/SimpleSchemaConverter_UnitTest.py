# ----------------------------------------------------------------------
# |  
# |  SimpleSchemaConverter_UnitTest.py
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
    
    from ..SimpleSchemaConverter import *
    from ...FundamentalTypes import *

    __package__ = ni.original

# ----------------------------------------------------------------------
class UnitTest(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    def test_Name(self):
        self.assertEqual(SimpleSchemaConveter.Convert(BoolTypeInfo(), name="Foo"), "<Foo boolean>")
        self.assertEqual(SimpleSchemaConveter.Convert(BoolTypeInfo(arity='?'), name="Foo"), "<Foo boolean ?>")
        self.assertEqual(SimpleSchemaConveter.Convert(BoolTypeInfo(arity='?'), name="Foo", arity_override='*'), "<Foo boolean *>")
        self.assertEqual(SimpleSchemaConveter.Convert(BoolTypeInfo(arity='?'), name="Foo", arity_override=Arity.FromString('+')), "<Foo boolean +>")

    # ----------------------------------------------------------------------
    def test_Collection(self):
        self.assertEqual(SimpleSchemaConveter.Convert(BoolTypeInfo()), "<boolean>")
        self.assertEqual(SimpleSchemaConveter.Convert(BoolTypeInfo(arity="(2)")), "<boolean {2}>")
        self.assertEqual(SimpleSchemaConveter.Convert(BoolTypeInfo(arity="(2,10)")), "<boolean {2,10}>")
        self.assertEqual(SimpleSchemaConveter.Convert(BoolTypeInfo(arity="?")), "<boolean ?>")
        self.assertEqual(SimpleSchemaConveter.Convert(BoolTypeInfo(arity="1")), "<boolean>")
        self.assertEqual(SimpleSchemaConveter.Convert(BoolTypeInfo(arity="*")), "<boolean *>")
        self.assertEqual(SimpleSchemaConveter.Convert(BoolTypeInfo(arity="+")), "<boolean +>")
    
    # ----------------------------------------------------------------------
    def test_SimpleItems(self):
        self.assertEqual(SimpleSchemaConveter.Convert(BoolTypeInfo()), "<boolean>")
        self.assertEqual(SimpleSchemaConveter.Convert(DateTimeTypeInfo()), "<datetime>")
        self.assertEqual(SimpleSchemaConveter.Convert(DateTypeInfo()), "<date>")
        self.assertEqual(SimpleSchemaConveter.Convert(DurationTypeInfo()), "<duration>")
        self.assertEqual(SimpleSchemaConveter.Convert(GuidTypeInfo()), "<guid>")
        self.assertEqual(SimpleSchemaConveter.Convert(TimeTypeInfo()), "<time>")

    # ----------------------------------------------------------------------
    def test_FilenameDirectory(self):
        self.assertEqual(SimpleSchemaConveter.Convert(DirectoryTypeInfo()), '<filename must_exist="True" type="directory">')
        self.assertEqual(SimpleSchemaConveter.Convert(FilenameTypeInfo()), '<filename must_exist="True" type="file">')
        self.assertEqual(SimpleSchemaConveter.Convert(FilenameTypeInfo(ensure_exists=False, match_any=True)), '<filename must_exist="False" type="either">')
        
    # ----------------------------------------------------------------------
    def test_Enum(self):
        self.assertEqual(SimpleSchemaConveter.Convert(EnumTypeInfo([ "one", "two", "three", ])), '<enum values=[ "one", "two", "three" ]>')
        self.assertEqual(SimpleSchemaConveter.Convert(EnumTypeInfo([ "one", "two", "three", ], friendly_values=[ "1", "2", "3", ])), '<enum values=[ "one", "two", "three" ] friendly_values=[ "1", "2", "3" ]>')

    # ----------------------------------------------------------------------
    def test_Float(self):
        self.assertEqual(SimpleSchemaConveter.Convert(FloatTypeInfo()), '<number>')
        self.assertEqual(SimpleSchemaConveter.Convert(FloatTypeInfo(min=2.0)), '<number min="2.0">')
        self.assertEqual(SimpleSchemaConveter.Convert(FloatTypeInfo(max=10.5)), '<number max="10.5">')
        self.assertEqual(SimpleSchemaConveter.Convert(FloatTypeInfo(min=2.0, max=10.5)), '<number min="2.0" max="10.5">')

    # ----------------------------------------------------------------------
    def test_Int(self):
        self.assertEqual(SimpleSchemaConveter.Convert(IntTypeInfo()), '<integer>')
        self.assertEqual(SimpleSchemaConveter.Convert(IntTypeInfo(min=2)), '<integer min="2">')
        self.assertEqual(SimpleSchemaConveter.Convert(IntTypeInfo(max=10)), '<integer max="10">')
        self.assertEqual(SimpleSchemaConveter.Convert(IntTypeInfo(min=2, max=10)), '<integer min="2" max="10">')
        self.assertEqual(SimpleSchemaConveter.Convert(IntTypeInfo(bytes=4)), '<integer min="-2147483648" max="2147483647" bytes="4">')
        
    # ----------------------------------------------------------------------
    def test_String(self):
        self.assertEqual(SimpleSchemaConveter.Convert(StringTypeInfo()), '<string min_length="1">')
        self.assertEqual(SimpleSchemaConveter.Convert(StringTypeInfo(min_length=2)), '<string min_length="2">')
        self.assertEqual(SimpleSchemaConveter.Convert(StringTypeInfo(max_length=10)), '<string min_length="1" max_length="10">')
        self.assertEqual(SimpleSchemaConveter.Convert(StringTypeInfo(min_length=2, max_length=10)), '<string min_length="2" max_length="10">')
        self.assertEqual(SimpleSchemaConveter.Convert(StringTypeInfo(validation_expression="foo")), '<string validation_expression="foo">')

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
