# ----------------------------------------------------------------------
# |  
# |  UriTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-06-23 10:05:22
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017-18.
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
    
    from ..UriTypeInfo import *
    
    __package__ = ni.original

# ----------------------------------------------------------------------
class UnitTest(unittest.TestCase):
    # ----------------------------------------------------------------------
    def test_Uri(self):
        self.assertRaises(Exception, lambda: Uri(None, "host", "path"))
        self.assertRaises(Exception, lambda: Uri("scheme", None, "path"))

        for s in [ "http://a.b.com",
                   "http://a.b.com:80",
                   "http://a.b.com/Path",
                   "http://a.b.com:80/Path",
                   "http://user:pass@a.b.com/Path",
                   "http://a.b.com/?a=b&c=d",
                   "https://user:pass_BSLASH__AT_@a.b.com/Path",
                 ]:
            self.assertEqual(Uri.FromString(s).ToString(), s)

    # ----------------------------------------------------------------------
    def test_UriTypeInfo(self):
        ti = UriTypeInfo()

        self.assertEqual(ti.PythonDefinitionString, "UriTypeInfo(arity=Arity(min=1, max_or_none=1))")

        ti.ValidateItem(Uri.FromString("http://one.two.three"))

    # ----------------------------------------------------------------------
    def test_UriTypes(self):
        uri = Uri.FromString("https://user:pass_BSLASH__AT_@a.b.com:123/Path/More")


        self.assertEqual(uri.Scheme, "https")
        self.assertEqual(uri.Host, "a.b.com")
        self.assertEqual(uri.Path, "/Path/More")
        self.assertEqual(uri.Query, {})
        self.assertEqual(uri.Port, 123)
        self.assertEqual(uri.Credentials[0], "user")
        self.assertEqual(uri.Credentials[1], "pass\\@")

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
