# ----------------------------------------------------------------------
# |  
# |  JsonSchemaConverter_UnitTest.py
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
    
    from ..JsonSchemaConverter import *
    
    from ...ClassTypeInfo import ClassTypeInfo
    from ...FundamentalTypes import *

    __package__ = ni.original

# ----------------------------------------------------------------------
class UnitTest(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    def test_Collection(self):
        self.assertEqual(JsonSchemaConverter.Convert(BoolTypeInfo()), { "type" : "boolean", })
        self.assertEqual(JsonSchemaConverter.Convert(BoolTypeInfo(arity="(3)")), {'minItems': 3, 'items': {'type': 'boolean'}, 'type': 'array', 'maxItems': 3})
        self.assertEqual(JsonSchemaConverter.Convert(BoolTypeInfo(arity="(1, 10)")), {'minItems': 1, 'items': {'type': 'boolean'}, 'type': 'array', 'maxItems': 10})

    # ----------------------------------------------------------------------
    def test_SimpleItems(self):
        self.assertEqual(JsonSchemaConverter.Convert(DateTimeTypeInfo()), { "type" : "string", "format" : "date-time", })
        self.assertEqual(JsonSchemaConverter.Convert(DateTypeInfo()), { "type" : "string", 'pattern': '^(?([0-9]{4})[-/\\.](?(0?[1-9]|1[0-2])[-/\\.](?([0-2][0-9]|3[0-1])$', })
        self.assertEqual(JsonSchemaConverter.Convert(DirectoryTypeInfo()), { "type" : "string", "minLength" : 1, })
        self.assertEqual(JsonSchemaConverter.Convert(DurationTypeInfo()), { "type" : "string", 'pattern': '^(?([1-9][0-9]*|0):(?([0-5][0-9]):(?([0-5][0-9])(?:\.(?([0-9]+))?$', })
        self.assertEqual(JsonSchemaConverter.Convert(EnumTypeInfo([ "one", "two", "three", ])), { "enum" : [ "one", "two", "three", ], })
        self.assertEqual(JsonSchemaConverter.Convert(FilenameTypeInfo()), { "type" : "string", "minLength" : 1, })
        self.assertEqual(JsonSchemaConverter.Convert(GuidTypeInfo()), { "type" : "string", "pattern" : "^\\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\\}$", })
        self.assertEqual(JsonSchemaConverter.Convert(TimeTypeInfo()), { "type" : "string", "pattern" : "^(?([0-1][0-9]|2[0-3]):(?([0-5][0-9]):(?([0-5][0-9])(?:\\.(?(\\d+))?(?:(?(Z)|(?([\\+\\-])(?(\\d{2}):(?([0-5][0-9]))?$", })

    # ----------------------------------------------------------------------
    def test_Float(self):
        self.assertEqual(JsonSchemaConverter.Convert(FloatTypeInfo()), { "type" : "number", })
        self.assertEqual(JsonSchemaConverter.Convert(FloatTypeInfo(min=2.0)), { "type" : "number", "minimum" : 2.0, })
        self.assertEqual(JsonSchemaConverter.Convert(FloatTypeInfo(max=10.5)), { "type" : "number", "maximum" : 10.5, })
        self.assertEqual(JsonSchemaConverter.Convert(FloatTypeInfo(min=2.0, max=10.5)), { "type" : "number", "minimum" : 2.0, "maximum" : 10.5, })

    # ----------------------------------------------------------------------
    def test_Int(self):
        self.assertEqual(JsonSchemaConverter.Convert(IntTypeInfo()), { "type" : "integer", })
        self.assertEqual(JsonSchemaConverter.Convert(IntTypeInfo(min=2)), { "type" : "integer", "minimum" : 2, })
        self.assertEqual(JsonSchemaConverter.Convert(IntTypeInfo(max=10)), { "type" : "integer", "maximum" : 10, })
        self.assertEqual(JsonSchemaConverter.Convert(IntTypeInfo(min=2, max=10)), { "type" : "integer", "minimum" : 2, "maximum" : 10, })

    # ----------------------------------------------------------------------
    def test_String(self):
        self.assertEqual(JsonSchemaConverter.Convert(StringTypeInfo()), { "type" : "string", "minLength" : 1, })
        self.assertEqual(JsonSchemaConverter.Convert(StringTypeInfo(min_length=0)), { "type" : "string", })
        self.assertEqual(JsonSchemaConverter.Convert(StringTypeInfo(min_length=10)), { "type" : "string", "minLength" : 10, })
        self.assertEqual(JsonSchemaConverter.Convert(StringTypeInfo(max_length=20)), { "type" : "string", "minLength" : 1, "maxLength" : 20, })
        self.assertEqual(JsonSchemaConverter.Convert(StringTypeInfo(min_length=10, max_length=20)), { "type" : "string", "minLength" : 10, "maxLength" : 20, })
        self.assertEqual(JsonSchemaConverter.Convert(StringTypeInfo(validation_expression="Foo")), { "type" : "string", "pattern" : "^Foo$", })

    # ----------------------------------------------------------------------
    def test_Class(self):
        self.assertEqual(JsonSchemaConverter.Convert(ClassTypeInfo(foo=StringTypeInfo(), bar=IntTypeInfo())), { "type" : "object",
                                                                                                                "properties" : { "foo" : { "type" : "string", "minLength" : 1, },
                                                                                                                                 "bar" : { "type" : "integer", },
                                                                                                                               },
                                                                                                                "required" : [ "foo", "bar", ],
                                                                                                              })

        self.assertEqual(JsonSchemaConverter.Convert(ClassTypeInfo(foo=StringTypeInfo(), bar=IntTypeInfo(arity='?'))), { "type" : "object",
                                                                                                                         "properties" : { "foo" : { "type" : "string", "minLength" : 1, },
                                                                                                                                          "bar" : { "type" : "integer", },
                                                                                                                                        },
                                                                                                                         "required" : [ "foo", ],
                                                                                                                       })

        self.assertEqual(JsonSchemaConverter.Convert(ClassTypeInfo(foo=StringTypeInfo(), bar=IntTypeInfo(arity='?'), baz=ClassTypeInfo(a=IntTypeInfo(), b=DateTimeTypeInfo()), )), 
                         { "type" : "object",
                           "properties" : { "foo" : { "type" : "string", "minLength" : 1, },
                                            "bar" : { "type" : "integer", },
                                            "baz" : { "type" : "object",
                                                      "properties" : { "a" : { "type" : "integer", },
                                                                       "b" : { "type" : "string", "format" : "date-time", },
                                                                     },
                                                      "required" : [ "a", "b", ],
                                                    },                         
                                          },
                           "required" : [ "baz", "foo", ],
                         })

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
