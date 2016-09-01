# ---------------------------------------------------------------------------
# |  
# |  Decorator.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/28/2015 07:48:09 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import inspect
import os
import sys

import wrapt

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Decorators
# |  
# ----------------------------------------------------------------------
def AsFunc(method_name):
    """\
    Invokes the class as if it were a function, calling the provided method_name
    with an instantiated class instance. Requires that the class is default
    constructible.

    Example:
        @AsFunc("Foo")
        class MyClass(object):
            @staticmethod
            def Foo():
                return "Bar"

            def __init__(self, value):
                self.value = value

            def Another(self):
                return "Another: {}".format(self.value)

        MyClass() => "Bar"                                                  # Using 'AsFunc' syntax
        MyClass(MyClass.StandardInit, 100).Another() => "Another: 100"      # Using standard instantiation syntax

    """
    # ----------------------------------------------------------------------
    @wrapt.decorator
    def Wrapper(wrapped, instance, args, kwargs):
        assert inspect.isclass(wrapped)

        # ----------------------------------------------------------------------
        class Wrapped(wrapped):
        
            # ----------------------------------------------------------------------
            def __new__(cls, *these_args, **these_kwargs):
                if these_args and isinstance(these_args[0], _StandardInitObj):
                    return wrapped(*these_args[1:], **these_kwargs)

                cls = wrapped.__new__(cls)
                return getattr(cls, method_name)(*these_args, **these_kwargs)

            # ----------------------------------------------------------------------
            def __init__(self, *these_args, **these_kwargs):
                super(Wrapped, self).__init__(*these_args, **these_kwargs)

        # ----------------------------------------------------------------------
        
        wrapped.StandardInit = _StandardInitObj()

        return Wrapped(*args, **kwargs)

    # ----------------------------------------------------------------------
    
    return Wrapper

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def GetDecorator(function):
    if not hasattr(function, "_self_wrapper"):
        return

    return getattr(function._self_wrapper, "_im_self", function._self_wrapper)

# ---------------------------------------------------------------------------
def EnumDecorators(function):
    while function:
        decorator = GetDecorator(function)
        if decorator:
            yield decorator

        function = getattr(function, "__wrapped__", None)

# ----------------------------------------------------------------------
# |  
# |  Private Classes
# |  
# ----------------------------------------------------------------------
class _StandardInitObj(object):
    pass
