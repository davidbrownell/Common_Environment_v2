# ----------------------------------------------------------------------
# |  
# |  __init___UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-01-19 08:03:49
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import datetime
import os
import sys
import unittest
import uuid

from CommonEnvironment import Package
from CommonEnvironment.TypeInfo import FundamentalTypes
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import StringSerialization

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with Package.NameInfo(__package__) as ni:
    __package__ = ni.created
    
    from .. import *

    __package__ = ni.original

# ----------------------------------------------------------------------
class UnitTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(UnitTest, self).__init__(*args, **kwargs)
        
        self._types = { "b" : FundamentalTypes.BoolTypeInfo(),
                        "dt" : FundamentalTypes.DateTimeTypeInfo(),
                        "date" : FundamentalTypes.DateTypeInfo(),
                        "dir" : FundamentalTypes.DirectoryTypeInfo(ensure_exists=False),
                        "duration" : FundamentalTypes.DurationTypeInfo(),
                        "enum" : FundamentalTypes.EnumTypeInfo([ 'a', 'b', 'c', ]),
                        "filename" : FundamentalTypes.FilenameTypeInfo(ensure_exists=False),
                        "f" : FundamentalTypes.FloatTypeInfo(),
                        "guid" : FundamentalTypes.GuidTypeInfo(),
                        "i" : FundamentalTypes.IntTypeInfo(),
                        "s" : FundamentalTypes.StringTypeInfo(),
                        "time" : FundamentalTypes.TimeTypeInfo(),
                        "constrained" : FundamentalTypes.IntTypeInfo(min=10, max=20),
                      }

        self._Parse = ParseFactory(**self._types)

    # ----------------------------------------------------------------------
    def test_Standard(self):
        for operator in [ '==', '!=', '<', '<=', '>', '>=', '~', "under", ]:
            if operator in [ '==', '!=', ]:
                self._ValidateStandard("b", operator, True)

            if operator not in [ '~', "under", ]:
                self._ValidateStandard("dt", operator, datetime.datetime.now())
                self._ValidateStandard("date", operator, datetime.date.today())
                self._ValidateStandard("duration", operator, datetime.timedelta(seconds=20))
                self._ValidateStandard("enum", operator, "a")
                self._ValidateStandard("f", operator, 10.2)
                self._ValidateStandard("guid", operator, uuid.uuid4())
                self._ValidateStandard("i", operator, 10)
                self._ValidateStandard("s", operator, "test")
                self._ValidateStandard("time", operator, datetime.datetime.now().time())

            if operator not in [ "under", ]:    
                self._ValidateStandard("filename", operator, os.path.join(os.getcwd(), "a filename"))

            self._ValidateStandard("dir", operator, os.path.join(os.getcwd(), "a directory"))

    # ----------------------------------------------------------------------
    def test_AndOr(self):
        for logical, expression_type in [ ( "and", AndExpression ),
                                          ( "or", OrExpression ),
                                        ]:
            # 2 terms
            result = self._Parse("i == 10 {} s <= 'foo'".format(logical))

            self.assertTrue(isinstance(result, expression_type))
            
            self.assertEqual(result.LHS.LHS, 'i')
            self.assertEqual(result.LHS.Operator, '==')
            self.assertEqual(result.LHS.RHS, 10)

            self.assertEqual(result.RHS.LHS, 's')
            self.assertEqual(result.RHS.Operator, '<=')
            self.assertEqual(result.RHS.RHS, 'foo')
    
            # 3 terms
            result = self._Parse("i == 10 {logical} s <= 'foo' {logical} b != 'False'".format(logical=logical))
            self.assertTrue(isinstance(result, expression_type))
            self.assertTrue(isinstance(result.LHS, expression_type))
            self.assertTrue(isinstance(result.RHS, StandardExpression))
            
            self.assertEqual(result.LHS.LHS.LHS, 'i')
            self.assertEqual(result.LHS.LHS.Operator, '==')
            self.assertEqual(result.LHS.LHS.RHS, 10)
            
            self.assertEqual(result.LHS.RHS.LHS, 's')
            self.assertEqual(result.LHS.RHS.Operator, '<=')
            self.assertEqual(result.LHS.RHS.RHS, 'foo')
            
            self.assertEqual(result.RHS.LHS, 'b')
            self.assertEqual(result.RHS.Operator, '!=')
            self.assertEqual(result.RHS.RHS, False)

    # ----------------------------------------------------------------------
    def test_Grouping(self):
        result = self._Parse("(i == 10 and s != 'foo') or f <= 10.2")
        self.assertTrue(isinstance(result, OrExpression))
        
        self.assertTrue(isinstance(result.LHS, AndExpression))
        self.assertEqual(result.LHS.LHS.LHS, 'i')
        self.assertEqual(result.LHS.LHS.Operator, '==')
        self.assertEqual(result.LHS.LHS.RHS, 10)
        self.assertEqual(result.LHS.RHS.LHS, 's')
        self.assertEqual(result.LHS.RHS.Operator, '!=')
        self.assertEqual(result.LHS.RHS.RHS, 'foo')

        self.assertEqual(result.RHS.LHS, 'f')
        self.assertEqual(result.RHS.Operator, '<=')
        self.assertEqual(result.RHS.RHS, 10.2)

        result = self._Parse("i == 10 and (s != 'foo' or f <= 10.2)")
        self.assertTrue(isinstance(result, AndExpression))

        self.assertEqual(result.LHS.LHS, 'i')
        self.assertEqual(result.LHS.Operator, '==')
        self.assertEqual(result.LHS.RHS, 10)

        self.assertTrue(isinstance(result.RHS, OrExpression))
        self.assertEqual(result.RHS.LHS.LHS, 's')
        self.assertEqual(result.RHS.LHS.Operator, '!=')
        self.assertEqual(result.RHS.LHS.RHS, 'foo')
        self.assertEqual(result.RHS.RHS.LHS, 'f')
        self.assertEqual(result.RHS.RHS.Operator, '<=')
        self.assertEqual(result.RHS.RHS.RHS, 10.2)
        
    # ----------------------------------------------------------------------
    def test_Now(self):
        now = datetime.datetime.now()

        result = self._Parse('date >= @now')
        self.assertAlmostEqual(result.RHS, now.date(), datetime.timedelta(hours=24))

        result = self._Parse('dt >= @now')
        self.assertAlmostEqual(result.RHS, now, delta=datetime.timedelta(minutes=1))
        
        result = self._Parse('time >= @now')
        self.assertAlmostEqual(result.RHS.utcoffset(), now.time().utcoffset(), datetime.timedelta(minutes=1))

        self.assertRaises(lambda: self._Parse('s != @now'))

        for value, delta in [ ( "2Y", datetime.timedelta(weeks=52 * 2) ),
                              ( "2W", datetime.timedelta(weeks=2) ),
                              ( "2M", datetime.timedelta(days=31 * 2) ),
                              ( "2D", datetime.timedelta(days=2) ),
                              ( "20h", datetime.timedelta(hours=20) ),
                              ( "2m", datetime.timedelta(minutes=2) ),
                              ( "2s", datetime.timedelta(seconds=2) ),
                              ( "2mi", datetime.timedelta(microseconds=2) ),
                            ]:
            for operation, func in [ ( '+', lambda: now + delta ),
                                     ( '-', lambda: now - delta ),
                                   ]:
                result = self._Parse('dt <= @now {} {}'.format(operation, value))
                self.assertAlmostEqual(result.RHS, func(), delta=datetime.timedelta(minutes=1))

    # ----------------------------------------------------------------------
    def test_Today(self):
        today = datetime.datetime.now()

        result = self._Parse('date >= @today')
        self.assertAlmostEqual(result.RHS, today.date(), datetime.timedelta(minutes=1))

        result = self._Parse('dt >= @today')
        self.assertAlmostEqual(result.RHS.date(), today.date(), datetime.timedelta(hours=24))

        self.assertRaises(lambda: self._Parse('s != @today'))

    # ----------------------------------------------------------------------
    def test_InvalidVar(self):
        self.assertRaises(lambda: self._Parse("does_not_exist != 20"))

    # ----------------------------------------------------------------------
    def test_InvalidOperator(self):
        self.assertRaises(lambda: self._Parse("b <= True"))

    # ----------------------------------------------------------------------
    def test_InvalidString(self):
        self.assertRaises(lambda: self._Parse("dt == 'invalid_datetime'"))

    # ----------------------------------------------------------------------
    def test_InvalidWithConstraint(self):
        self._Parse("constrained == 20")
        self.assertRaises(lambda: self._Parse("constrained == 100"))

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    def _ValidateStandard(self, lhs, operator, rhs):
        rhs_value = rhs
        if not isinstance(rhs_value, basestring):
            rhs_value = StringSerialization.SerializeItem(self._types[lhs], rhs_value)

        result = self._Parse("{} {} '{}'".format(lhs, operator, rhs_value))

        self.assertEqual(result.LHS, lhs)
        self.assertEqual(result.TypeInfo, self._types[lhs])
        self.assertEqual(result.Operator, operator)
        self.assertEqual(result.RHS, rhs)

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
