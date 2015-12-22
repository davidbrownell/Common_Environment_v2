# ---------------------------------------------------------------------------
# |  
# |  TypeInfo.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/18/2015 09:53:50 AM
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
import inflect
import inspect
import itertools
import os
import re
import sys
import uuid

from collections import OrderedDict

from QuickObject import QuickObject
from Interface import Interface, abstractproperty, abstractmethod

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

Plural = inflect.engine()

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# <Redefining build-in type> pylint: disable = W0622

# ---------------------------------------------------------------------------
class Arity(object):

    # ---------------------------------------------------------------------------
    @classmethod
    def FromString(cls, value):
        if value == '?':
            return cls(0, 1)
        elif value == '*':
            return cls(0, None)
        elif value == '+':
            return cls(1, None)
        elif value.startswith('{') and value.endswith('}'):
            values = [ int(v.strip()) for v in value[1:-1].split(',') ]

            if len(values) == 1:
                return cls(values[0], values[0])
            else:
                assert len(values) == 2, values
                return cls(values[0], values[1])
        else:
            raise Exception("'{}' is not a valid arity".format(arity))

    # ---------------------------------------------------------------------------
    def __init__(self, min, max):

        if max != None and min > max:
            raise Exception("Invalid argument - max")

        self.Min                            = min
        self.Max                            = max

    # ---------------------------------------------------------------------------
    @property
    def IsOptional(self):
        return self.Min == 0 and self.Max == 1

    # ---------------------------------------------------------------------------
    @property
    def IsCollection(self):
        return self.Max == None or self.Max > 1

    # ---------------------------------------------------------------------------
    @property
    def IsZeroOrMore(self):
        return self.Min == 0 and self.Max == None

    # ---------------------------------------------------------------------------
    @property
    def IsOneOrMore(self):
        return self.Min == 1 and self.Max == None

    # ---------------------------------------------------------------------------
    @property
    def IsSingle(self):
        return self.Min == 1 and self.Max == 1

    # ---------------------------------------------------------------------------
    @property
    def IsRange(self):
        return self.Max != None and self.Min != self.Max

# ---------------------------------------------------------------------------
class TypeInfo(Interface):

    # ---------------------------------------------------------------------------
    # |  Public Types
    class ValidationException(Exception):
        def __init__(self, *args, **kwargs):
            super(TypeInfo.ValidationException, self).__init__(*args, **kwargs)
    
    # ---------------------------------------------------------------------------
    # |  Public Properties
    @abstractproperty
    def ExpectedType(self):
        raise Exception("Abstract property")

    @abstractproperty
    def ConstraintsDesc(self):
        raise Exception("Abstract property")

    ExpectedTypeIsCallable                  = False

    # ---------------------------------------------------------------------------
    # |  Public Methods
    @staticmethod
    def CreateFundamental(type, **kwargs):
        if type in [ str, unicode, ]:
            return StringTypeInfo(**kwargs)

        for type_info in [ IntTypeInfo,
                           FloatTypeInfo,
                           BoolTypeInfo,
                           GuidTypeInfo,
                           DateTimeTypeInfo,
                           DateTypeInfo,
                           TimeTypeInfo,
                           DurationTypeInfo,
                         ]:
            if type_info.ExpectedType == type:
                return type_info(**kwargs)
        
        raise Exception("'{}' is not a recognized type".format(type))

    # ---------------------------------------------------------------------------
    def __init__( self, 
                  arity=None,
                  validation_func=None,
                ):
        if isinstance(arity, str):
            arity = Arity.FromString(arity)

        self.Arity                          = arity or Arity(1, 1)
        self.ValidationFunc                 = validation_func

    # ---------------------------------------------------------------------------
    def Validate(self, value):
        result = self.ValidateNoThrow(value)
        if result != None:
            raise self.ValidationException(result)

    # ---------------------------------------------------------------------------
    def ValidateItem(self, value):
        result = self.ValidateItemNoThrow(value)
        if result != None:
            raise self.ValidationException(result)

    # ---------------------------------------------------------------------------
    def ValidateArity(self, value):
        result = self.ValidateArityNoThrow(value)
        if result != None:
            raise self.ValidationException(result)

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
        if not self.Arity.IsCollection:
            if isinstance(value, list):
                return "Only 1 item was expected"

            return

        if not isinstance(value, (list, tuple)):
            return "A list or tuple was expected ({}, {})".format(self.Arity.Min, self.Arity.Max)

        if len(value) < self.Arity.Min:
            return "At least {} {} expected".format( Plural.no("item", self.Arity.Min), 
                                                     Plural.plural_verb("was", self.Arity.Min),
                                                   )

        if self.Arity.Max != None and len(value) > self.Arity.Max:
            return "At most {} {} expected".format( Plural.no("item", self.Arity.Max),
                                                    Plural.plural_verb("was", self.Arity.Max),
                                                  )
            
    # ---------------------------------------------------------------------------
    def ValidateItemNoThrow(self, item):
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

        result = self._ValidateItemNoThrowImpl(item)
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
            return [ self.PostprocessItem(v) for v in value ]

        return self.PostprocessItem(value)

    # ---------------------------------------------------------------------------
    @staticmethod
    def PostprocessItem(value):
        return value

    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
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
    @staticmethod
    @abstractmethod
    def _ValidateItemNoThrowImpl(value):
        raise Exception("Abstract method")

