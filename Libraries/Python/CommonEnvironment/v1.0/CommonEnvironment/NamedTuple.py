# ---------------------------------------------------------------------------
# |  
# |  NamedTuple.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/28/2015 06:36:59 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Convenience wrapper around collections.namedtuple
"""

import os
import sys

from collections import namedtuple

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

def NamedTuple(name, *args, **kwargs):
    """\
    Usage:

    Foo = NamedTuple("Foo", "bar", "baz", biz=10)

    f = Foo(1, 2)
    f = Foo(1, 2, 3)

    Bar = NamedTuple("Bar", "one", **OrderedDict([ ( "two", 2 ), ( "three", 3 ), ]))
    """

    if not kwargs and len(args) == 1 and isinstance(args[0], dict):
        kwargs = args[0]
        args = []

    T = namedtuple(name, list(args) + kwargs.keys())
    T.__new__.__defaults__ = tuple(kwargs.values())

    return T
