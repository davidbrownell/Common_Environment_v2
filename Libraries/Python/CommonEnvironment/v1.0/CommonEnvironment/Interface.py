# ---------------------------------------------------------------------------
# |  
# |  Interface.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/09/2015 03:50:37 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-18.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import abc
import inspect
import os
import sys
import textwrap

from collections import OrderedDict
from functools import wraps

import six

from .QuickObject import QuickObject

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# |  Introduce some abc items into the current namespace for convenience
abstractmethod                              = abc.abstractmethod            # <Invalid name> pylint: disable = C0103
abstractproperty                            = abc.abstractproperty          # <Invalid name> pylint: disable = C0103

# ---------------------------------------------------------------------------
class Interface(object):
    """\
    Augments python abstract base class functionality with support for static methods,
    parameter checking, derived type validation, and interface query/discovery functionality.

    Usage:

        class MyInterface(Interface):
            @abstractmethod
            def Method(self, a, b):
                raise Exception("Abstract method")

            # @staticabstractmethod
            @staticmethod
            @abstractmethod
            def StaticMethod(a, b, c, d=None):
                raise Exception("Abstract static method")

            @abstractproperty
            def Property(self):
                raise Exception("Abstract property")


        class Obj(MyInterface):
            def Method(self, a, b):     pass            # Good
            def Method(self, a):        pass            # Bad: 'b' is missing
            def Method(self, a, notB):  pass            # Bad: 'notB' != 'b'

            @staticmethod def StaticMethod(a, b, c, d):     pass            # Good
            @staticmethod def StaticMethod(a, b, c, d=int): pass            # Bad: 'int' != 'None'

            @property def Property(self):   pass        # Good

            Obj.AbstractItems is a list of the names of all abstract items defined by this class
    """

    if __debug__:
        __metaclass__ = abc.ABCMeta
        
        ExtensionMethods = []
        _verified_types = set()
        
        # ---------------------------------------------------------------------------
        def __new__(cls, *args, **kwargs):
            # If here, ABC has validated that abstract methods and properties are
            # present and named correctly. We now need to validate static methods and
            # parameters.
        
            instance = super(Interface, cls).__new__(cls)

            if cls in Interface._verified_types:
                return instance
        
            ( FunctionType, ClassFunctionType, MethodType, PropertyType ) = six.moves.range(4)   # <Invalid name> pylint: disable = C0103
        
            # ---------------------------------------------------------------------------
            def TypeToString(type_):
                if type_ == FunctionType:
                    return "function"
        
                if type_ == ClassFunctionType:
                    return "classmethod"
        
                if type_ == MethodType:
                    return "method"
        
                if type_ == PropertyType:
                    return "property"
        
                assert False, type_
        
            # ---------------------------------------------------------------------------
            def GenerateInfo(item):
                if IsStaticMethod(item):
                    type_ = FunctionType
                elif IsClassMethod(item):
                    type_ = ClassFunctionType
                elif IsStandardMethod(item):
                    type_ = MethodType
                else:
                    return QuickObject( type_=PropertyType,
                                      )

                return QuickObject( type_=type_,
                                    func_code=item.__code__,
                                    func_defaults=item.__defaults__,
                                  )

            # ---------------------------------------------------------------------------
            def LocationString(info):
                if hasattr(info, "func_code"):
                    filename = info.func_code.co_filename
                    line = info.func_code.co_firstlineno
                else:
                    filename = "Unknown"
                    line = 0
        
                return "<{filename} [{line}]>".format( filename=filename, 
                                                       line=line,
                                                     )
        
            # ---------------------------------------------------------------------------
            
            try:
                # Get all the abstract items and make that information available via the class type
                abstracts = OrderedDict()
                extension_methods = {}
        
                for base in reversed(inspect.getmro(cls)):
                    these_abstracts = []
        
                    for member_name, member_info in inspect.getmembers(base):
                        if getattr(member_info, "__extension_method", False):
                            info = GenerateInfo(member_info)
        
                            extension_methods[LocationString(info)] = "{}.{}".format(type(instance).__name__, member_name)
                            
                        if getattr(member_info, "__isabstractmethod__", False):
                            these_abstracts.append(member_name)
        
                            if member_name not in abstracts:
                                abstracts[member_name] = GenerateInfo(member_info)
        
                    if these_abstracts and base not in Interface._verified_types:
                        Interface._verified_types.add(base)
                        base.AbstractItems = these_abstracts
        
                extension_method_keys = list(six.iterkeys(extension_methods))
                extension_method_keys.sort()
        
                for emk in extension_method_keys:
                    instance.ExtensionMethods.append("{0:<50} {1}".format(extension_methods[emk], emk))
        
                # Verify that all abstracts exist
                errors = []
        
                # ----------------------------------------------------------------------
                def HasItem(abstract_name, abstract_info):
                    if abstract_info.type_ == MethodType:
                        value = getattr(cls, abstract_name, None)
                        if value == None:
                            return False

                        if six.get_function_code(value) == abstract_info.func_code:
                            return False

                    return hasattr(cls, abstract_name)

                # ----------------------------------------------------------------------
                
                for abstract_name, abstract_info in six.iteritems(abstracts):
                    if not HasItem(abstract_name, abstract_info):
                        errors.append("The abstract {type_} '{name}' is missing {location}".format( type_=TypeToString(abstract_info.type_),
                                                                                                    name=abstract_name,
                                                                                                    location=LocationString(abstract_info),
                                                                                                  ))
        
                if errors:
                    raise Exception(errors)
        
                # Ensure that all abstracts are of the correct type
                errors = []
        
                for abstract_name, abstract_info in six.iteritems(abstracts):
                    concrete_value = getattr(cls, abstract_name)
                    concrete_info = GenerateInfo(concrete_value)
        
                    # Check if the types are the same; this is interesting in that it should be possible
                    # to implement an abstract static/method with a standard method if the implementation
                    # requires state.
                    if not ( abstract_info.type_ == concrete_info.type_ or
                             (abstract_info.type_ in [ FunctionType, ClassFunctionType, MethodType, ] and concrete_info.type_ in [ FunctionType, ClassFunctionType, MethodType, ])
                           ):
                        errors.append("'{name}' was expected to be a {abstract_type} but {concrete_type} was found ({abstract_location}, {concrete_location})".format( name=abstract_name,
                                                                                                                                                                       abstract_type=TypeToString(abstract_info.type_),
                                                                                                                                                                       abstract_location=LocationString(abstract_info),
                                                                                                                                                                       concrete_type=TypeToString(concrete_info.type_),
                                                                                                                                                                       concrete_location=LocationString(concrete_info),
                                                                                                                                                                     ))
                if errors:
                    raise Exception(errors)
        
                # abc handles properties and methods, but not static methods. Use the information associated with
                # the function to ensure that the value defined is the same as the abstract value.
                errors = []
        
                for abstract_name, abstract_info in [ (k, v) for k, v in six.iteritems(abstracts) if v.type_ in [ FunctionType, ClassFunctionType, ] ]:
                    concrete_value = getattr(cls, abstract_name)
                    concrete_value_func_code = six.get_function_code(concrete_value)

                    if ( concrete_value_func_code.co_filename == abstract_info.func_code.co_filename and 
                         concrete_value_func_code.co_firstlineno == abstract_info.func_code.co_firstlineno
                       ):
                        errors.append("The abstract {type_} '{name}' is missing {location}".format( type_=TypeToString(abstract_info.type_),
                                                                                                    name=abstract_name,
                                                                                                    location=LocationString(abstract_info),
                                                                                                  ))
                if errors:
                    raise Exception(errors)
        
                # Ensure that the items are defined with the correct arguments
        
                # ---------------------------------------------------------------------------
                class NoDefault(object):
                    """\
                    Placeholder to indicate that a default value was not provided; we can't
                    use None, as None may be the default value provided.
                    """
                    pass
        
                # ---------------------------------------------------------------------------
                def GetParams(info):
                    params = OrderedDict()
        
                    var_names = info.func_code.co_varnames[:info.func_code.co_argcount]
                    default_value_offset = len(var_names) - len(info.func_defaults or [])
        
                    for index, name in enumerate(var_names):
                        # Skip the 'self' or 'cls' value as they aren't interesting when
                        # it comes to argument comparison.
                        if index == 0 and info.type_ in [ MethodType, ClassFunctionType, ]:
                            continue
        
                        if index >= default_value_offset:
                            params[name] = info.func_defaults[index - default_value_offset]
                        else:
                            params[name] = NoDefault
        
                    return params
        
                # ---------------------------------------------------------------------------
                def DisplayParams(params):
                    values = []
                    has_default_value = False
        
                    for name, default_value in six.iteritems(params):
                        if default_value != NoDefault:
                            has_default_value = True
                            
                            values.append("{name:<40}  {default:<20}  {type_}".format( name=name,
                                                                                       default=str(default_value),
                                                                                       type_=type(default_value),
                                                                                     ))
                        else:
                            values.append(name)
        
                    if has_default_value:
                        return '\n'.join([ "            {}".format(value) for value in values ])
        
                    return "            {}".format(", ".join(values))
        
                # ---------------------------------------------------------------------------
                
                kwargs_flag = 4
                var_args_flag = 8
        
                errors = []
        
                for abstract_name, abstract_info in [ (k, v) for k, v in six.iteritems(abstracts) if v.type_ != PropertyType ]:
                    concrete_value = getattr(cls, abstract_name)
                    concrete_info = GenerateInfo(concrete_value)
                    concrete_params = GetParams(concrete_info)
        
                    abstract_params = GetParams(abstract_info)
        
                    # We can skip the test if the concrete function is a forwarding function (def Func(*args, **kwargs))
                    if ( not concrete_params and
                         concrete_info.func_code.co_flags & kwargs_flag and
                         concrete_info.func_code.co_flags & var_args_flag
                       ):
                        continue
        
                    # If the abstract sepcifies a variable number of args, only check those that come
                    # before them.
                    require_exact_match = True
        
                    for flag in [ kwargs_flag, var_args_flag, ]:
                        if abstract_info.func_code.co_flags & flag:
                            require_exact_match = False
        
                    # This is not-standard from an object-oriented perspective, but allow custom parameters
                    # with default values in concrete definitions.
                    if len(concrete_params) > len(abstract_params):
                        params_to_remove = min(len(concrete_params) - len(abstract_params), len(concrete_info.func_defaults or []))
                        
                        keys = list(six.iterkeys(concrete_params))

                        for _ in range(params_to_remove):
                            del concrete_params[keys.pop()]
        
                    if ( (require_exact_match and len(concrete_params) != len(abstract_params)) or 
                         not all(k in concrete_params and concrete_params[k] == v for k, v in six.iteritems(abstract_params))
                       ):
                        errors.append((abstract_name, DisplayParams(abstract_params), LocationString(abstract_info), DisplayParams(concrete_params), LocationString(concrete_info)))
        
                if errors:
                    raise Exception([ textwrap.dedent(
                        """\
                        {name}
                                Abstract {abstract_location}
                        {abstract_params}
        
                                Concrete {concrete_location}
                        {concrete_params}
        
                        """).format( name=abstract_name,
                                     abstract_location=abstract_location,
                                     abstract_params=abstract_params,
                                     concrete_location=concrete_location,
                                     concrete_params=concrete_params,
                                   ) for abstract_name, abstract_params, abstract_location, concrete_params, concrete_location in errors ])
        
                Interface._verified_types.add(cls)
        
                return instance 
        
            except Exception as ex:
                raise Exception(textwrap.dedent(
                    """\
                    Can't instantiate class '{class_}' due to:
                        - {errors}
                    """).format( class_=cls.__name__,
                                 errors="\n    - ".join(ex.args[0] if isinstance(ex.args[0], ( list, tuple )) else [ ex.args[0], ]),
                               ))

