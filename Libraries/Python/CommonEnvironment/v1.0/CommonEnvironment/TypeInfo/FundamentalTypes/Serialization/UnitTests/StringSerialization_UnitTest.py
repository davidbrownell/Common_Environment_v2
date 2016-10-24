# ----------------------------------------------------------------------
# |  
# |  StringSerialization_UnitTest.py
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
import datetime
import os
import re
import sys
import unittest
import uuid

from CommonEnvironment import Package

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with Package.NameInfo(__package__) as ni:
    __package__ = ni.created
    
    from ..StringSerialization import *
    from ... import *

    __package__ = ni.original

# ----------------------------------------------------------------------
class UnitTest(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    def test_RegularExpressionString_Standard(self):
        self.assertEqual(StringSerialization.GetRegularExpressionString(BoolTypeInfo()), r"(true|t|yes|y|1|false|f|no|n|0)")
        self.assertEqual(StringSerialization.GetRegularExpressionString(DateTimeTypeInfo()), r"(?P<year0>[0-9]{4})[-/\.](?P<month0>0?[1-9]|1[0-2])[-/\.](?P<day0>[0-2][0-9]|3[0-1])[ T](?P<hour>[0-1][0-9]|2[0-3]):(?P<minute>[0-5][0-9]):(?P<second>[0-5][0-9])(?:\.(?P<fractional>\d+))?(?:(?P<tz_utc>Z)|(?P<tz_sign>[\+\-])(?P<tz_hour>\d{2}):(?P<tz_minute>[0-5][0-9]))?")
        self.assertEqual(StringSerialization.GetRegularExpressionString(DateTypeInfo()), r"(?P<year0>[0-9]{4})[-/\.](?P<month0>0?[1-9]|1[0-2])[-/\.](?P<day0>[0-2][0-9]|3[0-1])")
        self.assertEqual(StringSerialization.GetRegularExpressionString(DirectoryTypeInfo()), r".+")
        self.assertEqual(StringSerialization.GetRegularExpressionString(DurationTypeInfo()), r"(?P<hours>[1-9][0-0]*|0)?:(?P<minutes>[0-5][0-9])(?::(?P<seconds>[0-5][0-9])(?:\.(?P<fractional>[0-9]+))?)?")
        self.assertEqual(StringSerialization.GetRegularExpressionString(EnumTypeInfo([ "one", "two", "three", ])), r"(one|two|three)")
        self.assertEqual(StringSerialization.GetRegularExpressionString(FilenameTypeInfo()), r".+")
        self.assertEqual(StringSerialization.GetRegularExpressionString(FloatTypeInfo()), r"-?[0-9]+\.[0-9]+")
        self.assertEqual(StringSerialization.GetRegularExpressionString(GuidTypeInfo()), r"\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}")
        self.assertEqual(StringSerialization.GetRegularExpressionString(TimeTypeInfo()), r"(?P<hour>[0-1][0-9]|2[0-3]):(?P<minute>[0-5][0-9]):(?P<second>[0-5][0-9])(?:\.(?P<fractional>\d+))?(?:(?P<tz_utc>Z)|(?P<tz_sign>[\+\-])(?P<tz_hour>\d{2}):(?P<tz_minute>[0-5][0-9]))?")

    # ----------------------------------------------------------------------
    def test_RegularExpressionString_Int(self):
        self.assertEqual(StringSerialization.GetRegularExpressionString(IntTypeInfo()), r"-?[0-9]+")
        self.assertEqual(StringSerialization.GetRegularExpressionString(IntTypeInfo(min=0)), r"[0-9]+")
        self.assertEqual(StringSerialization.GetRegularExpressionString(IntTypeInfo(min=10)), r"[0-9]+")
        self.assertEqual(StringSerialization.GetRegularExpressionString(IntTypeInfo(max=0)), r"-[0-9]+")
        self.assertEqual(StringSerialization.GetRegularExpressionString(IntTypeInfo(max=10)), r"-?[0-9]+")
        self.assertEqual(StringSerialization.GetRegularExpressionString(IntTypeInfo(min=0, max=1000)), r"[0-9]{1,4}")
        self.assertEqual(StringSerialization.GetRegularExpressionString(IntTypeInfo(min=0, max=100000)), r"[0-9]{1,6}")
        self.assertEqual(StringSerialization.GetRegularExpressionString(IntTypeInfo(min=-100000, max=1000)), r"-?[0-9]{1,6}")

    # ----------------------------------------------------------------------
    def test_RegularExpressionString_String(self):
        self.assertEqual(StringSerialization.GetRegularExpressionString(StringTypeInfo()), r".+")
        self.assertEqual(StringSerialization.GetRegularExpressionString(StringTypeInfo(min_length=0)), r".*")
        self.assertEqual(StringSerialization.GetRegularExpressionString(StringTypeInfo(min_length=3, max_length=3)), r".{3}")
        self.assertEqual(StringSerialization.GetRegularExpressionString(StringTypeInfo(min_length=3, max_length=10)), r".{3,10}")
        self.assertEqual(StringSerialization.GetRegularExpressionString(StringTypeInfo(validation_expression="foo")), r"foo")

    # ----------------------------------------------------------------------
    def test_GetRegularExpressionStringInfo_Standard(self):
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(BoolTypeInfo()), [ ( r"(true|t|yes|y|1|false|f|no|n|0)", re.IGNORECASE ), ])
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(DateTimeTypeInfo()), [ r"(?P<year0>[0-9]{4})[-/\.](?P<month0>0?[1-9]|1[0-2])[-/\.](?P<day0>[0-2][0-9]|3[0-1])[ T](?P<hour>[0-1][0-9]|2[0-3]):(?P<minute>[0-5][0-9]):(?P<second>[0-5][0-9])(?:\.(?P<fractional>\d+))?(?:(?P<tz_utc>Z)|(?P<tz_sign>[\+\-])(?P<tz_hour>\d{2}):(?P<tz_minute>[0-5][0-9]))?", ])
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(DateTypeInfo()), [ r'(?P<year0>[0-9]{4})[-/\.](?P<month0>0?[1-9]|1[0-2])[-/\.](?P<day0>[0-2][0-9]|3[0-1])',
                                                                                               r'(?P<month1>0?[1-9]|1[0-2])[-/\.](?P<day1>[0-2][0-9]|3[0-1])[-/\.](?P<year1>[0-9]{4})',
                                                                                               r'(?P<year2>\d{2})[-/\.](?P<month2>0?[1-9]|1[0-2])[-/\.](?P<day2>[0-2][0-9]|3[0-1])',
                                                                                               r'(?P<month3>0?[1-9]|1[0-2])[-/\.](?P<day3>[0-2][0-9]|3[0-1])[-/\.](?P<year3>\d{2})',
                                                                                             ])
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(DirectoryTypeInfo()), [ r".+", ])
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(DurationTypeInfo()), [ r"(?P<hours>[1-9][0-0]*|0)?:(?P<minutes>[0-5][0-9])(?::(?P<seconds>[0-5][0-9])(?:\.(?P<fractional>[0-9]+))?)?", ])
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(EnumTypeInfo([ "one", "two", "three", ])), [ r"(one|two|three)", ])
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(FilenameTypeInfo()), [ r".+", ])
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(FloatTypeInfo()), [ r"-?[0-9]+\.[0-9]+", ])
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(GuidTypeInfo()), [ r"\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}", 
                                                                                               r'[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}',
                                                                                               r'\{[0-9A-Fa-f]{32}\}',
                                                                                               r'[0-9A-Fa-f]{32}',
                                                                                             ])
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(TimeTypeInfo()), [ r"(?P<hour>[0-1][0-9]|2[0-3]):(?P<minute>[0-5][0-9]):(?P<second>[0-5][0-9])(?:\.(?P<fractional>\d+))?(?:(?P<tz_utc>Z)|(?P<tz_sign>[\+\-])(?P<tz_hour>\d{2}):(?P<tz_minute>[0-5][0-9]))?", ])

    # ----------------------------------------------------------------------
    def test_RegularExpressionStringInfo_Int(self):
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(IntTypeInfo()), [ r"-?[0-9]+", ])
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(IntTypeInfo(min=0)), [ r"[0-9]+", ])
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(IntTypeInfo(min=10)), [ r"[0-9]+", ])
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(IntTypeInfo(max=0)), [ r"-[0-9]+", ])
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(IntTypeInfo(max=10)), [ r"-?[0-9]+", ])
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(IntTypeInfo(min=0, max=1000)), [ r"[0-9]{1,4}", ])
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(IntTypeInfo(min=0, max=100000)), [ r"[0-9]{1,6}", ])
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(IntTypeInfo(min=-100000, max=1000)), [ r"-?[0-9]{1,6}", ])

    # ----------------------------------------------------------------------
    def test_RegularExpressionStringInfo_String(self):
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(StringTypeInfo()), [ r".+", ])
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(StringTypeInfo(min_length=0)), [ r".*", ])
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(StringTypeInfo(min_length=3, max_length=3)), [ r".{3}", ])
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(StringTypeInfo(min_length=3, max_length=10)), [ r".{3,10}", ])
        self.assertEqual(StringSerialization.GetRegularExpressionStringInfo(StringTypeInfo(validation_expression="foo")), [ r"foo", ])

    # ----------------------------------------------------------------------
    def test_Serialize(self):
        self.assertEqual(StringSerialization.SerializeItem(BoolTypeInfo(), True), "True")
        self.assertEqual(StringSerialization.SerializeItem(BoolTypeInfo(), False), "False")

        self.assertEqual(StringSerialization.SerializeItem(DateTimeTypeInfo(), datetime.datetime(year=2016, month=9, day=10, hour=8, minute=10, second=0)), "2016-09-10 08:10:00")
        self.assertEqual(StringSerialization.SerializeItem(DateTimeTypeInfo(), datetime.datetime(year=2016, month=9, day=10, hour=8, minute=10, second=0), sep='T'), "2016-09-10T08:10:00")

        self.assertEqual(StringSerialization.SerializeItem(DateTypeInfo(), datetime.date(year=2016, month=9, day=10)), "2016-09-10")

        self.assertEqual(StringSerialization.SerializeItem(DirectoryTypeInfo(ensure_exists=False), os.path.sep.join([ "Foo", "Bar", "Baz", ])), "Foo/Bar/Baz")

        self.assertEqual(StringSerialization.SerializeItem(DurationTypeInfo(), datetime.timedelta(seconds=400)), "0:06:40.0")
    
        self.assertEqual(StringSerialization.SerializeItem(EnumTypeInfo([ "one", "two", "three", ]), "two"), "two")

        self.assertEqual(StringSerialization.SerializeItem(FilenameTypeInfo(ensure_exists=False), os.path.sep.join([ "Foo", "Bar", "Baz", ])), "Foo/Bar/Baz")

        self.assertEqual(StringSerialization.SerializeItem(FloatTypeInfo(), 1.0), "1.0")
        self.assertEqual(StringSerialization.SerializeItem(FloatTypeInfo(), -21.1234567), "-21.1234567")

        guid = uuid.uuid4()
        self.assertEqual(StringSerialization.SerializeItem(GuidTypeInfo(), guid), str(guid))

        self.assertEqual(StringSerialization.SerializeItem(IntTypeInfo(), 10), "10")
        self.assertEqual(StringSerialization.SerializeItem(IntTypeInfo(), -20), "-20")

        self.assertEqual(StringSerialization.SerializeItem(StringTypeInfo(), "foo"), "foo")

        self.assertEqual(StringSerialization.SerializeItem(TimeTypeInfo(), datetime.time(hour=18, minute=5, second=32)), "18:05:32")

    # ----------------------------------------------------------------------
    def test_Deserialize(self):
        self.assertEqual(StringSerialization.DeserializeItem(BoolTypeInfo(), "True"), True)
        self.assertEqual(StringSerialization.DeserializeItem(BoolTypeInfo(), "true"), True)
        self.assertEqual(StringSerialization.DeserializeItem(BoolTypeInfo(), "Yes"), True)
        self.assertEqual(StringSerialization.DeserializeItem(BoolTypeInfo(), "y"), True)
        self.assertEqual(StringSerialization.DeserializeItem(BoolTypeInfo(), "t"), True)
        self.assertEqual(StringSerialization.DeserializeItem(BoolTypeInfo(), "1"), True)
        self.assertEqual(StringSerialization.DeserializeItem(BoolTypeInfo(), "False"), False)
        self.assertEqual(StringSerialization.DeserializeItem(BoolTypeInfo(), "no"), False)
        self.assertEqual(StringSerialization.DeserializeItem(BoolTypeInfo(), "0"), False)

        self.assertEqual(StringSerialization.DeserializeItem(DateTimeTypeInfo(), "2016-09-10 08:10:00"), datetime.datetime(year=2016, month=9, day=10, hour=8, minute=10, second=0))
        self.assertEqual(StringSerialization.DeserializeItem(DateTimeTypeInfo(), "2016-09-10T08:10:00"), datetime.datetime(year=2016, month=9, day=10, hour=8, minute=10, second=0))

        self.assertEqual(StringSerialization.DeserializeItem(DateTypeInfo(), "2016-09-10"), datetime.date(year=2016, month=9, day=10))

        self.assertEqual(StringSerialization.DeserializeItem(DirectoryTypeInfo(ensure_exists=False), "Foo/Bar/Baz"), os.path.join(os.getcwd(), "Foo", "Bar", "Baz"))
        self.assertEqual(StringSerialization.DeserializeItem(DirectoryTypeInfo(ensure_exists=False), "Foo/Bar/Baz", normalize=False), os.path.join("Foo", "Bar", "Baz"))
        
        self.assertEqual(StringSerialization.DeserializeItem(DurationTypeInfo(), "0:06:40.0"), datetime.timedelta(seconds=400))
        self.assertEqual(StringSerialization.DeserializeItem(DurationTypeInfo(), "0:06"), datetime.timedelta(seconds=6))
    
        self.assertEqual(StringSerialization.DeserializeItem(EnumTypeInfo([ "one", "two", "three", ]), "two"), "two")

        self.assertEqual(StringSerialization.DeserializeItem(FilenameTypeInfo(ensure_exists=False), "Foo/Bar/Baz"), os.path.join(os.getcwd(), "Foo", "Bar", "Baz"))
        self.assertEqual(StringSerialization.DeserializeItem(FilenameTypeInfo(ensure_exists=False), "Foo/Bar/Baz", normalize=False), os.path.join("Foo", "Bar", "Baz"))

        self.assertEqual(StringSerialization.DeserializeItem(FloatTypeInfo(), "1.0"), 1.0)
        self.assertEqual(StringSerialization.DeserializeItem(FloatTypeInfo(), "-21.1234567"), -21.1234567)

        guid = uuid.uuid4()
        self.assertEqual(StringSerialization.DeserializeItem(GuidTypeInfo(), str(guid)), guid)

        self.assertEqual(StringSerialization.DeserializeItem(IntTypeInfo(), "10"), 10)
        self.assertEqual(StringSerialization.DeserializeItem(IntTypeInfo(), "-20"), -20)

        self.assertEqual(StringSerialization.DeserializeItem(StringTypeInfo(), "foo"), "foo")

        self.assertEqual(StringSerialization.DeserializeItem(TimeTypeInfo(), "18:05:32"), datetime.time(hour=18, minute=5, second=32))

    # ----------------------------------------------------------------------
    def test_Deserialize_Errors(self):
        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(IntTypeInfo(), "a1000"))
        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(IntTypeInfo(), "1000a"))
        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(IntTypeInfo(), "10 00"))

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