# ---------------------------------------------------------------------------
# |
# |  Fundamental Types
# |
# ---------------------------------------------------------------------------
class FundamentalTypeInfo(TypeInfo):

    # ---------------------------------------------------------------------------
    # |  Public Types
    _format_counter = itertools.count()

    Format_String                           = _format_counter.next()
    Format_Python                           = _format_counter.next()
    Format_JSON                             = _format_counter.next()
    
    del _format_counter

    SupportedDelimiters                     = [ '|', ';', ',', ]

    # ---------------------------------------------------------------------------
    # |  Public Properties
    @abstractproperty
    def Desc(self):
        raise Exception("Abstract property")
    
    # ---------------------------------------------------------------------------
    # |  Public Methods
    def FromString(self, value, format=Format_Python):
        if self.Arity.IsOptional and ( (format in [ self.Format_String, self.Format_Python, ] and value == "None") or
                                       (format == self.Format_JSON and value == "null")
                                     ):
            value = None
        
        elif self.Arity.IsCollection:
            if not isinstance(value, (list, tuple)):
                split = False

                for potential_delimiter in self.SupportedDelimiters:
                    if potential_delimiter in value:
                        split = True
                        value = [ v.strip() for v in value.split(potential_delimiter) if v.strip() ]
                        break

                if not split:
                    value = [ value, ]

            value = [ self.ItemFromString(v, format=format) for v in value ]

        else:
            value = self.ItemFromString(v, format=format)

        self.ValidateArity(value)
        return value

    # ---------------------------------------------------------------------------
    def ToString( self, 
                  value, 
                  format=Format_Python, 
                  delimiter=SupportedDelimiters[0],
                ):
        assert delimiter in self.SupportedDelimiters, delimiter

        if self.Arity.IsOptional and value == None:
            if format in [ self.Format_String, self.Format_Python, ]:
                return "None"
            elif format == self.Format_JSON:
                return "null"
            else:
                assert False, format

        elif self.Arity.IsCollection:
            if not isinstance(value, (list, tuple)):
                value = [ value, ]

            return ('{} '.format(delimiter)).join([ self.ItemToString(v) for v in value ])

        return self.ItemToString(value)

    # ---------------------------------------------------------------------------
    def ItemFromString(self, value, format=Format_Python):
        if not hasattr(self, "_regexes"):
            self._regexes = {}

        if format not in self._regexes:
            regex = self.ItemRegularExpression(format)
            self._regexes[format] = re.compile(regex)
                                                
        if not self._regexes[format].match(value):
            raise Exception("'{}' is not a valid '{}': {}".format( value,
                                                                   self._GetExpectedTypeString(),
                                                                   self.ConstraintsDesc or self.ItemRegularExpression(format),
                                                                 ))
                                                                                 
        value = self._ItemFromStringImpl(value, format=format)
        assert isinstance(value, self.ExpectedType), value

        self.ValidateItem(value)
        return value

    # ---------------------------------------------------------------------------
    def ItemToString(self, value, format=Format_Python):
        self.ValidateItem(value)
        return self._ItemToStringImpl(value, format=format)

    # ---------------------------------------------------------------------------
    @staticmethod
    def ItemRegularExpression(format):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _ItemFromStringImpl(value, format):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _ItemToStringImpl(value, format):
        raise Exception("Abstract method")

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
class StringTypeInfo(FundamentalTypeInfo):

    ExpectedType                            = (str, unicode)
    Desc                                    = "String"

    # ---------------------------------------------------------------------------
    def __init__( self, 
                  validation=None, 
                  min_length=1, 
                  max_length=None,
                  **type_info_args
                ):
        super(StringTypeInfo, self).__init__(**type_info_args)

        if min_length != None and max_length != None and max_length < min_length:
            raise Exception("Invalid argument - max_length")

        self.Validation                     = validation
        self.MinLength                      = min_length
        self.MaxLength                      = max_length
        
    # ---------------------------------------------------------------------------
    def __getstate__(self):
        # Help with pickling, as it isn't possible to pickle a function
        d = dict(self.__dict__)

        if "_Validate" in d:
            del d["_Validate"]
        
        return d

    # ---------------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        items = []

        if self.Validation:
            items.append("match the regular expression '{}'".format(self.Validation))
           
        if self.MinLength:
            items.append("have more than {}".format(Plural.no("character", self.MinLength)))

        if self.MaxLength:
            items.append("have less than {}".format(Plural.no("character", self.MaxLength)))

        if not items:
            return ''

        return "Value must {}".format(', '.join(items))

    # ---------------------------------------------------------------------------
    def ItemRegularExpression(self, format):
        if self.Validation:
            return self.Validation

        elif self.MinLength == 1 and self.MaxLength == None:
            return ".+"

        elif self.MinLength in [ 0, None, ] and self.MaxLength == None:
            return ".*"

        elif self.MinLength != None and self.MaxLength == None:
            return ".{%d}.*" % self.MinLength

        elif self.MinLength != None and self.MaxLength != None:
            if self.MinLength == self.MaxLength:
                return ".{%d}" % self.MaxLength

            return ".{%d,%d}" % (self.MinLength, self.MaxLength)

        assert False, "Unexpected"
            
    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, value):
        if not hasattr(self, "_Validate"):
            if self.Validation:
                regex = re.compile(self.Validation)
                self._Validate = regex.match
            else:
                self._Validate = lambda value: True

        if not self._Validate(value):
            return "'{}' did not match the validation expression '{}'".format(value, self.Validation)

        value_length = len(value)

        if self.MinLength != None and value_length < self.MinLength:
            return "{} found in the value '{}' (At least {} expected)".format( Plural.no("character", value_length),
                                                                               value,
                                                                               Plural.no("character", self.MinLength),
                                                                             )

        if self.MaxLength != None and value_length > self.MaxLength:
            return "{} found in the value '{}' (At most {} expected)".format( Plural.no("character", value_length),
                                                                              value,
                                                                              Plural.no("character", self.MaxLength),
                                                                            )

    # ---------------------------------------------------------------------------
    @staticmethod
    def _ItemFromStringImpl(value, format):
        return value

    # ---------------------------------------------------------------------------
    @staticmethod
    def _ItemToStringImpl(value, format):
        return value

