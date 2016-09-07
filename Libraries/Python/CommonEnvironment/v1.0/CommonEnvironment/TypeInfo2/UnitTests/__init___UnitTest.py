# ----------------------------------------------------------------------
# |  
# |  __init___UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-06 07:38:21
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
class ArityTest(unittest.TestCase):
    # ----------------------------------------------------------------------
    def test_Construct(self):
        Arity(0, 1)
        Arity(1, 1)
        Arity(1, None)
        Arity(0, None)
        Arity(3, 3)
        self.assertRaises(Exception, lambda: Arity(10, 1))

    # ----------------------------------------------------------------------
    def test_Compare(self):
        self.assertTrue(Arity(1, 1) == Arity(1, 1))
        self.assertTrue(Arity(0, None) < Arity(1, None))
        self.assertTrue(Arity(1, None) > Arity(0, None))
        self.assertTrue(Arity(5, None) > Arity(5, 10))
        self.assertTrue(Arity(5, 10) < Arity(5, None))
        self.assertTrue(Arity(5, 200) > Arity(5, 10))
        self.assertTrue(Arity(5, 10) < Arity(5, 200))

    # ----------------------------------------------------------------------
    def test_FromString(self):
        self.assertEqual(Arity.FromString('?'), Arity(0, 1))
        self.assertEqual(Arity.FromString('1'), Arity(1, 1))
        self.assertEqual(Arity.FromString('*'), Arity(0, None))
        self.assertEqual(Arity.FromString('+'), Arity(1, None))
        self.assertEqual(Arity.FromString("(3)"), Arity(3, 3))
        self.assertEqual(Arity.FromString("(4,7)"), Arity(4, 7))
        self.assertEqual(Arity.FromString("(  4   ,  7   )"), Arity(4, 7))
        self.assertRaises(Exception, lambda: Arity.FromString("invalid"))
           
    # ----------------------------------------------------------------------
    def test_Properties(self):
        self.assertTrue(Arity.FromString('1').IsSingle)
        self.assertTrue(Arity.FromString('(2)').IsSingle == False)
        self.assertTrue(Arity.FromString('+').IsSingle == False)

        self.assertTrue(Arity.FromString('?').IsOptional)
        self.assertTrue(Arity.FromString('1').IsOptional == False)
        self.assertTrue(Arity.FromString('*').IsOptional == False)

        self.assertTrue(Arity.FromString('*').IsCollection)
        self.assertTrue(Arity.FromString('+').IsCollection)
        self.assertTrue(Arity.FromString('(3, 5)').IsCollection)
        self.assertTrue(Arity.FromString('1').IsCollection == False)

        self.assertTrue(Arity.FromString('*').IsOptionalCollection)
        self.assertTrue(Arity.FromString('+').IsOptionalCollection == False)

        self.assertTrue(Arity.FromString("(3)").IsFixedCollection)
        self.assertTrue(Arity.FromString("+").IsFixedCollection == False)
        self.assertTrue(Arity.FromString("*").IsFixedCollection == False)
        self.assertTrue(Arity.FromString("(4,7)").IsFixedCollection == False)

        self.assertTrue(Arity.FromString('*').IsZeroOrMore)
        self.assertTrue(Arity.FromString('(0,10)').IsZeroOrMore == False)

        self.assertTrue(Arity.FromString('+').IsOneOrMore)
        self.assertTrue(Arity.FromString('*').IsOneOrMore == False)
        self.assertTrue(Arity.FromString('1').IsOneOrMore == False)
        self.assertTrue(Arity.FromString('(1,5)').IsOneOrMore == False)

        self.assertTrue(Arity.FromString("(1,5)").IsRange)
        self.assertTrue(Arity.FromString("*").IsRange == False)
        self.assertTrue(Arity.FromString("+").IsRange == False)
        self.assertTrue(Arity.FromString("(5)").IsRange == False)

    # ----------------------------------------------------------------------
    def test_PythonDefinitionString(self):
        self.assertEqual(Arity.FromString('?').PythonDefinitionString, "Arity(min=0, max_or_none=1)")
        self.assertEqual(Arity.FromString('1').PythonDefinitionString, "Arity(min=1, max_or_none=1)")
        self.assertEqual(Arity.FromString('*').PythonDefinitionString, "Arity(min=0, max_or_none=None)")
        self.assertEqual(Arity.FromString('+').PythonDefinitionString, "Arity(min=1, max_or_none=None)")
        self.assertEqual(Arity.FromString('(12,47)').PythonDefinitionString, "Arity(min=12, max_or_none=47)")
        self.assertEqual(Arity.FromString('(12)').PythonDefinitionString, "Arity(min=12, max_or_none=12)")

    # ----------------------------------------------------------------------
    def test_ToString(self):
        self.assertEqual(Arity(0, 1).ToString(), '?')
        self.assertEqual(Arity(1, 1).ToString(), '')
        self.assertEqual(Arity(0, None).ToString(), '*')
        self.assertEqual(Arity(1, None).ToString(), '+')
        self.assertEqual(Arity(3, 3).ToString(), '(3)')
        self.assertEqual(Arity(3, 10).ToString(), '(3,10)')
        self.assertEqual(Arity(3, 3).ToString(brackets=( '{', '}' )), '{3}')
        self.assertEqual(Arity(3, 10).ToString(brackets=( '{', '}' )), '{3,10}')

# ----------------------------------------------------------------------
class MyTypeInfo(TypeInfo):
    Desc                                    = "MyTypeInfo"
    ExpectedType                            = str
    ConstraintsDesc                         = ''
        
    # ----------------------------------------------------------------------
    def __init__( self, 
                  error_index=None,
                  **type_info_args
                ):
        super(MyTypeInfo, self).__init__(**type_info_args)

        self.ErrorIndex                     = error_index
        self._ctr                           = 0

    # ----------------------------------------------------------------------
    @property
    def PythonDefinitionString(self):
        return "MyTypeInfo({})".format(self._PythonDefinitionStringContents)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item, **custom_args):
        if self.ErrorIndex != None and self._ctr == self.ErrorIndex:
            return "Error"
    
        self._ctr += 1

# ----------------------------------------------------------------------
class TypeInfoTest(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._myTypeInfo                     = MyTypeInfo()
        cls._myTypeInfoError                = MyTypeInfo(0, arity='+')
        cls._myTypeInfoError2               = MyTypeInfo(2, arity='+')

    # ----------------------------------------------------------------------
    def test_Construct(self):
        MyTypeInfo()
        MyTypeInfo(arity='?')
        self.assertRaises(Exception, lambda: MyTypeInfo(collection_validation_func=lambda *args, **kwags: None))

    # ----------------------------------------------------------------------
    def test_Validate(self):
        self._myTypeInfo.Validate("Foo")
        self.assertRaises(ValidationException, lambda: self._myTypeInfoError.Validate("foo"))
        
        self._myTypeInfoError.ValidateArity([ "a", "b", "c", ])
        self.assertRaises(ValidationException, lambda: self._myTypeInfo.ValidateArity(["a", "b", "c", ]))
        
        self._myTypeInfoError.ValidateArityCount(100)
        self.assertRaises(ValidationException, lambda: self._myTypeInfo.ValidateArityCount(100))

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