# ---------------------------------------------------------------------------
# |
# |  Decorators
# |
# ---------------------------------------------------------------------------
def extensionmethod(func):
    """\
    Decorator that indicates the method is a method that can be extended by
    a derived class to override functionality (in other words, it is an "extension
    point"). Note that the class associated with the method must be based
    on interface for this construct to work properly.

    To view all extensions of an Interface-based type:

        print '\n'.join(MyClass.ExtensionMethods)

    """

    if isinstance(func, (staticmethod, classmethod)):
        actual_func = func.__func__
    elif callable(func):
        actual_func = func
    else:
        assert False, type(func)

    setattr(actual_func, "__extension_method", True)
    
    return func

# ----------------------------------------------------------------------
def staticderived(cls):
    """\
    Decorator designed to be used by concrete classes that only implement static
    abstract methods.

    When a concrete class implements an interface, the object's __new__ method is
    used to verify that all methods and properties have been implemented as expected.

    Unfortunately, __new__ is only invoked when an instance of an object is created.
    When it comes to static methods, it is possible to invoke the method without creating
    an instance of the object, meaning __new__ will never fire and the abstract verification
    code will never be called.

    This decorator, when used in conjunction with the concrete class based on the abstract
    interface, will ensure that __new__ is properly invoked and that the static methods
    are evaluated.
    """

    cls()
    return cls

