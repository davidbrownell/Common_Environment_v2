# ---------------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/06/2015 01:55:15 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import re
import sys

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class ModifiableValue(object):
    def __init__(self, value):
        self.value                          = value

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def Get( items, 
         functor,                           # def Func(item) -> Bool
         extractor=None,                    # def Func(item) -> Any
       ):
    for item in items:
        if functor(item):
            return extractor(item) if extractor else item

# ----------------------------------------------------------------------
def GetIndex( items,
              functor,                      # def Func(item) -> Bool
            ):
    for index, item in enumerate(items):
        if functor(item):
            return index

# ---------------------------------------------------------------------------
def All( items,
         functor=None,                      # def Func(item) -> Bool
       ):
    if functor == None:
        functor = lambda item: bool(item)

    for item in items:
        if not functor(item):
            return False

    return bool(items)

# ---------------------------------------------------------------------------
def Any( items,
         functor=None,                      # def Func(item) -> Bool
       ):
    if functor == None:
        functor = lambda item: bool(item)

    for item in items:
        if functor(item):
            return True

    return False

# ----------------------------------------------------------------------
def ToPascalCase(s):
    """Returns APascalCase string"""
    parts = s.split('_')

    # Handle corner case where the original string starts or ends with an underscore
    if not parts[0]:
        parts[0] = '_'

    if len(parts) > 1 and not parts[-1]:
        parts[-1] = '_'

    return ''.join([ "{}{}".format(part[0].upper(), part[1:]) for part in parts ])

# ----------------------------------------------------------------------
_ToSnakeCase_regex = re.compile("((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))")
    
def ToSnakeCase(s):
    """Returns a_snake_case string"""
    return _ToSnakeCase_regex.sub(r'_\1', s).lower().replace('__', '_')

# ----------------------------------------------------------------------
_ToPlural_engine = ModifiableValue(None)

def ToPlural(s):
    if _ToPlural_engine.value == None:
        import inflect

        _ToPlural_engine.value = inflect.engine()

    engine = _ToPlural_engine.value

    result = engine.singular_noun(s)
    if result == False:
        return engine.plural_noun(s)

    return s

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

# On Windows, python2.7 has problem with long filenames. Mokeypatch some
# of those methods to work around the most common problems. In all cases,
# the decoration '\\?\' is considered an implementation detail and should
# not be exposed to the caller.
import platform

# if...
#       We are on Windows, and...
#       The functionality hasn't been explicitly disabled, and...
#       This isn't IronPython (which doesn't have this problem)...
#
if ( platform.uname()[0] == "Windows" and \
     not os.getenv("DEVELOPMENT_ENVIRONMENT_NO_LONG_FILENAME_PATCH") and \
     platform.python_implementation().lower().find("ironpython") == -1
   ):
    import __builtin__

    # ----------------------------------------------------------------------
    def DecorateFilename(filename):
        if filename:
            filename = os.path.realpath(os.path.normpath(filename))

            if not filename.startswith("\\\\?\\"):
                filename = ur"\\?\{}".format(filename)

        return filename

    # ----------------------------------------------------------------------
    def Patch(original_method):
        # ----------------------------------------------------------------------
        def NewFunction(filename, *args, **kwargs):
            return original_method(DecorateFilename(filename), *args, **kwargs)

        # ----------------------------------------------------------------------
        
        return NewFunction

    # ----------------------------------------------------------------------
    def WalkItems(module, these_items):
        for item in these_items:
            if isinstance(item, basestring):
                setattr(module, item, Patch(getattr(module, item)))
            elif isinstance(item, dict):
                for k, v in item.iteritems():
                    WalkItems(getattr(module, k), v)
            else:
                assert False, type(item)

    # ----------------------------------------------------------------------
    
    for module_name, these_items in { "__builtin__" : [ "open",
                                                      ],
                                      "os" : [ "makedirs",
                                               "remove",
                                               "stat",
                                               { "path" : [ "exists",
                                                            "getsize",
                                                            "getmtime",
                                                            "isdir",
                                                            "isfile",
                                                          ],
                                               }             
                                             ],
                                    }.iteritems():
        assert module_name in sys.modules
        module = sys.modules[module_name]

        WalkItems(module, these_items)

    # os.walk needs to be handled in a special way
    _os_walk = os.walk

    # ----------------------------------------------------------------------
    def NewWalk(top, *args, **kwargs):
        top = DecorateFilename(top)

        for root, dirs, files in _os_walk(top, *args, **kwargs):
            if root.startswith("\\\\?\\"):
                root = root[len("\\\\?\\"):]

            yield root, dirs, files

    # ----------------------------------------------------------------------
    
    os.walk = NewWalk
