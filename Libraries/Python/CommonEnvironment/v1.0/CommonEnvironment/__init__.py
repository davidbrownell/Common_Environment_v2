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
# |  Copyright David Brownell 2015-18.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import re
import sys
import textwrap

import six
from six.moves import StringIO

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
# <Too few public methods> pylint: disable = R0903
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
        functor = bool

    for item in items:
        if not functor(item):
            return False

    return bool(items)

# ---------------------------------------------------------------------------
def Any( items,
         functor=None,                      # def Func(item) -> Bool
       ):
    if functor == None:
        functor = bool

    for item in items:
        if functor(item):
            return True

    return False

# ----------------------------------------------------------------------
# <Invalid argument name> pylint: disable = C0103
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
    
# <Invalid argument name> pylint: disable = C0103
def ToSnakeCase(s):
    """Returns a_snake_case string"""
    return _ToSnakeCase_regex.sub(r'_\1', s).lower().replace('__', '_')

# ----------------------------------------------------------------------
_ToPlural_engine = ModifiableValue(None)

# <Invalid argument name> pylint: disable = C0103
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
def Describe( item,                         # str, dict, iterable, obj 
              output_stream=sys.stdout,
            ):
    from CommonEnvironment.StreamDecorator import StreamDecorator

    # ----------------------------------------------------------------------
    def OutputDict(item, indentation_str):
        if not item:
            output_stream.write("-- empty --\n")
            return

        if hasattr(item, "_asdict"):
            item = item._asdict()

        keys = list(item.keys())
        keys.sort(key=str.lower)

        max_length = 0
        for key in keys:
            max_length = max(max_length, len(key))

        item_indentation_str = indentation_str + (' ' * (max_length + len(" : ")))

        for index, key in enumerate(keys):
            output_stream.write("{0}{1:<{2}} : ".format( indentation_str if index else '', 
                                                         key, 
                                                         max_length,
                                                       ))
            Impl(item[key], item_indentation_str)

    # ----------------------------------------------------------------------
    def OutputList(item, indentation_str):
        if not item:
            output_stream.write("-- empty --\n")
            return

        item_indentation_str = indentation_str + (' ' * 5)

        for index, i in enumerate(item):
            output_stream.write("{0}{1:<5}".format( indentation_str if index else '', 
                                                    "{})".format(index),
                                                  ))
            Impl(i, item_indentation_str)

    # ----------------------------------------------------------------------
    def Impl(item, indentation_str):
        if isinstance(item, six.string_types):
            output_stream.write("{}\n".format(item))
        elif isinstance(item, dict):
            OutputDict(item, indentation_str)
        elif isinstance(item, list):
            OutputList(item, indentation_str)
        else:
            # ----------------------------------------------------------------------
            def Display():
                try:
                    potential_attribute_name = next(iter(item))
                    
                    # Is the item dict-like?
                    try:
                        ignore_me = item[potential_attribute_name]
                        OutputDict(item, indentation_str)
                    except TypeError:
                        OutputList(item, indentation_str)

                    return True

                except (TypeError, IndexError, StopIteration):
                    return False

            # ----------------------------------------------------------------------

            if not Display():
                content = str(item).strip()

                if "<class" not in content:
                    content += "{}{}".format( '\n' if content.count('\n') > 1 else ' ',
                                              type(item),
                                              )

                output_stream.write("{}\n".format(StreamDecorator.LeftJustify(content, len(indentation_str))))

    # ----------------------------------------------------------------------

    Impl(item, '')
    output_stream.write('\n\n')

# ----------------------------------------------------------------------
def ObjectToDict(obj):
    keys = [ k for k in dir(obj) if not k.startswith("__") ]
    return { k : getattr(obj, k) for k in keys }

# ----------------------------------------------------------------------
def ObjStrImpl(obj, include_methods=False):
    """\
    def __str__(self):
        return CommonEnvironment.ObjStrImpl(self)
    """
    d = ObjectToDict(obj)

    if not include_methods:
        for k in list(six.iterkeys(d)):
            if callable(d[k]):
                del d[k]

    sink = StringIO()
    Describe(d, sink)
    
    return "{}\n{}\n".format(type(obj), sink.getvalue())

# ----------------------------------------------------------------------
def Listify( item_or_items_or_none,
             always_return_list=False,
           ):
    if item_or_items_or_none is None:
        return [] if always_return_list else None

    if isinstance(item_or_items_or_none, list):
        return item_or_items_or_none

    return [ item_or_items_or_none, ]
                                
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if sys.version_info[0] == 2:
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
        import __builtin__                  # <Unable to import> pylint: disable = F0401
    
        import six

        # ----------------------------------------------------------------------
        def DecorateFilename(filename):
            if filename:
                filename = os.path.realpath(os.path.normpath(filename))
    
                if not filename.startswith("\\\\?\\"):
                    filename = u"\\\\?\\{}".format(filename)
    
            return filename
    
        # ----------------------------------------------------------------------
        def Patch(original_method):
            # ----------------------------------------------------------------------
            def NewFunction(filename, *args, **kwargs):
                return original_method(DecorateFilename(filename), *args, **kwargs)
    
            # ----------------------------------------------------------------------
            
            return NewFunction
    
        # ----------------------------------------------------------------------
        def WalkItems(mod, items):
            for item in items:
                if isinstance(item, six.string_types):
                    setattr(mod, item, Patch(getattr(mod, item)))
                elif isinstance(item, dict):
                    for k, v in item.iteritems():
                        WalkItems(getattr(mod, k), v)
                else:
                    assert False, type(item)
    
        # ----------------------------------------------------------------------
        
        for module_name, these_items in six.iteritems({ "__builtin__" : [ "open",
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
                                                      }):
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
    