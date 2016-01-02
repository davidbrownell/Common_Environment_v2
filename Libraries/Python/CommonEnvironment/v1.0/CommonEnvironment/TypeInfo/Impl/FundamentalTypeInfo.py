# ---------------------------------------------------------------------------
# |  
# |  FundamentalTypeInfo.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/26/2015 05:12:48 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import re
import sys

from CommonEnvironment.Interface import *

from .. import TypeInfo

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
class FundamentalTypeInfo(TypeInfo):

    # ---------------------------------------------------------------------------
    # |  Public Properties
    @abstractproperty
    def PythonItemRegularExpressionStrings(self):
        raise Exception("Abstract Property")
    
    # ---------------------------------------------------------------------------
    # |  Public Methods
    @classmethod
    def Init(cls, string_module=None):
        if not string_module:
            from ..StringModules.PythonStringModule import PythonStringModule
            string_module = PythonStringModule

        cls._string_module = string_module

    # ---------------------------------------------------------------------------
    @staticmethod
    def CreateTypeInfo(type, **kwargs):
        from .. import FundamentalTypes
        
        if type in [ str, unicode, ]:
            return FundamentalTypes.StringTypeInfo(**kwargs)
        
        for potential_type_info in [ FundamentalTypes.IntTypeInfo,
                                     FundamentalTypes.FloatTypeInfo,
                                     FundamentalTypes.BoolTypeInfo,
                                     FundamentalTypes.GuidTypeInfo,
                                     FundamentalTypes.DateTimeTypeInfo,
                                     FundamentalTypes.DateTypeInfo,
                                     FundamentalTypes.TimeTypeInfo,
                                     FundamentalTypes.DurationTypeInfo,
                                   ]:
            if potential_type_info.ExpectedType == type:
                return potential_type_info(**kwargs)
                
        raise Exception("'{}' is not a recognized type".format(type))
        
    # ---------------------------------------------------------------------------
    def FromString(self, value):
        string_module = self._GetOrInit()
        
        if self.Arity.IsOptional and value == string_module.NoneString:
            value = None
        
        elif self.Arity.IsCollection:
            if not isinstance(value, (list, tuple)):
                value = string_module.SplitString(value)
                
            value = [ self.ItemFromString(item) for item in value ]
        else:
            value = self.ItemFromString(value)

        self.ValidateArity(value)
        return value

    # ---------------------------------------------------------------------------
    def ToString(self, value, delimiter=None):
        string_module = self._GetOrInit()

        self.ValidateArity(value)

        if self.Arity.IsOptional and value == None:
            return string_module.NoneString

        elif self.Arity.IsCollection:
            delimiter = delimiter or string_module.DefaultDelimiter

            if not isinstance(value, (list, tuple)):
                value = [ value, ]

            return ( '{}{}'.format( delimiter,
                                    '' if delimiter == '|' else ' ',
                                  )
                   ).join([ self.ItemToString(item) for item in value ])

        else:
            return self.ItemToString(value)
    
    # ---------------------------------------------------------------------------
    def ItemFromString( self, 
                        item, 
                        string_module=None, 
                      ):
        string_module = string_module or self._GetOrInit()
        
        if not hasattr(self, "_regexes"):
            self._regexes = {}

        if self.__class__ not in self._regexes:
            expressions = []
            
            for expression in string_module.GetItemRegularExpressionStrings(self):
                if isinstance(expression, tuple):
                    expression, regex_flags = expression
                else:
                    regex_flags = 0
            
                expressions.append(re.compile(expression, regex_flags))
                
            self._regexes[self.__class__] = expressions

        # ---------------------------------------------------------------------------
        class NoneType(object): pass

        def GetString():
            for index, regex in enumerate(self._regexes[self.__class__]):
                match = regex.match(item)
                if match:
                    return string_module.FromString(self, item, match, index)
                    
            return NoneType

        # ---------------------------------------------------------------------------
        
        result = GetString()
        if result == NoneType:
            error = "'{}' is not a valid '{}': {}" \
                        .format( item,
                                 self._GetExpectedTypeString(),
                                 self.ConstraintsDesc or ', '.join([ "'{}'".format(regex) for regex in string_module.GetItemRegularExpressionStrings(self) ]),
                               )
            raise Exception(error)

        item = result
        self.ValidateItem(item)
        
        return self.PostprocessItem(item)

    # ---------------------------------------------------------------------------
    def ItemToString( self, 
                      item, 
                      string_module=None, 
                    ):
        string_module = string_module or self._GetOrInit()

        self.ValidateItem(item)
        return string_module.ToString(self, item)

    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    def _GetOrInit(self):
        if not hasattr(type(self), "_string_module"):
            type(self).Init()

        return self._string_module
    