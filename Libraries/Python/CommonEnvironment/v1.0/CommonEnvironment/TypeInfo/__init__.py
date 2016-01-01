# ---------------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/26/2015 04:44:18 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import inflect
import os
import sys

from CommonEnvironment.Interface import *

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

Plural = inflect.engine()

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
class ValidationException(Exception):
    pass

# ---------------------------------------------------------------------------
class Arity(object):

    # ---------------------------------------------------------------------------
    @classmethod
    def FromString(cls, value):
        if value == '?':
            return cls(0, 1)

        if value == '*':
            return cls(0, None)

        if value == '+':
            return cls(1, None)

        if value.startswith('{') and value.endswith('}'):
            values = [ int(v.strip()) for v in value[1:-1].split(',') ]

            if len(values) == 1:
                return cls(values[0], values[0])
            elif len(values) == 2:
                return cls(values[0], values[1])

        raise Exception("'{}' is not a valid arity".format(Arity))

    # ---------------------------------------------------------------------------
    def __init__(self, min, max_or_none):
        if max_or_none != None and min > max_or_none:
            raise Exception("Invalid argument - max_or_none")

        self.Min                            = min
        self.Max                            = max_or_none

    # ---------------------------------------------------------------------------
    @property
    def IsSingle(self):
        return self.Min == 1 and self.Max == 1

    @property
    def IsOptional(self):
        return self.Min == 0 and self.Max == 1

    @property
    def IsCollection(self):
        return self.Max == None or self.Max > 1

    @property
    def IsFixedCollection(self):
        return self.Min == self.Max and self.Min != 1

    @property
    def IsZeroOrMore(self):
        return self.Min == 0 and self.Max == None

    @property
    def IsOneOrMore(self):
        return self.Min == 1 and self.Max == None

    @property
    def IsRange(self):
        return self.Max != None and self.Min != self.Max

    @property
    def PythonDefinitionString(self):
        return "Arity(min={}, max_or_none={})".format(self.Min, self.Max)

# ---------------------------------------------------------------------------
class TypeInfo(Interface):

    # ---------------------------------------------------------------------------
    # |  Public Properties
    @abstractproperty
    def Desc(self):
        raise Exception("Abstract property")

    @abstractproperty
    def ExpectedType(self):
        raise Exception("Abstract property")

    @abstractproperty
    def ConstraintsDesc(self):
        raise Exception("Abstract property")

    @abstractproperty
    def PythonDefinitionString(self):
        raise Exception("Abstract property")

    ExpectedTypeIsCallable                  = False
    
    # ---------------------------------------------------------------------------
    # |  Public Methods
    def __init__( self, 
                  arity=None,               # default is Arity(1, 1)
                  validation_func=None,     # def Func(value) -> string on error
                ):
        if isinstance(arity, (str, unicode)):
            arity = Arity.FromString(arity)

        self.Arity                          = arity or Arity(1, 1)
        self.ValidationFunc                 = validation_func

    # ---------------------------------------------------------------------------
    def Validate(self, value):
        result = self.ValidateNoThrow(value)
        if result != None:
            raise ValidationException(result)

    # ---------------------------------------------------------------------------
    def ValidateArity(self, value):
        result = self.ValidateArityNoThrow(value)
        if result != None:
            raise ValidationException(result)

    # ---------------------------------------------------------------------------
    def ValidateArityCount(self, value):
        result = self.ValidateArityCountNoThrow(value)
        if result != None:
            raise ValidationException(result)

    # ---------------------------------------------------------------------------
    def ValidateItem(self, value, **custom_args):
        result = self.ValidateItemNoThrow(value, **custom_args)
        if result != None:
            raise ValidationException(result)

    # ---------------------------------------------------------------------------
    def ValidateNoThrow(self, value):
        result = self.ValidateArityNoThrow(value)
        if result != None:
            return result

        if not self.Arity.IsCollection:
            value = [ value, ]

        for item in value:
            result = self.ValidateItemNoThrow(item)
            if result != None:
                return result

    # ---------------------------------------------------------------------------
    def ValidateArityNoThrow(self, value):
        if not self.Arity.IsCollection and isinstance(value, list):
            return "1 item was expected"

        return self.ValidateArityCountNoThrow(len(value) if isinstance(value, list) else 1 if value != None else 0)

    # ---------------------------------------------------------------------------
    def ValidateArityCountNoThrow(self, value):
        if not self.Arity.IsCollection:
            if (value == None and not self.Arity.IsOptional) or value > 1:
                return "1 item was expected"

            return

        if self.Arity.Min != None and value < self.Arity.Min:
            return "At least {} {} expected".format( Plural.no("item", self.Arity.Min),
                                                     Plural.plural_verb("was", self.Arity.Min),
                                                   )

        if self.Arity.Max != None and value > self.Arity.Max:
            return "At most {} {} expected".format( Plural.no("item", self.Arity.Max),
                                                    Plural.plural_verb("was", self.Arity.Max),
                                                  )

    # ---------------------------------------------------------------------------
    def ValidateItemNoThrow(self, item, **custom_args):
        if self.Arity.IsOptional and item == None:
            return

        is_expected_type = None

        if self.ExpectedTypeIsCallable:
            is_expected_type = self.ExpectedType(item)
        else:
            is_expected_type = isinstance(item, self.ExpectedType)

        assert is_expected_type != None

        if not is_expected_type:
            return "'{}' is not {}".format( item,
                                            Plural.a(self._GetExpectedTypeString()),
                                          )

        result = self._ValidateItemNoThrowImpl(item, **custom_args)
        if result != None:
            return result

        if self.ValidationFunc:
            result = self.ValidationFunc(item)
            if result != None:
                return result

    # ---------------------------------------------------------------------------
    def Postprocess(self, value):
        if self.Arity.IsOptional and value == None:
            return None

        if self.Arity.IsCollection:
            return [ self.PostprocessItem(item) for item in value ]

        return self.PostprocessItem(value)

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def PostprocessItem(item):
        raise Exception("Abstract method")
        
    # ---------------------------------------------------------------------------
    # |  Protected Properties
    @property
    def _PythonDefinitionStringContents(self):
        return "arity={}".format(self.Arity.PythonDefinitionString)
    
    # ---------------------------------------------------------------------------
    # |  Protected Methods
    def _GetExpectedTypeString(self):
        # ---------------------------------------------------------------------------
        def GetTypeName(t):
            return getattr(t, "__name__", str(t))

        # ---------------------------------------------------------------------------
        
        if self.ExpectedTypeIsCallable:
            return self.__class__.__name__

        if isinstance(self.ExpectedType, tuple):
            return ', '.join([ GetTypeName(t) for t in self.ExpectedType ])

        return GetTypeName(self.ExpectedType)

    # ---------------------------------------------------------------------------
    # |  Private Methods
    @staticmethod
    @abstractmethod
    def _ValidateItemNoThrowImpl(item, **custom_args):
        raise Exception("Abstract method")
