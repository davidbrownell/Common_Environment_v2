# Placeholder unit test

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

