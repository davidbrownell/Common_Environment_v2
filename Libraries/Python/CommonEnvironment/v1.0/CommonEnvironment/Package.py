# ---------------------------------------------------------------------------
# |  
# |  Package.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/23/2015 02:49:13 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""
Python packages are notoriously fickle - using relative imports within a file may
or may not work as expected depending on the way in which the file was invoked.
This code ensure that relative imports always work as expected through some pretty
extreme manipulation of the packaging internals.
"""

import inspect
import os
import sys
import traceback

from contextlib import contextmanager

from . import ModifiableValue
from .CallOnExit import CallOnExit

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
@contextmanager
def NameInfo(package_value):
    # Note that this is created as a generator so local var won't have a global lifetime
    # when invoked.
    
    # ---------------------------------------------------------------------------
    class _NameInfo(object):
        # ----------------------------------------------------------------------
        def __init__(self):
            frame = inspect.stack()[3]          # 1 for ctor, 1 for method, 1 for contextmanager
            mod = inspect.getmodule(frame[0])
            
            # This is a hack, but attempt to extract the module
            # name if mod is None (which will happen when the
            # script is frozen)
            if mod:
                mod_name = mod.__name__
                mod_file = mod.__file__
            else:
                mod_file = frame[1]
                mod_name = os.path.splitext(os.path.basename(mod_file))[0]

            self.original                       = package_value
            self.created                        = CreateName(package_value, mod_name, mod_file)
        
    # ---------------------------------------------------------------------------
    
    yield _NameInfo()
    
# ---------------------------------------------------------------------------
def CreateName(package, name, file):
    """
    Creates a package name:

    Usage:
        __package__ = CreateName(__package__, __name__, __file__)
    """

    if package:
        return package

    name_parts = name.split('.')
    if len(name_parts) > 1:
        # If the name already has dots, it means that the current
        # module is part of a package. By default, the name includes
        # the current filename, but that filename shouldn't be a part
        # of the package name.
        name = '.'.join(name_parts[:-1])
        assert name in sys.modules, name

        return name

    # Ensure that relative imports work as expected by inserting the current
    # dir at the head of the path.
    original_dir = os.path.dirname(os.path.realpath(file))
    
    if original_dir in sys.path:
        sys.path.remove(original_dir)

    sys.path.insert(0, original_dir)

    # Walk up all directories while there is an __init__ file...
    name_parts = []

    directory = original_dir
    while os.path.isfile(os.path.join(directory, "__init__.py")):
        directory, name = os.path.split(directory)
        name_parts.append(name)

    if not name_parts:
        # If we didn't find any __init__ files, it means that this
        # isn't a file that is part of a package. However, we want
        # to simulate that it is part of a package so that relative 
        # imports work as expected.
        if name == "__main__" or getattr(sys, "frozen", False):
            name = "___EntryPoint___"
        else:
            name = "___{}Lib___".format(name)

        sys.modules[name] = None

        return name

    # If here, we are looking at a file in a package. Ensure that the
    # entire package is included with fully qualified names.
    name_parts.reverse()
    
    for index, name_part in enumerate(name_parts):
        this_name = '.'.join(name_parts[:index + 1])
        
        if this_name not in sys.modules:
            # If here, we need to add the fully qualified name to the
            # list of modules.
            item_exists = name_part in sys.modules
            if not item_exists:
                # If here, we need to import the current package under its
                # own name so that dependent imports will be successful.
                sys.path.insert(0, directory)
                with CallOnExit(lambda: sys.path.pop(0)):
                    sys.modules[name_part] = __import__(name_part)
                    
            sys.modules[this_name] = sys.modules[name_part]

            if not item_exists and len(name_parts) > 1 and index != 0:
                # Remove the individual package if we added it only
                # for the fully qualified package.
                del sys.modules[name_part]

        directory = os.path.join(directory, name_part)

    return this_name
    
# ---------------------------------------------------------------------------
def ImportInit( dotted_name=None,
              ):
    original_calling_dir = os.path.dirname(traceback.extract_stack(limit=2)[0][0])

    if dotted_name:
        path_parts = []

        if dotted_name.startswith(".."):
            dots = 0
            while dots < len(dotted_name) and dotted_name[dots] == '.':
                dots += 1

            dotted_name = dotted_name[dots:]

            path_parts += [ "..", ] * (dots - 1)

        path_parts += dotted_name.split('.')

        original_calling_dir = os.path.join(original_calling_dir, *path_parts)
        assert os.path.isdir(original_calling_dir), original_calling_dir

    original_calling_dir = os.path.realpath(os.path.normpath(original_calling_dir))

    name_stack = []

    calling_dir = original_calling_dir
    while True:
        if not os.path.isfile(os.path.join(calling_dir, "__init__.py")):
            break

        name_stack.append(os.path.basename(calling_dir))
        
        potential_calling_dir = os.path.dirname(calling_dir)
        if potential_calling_dir == calling_dir:
            break

        calling_dir = potential_calling_dir

    assert name_stack, original_calling_dir

    if calling_dir:
        sys.path.insert(0, calling_dir)
        Cleanup = lambda: sys.path.pop(0)
    else:
        Cleanup = lambda: None

    with CallOnExit(Cleanup):
        prefix = []
        
        while name_stack:
            prefix.append(name_stack.pop())

            module_name = '.'.join(prefix)

            if module_name not in sys.modules:
                __import__(module_name)

        return sys.modules[module_name]
        