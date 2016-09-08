# ----------------------------------------------------------------------
# |  
# |  ClassTypeInfo_UnitTest.py
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
import copy
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
    
    from ..ClassTypeInfo import *
    from .. import ValidationException

    __package__ = ni.original

# ----------------------------------------------------------------------
class UnitTests(unittest.TestCase):
    # ----------------------------------------------------------------------
    class MyObject(object):
        def Method(self): 
            pass
        
        @classmethod
        def ClassMethod(cls):
            pass

        @staticmethod
        def StaticMethod():
            pass

    # ----------------------------------------------------------------------
    @classmethod
    def setUp(cls):
        cls._ti = ClassTypeInfo( { "ClassMethod" : ClassMethodTypeInfo(),
                                   "StaticMethod" : StaticMethodTypeInfo(),
                                   "Method" : MethodTypeInfo(),
                                 },
                                 require_exact_match=False,
                               )
        
        cls._ti_exact = ClassTypeInfo( { "ClassMethod" : ClassMethodTypeInfo(),
                                         "StaticMethod" : StaticMethodTypeInfo(),
                                         "Method" : MethodTypeInfo(),
                                       },
                                       require_exact_match=True,
                                     )

        cls._obj = UnitTests.MyObject()

        cls._obj_extra = UnitTests.MyObject()
        cls._obj_extra.new_value = 10
                                         
    # ----------------------------------------------------------------------
    def test_Standard(self):
        self.assertTrue(self._ti.IsValidItem(self._obj))
        self.assertTrue(self._ti.IsValidItem(self._obj_extra))

        self.assertTrue(self._ti_exact.IsValidItem(self._obj))
        self.assertTrue(self._ti_exact.IsValidItem(self._obj_extra) == False)
        
    # ----------------------------------------------------------------------
    def test_WrongTypes(self):
        obj = copy.deepcopy(type(self._obj))
        obj.Method = 20
        self.assertRaises(ValidationException, lambda: self._ti.ValidateItem(obj()))

        obj = copy.deepcopy(type(self._obj))
        obj.StaticMethod = 20
        self.assertRaises(ValidationException, lambda: self._ti.ValidateItem(obj()))

        obj = copy.deepcopy(type(self._obj))
        obj.ClassMethod = 20
        self.assertRaises(ValidationException, lambda: self._ti.ValidateItem(obj()))

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
