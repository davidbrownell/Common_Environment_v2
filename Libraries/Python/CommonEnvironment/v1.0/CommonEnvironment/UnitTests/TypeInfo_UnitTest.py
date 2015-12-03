# ---------------------------------------------------------------------------
# |  
# |  TypeInfo_UnitTest.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/18/2015 09:52:46 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Unit test for TypeInfo.py
"""

import datetime
import os
import sys
import unittest

from collections import OrderedDict, namedtuple

from CommonEnvironment.CallOnExit import CallOnExit

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, ".."))
with CallOnExit(lambda: sys.path.pop(0)):
    from TypeInfo import *

# ---------------------------------------------------------------------------
class Arity(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._zero_or_more = IntTypeInfo(arity='*')
        cls._one_or_more = IntTypeInfo(arity='+')
        cls._fixed = IntTypeInfo(arity=3)
        cls._range = IntTypeInfo(arity=(2, 4))

    # ---------------------------------------------------------------------------
    def test_ZeroOrMore(self):
        self._zero_or_more.Validate([])
        self._zero_or_more.Validate([ 1, 2, 3, ])
        self.assertRaises(Exception, lambda: self._zero_or_more.Validate(1))

    # ---------------------------------------------------------------------------
    def test_OneOrMore(self):
        self._one_or_more.Validate([ 1, ])
        self._one_or_more.Validate([ 1, 2, 3, ])
        self.assertRaises(Exception, lambda: self._one_or_more.Valudate(1))
        self.assertRaises(Exception, lambda: self._one_or_more.Valudate([]))

    # ---------------------------------------------------------------------------
    def test_Fixed(self):
        self._fixed.Validate([ 1, 2, 3, ])
        self.assertRaises(Exception, lambda: self._fixed.Validate(1))
        self.assertRaises(Exception, lambda: self._fixed.Validate([]))
        self.assertRaises(Exception, lambda: self._fixed.Validate([ 1, 2, ]))
        self.assertRaises(Exception, lambda: self._fixed.Validate([ 1, 2, 3, 4, ]))

    # ---------------------------------------------------------------------------
    def test_Range(self):
        self._range.Validate([ 1, 2, ])
        self._range.Validate([ 1, 2, 3, ])
        self._range.Validate([ 1, 2, 3, 4, ])
        self.assertRaises(Exception, lambda: self._range.Validate(1))
        self.assertRaises(Exception, lambda: self._range.Validate([]))
        self.assertRaises(Exception, lambda: self._range.Validate([ 1, ]))
        self.assertRaises(Exception, lambda: self._range.Validate([ 1, 2, 3, 4, 5, ]))

# ---------------------------------------------------------------------------
class FundamentalOptionalArity(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._optional_type_info = StringTypeInfo(arity='?')
        cls._type_info = StringTypeInfo()

    # ---------------------------------------------------------------------------
    def test_Validate(self):
        self._optional_type_info.Validate("value")
        self._optional_type_info.Validate(None)
        self._type_info.Validate("value")
        self.assertRaises(Exception, lambda: self._type_info.Validate(None))

    # ---------------------------------------------------------------------------
    def test_StringConversion(self):
        self.assertEqual(None, self._optional_type_info.FromString(self._optional_type_info.ToString(None, self._optional_type_info.Format_String), self._optional_type_info.Format_String))
        self.assertEqual(None, self._optional_type_info.FromString(self._optional_type_info.ToString(None, self._optional_type_info.Format_Python), self._optional_type_info.Format_Python))
        self.assertEqual(None, self._optional_type_info.FromString(self._optional_type_info.ToString(None, self._optional_type_info.Format_JSON), self._optional_type_info.Format_JSON))
        
# ---------------------------------------------------------------------------
class FundamentalString(unittest.TestCase):
    
    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = StringTypeInfo( validation="\d+",
                                         max_length=5,
                                       )

        cls._empty_type_info = StringTypeInfo(min_length=0)

    # ---------------------------------------------------------------------------
    def test_Validate(self):
        
        self._type_info.Validate("123")
        self.assertRaises(Exception, lambda: _self._type_info.Validate("abcd"))     # Not valid
        self.assertRaises(Exception, lambda: _self._type_info.Validate(""))         # Too short
        self.assertRaises(Exception, lambda: _self._type_info.Validate("123456"))   # Too long

        self._empty_type_info.Validate("123")
        self._empty_type_info.Validate("abcd")
        self._empty_type_info.Validate("")
        self._empty_type_info.Validate("123456")

        self.assertRaises(Exception, lambda: self._empty_type_info.Validate(10))    # Wrong type

    # ---------------------------------------------------------------------------
    def test_ToString(self):
        self.assertEqual(self._empty_type_info.ItemToString("foo"), "foo")
        self.assertRaises(Exception, lambda: _type_info.ItemToString("abc"))        # Not valid

    # ---------------------------------------------------------------------------
    def test_FromString(self):
        self.assertEqual(self._empty_type_info.ItemFromString("foo"), "foo")
        self.assertRaises(Exception, lambda: _type_info.ItemFromString("abc"))          # Not valid

# ---------------------------------------------------------------------------
class FundamentalEnum(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = EnumTypeInfo([ "a", "b", "c", ])

    # ---------------------------------------------------------------------------
    def test_Invalid(self):
        self.assertRaises(Exception, lambda: EnumTypeInfo([ "a", "b", ], friendly_values=[ "c", ]))     # Wrong number of args between values and friendly_values

    # ---------------------------------------------------------------------------
    def test_Validate(self):
        self._type_info.Validate("a")
        self.assertRaises(Exception, lambda: self._type_info.Validate("not_here"))  # Invalid value

    # ---------------------------------------------------------------------------
    def test_ToString(self):
        self.assertEqual(self._type_info.ItemToString("a"), "a")
        self.assertRaises(Exception, lambda: self._type_info.ItemToString("invalid"))

    # ---------------------------------------------------------------------------
    def test_FromString(self):
        self.assertEqual(self._type_info.ItemFromString("a"), "a")
        self.assertRaises(Exception, lambda: self._type_info.ItemToString("invalid"))

# ---------------------------------------------------------------------------
class FundamentalInt(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = IntTypeInfo(10, 20)

    # ---------------------------------------------------------------------------
    def test_Invalid(self):
        self.assertRaises(Exception, lambda: IntTypeInfo(20, 10))

    # ---------------------------------------------------------------------------
    def test_Validate(self):
        self._type_info.Validate(10)
        self._type_info.Validate(20)
        self._type_info.Validate(15)
        self.assertRaises(Exception, lambda: self._type_info.Validate(5))       # Below min
        self.assertRaises(Exception, lambda: self._type_info.Validate(25))      # Above max
        self.assertRaises(Exception, lambda: self._type_info.Validate("foo"))   # Wrong type

    # ---------------------------------------------------------------------------
    def test_ToString(self):
        self.assertEqual(self._type_info.ItemToString(15), "15")
        self.assertRaises(Exception, lambda: self._type_info.ItemToString(5))       # Below min
        self.assertRaises(Exception, lambda: self._type_info.ItemToString("foo"))   # Wrong type

    # ---------------------------------------------------------------------------
    def test_FromString(self):
        self.assertEqual(self._type_info.ItemFromString("15"), 15)
        self.assertRaises(Exception, lambda: self._type_info.ItemFromString("5"))   # Below min
        self.assertRaises(Exception, lambda: self._type_info.ItemFromString("foo")) # Wrong type

# ---------------------------------------------------------------------------
class FundamentalFloat(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = FloatTypeInfo(10, 20)

    # ---------------------------------------------------------------------------
    def test_Invalid(self):
        self.assertRaises(Exception, lambda: FloatTypeInfo(20, 10))

    # ---------------------------------------------------------------------------
    def test_Validate(self):
        self._type_info.Validate(10)
        self._type_info.Validate(20.0)
        self._type_info.Validate(15.5)
        self.assertRaises(Exception, lambda: self._type_info.Validate(5))       # Below min
        self.assertRaises(Exception, lambda: self._type_info.Validate(25.2))    # Above max
        self.assertRaises(Exception, lambda: self._type_info.Validate("foo"))   # Wrong type

    # ---------------------------------------------------------------------------
    def test_ToString(self):
        self.assertEqual(self._type_info.ItemToString(15.2), "15.2")
        self.assertRaises(Exception, lambda: self._type_info.ItemToString(5.0))     # Below min
        self.assertRaises(Exception, lambda: self._type_info.ItemToString("foo"))   # Wrong type

    # ---------------------------------------------------------------------------
    def test_FromString(self):
        self.assertEqual(self._type_info.ItemFromString("15.0"), 15.0)
        self.assertRaises(Exception, lambda: self._type_info.ItemFromString("5"))   # Below min
        self.assertRaises(Exception, lambda: self._type_info.ItemFromString("foo")) # Wrong type

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
class FundamentalBool(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = BoolTypeInfo()

    # ---------------------------------------------------------------------------
    def test_Validate(self):
        self._type_info.Validate(True)
        self.assertRaises(Exception, lambda: self._type_info.Validate("wrong type"))

    # ---------------------------------------------------------------------------
    def test_ToString(self):
        self.assertEqual(self._type_info.ItemToString(True, BoolTypeInfo.Format_Python), "True")
        self.assertEqual(self._type_info.ItemToString(False, BoolTypeInfo.Format_Python), "False")
        self.assertEqual(self._type_info.ItemToString(True, BoolTypeInfo.Format_JSON), "true")
        self.assertEqual(self._type_info.ItemToString(False, BoolTypeInfo.Format_JSON), "false")
        
    # ---------------------------------------------------------------------------
    def test_FromString(self):
        self.assertEqual(self._type_info.ItemFromString("True", BoolTypeInfo.Format_Python), True)
        self.assertEqual(self._type_info.ItemFromString("False", BoolTypeInfo.Format_Python), False)
        self.assertEqual(self._type_info.ItemFromString("true", BoolTypeInfo.Format_JSON), True)
        self.assertEqual(self._type_info.ItemFromString("false", BoolTypeInfo.Format_JSON), False)
        self.assertEqual(self._type_info.ItemFromString("yes", BoolTypeInfo.Format_String), True)
        self.assertRaises(Exception, lambda: self._type_info.ItemFromString("yes", BoolTypeInfo.Format_Python))
    
# ---------------------------------------------------------------------------
class FundamentalGuid(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = GuidTypeInfo()

    # ---------------------------------------------------------------------------
    def test_Validate(self):
        self._type_info.Validate(self._type_info.Create())
        self.assertRaises(Exception, lambda: self._type_info.Validate("wrong type"))

    # ---------------------------------------------------------------------------
    def test_StringConversion(self):
        guid = self._type_info.Create()
        self.assertEqual(guid, self._type_info.ItemFromString(self._type_info.ItemToString(guid)))

# ---------------------------------------------------------------------------
class FundamentalDateTime(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = DateTimeTypeInfo()

    # ---------------------------------------------------------------------------
    def test_Validate(self):
        self._type_info.Validate(self._type_info.Create())
        self.assertRaises(Exception, lambda: self._type_info.Validate("wrong type"))
        self.assertRaises(Exception, lambda: self._type_info.Validate(10))

    # ---------------------------------------------------------------------------
    def test_StringConversion(self):
        now = self._type_info.Create()
        self.assertEqual(now, self._type_info.ItemFromString(self._type_info.ItemToString(now, DateTimeTypeInfo.Format_Python), DateTimeTypeInfo.Format_Python))
        self.assertEqual(now, self._type_info.ItemFromString(self._type_info.ItemToString(now, DateTimeTypeInfo.Format_JSON), DateTimeTypeInfo.Format_JSON))
        self.assertEqual(now, self._type_info.ItemFromString(self._type_info.ItemToString(now, DateTimeTypeInfo.Format_Python), DateTimeTypeInfo.Format_JSON))
        self.assertEqual(now, self._type_info.ItemFromString(self._type_info.ItemToString(now, DateTimeTypeInfo.Format_JSON), DateTimeTypeInfo.Format_Python))

# ---------------------------------------------------------------------------
class FundamentalDate(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = DateTypeInfo()

    # ---------------------------------------------------------------------------
    def test_Validate(self):
        self._type_info.Validate(self._type_info.Create())
        self.assertRaises(Exception, lambda: self._type_info.Validate("wrong type"))
        self.assertRaises(Exception, lambda: self._type_info.Validate(10))

    # ---------------------------------------------------------------------------
    def test_StringConversion(self):
        now = self._type_info.Create()
        self.assertEqual(now, self._type_info.ItemFromString(self._type_info.ItemToString(now)))
        
# ---------------------------------------------------------------------------
class FundamentalTime(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = TimeTypeInfo()

    # ---------------------------------------------------------------------------
    def test_Validate(self):
        self._type_info.Validate(self._type_info.Create())
        self.assertRaises(Exception, lambda: self._type_info.Validate("wrong type"))
        self.assertRaises(Exception, lambda: self._type_info.Validate(10))

    # ---------------------------------------------------------------------------
    def test_StringConversion(self):
        now = self._type_info.Create()
        self.assertEqual(now, self._type_info.ItemFromString(self._type_info.ItemToString(now)))

# ---------------------------------------------------------------------------
class FundamentalDuration(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = DurationTypeInfo()

    # ---------------------------------------------------------------------------
    def test_Validate(self):
        self._type_info.Validate(datetime.timedelta(seconds=0))
        self.assertRaises(Exception, lambda: self._type_info.Validate("wrong type"))
        self.assertRaises(Exception, lambda: self._type_info.Validate(10))

    # ---------------------------------------------------------------------------
    def test_StringConversion(self):
        d = datetime.timedelta(seconds=140)
        self.assertEqual(d, self._type_info.ItemFromString(self._type_info.ItemToString(d)))
        self.assertEqual(datetime.timedelta(seconds=22), self._type_info.ItemFromString(":22"))
        self.assertEqual(datetime.timedelta(seconds=22, minutes=1), self._type_info.ItemFromString("1:22"))
        self.assertEqual(datetime.timedelta(seconds=22, minutes=1, hours=3), self._type_info.ItemFromString("3:01:22"))

# ---------------------------------------------------------------------------
class DictTest(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = DictTypeInfo( foo=StringTypeInfo(),
                                       bar=IntTypeInfo(min=10, max=20),
                                       baz=BoolTypeInfo(),
                                     )

    # ---------------------------------------------------------------------------
    def test_Valid(self):
        d = { "foo" : "hello",
              "bar" : 15,
              "baz" : True,
            }

        self._type_info.Validate(d)

    # ---------------------------------------------------------------------------
    def test_Invalid(self):
        self.assertRaises(Exception, lambda: self._type_info.Validate({}))
        self.assertRaises(Exception, lambda: self._type_info.Validate({ "foo" : "valid", "bar" : 15, }))
        self.assertRaises(Exception, lambda: self._type_info.Validate({ "foo" : "valid", "baz" : True, }))
        self.assertRaises(Exception, lambda: self._type_info.Validate({ "bar" : 15, "baz" : True, }))
        self.assertRaises(Exception, lambda: self._type_info.Validate({ "foo" : "", "bar" : 15, "baz" : True, }))
        self.assertRaises(Exception, lambda: self._type_info.Validate({ "foo" : "valid", "bar" : 5, "baz" : True, }))
        self.assertRaises(Exception, lambda: self._type_info.Validate({ "foo" : "valid", "bar" : 15, "baz" : "Trueish", }))

# ---------------------------------------------------------------------------
class NamedTupleTest(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = ClassTypeInfo( foo=StringTypeInfo(),
                                        bar=IntTypeInfo(min=10, max=20),
                                        baz=BoolTypeInfo(),
                                      )
        cls._tuple = namedtuple("MyTuple", [ "foo", "bar", "baz", ])

    # ---------------------------------------------------------------------------
    def test_Valid(self):
        self._type_info.Validate(self._tuple("hello", 15, True))

    # ---------------------------------------------------------------------------
    def test_Invalid(self):
        self.assertRaises(Exception, lambda: self._type_info.Validate({}))
        self.assertRaises(Exception, lambda: self._type_info.Validate(namedtuple("Other", [ "foo", "bar", ])("valid", 15)))
        self.assertRaises(Exception, lambda: self._type_info.Validate(self._tuple("", 15, True)))
        self.assertRaises(Exception, lambda: self._type_info.Validate(self._tuple("valid", 5, True)))

# ---------------------------------------------------------------------------
class ClassTest(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = ClassTypeInfo( foo=StringTypeInfo(max_length=5),
                                        static_method=ClassTypeInfo.StaticMethodTypeInfo(),
                                        class_method=ClassTypeInfo.ClassMethodTypeInfo(),
                                        method=ClassTypeInfo.MethodTypeInfo(),
                                      )

    # ---------------------------------------------------------------------------
    def test_Valid(self):
        # ---------------------------------------------------------------------------
        class Foo(object):
            def __init__(self):
                self.foo = "test"

            @staticmethod
            def static_method():
                pass

            @classmethod
            def class_method(cls):
                pass

            def method(self):
                pass

        # ---------------------------------------------------------------------------
        
        self._type_info.Validate(Foo())
        self.assertRaises(Exception, lambda: self._type_info.Validate(Foo("too long")))

    # ---------------------------------------------------------------------------
    def test_Invalid(self):
        # ---------------------------------------------------------------------------
        class NoFoo(object):
            @staticmethod
            def static_method():
                pass

            @classmethod
            def class_method(cls):
                pass

            def method(self):
                pass

        # ---------------------------------------------------------------------------
        
        self.assertRaises(Exception, lambda: self._type_info.Validate(NoFoo()))

        # ---------------------------------------------------------------------------
        class BadFoo(object):
            def __init__(self):
                self.foo = "too long"

            @staticmethod
            def static_method():
                pass

            @classmethod
            def class_method(cls):
                pass

            def method(self):
                pass

        # ---------------------------------------------------------------------------
        
        self.assertRaises(Exception, lambda: self._type_info.Validate(BadFoo()))

        # ---------------------------------------------------------------------------
        class NoStaticMethod(object):
            def __init__(self):
                self.foo = "test"

            # @staticmethod
            # def static_method():
            #     pass

            @classmethod
            def class_method(cls):
                pass

            def method(self):
                pass

        # ---------------------------------------------------------------------------
        
        self.assertRaises(Exception, lambda: self._type_info.Validate(NoStaticMethod()))

        # ---------------------------------------------------------------------------
        class NoClassMethod(object):
            def __init__(self):
                self.foo = "test"

            @staticmethod
            def static_method():
                pass

            # @classmethod
            # def class_method(cls):
            #     pass

            def method(self):
                pass

        # ---------------------------------------------------------------------------
        
        self.assertRaises(Exception, lambda: self._type_info.Validate(NoClassMethod()))

        # ---------------------------------------------------------------------------
        class NoMethod(object):
            def __init__(self):
                self.foo = "test"

            @staticmethod
            def static_method():
                pass

            @classmethod
            def class_method(cls):
                pass

            # def method(self):
            #     pass

        # ---------------------------------------------------------------------------
        
        self.assertRaises(Exception, lambda: self._type_info.Validate(NoMethod()))

        # ---------------------------------------------------------------------------
        class WrongMethodType(object):
            def __init__(self):
                self.foo = "test"

            @staticmethod
            def static_method():
                pass

            # @classmethod
            def class_method(cls):
                pass

            def method(self):
                pass

        # ---------------------------------------------------------------------------
        
        self.assertRaises(Exception, lambda: self._type_info.Validate(WrongMethodType()))

# ---------------------------------------------------------------------------
class ListTest(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = ListTypeInfo( StringTypeInfo(arity='+'),
                                       arity='*',
                                     )

    # ---------------------------------------------------------------------------
    def test_All(self):
        self._type_info.Validate([ [ "1", "2", "3", ], [ "4", "5", ], [ "6", ], ])
        self._type_info.Validate([])
        self.assertRaises(Exception, lambda: self._type_info.Validate([ [ "1", "2", "3", ], [], [ "4", "5", ], ]))

# ---------------------------------------------------------------------------
class AnyOfTest(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = AnyOfTypeInfo( [ StringTypeInfo(max_length=5),
                                          IntTypeInfo(min=1, max=5),
                                        ],
                                      )

    # ---------------------------------------------------------------------------
    def test_All(self):
        self._type_info.Validate("foo")
        self._type_info.Validate(4)
        self.assertRaises(Exception, lambda: self._type_info.Validate(10.0))    # Wrong type
        self.assertRaises(Exception, lambda: self._type_info.Validate("too long"))
        self.assertRaises(Exception, lambda: self._type_info.Validate(10))      # Too large

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