# ---------------------------------------------------------------------------

# Note that this doesn't work when attempting to determine if the parameters are 
# correct, as the parameter count is 0 since the function being inspected is the
# function defined below rather than the funcobj originally provided.

# def staticabstractmethod(funcobj):
#     """\
#     Decorator that combines the functionality of the staticmethod and abstractmethod
#     decorators.
# 
#     What was:
# 
#         @staticmethod
#         @abstractmethod
#         def MyMethod():
#             ...
# 
#     becomes:
# 
#         @staticabstractmethod
#         def MyMethod():
#             ...
#     """
# 
#     @staticmethod
#     @abstractmethod
#     def Func(*args, **kwargs):
#         return funcobj(*args, **kwargs)
# 
#     return Func

# ---------------------------------------------------------------------------
def final(class_obj):
    """\
    Finalizes a class object so that new data cannot be added to it.

    Before:
        class MyObject(object):
            pass
        
        obj = MyObject()
        obj.foo = "Bar"     # OK to add new attributes

    After:
        @final
        class MyObject(object):
            def __init__(self, a):
                self.a = a

        obj = MyObject()
        obj.foo = "Bar"     # ERROR, raises TypeError
        obj.a = 10          # OK
    """
    
    # ---------------------------------------------------------------------------
    # <Too few public methods> pylint: disable = R0903
    @wraps(class_obj)
    class Final(class_obj):
        
        # ---------------------------------------------------------------------------
        # <Use super on an old style class> pylint: disable = E1002
        def __init__(self, *args, **kwargs):
            self._final_initializing = True
            super(Final, self).__init__(*args, **kwargs)

            del self._final_initializing

        # ---------------------------------------------------------------------------
        # <Use super on an old style class> pylint: disable = E1002
        def __setattr__(self, key, value):
            if ( not hasattr(self, key) and \
                 not hasattr(self, "_final_initializing") and \
                 not (key == "_final_initializing" and value)
               ):
                raise TypeError("This class has been declared as 'final' and new attributes may not be added")

            return super(Final, self).__setattr__(key, value)

    # ---------------------------------------------------------------------------
    
    return Final
    