# ---------------------------------------------------------------------------
class EnumTypeInfo(FundamentalTypeInfo):

    ExpectedType                            = (str, unicode)
    Desc                                    = "Enum"

    # ---------------------------------------------------------------------------
    def __init__( self,
                  values,
                  friendly_values=None,
                  **type_info_args
                ):
        super(EnumTypeInfo, self).__init__(**type_info_args)

        if not values:
            raise Exception("A list of values must be provided")

        if friendly_values != None and len(friendly_values) != len(values):
            raise Exception("The number of friendly values must match the number of values (values: {}, friendly: {})".format(len(values), len(friendly_values)))

        self.Values                         = values
        self.FriendlyValues                 = friendly_values

    # ---------------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        if len(self.Values) == 1:
            return "Value must be '{}'".format(self.Values[0])

        return "Value must be one of {}".format(', '.join([ "'{}'".format(value) for value in self.Values ]))

    # ---------------------------------------------------------------------------
    def ItemRegularExpression(self, format):
        return "({})".format('|'.join(self.Values))

    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, value):
        if value not in self.Values:
            return "'{}' is not a valid value ({} expected)".format( value,
                                                                     ', '.join([ "'{}'".format(v) for v in self.Values ]),
                                                                   )

    # ---------------------------------------------------------------------------
    @staticmethod
    def _ItemFromStringImpl(value, format):
        return value

    # ---------------------------------------------------------------------------
    @staticmethod
    def _ItemToStringImpl(value, format):
        return value

