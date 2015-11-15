# ---------------------------------------------------------------------------
# |  
# |  TimeDelta.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/21/2015 02:00:27 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import datetime
import os
import sys
import time

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# <Too few public methods> pylint: disable = R0903
class TimeDelta(object):
    
    # ---------------------------------------------------------------------------
    def __init__(self):
        self._start_time = time.time()

    # ---------------------------------------------------------------------------
    def CalculateDelta(self, as_string=False):
        current_seconds = time.time()

        # There is a bug (and I have seen it) where the value calculated
        # in the past will be greater than the value calculated now. This is
        # wrong in theory, but apparently there is a BIOS bug that causes the
        # behavior on multicore machines (I have a hunch that virtualized machines
        # contribute to the problem as well). More info at http://bytes.com/topic/python/answers/527849-time-clock-going-backwards.
        # Regardless, asserting here is causing problems and this method is
        # only used for scripts. If we encounter the scenario, populate with 
        # bogus data.
        if self._start_time > current_seconds:
            # This is a total lie, but hopefully the value is unique enough to
            # generate a double take. This is preferable to causing a long-
            # running process to fail.
            current_seconds = current_seconds + (12 * 60 * 60) + (34 * 60) + 56         # 12:34:56      
        
        assert current_seconds >= self._start_time, (current_seconds, self._start_time)
        delta = current_seconds - self._start_time

        if not as_string:
            return delta

        return str(datetime.timedelta(seconds=delta))