# ---------------------------------------------------------------------------
def immutable(class_obj):
    """\
    Makes a class object immutable so that it cannot be modified.
    
    Before:
        class MyObject(object):
            def __init__(self, value):
                self.value = value
                
        obj = MyObject(10)
        obj.foo = "Bar"         # OK to add new attributes
        obj.value -= 1          # OK to modify attributes
        
    After:
        @immutable
        class MyObject(object):
            def __init__(self, value):
                self.value = value 
                
        obj = MyObject(10)
        obj.foo = "Bar"         # ERROR, raises TypeError
        obj.value -= 1          # ERROR, raises TypeError
    """
    
    # ---------------------------------------------------------------------------
    # <Too few public methods> pylint: disable = R0903
    @wraps(class_obj)
    class Immutable(class_obj):
    
        # ---------------------------------------------------------------------------
        # <Use super on an old style class> pylint: disable = E1002
        def __init__(self, *args, **kwargs):
            self._immutable_initializing = True
            super(Immutable, self).__init__(*args, **kwargs)
            
            del self._immutable_initializing
            
        # ---------------------------------------------------------------------------
        # <Use super on an old style class> pylint: disable = E1002
        def __setattr__(self, key, value):
            if ( (hasattr(self, "_immutable_initializing") and self._immutable_initializing) or
                 (key == "_immutable_initializing" and value)
               ):
                return super(Immutable, self).__setattr__(key, value)
            
            raise TypeError("This class has been declared as 'immutable' and cannot be modified")
            
        # ---------------------------------------------------------------------------
        def Clone(self):
            return class_obj(**self.__dict__)

    # ---------------------------------------------------------------------------
    
    return Immutable

