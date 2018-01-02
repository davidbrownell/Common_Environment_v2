# ----------------------------------------------------------------------
# |  
# |  __init___UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-06 17:31:15
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-18.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import sys
import unittest

from CommonEnvironment.Interface import staticderived
from CommonEnvironment import Package

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with Package.NameInfo(__package__) as ni:
    __package__ = ni.created
    
    from .. import *
    from ... import *
    from .... import ValidationException

    __package__ = ni.original

# ----------------------------------------------------------------------
@staticderived
class MySerialization(Serialization):
    # ----------------------------------------------------------------------
    @staticmethod
    def _SerializeItemImpl(type_info, item):
        return (item, True)

    # ----------------------------------------------------------------------
    @staticmethod
    def _DeserializeItemImpl(type_info, item):
        assert isinstance(item, tuple)
        return item[0]

# ----------------------------------------------------------------------
class UnitTest(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    def test_SerializeItems(self):
        self.assertEqual(MySerialization.SerializeItems(StringTypeInfo(), "Foo"), ( "Foo", True ))
        self.assertEqual(MySerialization.SerializeItems(StringTypeInfo(arity=Arity.FromString('*')), [ "Foo", "Bar", "Baz", ]), [ ( "Foo", True ), ( "Bar", True ), ( "Baz", True ), ])
        self.assertEqual(MySerialization.SerializeItems(StringTypeInfo(arity=Arity.FromString('*')), []), [])

        self.assertRaises(ValidationException, lambda: MySerialization.SerializeItems(BoolTypeInfo(arity=Arity(3, 3)), [ 1, 2, 3, 4, ]))
        
        self.assertEqual(MySerialization.SerializeItems(BoolTypeInfo(arity=Arity.FromString('?')), True), (True, True))
        self.assertEqual(MySerialization.SerializeItems(BoolTypeInfo(arity=Arity.FromString('?')), None), None)

    # ----------------------------------------------------------------------
    def test_DeserializeItems(self):
        self.assertEqual(MySerialization.DeserializeItems(StringTypeInfo(), ( "Foo", True )), "Foo")
        self.assertEqual(MySerialization.DeserializeItems(StringTypeInfo(arity=Arity.FromString('*')), [ ( "Foo", True ), ( "Bar", True ), ( "Baz", True ), ]), [ "Foo", "Bar", "Baz", ])
        self.assertEqual(MySerialization.DeserializeItems(StringTypeInfo(arity=Arity.FromString('*')), []), [])

        self.assertRaises(ValidationException, lambda: MySerialization.DeserializeItems(BoolTypeInfo(arity=Arity(2, 2)), [ 1, 2, 3, 4, ]))

        self.assertEqual(MySerialization.DeserializeItems(BoolTypeInfo(arity=Arity.FromString('?')), ( True, True )), True)
        self.assertEqual(MySerialization.DeserializeItems(BoolTypeInfo(arity=Arity.FromString('?')), None), None)

    # ----------------------------------------------------------------------
    def test_SerializeItem(self):
        ti = StringTypeInfo(min_length=2)

        self.assertEqual(MySerialization.SerializeItem(ti, "Foo"), ( "Foo", True ))
        self.assertRaises(ValidationException, lambda: MySerialization.SerializeItem(ti, "f"))

    # ----------------------------------------------------------------------
    def test_DeserializeItem(self):
        ti = StringTypeInfo(min_length=2)

        self.assertEqual(MySerialization.DeserializeItem(ti, ( "Foo", True )), "Foo")
        self.assertRaises(ValidationException, lambda: MySerialization.DeserializeItem(ti, ( "f", True)))

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
