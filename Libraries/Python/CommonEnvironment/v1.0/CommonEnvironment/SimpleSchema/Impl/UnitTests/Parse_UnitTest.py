# ---------------------------------------------------------------------------
# |  
# |  Parse_UnitTest.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/08/2015 07:43:29 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Unit test for Parse.py
"""

import os
import sys
import textwrap
import unittest

from collections import OrderedDict

from CommonEnvironment import CallOnExit
from CommonEnvironment import QuickObject

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.normpath(os.path.join(_script_dir, "..")))
with CallOnExit.CallOnExit(lambda: sys.path.pop(0)):
    from Parse import *

# ---------------------------------------------------------------------------
class FundamentalBaseTestCase(unittest.TestCase):

    BRACKETS                                = [ ( '<', '>' ),
                                                ( '(', ')' ),
                                                ( '[', ']', ),
                                              ]

    NAMES                                   = [ "MyItem", None, ]

    # ---------------------------------------------------------------------------
    def Test(self, brackets, type, metadata, name=None, observer=None):
        definition = "{lbrack}{name}{type} {metadata}{rbrack}".format( lbrack=brackets[0],
                                                                       rbrack=brackets[1],
                                                                       name="{} ".format(name) if name else '',
                                                                       type=type,
                                                                       metadata=' '.join([ "{}={}".format(k, v) for k, v in metadata.iteritems() ]),
                                                                     )
        root = ParseStrings({ "Test" : definition, }, observer=observer)
        self.assertTrue(len(root.items) == 1)

        return root.items[0]

    # ---------------------------------------------------------------------------
    @staticmethod
    def MetadataToUnicode(metadata, **conversion_items):
        # ---------------------------------------------------------------------------
        def ToUnicode(s):
            return unicode(s, "utf-8")

        # ---------------------------------------------------------------------------
        
        new_metadata = OrderedDict()

        for k, v in metadata.iteritems():
            k = ToUnicode(k)

            if ( (v[0] == '"' and v[-1] == '"') or
                 (v[0] == "'" and v[-1] == "'")
               ):
                v = v[1:-1]
            
            if k in conversion_items:
                v = conversion_items[k](v)
            else:
                v = ToUnicode(v)

            new_metadata[k] = v

        return new_metadata

# ---------------------------------------------------------------------------
class FundamentalBaseTestCaseNoCustomMetadata(FundamentalBaseTestCase):

    TYPE_STRING                             = None
    TYPE_VALUE                              = None
    OBSERVER                                = None

    # ---------------------------------------------------------------------------
    def test_Basic(self):
        if self.TYPE_STRING == None:
            return

        for name in self.NAMES:
            for brackets in self.BRACKETS:
                item = self.Test(brackets, self.TYPE_STRING, {}, name=name, observer=self.OBSERVER)

                self.assertEqual(item.name, name)
                self.assertEqual(item.declaration_type, self.TYPE_VALUE)
                self.assertEqual(len(item.metadata), 0)

    # ---------------------------------------------------------------------------
    def test_SingleMetadata(self):
        if self.TYPE_STRING == None:
            return

        for name in self.NAMES:
            for brackets in self.BRACKETS:
                item = self.Test(brackets, self.TYPE_STRING, { "foo" : '"bar"', }, name=name, observer=self.OBSERVER)

                self.assertEqual(item.name, name)
                self.assertEqual(item.declaration_type, self.TYPE_VALUE)
                self.assertEqual(len(item.metadata), 1)
                self.assertEqual(item.metadata.keys()[0], "foo")
                self.assertEqual(item.metadata.values()[0], "bar")

    # ---------------------------------------------------------------------------
    def test_DualMetadata(self):
        if self.TYPE_STRING == None:
            return

        for name in self.NAMES:
            for brackets in self.BRACKETS:
                item = self.Test(brackets, self.TYPE_STRING, OrderedDict([ ( "foo", '"bar"' ), ( "baz", '"100"' ) ]), name=name, observer=self.OBSERVER)

                self.assertEqual(item.name, name)
                self.assertEqual(item.declaration_type, self.TYPE_VALUE)
                self.assertEqual(len(item.metadata), 2)
                
                self.assertEqual(item.metadata.keys()[0], "foo")
                self.assertEqual(item.metadata.values()[0], "bar")

                self.assertEqual(item.metadata.keys()[1], "baz")
                self.assertEqual(item.metadata.values()[1], "100")

# ---------------------------------------------------------------------------
class FundamentalTests_String(FundamentalBaseTestCase):
    
    # ---------------------------------------------------------------------------
    def test_Basic(self):
        for name in self.NAMES:
            for brackets in self.BRACKETS:
                item = self.Test(brackets, "string", {}, name=name)

                self.assertEqual(item.name, name)
                self.assertEqual(item.declaration_type, SimpleSchemaParser.STRING_TYPE)
                self.assertTrue(len(item.metadata) == 0)

    # ---------------------------------------------------------------------------
    def test_SingleValidMetadata(self):
        for name in self.NAMES:
            for brackets in self.BRACKETS:
                for metadata_tag in [ "validation", "other", ]:
                    item = self.Test(brackets, "string", { metadata_tag : '"foo"', }, name=name)

                    self.assertEqual(item.name, name)
                    self.assertEqual(item.declaration_type, SimpleSchemaParser.STRING_TYPE)
                    self.assertTrue(len(item.metadata) == 1)
                    self.assertEqual(item.metadata.keys()[0], metadata_tag)
                    self.assertEqual(item.metadata.values()[0], "foo")

    # ---------------------------------------------------------------------------
    def test_MultipleValidMetadata(self):
        for name in self.NAMES:
            for brackets in self.BRACKETS:
                for metadata in [ OrderedDict([ ( "validation", '"foo"' ), ( "min_length", '"10"' ), ]),
                                  OrderedDict([ ( "max_length", '"20"' ), ( "foo", '"bar"' ), ]),
                                  OrderedDict([ ( "foo", '"bar"' ), ( "baz", '"biz"' ), ]),
                                ]:
                    item = self.Test(brackets, "string", metadata, name=name)

                    metadata = self.MetadataToUnicode( metadata, 
                                                       min_length=int,
                                                       max_length=int,
                                                     )
                    
                    self.assertEqual(item.name, name)
                    self.assertEqual(item.declaration_type, SimpleSchemaParser.STRING_TYPE)
                    self.assertEqual(item.metadata, metadata)

# ---------------------------------------------------------------------------
class FundamentalTests_Enum(FundamentalBaseTestCase):

    # ---------------------------------------------------------------------------
    def test_Basic(self):
        for name in self.NAMES:
            for brackets in self.BRACKETS:
                item = self.Test(brackets, "enum", { "values" : "[ 'a', 'b', 'c', ]", }, name=name)

                self.assertEqual(item.name, name)
                self.assertEqual(item.declaration_type, SimpleSchemaParser.ENUM_TYPE)
                self.assertTrue(len(item.metadata) == 1)
                self.assertEqual(item.metadata["values"], [ 'a', 'b', 'c', ])

    # ---------------------------------------------------------------------------
    def test_SingleValidMetadata(self):
        for name in self.NAMES:
            for brackets in self.BRACKETS:
                for metadata_tag in [ "friendly_values", ]:
                    item = self.Test( brackets, 
                                      "enum", 
                                      OrderedDict([ ( "values", "[ 'a', 'b', 'c', ]" ),
                                                    ( metadata_tag, "[ '1', '2', '3', ]" ), 
                                                  ]), 
                                      name=name,
                                    )

                    self.assertEqual(item.name, name)
                    self.assertEqual(item.declaration_type, SimpleSchemaParser.ENUM_TYPE)
                    self.assertTrue(len(item.metadata) == 2)
                    self.assertEqual(item.metadata.keys()[0], "values")
                    self.assertEqual(item.metadata.values()[0], [ 'a', 'b', 'c', ])
                    self.assertEqual(item.metadata.keys()[1], metadata_tag)
                    self.assertEqual(item.metadata.values()[1], [ '1', '2', '3', ])

# ---------------------------------------------------------------------------
class FundamentalTests_Integer(FundamentalBaseTestCase):

    # ---------------------------------------------------------------------------
    def test_Basic(self):
        for name in self.NAMES:
            for brackets in self.BRACKETS:
                item = self.Test(brackets, "integer", {}, name=name)

                self.assertEqual(item.name, name)
                self.assertEqual(item.declaration_type, SimpleSchemaParser.INTEGER_TYPE)
                self.assertTrue(len(item.metadata) == 0)

    # ---------------------------------------------------------------------------
    def test_SingleValidMetadata(self):
        for name in self.NAMES:
            for brackets in self.BRACKETS:
                for metadata_tag in [ "min", "other", ]:
                    item = self.Test(brackets, "integer", { metadata_tag : '"10"', }, name=name)

                    self.assertEqual(item.name, name)
                    self.assertEqual(item.declaration_type, SimpleSchemaParser.INTEGER_TYPE)
                    self.assertTrue(len(item.metadata) == 1)
                    self.assertEqual(item.metadata.keys()[0], metadata_tag)
                    self.assertEqual(item.metadata.values()[0], 10 if metadata_tag == "min" else "10")

# ---------------------------------------------------------------------------
class FundamentalTests_Number(FundamentalBaseTestCase):

    # ---------------------------------------------------------------------------
    def test_Basic(self):
        for name in self.NAMES:
            for brackets in self.BRACKETS:
                item = self.Test(brackets, "number", {}, name=name)

                self.assertEqual(item.name, name)
                self.assertEqual(item.declaration_type, SimpleSchemaParser.NUMBER_TYPE)
                self.assertTrue(len(item.metadata) == 0)

    # ---------------------------------------------------------------------------
    def test_SingleValidMetadata(self):
        for name in self.NAMES:
            for brackets in self.BRACKETS:
                for metadata_tag in [ "min", "other", ]:
                    item = self.Test(brackets, "number", { metadata_tag : '"10.0"', }, name=name)

                    self.assertEqual(item.name, name)
                    self.assertEqual(item.declaration_type, SimpleSchemaParser.NUMBER_TYPE)
                    self.assertTrue(len(item.metadata) == 1)
                    self.assertEqual(item.metadata.keys()[0], metadata_tag)
                    self.assertEqual(item.metadata.values()[0], 10.0 if metadata_tag == "min" else "10.0")

# ---------------------------------------------------------------------------
class FundamentalTests_Boolean(FundamentalBaseTestCaseNoCustomMetadata):
    TYPE_STRING                             = "boolean"
    TYPE_VALUE                              = SimpleSchemaParser.BOOLEAN_TYPE

# ---------------------------------------------------------------------------
class FundamentalTests_Guid(FundamentalBaseTestCaseNoCustomMetadata):
    TYPE_STRING                             = "guid"
    TYPE_VALUE                              = SimpleSchemaParser.GUID_TYPE

# ---------------------------------------------------------------------------
class FundamentalTests_DateTime(FundamentalBaseTestCaseNoCustomMetadata):
    TYPE_STRING                             = "datetime"
    TYPE_VALUE                              = SimpleSchemaParser.DATETIME_TYPE

# ---------------------------------------------------------------------------
class FundamentalTests_Date(FundamentalBaseTestCaseNoCustomMetadata):
    TYPE_STRING                             = "date"
    TYPE_VALUE                              = SimpleSchemaParser.DATE_TYPE

# ---------------------------------------------------------------------------
class FundamentalTests_Time(FundamentalBaseTestCaseNoCustomMetadata):
    TYPE_STRING                             = "time"
    TYPE_VALUE                              = SimpleSchemaParser.TIME_TYPE

# ---------------------------------------------------------------------------
class FundamentalTests_Duration(FundamentalBaseTestCaseNoCustomMetadata):
    TYPE_STRING                             = "duration"
    TYPE_VALUE                              = SimpleSchemaParser.DURATION_TYPE

# ---------------------------------------------------------------------------
class FundamentalTests_Filename(FundamentalBaseTestCase):

    # ---------------------------------------------------------------------------
    def test_Basic(self):
        for name in self.NAMES:
            for brackets in self.BRACKETS:
                item = self.Test(brackets, "filename", {}, name=name)

                self.assertEqual(item.name, name)
                self.assertEqual(item.declaration_type, SimpleSchemaParser.FILENAME_TYPE)
                self.assertTrue(len(item.metadata) == 0)

    # ---------------------------------------------------------------------------
    def test_SingleValidMetadata(self):
        for name in self.NAMES:
            for brackets in self.BRACKETS:
                for metadata in [ { "type" : '"file"' },
                                  { "type" : '"directory"' },
                                  { "must_exist" : '"true"' },
                                  { "must_exist" : '"false"' },
                                ]:
                    item = self.Test(brackets, "filename", metadata, name=name)

                    metadata = self.MetadataToUnicode(metadata, must_exist=lambda v: v == "true")

                    self.assertEqual(item.name, name)
                    self.assertEqual(item.declaration_type, SimpleSchemaParser.FILENAME_TYPE)
                    self.assertEqual(item.metadata, metadata)

# ---------------------------------------------------------------------------
class FundamentalTests_Custom(FundamentalBaseTestCase):

    # ---------------------------------------------------------------------------
    def test_Basic(self):
        for name in self.NAMES:
            for brackets in self.BRACKETS:
                item = self.Test(brackets, "custom", { "t" : '"foo"', }, name=name)

                self.assertEqual(item.name, name)
                self.assertEqual(item.declaration_type, SimpleSchemaParser.CUSTOM_TYPE)
                self.assertTrue(len(item.metadata) == 1)
                self.assertEqual(item.metadata.keys()[0], "t")
                self.assertEqual(item.metadata.values()[0], "foo")

    # ---------------------------------------------------------------------------
    def test_SingleValidMetadata(self):
        for name in self.NAMES:
            for brackets in self.BRACKETS:
                for metadata in [ OrderedDict([ ( "t", '"foo"' ), ( "description", '"desc"' ), ]),
                                  OrderedDict([ ( "t", '"foo"' ), ( "bar", '"baz"' ), ]),
                                  OrderedDict([ ( "t", '"foo"' ), ( "description", '"desc"' ), ( "bar", '"baz"' ), ]),
                                ]:
                    item = self.Test(brackets, "custom", metadata, name=name)

                    metadata = self.MetadataToUnicode(metadata)

                    self.assertEqual(item.name, name)
                    self.assertEqual(item.declaration_type, SimpleSchemaParser.CUSTOM_TYPE)
                    self.assertEqual(item.metadata, metadata)

# ---------------------------------------------------------------------------
class FundamentalTests_Id(FundamentalBaseTestCaseNoCustomMetadata):
    TYPE_STRING                             = "custom_id"
    TYPE_VALUE                              = SimpleSchemaParser.ID

    observer = DefaultObserver()
    observer.Flags &= ~observer.ParseFlags.ResolveReferences

    OBSERVER                                = observer

# ---------------------------------------------------------------------------
class ObjectTests(unittest.TestCase):

    # ---------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super(ObjectTests, self).__init__(*args, **kwargs)

        observer = DefaultObserver()
        observer.Flags &= observer.Flags & ~observer.ParseFlags.ResolveReferences

        self._observer = observer

    # ---------------------------------------------------------------------------
    def test_Pass(self):
        for name in [ "MyItem", None, ]:
            for brackets in [ ( '<', '>' ),
                              ( '(', ')' ),
                            ]:
                for base in [ None, "base", ]:
                    if name == None and base != None:
                        continue

                    for arity, expected_arity in [ ( None, None ),
                                                   ( '?', (0, 1) ),
                                                   ( '*', (0, None) ),
                                                   ( '+', (1, None) ),
                                                   ( '{1}', (1, 1) ),
                                                   ( '{2,10}', (2, 10) ),
                                                 ]:
                        definition = "{lbracket}{name}{base}{arity}{rbracket}: pass".format( lbracket=brackets[0],
                                                                                             rbracket=brackets[1],
                                                                                             name=name or '',
                                                                                             base=" {}".format(base) if base else '',
                                                                                             arity=" {}".format(arity) if arity else '',
                                                                                           )

                        root = ParseStrings({ "Test" : definition, }, self._observer)
                        self.assertTrue(len(root.items) == 1)

                        item = root.items[0]

                        self.assertEqual(item.name, name)
                        self.assertEqual(item.declaration_type, -SimpleSchemaParser.RULE_obj)
                        self.assertEqual(item.arity, expected_arity)
                        self.assertEqual(item.reference, base)
                        self.assertEqual(len(item.items), 0)

    # ---------------------------------------------------------------------------
    def test_SingleItem(self):
        for name in [ "MyItem", None, ]:
            for brackets in [ ( '<', '>' ),
                              ( '(', ')' ),
                            ]:
                for base in [ None, "base", ]:
                    if name == None and base != None:
                        continue

                    for arity, expected_arity in [ ( None, None ),
                                                   ( '?', (0, 1) ),
                                                   ( '*', (0, None) ),
                                                   ( '+', (1, None) ),
                                                   ( '{1}', (1, 1) ),
                                                   ( '{2,10}', (2, 10) ),
                                                 ]:
                        definition = "{lbracket}{name}{base}{arity}{rbracket}: <foo string>".format( lbracket=brackets[0],
                                                                                                     rbracket=brackets[1],
                                                                                                     name=name or '',
                                                                                                     base=" {}".format(base) if base else '',
                                                                                                     arity=" {}".format(arity) if arity else '',
                                                                                                   )

                        root = ParseStrings({ "Test" : definition, }, self._observer)
                        self.assertTrue(len(root.items) == 1)

                        item = root.items[0]

                        self.assertEqual(item.name, name)
                        self.assertEqual(item.declaration_type, -SimpleSchemaParser.RULE_obj)
                        self.assertEqual(item.arity, expected_arity)
                        self.assertEqual(item.reference, base)

                        self.assertEqual(len(item.items), 1)
                        self.assertEqual(item.items[0].name, "foo")
                        self.assertEqual(item.items[0].declaration_type, SimpleSchemaParser.STRING_TYPE)

# ---------------------------------------------------------------------------
class ConfigTests(unittest.TestCase):

    # ---------------------------------------------------------------------------
    def test_Empty(self):
        for definition in [ 'config("foo"): pass',
                            'config("foo"):\n    pass',
                          ]:
            root = ParseStrings({ "Test" : definition, })

            self.assertEqual(len(root.items), 0)
            self.assertEqual(len(root.config), 1)
            self.assertEqual(root.config.keys()[0], "foo")
            self.assertEqual(len(root.config["foo"].metadata), 0)

    # ---------------------------------------------------------------------------
    def test_Populated(self):
        definition = textwrap.dedent(
            """\
            config("foo"):
                a="b"

                c='d'

            config("bar"):
                one='1'
                two="2"

            config("baz"):
                single="true"
            """)
    
        root = ParseStrings({ "Test" : definition, })

        self.assertEqual(len(root.items), 0)
        self.assertEqual(len(root.config), 3)
        self.assertEqual(root.config.keys()[0], "foo")
        self.assertEqual(root.config.keys()[1], "bar")
        self.assertEqual(root.config.keys()[2], "baz")

        self.assertEqual(root.config["foo"].metadata.keys(), [ u"a", u"c", ])
        self.assertEqual(root.config["foo"].metadata.values(), [ u"b", u"d", ])

        self.assertEqual(root.config["bar"].metadata.keys(), [ u"one", u"two", ])
        self.assertEqual(root.config["bar"].metadata.values(), [ u"1", u"2", ])

        self.assertEqual(root.config["baz"].metadata.keys(), [ u"single", ])
        self.assertEqual(root.config["baz"].metadata.values(), [ u"true", ])

# ---------------------------------------------------------------------------
class ExtensionTests(unittest.TestCase):

    # ---------------------------------------------------------------------------
    class ThisObserver(DefaultObserver):

        # ---------------------------------------------------------------------------
        def GetExtensions(self):
            return [ QuickObject( Name="foo", AllowDuplicates=False, ), 
                     QuickObject( Name="bar", AllowDuplicates=False, ), 
                     QuickObject( Name="baz", AllowDuplicates=False, ), 
                   ]

    # ---------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super(ExtensionTests, self).__init__(*args, **kwargs)

        self._observer = ExtensionTests.ThisObserver()

    # ---------------------------------------------------------------------------
    def test_Empty(self):
        definition = textwrap.dedent(
            """\
            foo()
            bar()*
            baz() {1, 3}
            """)

        root = ParseStrings({ "Test" : definition, }, observer=self._observer)

        self.assertEqual(len(root.items), 3)

        self.assertEqual(root.items[0].name, "foo")
        self.assertEqual(root.items[0].declaration_type, -SimpleSchemaParser.RULE_extension)
        self.assertEqual(root.items[0].arity, None)
        self.assertEqual(len(root.items[0].positional_arguments), 0)
        self.assertEqual(len(root.items[0].keyword_arguments), 0)

        self.assertEqual(root.items[1].name, "bar")
        self.assertEqual(root.items[1].declaration_type, -SimpleSchemaParser.RULE_extension)
        self.assertEqual(root.items[1].arity, (0, None))
        self.assertEqual(len(root.items[1].positional_arguments), 0)
        self.assertEqual(len(root.items[1].keyword_arguments), 0)

        self.assertEqual(root.items[2].name, "baz")
        self.assertEqual(root.items[2].declaration_type, -SimpleSchemaParser.RULE_extension)
        self.assertEqual(root.items[2].arity, (1, 3))
        self.assertEqual(len(root.items[2].positional_arguments), 0)
        self.assertEqual(len(root.items[2].keyword_arguments), 0)

    # ---------------------------------------------------------------------------
    def test_Positional(self):
        definition = textwrap.dedent(
            """\
            foo(a, 10, 20.0, '''
                             s1
                             ''', "s2", "30", "40.5", "true", [ [ "one", ], "two", "three", ])
            """)

        root = ParseStrings({ "Test" : definition, }, observer=self._observer)

        self.assertEqual(len(root.items), 1)
        self.assertEqual(root.items[0].name, "foo")
        self.assertEqual(root.items[0].declaration_type, -SimpleSchemaParser.RULE_extension)
        self.assertEqual(root.items[0].arity, None)
        self.assertEqual(root.items[0].positional_arguments, [ u'a', 10, 20.0, '"s1"', u'"s2"', u'"30"', u'"40.5"', u'"true"', [ [ u'"one"', ], u'"two"', u'"three"', ] ])
        self.assertEqual(len(root.items[0].keyword_arguments), 0)

    # ---------------------------------------------------------------------------
    def test_Keyword(self):
        definition = textwrap.dedent(
            """\
            bar(one=1, two="2", three="three"){3}
            """)

        root = ParseStrings({ "Test" : definition, }, observer=self._observer)

        self.assertEqual(len(root.items), 1)
        self.assertEqual(root.items[0].name, "bar")
        self.assertEqual(root.items[0].declaration_type, -SimpleSchemaParser.RULE_extension)
        self.assertEqual(root.items[0].arity, (3,3))
        self.assertEqual(len(root.items[0].positional_arguments), 0)
        self.assertEqual(root.items[0].keyword_arguments, OrderedDict([ ( "one", 1 ),
                                                                        ( "two", '"2"' ),
                                                                        ( "three", '"three"' ),
                                                                      ]))
    
    # ---------------------------------------------------------------------------
    def test_Both(self):
        definition = textwrap.dedent(
            """\
            bar(a, 10, 20.0, '''
                             s1
                             ''', "s2", "30", "40.5", "true", [ [ "one", ], "two", "three", ], one=1, two="2", three="three"){3, 5}
            """)

        root = ParseStrings({ "Test" : definition, }, observer=self._observer)

        self.assertEqual(len(root.items), 1)
        self.assertEqual(root.items[0].name, "bar")
        self.assertEqual(root.items[0].declaration_type, -SimpleSchemaParser.RULE_extension)
        self.assertEqual(root.items[0].arity, (3, 5))
        self.assertEqual(root.items[0].positional_arguments, [ u'a', 10, 20.0, '"s1"', u'"s2"', u'"30"', u'"40.5"', u'"true"', [ [ u'"one"', ], u'"two"', u'"three"', ] ])
        self.assertEqual(root.items[0].keyword_arguments, OrderedDict([ ( "one", 1 ),
                                                                        ( "two", '"2"' ),
                                                                        ( "three", '"three"' ),
                                                                      ]))

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
