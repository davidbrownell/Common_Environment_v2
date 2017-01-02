# ----------------------------------------------------------------------
# |  
# |  JsonLikeSerialization_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-06 17:31:15
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-17.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import datetime
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
    
    from ..JsonLikeSerialization import *
    from ... import *

    __package__ = ni.original

# ----------------------------------------------------------------------
class UnitTest(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    def test_SerializeItem(self):
        self.assertEqual(JsonLikeSerialization.SerializeItem(BoolTypeInfo(), True), True)
        self.assertEqual(JsonLikeSerialization.SerializeItem(FloatTypeInfo(), 1.0), 1.0)
        self.assertEqual(JsonLikeSerialization.SerializeItem(IntTypeInfo(), 100), 100)
        self.assertEqual(JsonLikeSerialization.SerializeItem(DurationTypeInfo(), datetime.timedelta(seconds=130)), "0:02:10.000000")

    # ----------------------------------------------------------------------
    def test_DeserializeItem(self):
        self.assertEqual(JsonLikeSerialization.DeserializeItem(BoolTypeInfo(), True), True)
        self.assertEqual(JsonLikeSerialization.DeserializeItem(FloatTypeInfo(), 1.0), 1.0)
        self.assertEqual(JsonLikeSerialization.DeserializeItem(IntTypeInfo(), 100), 100)
        self.assertEqual(JsonLikeSerialization.DeserializeItem(DurationTypeInfo(), "0:02:10.0"), datetime.timedelta(seconds=130))

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