# ---------------------------------------------------------------------------
def clsinit(class_obj):
    class_obj.__clsinit__()
    return class_obj

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def CreateCulledCallable(func):
    """\
    Returns a method that will be called with a subset of the potential parameters based on its implementation.

    Example:
        def MyMethod(a): ....

        culled_method = CreateCulledCallable(MyMethod)

        culled_method(2, a=1, c=3) -> MyMethod(a=2)
    """

    if sys.version_info[0] == 2:
        arg_spec = inspect.getargspec(func)
    else:
        arg_spec = inspect.getfullargspec(func)
    
    arg_names = { arg for arg in arg_spec.args }
    positional_arg_names = arg_spec.args[:len(arg_spec.args) - len(arg_spec.defaults or [])]
    
    # Handle perfect forwarding scenarios
    if not arg_names and not positional_arg_names:
        if arg_spec.varkw is not None:
            # ----------------------------------------------------------------------
            def Invoke(kwargs):
                return func(**kwargs)

            # ----------------------------------------------------------------------

        elif arg_spec.varargs is not None:
            # ----------------------------------------------------------------------
            def Invoke(kwargs):
                return func(*tuple(six.itervalues(kwargs)))

            # ----------------------------------------------------------------------

        else:
            # ----------------------------------------------------------------------
            def Invoke(kwargs):
                return func()

            # ----------------------------------------------------------------------

    else:
        # ----------------------------------------------------------------------
        def Invoke(kwargs):
            potential_positional_args = []

            invoke_kwargs = {}

            for k in list(six.iterkeys(kwargs)):
                if k in arg_names:
                    invoke_kwargs[k] = kwargs[k]
                else:
                    potential_positional_args.append(kwargs[k])

            for name in positional_arg_names:
                if name not in kwargs and potential_positional_args:
                    invoke_kwargs[name] = potential_positional_args.pop(0)

            return func(**invoke_kwargs)

        # ----------------------------------------------------------------------
    
    return Invoke

# ----------------------------------------------------------------------
if sys.version_info[0] == 2:
    # ----------------------------------------------------------------------
    def IsStaticMethod(item):
        return inspect.isfunction(item)

    # ----------------------------------------------------------------------
    def IsClassMethod(item):
        if not inspect.ismethod(item):
            return False

        # This is a bit strange, but class functions will have a __self__ value != None
        return item.__self__ != None and type(item.__self__) == type

    # ----------------------------------------------------------------------
    def IsStandardMethod(item):
        if not inspect.ismethod(item):
            return False

        return item.__self__ == None or type(item.__self__) != type

else:
    # ----------------------------------------------------------------------
    def IsStaticMethod(item):
        if type(item).__name__ != "function":
            return False
    
        # There should be a more definitive way to differentiate
        # between static/class/standard methods. Things are more
        # predictable if we have an item associated with an instance
        # of an object, but not as clear when given a method associated
        # with the class instance.
        #
        # This is a hack!
        var_names = item.__code__.co_varnames
        return not var_names or not _CheckVariableNameVariants(var_names[0], "self", "cls")
    
    # ----------------------------------------------------------------------
    def IsClassMethod(item):
        if type(item).__name__ not in [ "function", "method", ]:
            return False
    
        # See notes in IsStaticMethod
        var_names = item.__code__.co_varnames
        return var_names and _CheckVariableNameVariants(var_names[0], "cls")
    
    # ----------------------------------------------------------------------
    def IsStandardMethod(item):
        if type(item).__name__ not in [ "function", "method", ]:
            return False
    
        # See notes in IsStaticMethod
        var_names = item.__code__.co_varnames
        return var_names and _CheckVariableNameVariants(var_names[0], "self")

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _CheckVariableNameVariants(var, *variants):
    for variant in variants:
        if var.startswith(variant) or var.endswith(variant):
            return True

    return False