# ---------------------------------------------------------------------------
class IntTypeInfo(FundamentalTypeInfo):

    ExpectedType                            = int
    Desc                                    = "Integer"

    # ---------------------------------------------------------------------------
    def __init__( self,
                  min=None,
                  max=None,
                  bytes=None,
                  **type_info_args
                ):
        super(IntTypeInfo, self).__init__(**type_info_args)

        if min != None and max != None and max < min:
            raise Exception("Invalid argument - max")

        if bytes not in [ None, 1, 2, 4, 8, ]:
            raise Exception("Invalid argument - bytes")

        self.Min                            = min
        self.Max                            = max
        self.Bytes                          = bytes

    # ---------------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        items = []

        if self.Min != None:
            items.append("be >= {}".format(self.Min))

        if self.Max != None:
            items.append("be <= {}".format(self.Max))

        if not items:
            return ''

        return "Value must {}".format(', '.join(items))

    # ---------------------------------------------------------------------------
    def ItemRegularExpression(self, format):
        return self.ItemRegularExpressionImpl(self.Min, self.Max)
        
    # ---------------------------------------------------------------------------
    @staticmethod
    def ItemRegularExpressionImpl(min, max):
        patterns = []

        if min < 0 or min == None:
            patterns.append('-')

            if max > 0 or max == None:
                patterns.append('?')

        patterns.append('[0-9]')

        if min == None or max == None:
            patterns.append('+')
        else:
            value = 10
            count = 1

            while True:
                if min >= -value and max <= value:
                    break

                value *= 10
                count += 1

            patterns.append("{%d}" % count)

        return ''.join(patterns)

    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, value):
        if self.Min != None and value < self.Min:
            return "{} is not >= {}".format(value, self.Min)

        if self.Max != None and value > self.Max:
            return "{} is not <= {}".format(value, self.Max)

    # ---------------------------------------------------------------------------
    @classmethod
    def _ItemFromStringImpl(cls, value, format):
        return int(value)

    # ---------------------------------------------------------------------------
    @staticmethod
    def _ItemToStringImpl(value, format):
        return str(value)

# ---------------------------------------------------------------------------
class FloatTypeInfo(FundamentalTypeInfo):

    ExpectedType                            = (int, float)
    Desc                                    = "Float"

    # ---------------------------------------------------------------------------
    def __init__( self,
                  min=None,
                  max=None,
                  **type_info_args
                ):
        super(FloatTypeInfo, self).__init__(**type_info_args)

        if min != None and max != None and max < min:
            raise Exception("Invalid argument - max")

        self.Min                            = min
        self.Max                            = max

    # ---------------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        items = []

        if self.Min != None:
            items.append("be >= {}".format(self.Min))

        if self.Max != None:
            items.append("be <= {}".format(self.Max))

        if not items:
            return ''

        return "Value must {}".format(', '.join(items))

    # ---------------------------------------------------------------------------
    def ItemRegularExpression(self, format):
        return r"{}\.[0-9]+".format(IntTypeInfo.ItemRegularExpressionImpl(self.Min, self.Max))

    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, value):
        if self.Min != None and value < self.Min:
            return "{} is not >= {}".format(value, self.Min)

        if self.Max != None and value > self.Max:
            return "{} is not <= {}".format(value, self.Max)

    # ---------------------------------------------------------------------------
    @classmethod
    def _ItemFromStringImpl(cls, value, format):
        return float(value)

    # ---------------------------------------------------------------------------
    @staticmethod
    def _ItemToStringImpl(value, format):
        return str(value)

# ---------------------------------------------------------------------------
class FilenameTypeInfo(FundamentalTypeInfo):

    ExpectedType                            = (str, unicode)
    Desc                                    = "Filename"

    # ---------------------------------------------------------------------------
    # |  Public Types
    _type_counter = itertools.count()

    Type_File                               = _type_counter.next()
    Type_Directory                          = _type_counter.next()
    Type_Either                             = _type_counter.next()

    del _type_counter

    # ---------------------------------------------------------------------------
    def __init__( self,
                  type=Type_File,
                  ensure_exists=True,
                  **type_info_args
                ):
        super(FilenameTypeInfo, self).__init__(**type_info_args)

        self.Type                           = type
        self.EnsureExists                   = ensure_exists

        if not ensure_exists:
            self._ValidateFunc = lambda value: True
        elif type == self.Type_File:
            self._ValidateFunc = os.path.isfile
        elif type == self.Type_Directory:
            self._ValidateFunc = os.path.isdir
        elif type == self.Type_Either:
            self._ValidateFunc = os.path.exists
        else:
            assert False

    # ---------------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        if not self.EnsureExists:
            return ''

        if self.Type == self.Type_File:
            type = "file name"
        elif self.Type == self.Type_Directory:
            type = "directory name"
        elif self.Type == self.Type_Either:
            type = "file or directory name"
        else:
            assert False

        return "Value must be a valid {}".format(type)

    # ---------------------------------------------------------------------------
    @staticmethod
    def ItemRegularExpression(format):
        return ".+"

    # ---------------------------------------------------------------------------
    @staticmethod
    def PostprocessItem(value):
        return os.path.realpath(os.path.normpath(value))

    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, value):
        if not self._ValidateFunc(value):
            if self.Type == self.Type_File:
                type = "file"
            elif self.Type == self.Type_Directory:
                type = "directory"
            elif self.Type == self.Type_Either:
                type = "file or directory"
            else:
                assert False

            return "'{}' is not a valid {}".format(value, type)

    # ---------------------------------------------------------------------------
    def _ItemFromStringImpl(self, value, format):
        return os.path.realpath(os.path.join(os.getcwd(), value.replace('/', os.path.sep)))

    # ---------------------------------------------------------------------------
    def _ItemToStringImpl(self, value, format):
        return value.replace(os.path.sep, '/')

