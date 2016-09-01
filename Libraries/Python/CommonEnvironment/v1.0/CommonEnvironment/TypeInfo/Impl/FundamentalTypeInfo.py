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

from contextlib import contextmanager

from CommonEnvironment.Interface import *

from .. import TypeInfo, ValidationException
            
# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class FundamentalTypeInfo(TypeInfo):

    # ---------------------------------------------------------------------------
    # |  Public Properties
    @property
    def PythonItemRegularExpressionStrings(self):
        from ..StringModules.StandardStringModule import StandardStringModule
        return self.ItemRegularExpressionStrings(StandardStringModule)

    @property
    def PythonItemRegularExpressionString(self):
        from ..StringModules.StandardStringModule import StandardStringModule
        return self.ItemRegularExpressionString(StandardStringModule)

    # ----------------------------------------------------------------------
    # |  
    # |  Public Methods
    # |  
    # ----------------------------------------------------------------------
    @staticmethod
    def CreateTypeInfo(type, **kwargs):
        from .. import FundamentalTypes
        
        if type in [ str, unicode, ]:
            return FundamentalTypes.StringTypeInfo(**kwargs)
        
        for potential_type_info in [ FundamentalTypes.BoolTypeInfo,
                                     FundamentalTypes.DateTimeTypeInfo,
                                     FundamentalTypes.DateTypeInfo,
                                     FundamentalTypes.DurationTypeInfo,
                                     # FundamentalTypes.EnumTypeInfo,
                                     # FundamentalTypes.FilenameTypeInfo,
                                     # FundamentalTypes.DirectoryTypeInfo,
                                     FundamentalTypes.FloatTypeInfo,
                                     FundamentalTypes.GuidTypeInfo,
                                     FundamentalTypes.IntTypeInfo,
                                     FundamentalTypes.TimeTypeInfo,
                                   ]:
            if potential_type_info.ExpectedType == type:
                return potential_type_info(**kwargs)
                
        raise Exception("'{}' is not a recognized type".format(type))
        
    # ----------------------------------------------------------------------
    def ItemRegularExpressionInfo(self, string_module=None):
        string_module = string_module or self._GetStringModule()
        return string_module.ItemRegularExpressionInfo(self)

    # ---------------------------------------------------------------------------
    def FromString(self, value):
        string_module = self._GetStringModule()
        
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
        string_module = self._GetStringModule()

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
        string_module = string_module or self._GetStringModule()
        
        if not hasattr(self, "_regexes"):
            self._regexes = {}

        key = ( self.__class__, string_module )

        if key not in self._regexes:
            self._regexes[key] = [ re.compile(expression, regex_flags) for expression, regex_flags in self._GetRegexInfo(string_module) ]
            
        # ---------------------------------------------------------------------------
        class NoneType(object): pass

        def ExtractValue():
            # Don't attempt to convert from a string if the item is already the expected type. Note
            # that we have to ignore string types, as they may have a regex that needs application.
            if not self.ExpectedTypeIsCallable and isinstance(item, self.ExpectedType) and self.ExpectedType != str:
                return item

            try:
                for index, regex in enumerate(self._regexes[key]):
                    match = regex.match(item)
                    if match:
                        return string_module.FromString(self, item, match, index)
            except:
                pass

            return NoneType

        # ---------------------------------------------------------------------------
        
        result = ExtractValue()
        if result == NoneType:
            error = "'{}' is not a valid '{}': {}" \
                        .format( item,
                                 self._GetExpectedTypeString(),
                                 self.ConstraintsDesc or ', '.join([ "'{}'".format(regex) for regex in self.PythonItemRegularExpressionStrings ]),
                               )
            raise ValidationException(error)

        item = result
        self.ValidateItem(item)
        
        return self.PostprocessItem(item)

    # ---------------------------------------------------------------------------
    def ItemToString( self, 
                      item, 
                      string_module=None, 
                    ):
        string_module = string_module or self._GetStringModule()

        self.ValidateItem(item)
        return string_module.ToString(self, item)

    # ----------------------------------------------------------------------
    def ItemRegularExpressionStrings( self, 
                                      string_module=None,
                                    ):
        return [ expression for expression, _ in self._GetRegexInfo(string_module or self._GetStringModule()) ]

    # ----------------------------------------------------------------------
    def ItemRegularExpressionString( self,
                                     string_module=None,
                                   ):
        results = self._GetRegexInfo(string_module or self._GetStringModule())

        if len(results) == 1:
            return results[0][0]

        return '|'.join([ "({})".format(expression) for expression, _ in results ])

    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    def _GetStringModule(self):
        if hasattr(FundamentalTypeInfo, "_global_string_module"):
            return FundamentalTypeInfo._global_string_module

        from ..StringModules.StandardStringModule import StandardStringModule
        return StandardStringModule

    # ----------------------------------------------------------------------
    def _GetRegexInfo(self, string_module):
        results = string_module.RegexInfo(self)
        if not isinstance(results, list):
            results = [ results, ]

        info = []

        for result in results:
            if isinstance(result, tuple):
                expression, regex_flags = result
            else:
                expression = result
                regex_flags = re.DOTALL | re.MULTILINE

            info.append((expression, regex_flags))

        return info

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
@contextmanager
def PushGlobalStringModule(string_module):
    from CommonEnvironment.CallOnExit import CallOnExit

    prev_string_module = getattr(FundamentalTypeInfo, "_global_string_module", None)

    # ----------------------------------------------------------------------
    def RestoreStringModuleOverride():
        if prev_string_module == None:
            del FundamentalTypeInfo._global_string_module
        else:
            FundamentalTypeInfo._global_string_module = prev_string_module

    # ----------------------------------------------------------------------
    
    with CallOnExit(RestoreStringModuleOverride):
        FundamentalTypeInfo._global_string_module = string_module
        yield

    