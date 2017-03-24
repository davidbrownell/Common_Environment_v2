import os
import sys
import unittest

from collections import OrderedDict

from CommonEnvironment import Package

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

with Package.NameInfo(__package__) as ni:
    __package__ = ni.created

    from ..Interface import *

    __package__ = ni.original

# ----------------------------------------------------------------------
class TestInterfaceMethods(unittest.TestCase):

    # ----------------------------------------------------------------------
    class Base(Interface):
        @abstractmethod
        def Method(self, a, b):
            raise Exception("Abstract method")

        @classmethod
        @abstractmethod
        def ClassMethod(cls, a, b):
            raise Exception("Abstract method")

        @staticmethod
        @abstractmethod
        def StaticMethod(a, b):
            raise Excpetion("Abstract method")

        @abstractproperty
        def Property(self):
            raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    class Derived(Base):
        def Method(self, a, b): pass
        def ClassMethod(self, a, b): pass
        def StaticMethod(self, a, b): pass
        
        @property
        def Property(self): pass
        
    # ----------------------------------------------------------------------
    @staticderived
    class StaticDerived(Base):
        @staticmethod
        def Method(a, b): pass

        @staticmethod
        def ClassMethod(a, b): pass

        @staticmethod
        def StaticMethod(a, b): pass

        @property
        def Property(self): pass

    # ----------------------------------------------------------------------
    @staticderived
    class ClassDerived(Base):
        @classmethod
        def Method(cls, a, b): pass

        @classmethod
        def ClassMethod(cls, a, b): pass

        @classmethod
        def StaticMethod(cls, a, b): pass

        @property
        def Property(self): pass

    # ----------------------------------------------------------------------
    class NoMethod(Base):    
        # def Method(self, a, b): pass
        def ClassMethod(self, a, b): pass
        def StaticMethod(self, a, b): pass
        
        @property
        def Property(self): pass

    # ----------------------------------------------------------------------
    class NoClassMethod(Base):
        def Method(self, a, b): pass
        # def ClassMethod(self, a, b): pass
        def StaticMethod(self, a, b): pass
        
        @property
        def Property(self): pass

    # ----------------------------------------------------------------------
    class NoStaticMethod(Base):
        def Method(self, a, b): pass
        def ClassMethod(self, a, b): pass
        # def StaticMethod(self, a, b): pass
        
        @property
        def Property(self): pass

    # ----------------------------------------------------------------------
    class NoProperty(Base):
        def Method(self, a, b): pass
        def ClassMethod(self, a, b): pass
        def StaticMethod(self, a, b): pass
        
        # @property
        # def Property(self): pass

    # ----------------------------------------------------------------------
    def test_Standard(self):
        self.Derived()
        
        self.assertRaises(Exception, lambda: self.NoMethod())
        self.assertRaises(Exception, lambda: self.NoClassMethod())
        self.assertRaises(Exception, lambda: self.NoStaticMethod())
        self.assertRaises(Exception, lambda: self.NoPropertyMethod())

    # ----------------------------------------------------------------------
    def test_AbstractItems(self):
        items = self.Derived().AbstractItems
        items.sort()

        self.assertEqual(items, [ "ClassMethod", "Method", "Property", "StaticMethod", ])

    # ----------------------------------------------------------------------
    def test_WithInitArgs(self):
        class Derived(self.Base):
            def __init__(self, a, b):
                self.a = a
                self.b = b

            def Method(self, a, b): pass
            def ClassMethod(self, a, b): pass
            def StaticMethod(self, a, b): pass

            @property 
            def Property(self): pass

        d = Derived(10, 20)

        self.assertEqual(d.a, 10)
        self.assertEqual(d.b, 20)

