# ----------------------------------------------------------------------
# |  
# |  Python2to3Helpers.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-03-19 14:19:28
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import sys

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

try:
    unicode = unicode
except NameError:
    # 'unicode' is undefined, must be Python 3
    str                                     = str
    unicode                                 = str
    bytes                                   = bytes
    basestring                              = (str,bytes)
else:
    # 'unicode' exists, must be Python 2
    str                                     = str
    unicode                                 = unicode
    bytes                                   = str
    basestring                              = basestring

# ----------------------------------------------------------------------
_IS_PYTHON2                                 = sys.version_info[0] == 2

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def Dict_Enumerate(d):
    if _IS_PYTHON2:
        for item in d.iteritems():
            yield item
    else:
        for item in d.items():
            yield item

# ----------------------------------------------------------------------
def Dict_KeysList(d):
    if _IS_PYTHON2:
        return d.keys()
    else:
        return list(d.keys())

# ----------------------------------------------------------------------
def Dict_ValuesList(d):
    if _IS_PYTHON2:
        return d.values()
    else:
        return list(d.values())

# ----------------------------------------------------------------------
def zip(*args):
    if _IS_PYTHON2:
        import itertools

        for item in itertools.izip(*args):
            yield item
    else:
        for item in zip(*args):
            yield item