# ---------------------------------------------------------------------------
class DirectoryTypeInfo(FilenameTypeInfo):

    Desc                                    = "Directory Name"

    # ---------------------------------------------------------------------------
    def __init__( self,
                  ensure_exists=True,
                  **type_info_args
                ):
        super(DirectoryTypeInfo, self).__init__( type=self.Type_Directory,
                                                 ensure_exists=ensure_exists,
                                                 **type_info_args
                                               )
    
# ---------------------------------------------------------------------------
class BoolTypeInfo(FundamentalTypeInfo):

    ExpectedType                            = bool
    Desc                                    = "Boolean"

    # ---------------------------------------------------------------------------
    def __init__( self, 
                  **type_info_args
                ):
        super(BoolTypeInfo, self).__init__(**type_info_args)

    # ---------------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        return ''

    # ---------------------------------------------------------------------------
    @classmethod
    def ItemRegularExpression(cls, format):
        if format == cls.Format_String:
            return "(true|t|yes|y|1|false|f|no|n|0)"

        elif format == cls.Format_Python:
            return "(True|False)"

        elif format == cls.Format_JSON:
            return "(true|false)"

        assert False, format

    # ---------------------------------------------------------------------------
    @staticmethod
    def _ValidateItemNoThrowImpl(value):
        return

    # ---------------------------------------------------------------------------
    @classmethod
    def _ItemFromStringImpl(cls, value, format):
        return value.lower() in [ "true", "t", "yes", "y", "1", ]

    # ---------------------------------------------------------------------------
    @classmethod
    def _ItemToStringImpl(cls, value, format):
        if format in [ cls.Format_String, cls.Format_JSON, ]:
            return "true" if value else "false"

        elif format == cls.Format_Python:
            return str(value)

        assert False, (value, format)

# ---------------------------------------------------------------------------
class GuidTypeInfo(FundamentalTypeInfo):

    ExpectedType                            = uuid.UUID
    Desc                                    = "Guid"

    # ---------------------------------------------------------------------------
    @staticmethod
    def Create():
        return uuid.uuid4()

    # ---------------------------------------------------------------------------
    def __init__( self,
                  **type_info_args
                ):
        super(GuidTypeInfo, self).__init__(**type_info_args)

    # ---------------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        return ''

    # ---------------------------------------------------------------------------
    @staticmethod
    def ItemRegularExpression(format):
        d = { "char" : "[0-9A-Fa-f]", }

        return "({})".format('|'.join([ r"\{%(char)s{32}\}" % d,
                                        r"%(char)s{32}" % d,
                                        r"\{%(char)s{8}-%(char)s{4}-%(char)s{4}-%(char)s{4}-%(char)s{12}\}" % d,
                                        r"%(char)s{8}-%(char)s{4}-%(char)s{4}-%(char)s{4}-%(char)s{12}" % d,
                                      ]))

    # ---------------------------------------------------------------------------
    @staticmethod
    def _ValidateItemNoThrowImpl(value):
        return 

    # ---------------------------------------------------------------------------
    @classmethod
    def _ItemFromStringImpl(cls, value, format):
        return uuid.UUID(value)

    # ---------------------------------------------------------------------------
    @staticmethod
    def _ItemToStringImpl(value, format):
        return str(value).upper()

# ---------------------------------------------------------------------------
class DateTimeTypeInfo(FundamentalTypeInfo):

    ExpectedType                            = datetime.datetime
    Desc                                    = "Datetime"

    # ---------------------------------------------------------------------------
    @staticmethod
    def Create():
        return datetime.datetime.now()

    # ---------------------------------------------------------------------------
    def __init__( self, 
                  **type_info_args
                ):
        super(DateTimeTypeInfo, self).__init__(**type_info_args)

    # ---------------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        return ''

    # ---------------------------------------------------------------------------
    @classmethod
    def ItemRegularExpression(cls, format):
        if format == cls.Format_String:
            return ".+ .+ [0-9]{2} ([0-1][0-9]|2[0-4]):[0-5][0-9]:[0-5][0-9] [0-9]{4}"

        elif format in [ cls.Format_JSON, cls.Format_Python, ]:
            return "{}.{}".format( DateTypeInfo.ItemRegularExpression(format),
                                   TimeTypeInfo.ItemRegularExpression(format),
                                 )

        assert False

    # ---------------------------------------------------------------------------
    @staticmethod
    def _ValidateItemNoThrowImpl(value):
        return

    # ---------------------------------------------------------------------------
    @classmethod
    def _ItemFromStringImpl(cls, value, format):
        if format == cls.Format_String:
            return datetime.datetime.strptime("%a %b %d %H:%M:%S %Y")

        elif format in [ cls.Format_JSON, cls.Format_Python, ]:
            fmt = "%Y-%m-%d{separator}%H:%M{seconds}{fraction_seconds}{time_zone}".format \
                      ( separator='T' if 'T' in value else ' ', 
                        seconds=":%S" if value.count(':') > 1 else '',
                        fraction_seconds=".%f" if '.' in value else '',
                        time_zone="%z" if '+' in value else '',
                      )

            return datetime.datetime.strptime(value, fmt)

        assert False

    # ---------------------------------------------------------------------------
    @classmethod
    def _ItemToStringImpl(cls, value, format):
        if format == cls.Format_String:
            return value.strftime("%a %b %d %H:%M:%S %Y")

        if format == cls.Format_JSON:
            sep = 'T'
        elif format == cls.Format_Python:
            sep = ' '
        else:
            assert False

        return value.isoformat(sep=sep)

# ---------------------------------------------------------------------------
class DateTypeInfo(FundamentalTypeInfo):

    ExpectedType                            = datetime.date
    Desc                                    = "Date"

    # ---------------------------------------------------------------------------
    @staticmethod
    def Create():
        return datetime.date.today()

    # ---------------------------------------------------------------------------
    def __init__( self,
                  **type_info_args
                ):
        super(DateTypeInfo, self).__init__(**type_info_args)

    # ---------------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        return ''

    # ---------------------------------------------------------------------------
    @staticmethod
    def ItemRegularExpression(format):
        return "[0-9]{4}-(0?[0-9]|1[0-2])-([0-2][0-9]|3[0-1])"

    # ---------------------------------------------------------------------------
    @staticmethod
    def _ValidateItemNoThrowImpl(value):
        return

    # ---------------------------------------------------------------------------
    @classmethod
    def _ItemFromStringImpl(cls, value, format):
        parts = value.split('-')

        return datetime.date( int(parts[0]),
                              int(parts[1]),
                              int(parts[2]),
                            )

    # ---------------------------------------------------------------------------
    @staticmethod
    def _ItemToStringImpl(value, format):
        return value.isoformat()
        
# ---------------------------------------------------------------------------
class TimeTypeInfo(FundamentalTypeInfo):
    
    ExpectedType                            = datetime.time
    Desc                                    = "Time"

    # ---------------------------------------------------------------------------
    @staticmethod
    def Create():
        return datetime.datetime.now().time()

    # ---------------------------------------------------------------------------
    def __init__( self,  
                  **type_info_args
                ):
        super(TimeTypeInfo, self).__init__(**type_info_args)

    # ---------------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        return ''

    # ---------------------------------------------------------------------------
    @staticmethod
    def ItemRegularExpression(format):
        return r"([0-1][0-9]|[2][0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?(\+[0-9]+:[0-9]+)?"

    # ---------------------------------------------------------------------------
    @staticmethod
    def _ValidateItemNoThrowImpl(value):
        return

    # ---------------------------------------------------------------------------
    @classmethod
    def _ItemFromStringImpl(cls, value, format):
        return datetime.datetime.strptime(value, "%H:%M:%S{microseconds}{time_zone}".format(
            microseconds=".%f" if '.' in value else '',
            time_zone="%z" if '+' in value else '',
        )).time()

    # ---------------------------------------------------------------------------
    @staticmethod
    def _ItemToStringImpl(value, format):
        return value.isoformat()

# ---------------------------------------------------------------------------
class DurationTypeInfo(FundamentalTypeInfo):

    ExpectedType                            = datetime.timedelta
    Desc                                    = "Duration"

    # ---------------------------------------------------------------------------
    def __init__( self,
                  **type_info_args
                ):
        super(DurationTypeInfo, self).__init__(**type_info_args)

    # ---------------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        return ''

    # ---------------------------------------------------------------------------
    @staticmethod
    def ItemRegularExpression(format):
        return r"[0-9]+:[0-5][0-9](:[0-5][0-9](\.[0-9]+)?)?"

    # ---------------------------------------------------------------------------
    @staticmethod
    def _ValidateItemNoThrowImpl(value):
        return

    # ---------------------------------------------------------------------------
    @classmethod
    def _ItemFromStringImpl(cls, value, format):
        parts = value.split(':')

        if len(parts) > 2:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(float(parts[2]))
        else:
            hours = 0
            minutes = int(parts[0])
            seconds = int(float(parts[1]))
        
        return datetime.timedelta( hours=hours,
                                   minutes=minutes,
                                   seconds=seconds,
                                 )
            
    # ---------------------------------------------------------------------------
    @staticmethod
    def _ItemToStringImpl(value, format):
        seconds = value.total_seconds()

        hours = int(seconds / ( 60 * 60))
        seconds %= (60 * 60)

        minutes = int(seconds / 60)
        seconds %= 60

        return "{hours}:{minutes:02}:{seconds:02}".format( hours=hours,
                                                           minutes=minutes,
                                                           seconds=seconds,
                                                         )

# ---------------------------------------------------------------------------
# |
# |  Object-like Types
# |
# ---------------------------------------------------------------------------
class _ObjectLikeTypeInfo(TypeInfo):

    # ---------------------------------------------------------------------------
    def __init__( self,
                  items=None,                           # { "attribute name" : <Type Info>, }
                  require_exact_match=False,
                  arity=None,
                  validation_func=None,
                  **kwargs
                ):
        super(_ObjectLikeTypeInfo, self).__init__( arity=arity,
                                                   validation_func=validation_func,
                                                 )
        self.RequireExactMatch              = require_exact_match
        self.Items                          = items or OrderedDict()

        for k, v in kwargs.iteritems():
            assert k not in self.Items, k
            self.Items[k] = v

    # ---------------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        if not self.Items:
            return ''

        return "Value must {only}contain the {attribute} {values}".format( only="only " if self.RequireExactMatch else '',
                                                                           attribute=Plural.plural("attribute", len(self.Items)),
                                                                           values=', '.join([ "'{}'".format(name) for name in self.Items.iterkeys() ]),
                                                                         )

    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, value):
        if self.RequireExactMatch:
            attributes = set(a for a in self.__dict__.keys() if not a.startswith("__"))

            # ---------------------------------------------------------------------------
            def ProcessAttribute(attr):
                attributes.remove(attr)

            # ---------------------------------------------------------------------------
            def OnComplete():
                if attributes:
                    return "The item contained extraneous data: {}".format(', '.join([ "'{}'".format(attr) for attr in attributes ]))

            # ---------------------------------------------------------------------------
            
        else:
            ProcessAttribute = lambda attr: None        # <Invalid variable name> pylint: disable = C0103
            OnComplete = lambda: None                   # <Invalid variable name> pylint: disable = C0103

        for attribute_name, type_info in self.Items.iteritems():
            ProcessAttribute(attribute_name)
            if not self._HasAttribute(value, attribute_name):
                return "The attribute '{}' was not found".format(attribute_name)

            this_value = self._GetAttributeValue(type_info, value, attribute_name)

            result = type_info.ValidateNoThrow(this_value)
            if result != None:
                return "The attribute '{}' is not valid - {}".format(attribute_name, result)

        result = OnComplete()
        if result:
            return result
            
    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _HasAttribute(value, attr):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _GetAttributeValue(type_info, value, attr):
        raise Exception("Abstract method")

# ---------------------------------------------------------------------------
class ClassTypeInfo(_ObjectLikeTypeInfo):

    # ---------------------------------------------------------------------------
    # |
    # |  Public Types
    # |
    # ---------------------------------------------------------------------------
    class _MethodTypeInfo(TypeInfo):
        ExpectedTypeIsCallable              = True

        def __init__(self):
            super(ClassTypeInfo._MethodTypeInfo, self).__init__(arity=None)

        @property
        def ConstraintsDesc(self):
            return ''

        @staticmethod
        def _ValidateItemNoThrowImpl(value):
            return

    # ---------------------------------------------------------------------------
    class MethodTypeInfo(_MethodTypeInfo):
        ExpectedType                        = staticmethod(lambda item: inspect.ismethod(item) and item.__self__ == None)
        
    # ---------------------------------------------------------------------------
    class ClassMethodTypeInfo(_MethodTypeInfo):
        ExpectedType                        = staticmethod(lambda item: inspect.ismethod(item) and item.__self__ != None)

    # ---------------------------------------------------------------------------
    class StaticMethodTypeInfo(_MethodTypeInfo):
        ExpectedType                        = staticmethod(lambda item: inspect.isfunction(item))

    # ---------------------------------------------------------------------------
    # |
    # |  Public Data
    # |
    # ---------------------------------------------------------------------------
    ExpectedType                            = staticmethod(lambda item: True) # Everything is a class in Python
    ExpectedTypeIsCallable                  = True

    # ---------------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ---------------------------------------------------------------------------
    def __init__( self,
                  items=None,               # { "attribute name" : <Type Info>, }
                  require_exact_match=False,
                  arity=None,
                  validation_func=None,
                  **kwargs
                ):
        super(ClassTypeInfo, self).__init__( items=items,
                                             require_exact_match=require_exact_match,
                                             arity=arity,
                                             validation_func=validation_func,
                                             **kwargs
                                           )

    # ---------------------------------------------------------------------------
    # |
    # |  Private Methods
    # |
    # ---------------------------------------------------------------------------
    @staticmethod
    def _HasAttribute(value, attr):
        return hasattr(value, attr)

    # ---------------------------------------------------------------------------
    @classmethod
    def _GetAttributeValue(cls, type_info, value, attr):
        if isinstance(type_info, cls._MethodTypeInfo):
            value = type(value)

        return getattr(value, attr)