# ----------------------------------------------------------------------
class TestInterfaceParams(unittest.TestCase):

    # ----------------------------------------------------------------------
    class Base(Interface):
        @abstractmethod
        def Method(self, a, b=None):
            raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    def test_Same(self):
        class Derived(self.Base):
            def Method(self, a, b=None): pass

        Derived()
        self.assertTrue(True) # Avoid warnings

    # ----------------------------------------------------------------------
    def test_Required(self):
        class Derived(self.Base):
            def Method(self, a, b): pass

        self.assertRaises(Exception, lambda: Derived())

    # ----------------------------------------------------------------------
    def test_Args(self):
        class Derived(self.Base):
            def Method(self, a, b=None, *args): pass

        Derived()
        self.assertTrue(True) # Avoid warnings

    # ----------------------------------------------------------------------
    def test_Kwargs(self):
        class Derived(self.Base):
            def Method(self, a, b=None, *args, **kwargs): pass

        Derived()
        self.assertTrue(True) # Avoid warnings

# ----------------------------------------------------------------------
class TestCreateCulledCallable(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Invoke(self):
        single_arg_func = CreateCulledCallable(lambda a: a)

        self.assertEqual(single_arg_func(OrderedDict([ ( "a", 10 ), 
                                                     ])), 10)
        self.assertEqual(single_arg_func(OrderedDict([ ( "a", 10 ),
                                                       ( "b", 20 ),
                                                     ])), 10)
        self.assertEqual(single_arg_func(OrderedDict([ ( "b", 20 ),
                                                       ( "a", 10 ),
                                                     ])), 10)

        multiple_arg_func = CreateCulledCallable(lambda a, b: ( a, b ))

        self.assertEqual(multiple_arg_func(OrderedDict([ ( "a", 10 ),
                                                         ( "b", 20 ),
                                                       ])), ( 10, 20 ))
        self.assertEqual(multiple_arg_func(OrderedDict([ ( "a", 10 ),
                                                         ( "b", 20 ),
                                                         ( "c", 30 ),
                                                       ])), ( 10, 20 ))

        self.assertEqual(multiple_arg_func(OrderedDict([ ( "b", 20 ),
                                                         ( "a", 10 ),
                                                         ( "c", 30 ),
                                                       ])), ( 10, 20 ))

        self.assertEqual(multiple_arg_func(OrderedDict([ ( "foo", 20 ),
                                                         ( "bar", 10 ),
                                                         ( "baz", 30 ),
                                                       ])), ( 20, 10 ))

        self.assertEqual(multiple_arg_func(OrderedDict([ ( "foo", 20 ),
                                                         ( "bar", 10 ),
                                                         ( "baz", 30 ),
                                                         ( "a", 1 ),
                                                       ])), ( 1, 20 ))

        self.assertEqual(multiple_arg_func(OrderedDict([ ( "foo", 20 ),
                                                         ( "bar", 10 ),
                                                         ( "baz", 30 ),
                                                         ( "b", 2 ),
                                                       ])), ( 20, 2 ))

        self.assertEqual(multiple_arg_func(OrderedDict([ ( "foo", 20 ),
                                                         ( "bar", 10 ),
                                                         ( "baz", 30 ),
                                                         ( "b", 2 ),
                                                         ( "a", 1 ),
                                                       ])), ( 1, 2 ))

        with_defaults_func = CreateCulledCallable(lambda a, b, c=30, d=40: ( a, b, c, d ))

        self.assertEqual(with_defaults_func(OrderedDict([ ( "a", 10 ),
                                                          ( "b", 20 ),
                                                        ])), ( 10, 20, 30, 40 ))

        self.assertEqual(with_defaults_func(OrderedDict([ ( "b", 20 ),
                                                          ( "a", 10 ),
                                                        ])), ( 10, 20, 30, 40 ))

        self.assertEqual(with_defaults_func(OrderedDict([ ( "foo", 10 ),
                                                          ( "bar", 20 ),
                                                        ])), ( 10, 20, 30, 40 ))

        self.assertEqual(with_defaults_func(OrderedDict([ ( "foo", 10 ),
                                                          ( "d", 400 ),
                                                          ( "bar", 20 ),
                                                        ])), ( 10, 20, 30, 400 ))

        self.assertEqual(with_defaults_func(OrderedDict([ ( "foo", 10 ),
                                                          ( "bar", 20 ),
                                                          ( "baz", 300 ),
                                                        ])), ( 10, 20, 30, 40 ))

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass

