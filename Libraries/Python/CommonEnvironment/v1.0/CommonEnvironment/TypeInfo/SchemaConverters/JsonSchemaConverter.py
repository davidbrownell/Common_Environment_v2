# ----------------------------------------------------------------------
# |  
# |  JsonSchemaConverter.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-09-05 15:08:25
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-17.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import sys

import six

from CommonEnvironment.Interface import staticderived
from CommonEnvironment import Package
from CommonEnvironment import RegularExpression

with Package.NameInfo(__package__) as ni:
    __package__ = ni.created
    
    from . import SchemaConverter

    from ..FundamentalTypes import ( DateTypeInfo,
                                     DurationTypeInfo,
                                     GuidTypeInfo,
                                     TimeTypeInfo,
                                     Visitor as VisitorBase,
                                     FUNDAMENTAL_TYPES
                                   )
    
    from ..AnyOfTypeInfo import AnyOfTypeInfo
    from ..ClassTypeInfo import ClassTypeInfo
    from ..DictTypeInfo import DictTypeInfo
    
    from ..FundamentalTypes.Serialization.StringSerialization import StringSerialization
    
    __package__ = ni.original

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@staticderived
class JsonSchemaConverter(SchemaConverter):

    # ----------------------------------------------------------------------
    @classmethod
    def Convert(cls, type_info):
        # ----------------------------------------------------------------------
        @staticderived
        class FundamentalVisitor(VisitorBase):
            # ----------------------------------------------------------------------
            @staticmethod
            def OnBool(type_info, *args, **kwargs):
                return { "type" : "boolean", }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDateTime(type_info, *args, **kwargs):
                return { "type" : "string",
                         "format" : "date-time",
                       }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDate(type_info, *args, **kwargs):
                return { "type" : "string",
                         "pattern" : "^{}$".format(RegularExpression.PythonToJavaScript(StringSerialization.GetRegularExpressionString(DateTypeInfo()))),
                       }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDirectory(type_info, *args, **kwargs):
                return { "type" : "string",
                         "minLength" : 1,
                       }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnDuration(type_info, *args, **kwargs):
                return { "type" : "string",
                         "pattern" : "^{}$".format(RegularExpression.PythonToJavaScript(StringSerialization.GetRegularExpressionString(DurationTypeInfo()))),
                       }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnEnum(type_info, *args, **kwargs):
                return { "enum" : type_info.Values, }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnFilename(type_info, *args, **kwargs):
                return { "type" : "string",
                         "minLength" : 1,
                       }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnFloat(type_info, *args, **kwargs):
                result = { "type" : "number", }

                for attribute, json_schema_key in [ ( "Min", "minimum" ),
                                                    ( "Max", "maximum" ),
                                                  ]:
                    value = getattr(type_info, attribute)
                    if value != None:
                        result[json_schema_key] = value

                return result
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnGuid(type_info, *args, **kwargs):
                return { "type" : "string",
                         "pattern" : "^{}$".format(RegularExpression.PythonToJavaScript(StringSerialization.GetRegularExpressionString(GuidTypeInfo()))),
                       }
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnInt(type_info, *args, **kwargs):
                result = { "type" : "integer", }

                for attribute, json_schema_key in [ ( "Min", "minimum" ),
                                                    ( "Max", "maximum" ),
                                                  ]:
                    value = getattr(type_info, attribute)
                    if value != None:
                        result[json_schema_key] = value

                return result
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnString(type_info, *args, **kwargs):
                result = { "type" : "string", }

                if type_info.ValidationExpression != None:
                    validation = RegularExpression.PythonToJavaScript(type_info.ValidationExpression)

                    if validation[0] != '^': validation = "^{}".format(validation)
                    if validation[-1] != '$': validation = "{}$".format(validation)

                    result["pattern"] = validation

                else:
                    if type_info.MinLength not in [ 0, None, ]:
                        result["minLength"] = type_info.MinLength

                    if type_info.MaxLength:
                        result["maxLength"] = type_info.MaxLength

                return result
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnTime(type_info, *args, **kwargs):
                return { "type" : "string",
                         "pattern" : "^{}$".format(RegularExpression.PythonToJavaScript(StringSerialization.GetRegularExpressionString(TimeTypeInfo()))),
                       }

        # ----------------------------------------------------------------------
        
        if isinstance(type_info, FUNDAMENTAL_TYPES):
            schema = FundamentalVisitor.Accept(type_info)

        elif isinstance(type_info, AnyOfTypeInfo):
            # Only suport AnyOfTypeInfo in the scenarios where the potential elements
            # are Dict- and Class-TypeInfos.
            class_type_info = None
            dict_type_info = None
            other_type_infos = []

            for ti in type_info.ElementTypeInfos:
                if isinstance(ti, ClassTypeInfo):
                    assert class_type_info == None, class_type_info
                    class_type_info = ti
                elif isinstance(ti, DictTypeInfo):
                    assert dict_type_info == None, dict_type_info
                    dict_type_info = ti
                else:
                    other_type_infos.append(ti)

            if ( not class_type_info or
                 not dict_type_info or
                 other_type_infos
               ):
                raise Exception("AnyOfTypeInfo is not in a supported state")

            schema = cls.Classify(class_type_info.Items)
                 
        elif isinstance(type_info, ClassTypeInfo):
            schema = cls.Classify(type_info.Items)

        else:
            raise Exception("'{}' is not a supported type".format(type_info))

        return cls.Collectionize(type_info.Arity, schema)

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

    # ----------------------------------------------------------------------
    @classmethod
    def Classify( cls, 
                  items,                    # { name : type_info, }
                ):
        required = [ k for k, v in six.iteritems(items) if v.Arity.Min != 0 ]
        required.sort()

        return { "type" : "object",
                 "properties" : { k : cls.Convert(v) for k, v in six.iteritems(items) },
                 "required" : required,
               }
