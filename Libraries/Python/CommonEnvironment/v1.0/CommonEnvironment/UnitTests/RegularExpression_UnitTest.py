# Placeholder unit test

import os
import sys
import unittest

from CommonEnvironment.CallOnExit import CallOnExit

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, ".."))
with CallOnExit(lambda: sys.path.pop(0)):
    from RegularExpression import *

# ----------------------------------------------------------------------
class GenerateTest(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    def test_NoMatches(self):
        results = list(Generate(r"\s", "OneTwoThree"))
        self.assertEqual(len(results), 0)

    # ----------------------------------------------------------------------
    def test_Matches(self):
        results = list(Generate(re.compile(r"[A-Z]"), "One Two Three"))
        self.assertEqual(len(results), 3)

        self.assertEqual(results[0], { "__data__" : "ne ", })
        self.assertEqual(results[1], { "__data__" : "wo ", })
        self.assertEqual(results[2], { "__data__" : "hree", })

    # ----------------------------------------------------------------------
    def test_MatchesWithPrefix(self):
        results = list(Generate(r"\s", "One Two Three", yield_prefix=True))
        self.assertEqual(len(results), 3)

        self.assertEqual(results[0], { "__data__" : "One", })
        self.assertEqual(results[1], { "__data__" : "Two", })
        self.assertEqual(results[2], { "__data__" : "Three", })

    # ----------------------------------------------------------------------
    def test_NoMatchesWithCapture(self):
        results = list(Generate(r"\s(?P<c>\S)", "OneTwoThree"))
        self.assertEqual(len(results), 0)

    # ----------------------------------------------------------------------
    def test_MatchesWithCapture(self):
        results = list(Generate(r"(?P<c>[A-Z][a-z])", "One Two Three"))
        self.assertEqual(len(results), 3)

        self.assertEqual(results[0], { "__data__" : "e ", "c" : "On", })
        self.assertEqual(results[1], { "__data__" : "o ", "c" : "Tw", })
        self.assertEqual(results[2], { "__data__" : "ree", "c" : "Th", })

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass

