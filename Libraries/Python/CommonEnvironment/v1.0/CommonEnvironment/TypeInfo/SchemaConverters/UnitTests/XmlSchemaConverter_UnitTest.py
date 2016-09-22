# ----------------------------------------------------------------------
# |  
# |  XmlSchemaConverter_UnitTest.py
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
import textwrap
import unittest

from CommonEnvironment import Package

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with Package.NameInfo(__package__) as ni:
    __package__ = ni.created
    
    from ..XmlSchemaConverter import *
    from ...FundamentalTypes import *

    __package__ = ni.original

# ----------------------------------------------------------------------
class UnitTest(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    def test_Standard(self):
        self.assertEqual(XmlSchemaConverter.Convert(BoolTypeInfo()), "xs:boolean")
        self.assertEqual(XmlSchemaConverter.Convert(DateTimeTypeInfo()), "xs:dateTime")
        self.assertEqual(XmlSchemaConverter.Convert(DateTypeInfo()), "xs:date")
        self.assertEqual(XmlSchemaConverter.Convert(DurationTypeInfo()), "xs:duration")
        self.assertEqual(XmlSchemaConverter.Convert(GuidTypeInfo()), textwrap.dedent(
                                                                        """\
                                                                        <xs:restriction base="xs:string">
                                                                          <xs:pattern value="\\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\\}" />
                                                                        </xs:restriction>
                                                                        """))
        self.assertEqual(XmlSchemaConverter.Convert(TimeTypeInfo()), "xs:time")

    # ----------------------------------------------------------------------
    def test_FilenameDirectory(self):
        # TODO: ensure_exists [Filename/Directory]
        # TODO: match_directory [Filename]
        self.assertEqual(XmlSchemaConverter.Convert(DirectoryTypeInfo()), textwrap.dedent(
                                                                            """\
                                                                            <xs:restriction base="xs:string">
                                                                              <xs:minLength value="1" />
                                                                            </xs:restriction>
                                                                            """))

        self.assertEqual(XmlSchemaConverter.Convert(FilenameTypeInfo()), textwrap.dedent(
                                                                            """\
                                                                            <xs:restriction base="xs:string">
                                                                              <xs:minLength value="1" />
                                                                            </xs:restriction>
                                                                            """))
    
    # ----------------------------------------------------------------------
    def test_Enum(self):
        self.assertEqual(XmlSchemaConverter.Convert(EnumTypeInfo([ "one", "two", "three", ])), textwrap.dedent(
                                                                                                    """\
                                                                                                    <xs:restriction base="xs:string">
                                                                                                      <xs:enumeration value="one" />
                                                                                                      <xs:enumeration value="two" />
                                                                                                      <xs:enumeration value="three" />
                                                                                                    </xs:restriction>
                                                                                                    """))

        self.assertEqual(XmlSchemaConverter.Convert(EnumTypeInfo([ "one", "two", "three", ], friendly_values=[ "1", "2", "3", ])), textwrap.dedent(
                                                                                                    """\
                                                                                                    <xs:restriction base="xs:string">
                                                                                                      <xs:enumeration value="one" />
                                                                                                      <xs:enumeration value="two" />
                                                                                                      <xs:enumeration value="three" />
                                                                                                    </xs:restriction>
                                                                                                    """))

    # ----------------------------------------------------------------------
    def test_Float(self):
        self.assertEqual(XmlSchemaConverter.Convert(FloatTypeInfo()), "xs:decimal")
        self.assertEqual(XmlSchemaConverter.Convert(FloatTypeInfo(min=2.0)), textwrap.dedent(
                                                                                """\
                                                                                <xs:restriction base="xs:decimal">
                                                                                  <xs:minInclusive value="2.0" />
                                                                                </xs:restriction>
                                                                                """))
        self.assertEqual(XmlSchemaConverter.Convert(FloatTypeInfo(max=10.5)), textwrap.dedent(
                                                                                """\
                                                                                <xs:restriction base="xs:decimal">
                                                                                  <xs:maxInclusive value="10.5" />
                                                                                </xs:restriction>
                                                                                """))
        self.assertEqual(XmlSchemaConverter.Convert(FloatTypeInfo(min=2.0, max=10.5)), textwrap.dedent(
                                                                                """\
                                                                                <xs:restriction base="xs:decimal">
                                                                                  <xs:minInclusive value="2.0" />
                                                                                  <xs:maxInclusive value="10.5" />
                                                                                </xs:restriction>
                                                                                """))

    # ----------------------------------------------------------------------
    def test_Int(self):
        self.assertEqual(XmlSchemaConverter.Convert(IntTypeInfo()), "xs:integer")
        self.assertEqual(XmlSchemaConverter.Convert(IntTypeInfo(bytes=1)), "xs:byte")
        self.assertEqual(XmlSchemaConverter.Convert(IntTypeInfo(bytes=2)), "xs:short")
        self.assertEqual(XmlSchemaConverter.Convert(IntTypeInfo(bytes=4)), "xs:int")
        self.assertEqual(XmlSchemaConverter.Convert(IntTypeInfo(bytes=8)), "xs:long")

        self.assertEqual(XmlSchemaConverter.Convert(IntTypeInfo(min=0)), "xs:nonNegativeInteger")
        self.assertEqual(XmlSchemaConverter.Convert(IntTypeInfo(min=0, bytes=1)), "xs:nonNegativeByte")
        self.assertEqual(XmlSchemaConverter.Convert(IntTypeInfo(min=0, bytes=2)), "xs:nonNegativeShort")
        self.assertEqual(XmlSchemaConverter.Convert(IntTypeInfo(min=0, bytes=4)), "xs:nonNegativeInt")
        self.assertEqual(XmlSchemaConverter.Convert(IntTypeInfo(min=0, bytes=8)), "xs:nonNegativeLong")

        self.assertEqual(XmlSchemaConverter.Convert(IntTypeInfo(min=2)), textwrap.dedent(
                                                                            """\
                                                                            <xs:restrictions base="xs:nonNegativeInteger">
                                                                              <xs:minInclusive value="2" />
                                                                            </xs:restrictions>
                                                                            """))

        self.assertEqual(XmlSchemaConverter.Convert(IntTypeInfo(min=2, bytes=1)), textwrap.dedent(
                                                                            """\
                                                                            <xs:restrictions base="xs:nonNegativeByte">
                                                                              <xs:minInclusive value="2" />
                                                                              <xs:maxInclusive value="255" />
                                                                            </xs:restrictions>
                                                                            """))

        self.assertEqual(XmlSchemaConverter.Convert(IntTypeInfo(min=2, bytes=2)), textwrap.dedent(
                                                                            """\
                                                                            <xs:restrictions base="xs:nonNegativeShort">
                                                                              <xs:minInclusive value="2" />
                                                                              <xs:maxInclusive value="65535" />
                                                                            </xs:restrictions>
                                                                            """))

        self.assertEqual(XmlSchemaConverter.Convert(IntTypeInfo(min=2, bytes=4)), textwrap.dedent(
                                                                            """\
                                                                            <xs:restrictions base="xs:nonNegativeInt">
                                                                              <xs:minInclusive value="2" />
                                                                              <xs:maxInclusive value="4294967295" />
                                                                            </xs:restrictions>
                                                                            """))

        self.assertEqual(XmlSchemaConverter.Convert(IntTypeInfo(min=2, bytes=8)), textwrap.dedent(
                                                                            """\
                                                                            <xs:restrictions base="xs:nonNegativeLong">
                                                                              <xs:minInclusive value="2" />
                                                                              <xs:maxInclusive value="18446744073709551615" />
                                                                            </xs:restrictions>
                                                                            """))

        self.assertEqual(XmlSchemaConverter.Convert(IntTypeInfo(max=10)), textwrap.dedent(
                                                                            """\
                                                                            <xs:restrictions base="xs:integer">
                                                                              <xs:maxInclusive value="10" />
                                                                            </xs:restrictions>
                                                                            """))
        
        self.assertEqual(XmlSchemaConverter.Convert(IntTypeInfo(max=-2)), textwrap.dedent(
                                                                            """\
                                                                            <xs:restrictions base="xs:negativeInteger">
                                                                              <xs:maxInclusive value="-2" />
                                                                            </xs:restrictions>
                                                                            """))

    # ----------------------------------------------------------------------
    def test_String(self):
        self.assertEqual(XmlSchemaConverter.Convert(StringTypeInfo(min_length=0)), "xs:string")
        self.assertEqual(XmlSchemaConverter.Convert(StringTypeInfo()), textwrap.dedent(
                                                                        """\
                                                                        <xs:restriction base="xs:string">
                                                                          <xs:minLength value="1" />
                                                                        </xs:restriction>
                                                                        """))
        self.assertEqual(XmlSchemaConverter.Convert(StringTypeInfo(min_length=2)), textwrap.dedent(
                                                                        """\
                                                                        <xs:restriction base="xs:string">
                                                                          <xs:minLength value="2" />
                                                                        </xs:restriction>
                                                                        """))
        self.assertEqual(XmlSchemaConverter.Convert(StringTypeInfo(max_length=10)), textwrap.dedent(
                                                                        """\
                                                                        <xs:restriction base="xs:string">
                                                                          <xs:minLength value="1" />
                                                                          <xs:maxLength value="10" />
                                                                        </xs:restriction>
                                                                        """))
        self.assertEqual(XmlSchemaConverter.Convert(StringTypeInfo(min_length=2, max_length=10)), textwrap.dedent(
                                                                        """\
                                                                        <xs:restriction base="xs:string">
                                                                          <xs:minLength value="2" />
                                                                          <xs:maxLength value="10" />
                                                                        </xs:restriction>
                                                                        """))
        self.assertEqual(XmlSchemaConverter.Convert(StringTypeInfo(validation_expression="foo")), textwrap.dedent(
                                                                        """\
                                                                        <xs:restriction base="xs:string">
                                                                          <xs:pattern value="foo" />
                                                                        </xs:restriction>
                                                                        """))

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