# ---------------------------------------------------------------------------
class DictTypeInfo(_ObjectLikeTypeInfo):

    ExpectedType                            = dict

    # ---------------------------------------------------------------------------
    def __init__( self,
                  items=None,
                  require_exact_match=False,
                  arity=None,
                  validation_func=None,
                  **kwargs
                ):
        super(DictTypeInfo, self).__init__( items=items,
                                            require_exact_match=require_exact_match,
                                            arity=arity,
                                            validation_func=validation_func,
                                            **kwargs
                                          )

    # ---------------------------------------------------------------------------
    @staticmethod
    def _HasAttribute(value, attr):
        return attr in value

    # ---------------------------------------------------------------------------
    @staticmethod
    def _GetAttributeValue(type_info, value, attr):
        return value[attr]

# ---------------------------------------------------------------------------
# |
# |  CollectionTypeInfo
# |
# ---------------------------------------------------------------------------
class ListTypeInfo(TypeInfo):

    ExpectedType                            = list

    # ---------------------------------------------------------------------------
    def __init__( self,
                  element_type_info,
                  **type_info_args
                ):
        super(ListTypeInfo, self).__init__(**type_info_args)
        self.ElementTypeInfo                = element_type_info

    # ---------------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        return ''

    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, value):
        return self.ElementTypeInfo.ValidateNoThrow(value)

# ---------------------------------------------------------------------------
class AnyOfTypeInfo(TypeInfo):

    ExpectedTypeIsCallable                  = True

    # ---------------------------------------------------------------------------
    def __init__( self,
                  element_type_info_list,
                  **type_info_args
                ):
        super(AnyOfTypeInfo, self).__init__(**type_info_args)
        self.ElementTypeInfos               = element_type_info_list

    # ---------------------------------------------------------------------------
    @property
    def Desc(self):
        return '/'.join([ eti.Desc for eti in self.ElementTypeInfos ])

    # ---------------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        items = []

        for eti in self.ElementTypeInfos:
            constraint_desc = eti.ConstraintsDesc
            if constraint_desc:
                items.append(constraint_desc)

        return '/'.join(items)

    # ---------------------------------------------------------------------------
    def ExpectedType(self, value):
        for eti in self.ElementTypeInfos:
            if callable(eti.ExpectedType):
                if eti.ExpectedType(value):
                    return True
            else:
                if isinstance(value, eti.ExpectedType):
                    return True

        return False

    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, value):
        for eti in self.ElementTypeInfos:
            result = eti.ValidateItemNoThrow(value)
            if result == None:
                return

        return "'{}' could not be validated".format(value)

# ---------------------------------------------------------------------------
class CustomTypeInfo(TypeInfo):

    ExpectedTypeIsCallable                  = True

    # ---------------------------------------------------------------------------
    def __init__( self,
                  expected_type_func,       # def Func(item) -> bool
                  validate_item_func,       # def Func(item) -> string on error
                  postprocess_func=None,    # def Func(item) -> item
                  constraints_desc="Custom constraint",
                  **type_info_args
                ):
        super(CustomTypeInfo, self).__init__(**type_info_args)

        self._expected_type_func            = expected_type_func
        self._validate_item_func            = validate_item_func
        self._postprocess_func              = postprocess_func
        self._constraints_desc              = constraints_desc

    # ---------------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        return self._constraints_desc

    # ---------------------------------------------------------------------------
    def ExpectedType(self, item):
        return self._expected_type_func(item)

    # ---------------------------------------------------------------------------
    def Postprocess(self, item):
        if self._postprocess_func == None:
            return super(CustomTypeInfo, self).Postprocess(value)

        return self._postprocess_func(item)

    # ---------------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        return self._vallidate_item_func(item)
