# ----------------------------------------------------------------------
# |  
# |  JsonSchemaConverter.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-04-24 21:23:05
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import sys

from CommonEnvironment.Interface import staticderived
from CommonEnvironment import RegularExpression
from CommonEnvironment.TypeInfo import FundamentalConverters

from ..FundamentalTypes import *

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@staticderived
class JsonSchemaConverter(FundamentalConverters.Converter):
    # ----------------------------------------------------------------------
    @staticmethod
    def OnBool(type_info):
        return { "type" : "boolean", }

    # ----------------------------------------------------------------------
    @staticmethod
    def OnDateTime(type_info):
        return { "type" : "string",
                 "format" : "date-time", 
               }
    
    # ----------------------------------------------------------------------
    @staticmethod
    def OnDate(type_info):
        return { "type" : "string",
                 "pattern" : "^{}$".format(RegularExpression.PythonToJavaScript(DateTypeInfo().PythonItemRegularExpressionStrings[0])),
               }
    
    # ----------------------------------------------------------------------
    @staticmethod
    def OnDuration(type_info):
        return { "type" : "string",
                 "pattern" : "^{}$".format(RegularExpression.PythonToJavaScript(DurationTypeInfo().PythonItemRegularExpressionStrings[0])),
               }
    
    # ----------------------------------------------------------------------
    @staticmethod
    def OnEnum(type_info):
        return { "enum" : type_info.Values, }
    
    # ----------------------------------------------------------------------
    @staticmethod
    def OnFilename(type_info):
        return { "type" : "string",
                 "minLength" : 1,
               }
    
    # ----------------------------------------------------------------------
    @staticmethod
    def OnFloat(type_info):
        schema = { "type" : "number", }

        for attribute, json_schema_key in [ ( "Min", "minimum" ),
                                            ( "Max", "maximum" ),
                                          ]:
            value = getattr(type_info, attribute)
            if value != None:
                schema[json_schema_key] = value

        return schema
    
    # ----------------------------------------------------------------------
    @staticmethod
    def OnGuid(type_info):
        return { "type" : "string",
                 "pattern" : "^{}$".format(RegularExpression.PythonToJavaScript(GuidTypeInfo().PythonItemRegularExpressionStrings[0])),
               }
    
    # ----------------------------------------------------------------------
    @staticmethod
    def OnInt(type_info):
        schema = { "type" : "integer", }

        for attribute, json_schema_key in [ ( "Min", "minimum" ),
                                            ( "Max", "maximum" ),
                                          ]:
            value = getattr(type_info, attribute)
            if value != None:
                schema[json_schema_key] = value

        return schema
    
    # ----------------------------------------------------------------------
    @staticmethod
    def OnString(type_info):
        schema = { "type" : "string", }

        if type_info.ValidationExpression != None:
            validation = RegularExpression.PythonToJavaScript(type_info.ValidationExpression)

            if validation[0] == '^': validation = validation[1:]
            if validation[-1] == '$': validation = validation[:-1]

            schema["pattern"] = "^{}$".format(validation)

        if type_info.MinLength not in [ 0, None, ]:
            schema["minLength"] = type_info.MinLength

        if type_info.MaxLength:
            schema["maxLength"] = type_info.MaxLength

        return schema

    # ----------------------------------------------------------------------
    @staticmethod
    def OnTime(type_info):
        return { "type" : "string",
                 "pattern" : "^{}$".format(RegularExpression.PythonToJavaScript(TimeTypeInfo().PythonItemRegularExpressionStrings[0])),
               }

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def Collectionize(arity, schema):
        if not arity.IsCollection:
            return schema
    
        schema = { "type" : "array",
                   "items" : schema,
                 }
    
        if arity.Min != 0:
            schema["minItems"] = arity.Min
    
        if arity.Max != None:
            schema["maxItems"] = arity.Max
    
        return schema
    
    