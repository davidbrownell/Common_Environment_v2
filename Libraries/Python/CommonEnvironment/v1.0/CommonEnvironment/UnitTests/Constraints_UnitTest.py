# ---------------------------------------------------------------------------
# |  
# |  Constraints_UnitTest.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/27/2015 06:43:59 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Unit test for Constraints.py
"""

import itertools
import os
import sys
import unittest

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import Decorator

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, ".."))
with CallOnExit(lambda: sys.path.pop(0)):
    from Constraints import *
    from TypeInfo.FundamentalTypes import *

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
class Tests(unittest.TestCase):

    # ---------------------------------------------------------------------------
    def test_Invalid(self):
        @FunctionConstraint(a=StringTypeInfo())
        def MissingPrecondition(a, b):
            pass

        self.assertRaises(Exception, lambda: MissingPrecondition("foo", "bar"))

        @FunctionConstraint( a=StringTypeInfo(),
                             invalid=StringTypeInfo(),
                           )
        def InvalidPreconditions(a):
            pass

        self.assertRaises(Exception, lambda: InvalidPrecondition("foo", "bar"))

    # ---------------------------------------------------------------------------
    def test_Preconditions(self):
        
        # ---------------------------------------------------------------------------
        @FunctionConstraint( a=IntTypeInfo(min=5),
                             b=IntTypeInfo(min=5, arity='+'),
                             c=IntTypeInfo(min=5, arity='?'),
                           )
        def Func(a, b, c=None):
            b_sum = 0
            for val in b:
                b_sum += val

            return a + b_sum + (c or 0)
        
        # ---------------------------------------------------------------------------
        
        self.assertEqual(Func(5, [ 5, ]), 10)
        self.assertEqual(Func(5, [ 5, ], 5), 15) 
        self.assertEqual(Func(5, [ 5, 5, ], 5), 20) 
        self.assertEqual(Func(c=5, a=5, b=[ 5, 5, ]), 20) 

        self.assertRaises(Exception, lambda: Func(0, [ 5, ]))
        self.assertRaises(Exception, lambda: Func(5, []))
        self.assertRaises(Exception, lambda: Func(5, [ 0, ]))
        self.assertRaises(Exception, lambda: Func(5, [ 5, ], 0))

    # ---------------------------------------------------------------------------
    def test_Postconditions(self):

        # ---------------------------------------------------------------------------
        @FunctionConstraint(postcondition=IntTypeInfo(min=5))
        def Func(a):
            return a

        # ---------------------------------------------------------------------------
        
        Func(5)
        self.assertRaises(Exception, lambda: Func(0))

    # ---------------------------------------------------------------------------
    def test_Enumeration(self):
    
        # ---------------------------------------------------------------------------
        @FunctionConstraint( a=IntTypeInfo(),
                             b=IntTypeInfo(),
                             c=None,
                           )
        @FunctionConstraint(postcondition=IntTypeInfo())
        @FunctionConstraint( a=IntTypeInfo(),
                             b=IntTypeInfo(),
                             c=IntTypeInfo(),
                           )
        def Func(a, b, c):
            return a + b + c
    
        # ---------------------------------------------------------------------------
        
        self.assertEqual(Func(5, 10, 15), 30)
    
        counter= 0
        for constraint, (expected_constraint, num_preconditions, num_postconditions) in itertools.izip( Decorator.EnumDecorators(Func),
                                                                                                        [ ( FunctionConstraint, 3, 0 ),
                                                                                                          ( FunctionConstraint, 0, 1 ),
                                                                                                          ( FunctionConstraint, 3, 0 ),
                                                                                                        ],
                                                                                                      ):
            self.assertEqual(type(constraint), expected_constraint)
            self.assertEqual(len(constraint.Preconditions), num_preconditions)
            self.assertEqual(len(constraint.Postconditions), num_postconditions)

            counter += 1

        self.assertEqual(counter, 3)

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
