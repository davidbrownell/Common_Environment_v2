# ---------------------------------------------------------------------------
# |  
# |  ClassTypeInfo_UnitTest.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/29/2015 04:42:29 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Unit test for ClassTypeInfo.py
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

    from ..ClassTypeInfo import *
    from ..FundamentalTypes import *

    __package__ = ni.original

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
        self._type_info.Validate(self._tuple("hello", 15, True), require_exact_match=False)

    # ---------------------------------------------------------------------------
    def test_Invalid(self):
        self.assertRaises(Exception, lambda: self._type_info.Validate({}))
        self.assertRaises(Exception, lambda: self._type_info.Validate(namedtuple("Other", [ "foo", "bar", ])("valid", 15)))
        self.assertRaises(Exception, lambda: self._type_info.Validate(self._tuple("", 15, True)))
        self.assertRaises(Exception, lambda: self._type_info.Validate(self._tuple("valid", 5, True)))
        
    # ---------------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(self._type_info.PythonDefinitionString, r'ClassTypeInfo(arity=Arity(min=1, max_or_none=1), items={ "baz" : BoolTypeInfo(arity=Arity(min=1, max_or_none=1)), "foo" : StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=1), "bar" : IntTypeInfo(arity=Arity(min=1, max_or_none=1), min=10, max=20) })')
        
    # ---------------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(self._type_info.ConstraintsDesc, "Value must contain the attributes 'baz', 'foo', 'bar'")
        
# ---------------------------------------------------------------------------
class ClassTest(unittest.TestCase):

    # ---------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._type_info = ClassTypeInfo( foo=StringTypeInfo(max_length=5),
                                        static_method=StaticMethodTypeInfo(),
                                        class_method=ClassMethodTypeInfo(),
                                        method=MethodTypeInfo(),
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
    def test_PythonDefinitionString(self):
        self.assertEqual(self._type_info.PythonDefinitionString, r'ClassTypeInfo(arity=Arity(min=1, max_or_none=1), items={ "static_method" : StaticMethodTypeInfo(arity=Arity(min=1, max_or_none=1)), "class_method" : ClassMethodTypeInfo(arity=Arity(min=1, max_or_none=1)), "method" : MethodTypeInfo(arity=Arity(min=1, max_or_none=1)), "foo" : StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=1, max_length=5) })')
        
    # ---------------------------------------------------------------------------
    def test_ConstraintsDesc(self):
        self.assertEqual(self._type_info.ConstraintsDesc, "Value must contain the attributes 'static_method', 'class_method', 'method', 'foo'")
    
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
