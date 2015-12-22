# ---------------------------------------------------------------------------
# |  
# |  XsdPlugin.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/11/2015 05:00:24 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import itertools
import os
import sys
import textwrap

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment.Interface import staticderived
from CommonEnvironment import RegularExpression
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment.TypeInfo import *

# Note that these imports have already been imported by SimpleSchemaCodeGenerator and
# should always be available without explicit path information.
from SimpleSchema.Elements import *
from Plugin import Plugin as PluginBase

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

@staticderived
class Plugin(PluginBase):

    # ---------------------------------------------------------------------------
    # |
    # |  Public Properties
    # |
    # ---------------------------------------------------------------------------
    Name                                    = "Xsd"
    Flags                                   = ( PluginBase.ParseFlags.SupportAttributes |
                                                PluginBase.ParseFlags.SupportIncludeStatements |
                                                PluginBase.ParseFlags.SupportNamedDeclarations |
                                                PluginBase.ParseFlags.SupportNamedObjects |
                                                PluginBase.ParseFlags.SupportRootDeclarations |
                                                PluginBase.ParseFlags.SupportRootObjects |
                                                PluginBase.ParseFlags.SupportChildDeclarations |
                                                PluginBase.ParseFlags.SupportChildObjects |
                                                PluginBase.ParseFlags.SupportAliases |
                                                PluginBase.ParseFlags.SupportAugmentations |
                                                PluginBase.ParseFlags.SupportSimpleObjects |
                                                PluginBase.ParseFlags.ResolveReferences
                                              )

    # ---------------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ---------------------------------------------------------------------------
    @staticmethod
    def GetExtensions():
       return []

    # ---------------------------------------------------------------------------
    @staticmethod
    def GetRequiredMetadata(item_type, name):
        return []

    # ---------------------------------------------------------------------------
    @staticmethod
    def GetOptionalMetadata(item_type, name):
        return []

    # ---------------------------------------------------------------------------
    @staticmethod
    def DoesOptionalReferenceRepresentNewType(is_fundamental_reference):
        return True

    # ---------------------------------------------------------------------------
    @staticmethod
    def GenerateOutputFilenames(context):
        return [ os.path.join(context.output_dir, "{}.xsd".format(context.output_name)), ]

    # ---------------------------------------------------------------------------
    @staticmethod
    def GenerateCustomSettingsAndDefaults():
        return {}

    # ---------------------------------------------------------------------------
    @staticmethod
    def GetAdditionalGeneratorItems(context):
        return []

    # ---------------------------------------------------------------------------
    @staticmethod
    def PostprocessContextItem(context):
        return context

    # ---------------------------------------------------------------------------
    @classmethod
    def Generate( cls, 
                  simple_schema_code_generator,
                  invoke_reason,
                  input_filenames,
                  output_filenames,
                  name,
                  elements,
                  include_indexes,
                  status_stream,
                  output_stream,
                  **custom_settings_and_defaults
                ):
        assert len(output_filenames) == 1

        output_filename = output_filenames[0]
        del output_filenames

        status_stream.write("Creating '{}'...".format(output_filename))
        with status_stream.DoneManager() as status_dm:
            with open(output_filename, 'w') as f:
                f.write(textwrap.dedent(
                    """\
                    <?xml version="1.0"?>
                    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">

                    """))

                # ---------------------------------------------------------------------------
                def ArityToString(arity):
                    if arity.Min == 1 and arity.Max == 1:
                        return ''

                    return ' minOccurs="{}" maxOccurs="{}"'.format( arity.Min,
                                                                    arity.Max if arity.Max != None else "unbounded",
                                                                  )

                # ---------------------------------------------------------------------------
                def TypeInfoToString_String(type_info):
                    restrictions = OrderedDict()

                    if type_info.MinLength != 1:
                        restrictions["minLength"] = type_info.MinLength

                    if type_info.MaxLength != None:
                        restrictions["maxLength"] = type_info.MaxLength

                    if type_info.Validation != None:
                        restrictions["pattern"] = RegularExpression.PythonToJavaScript(type_info.Validation)
                        
                    return textwrap.dedent(
                        """\
                        <xs:restriction base="xs:string">{}</xs:restriction>
                        """).format("\n{}\n".format('\n'.join([ '    <xs:{k} value="{v}" />'.format(k=k, v=v) for k, v in restrictions.iteritems() ])) if restrictions else '')

                # ---------------------------------------------------------------------------
                def TypeInfoToString_Enum(type_info):
                    return textwrap.dedent(
                        """\
                        <xs:restriction base="xs:string">
                        {}
                        </xs:restriction>
                        """).format('\n'.join([ '    <xs:enumeration value="{}" />'.format(value) for value in type_info.Values ]))

                # ---------------------------------------------------------------------------
                def TypeInfoToString_Int(type_info):
                    type = None

                    if type_info.Bytes == None:
                        type = "integer"
                    elif type_info.Bytes == 1:
                        type = "byte"
                    elif type_info.Bytes == 2:
                        type = "short"
                    elif type_info.Bytes == 4:
                        type = "int"
                    elif type_info.Bytes == 8:
                        type = "long"
                    else:
                        assert False, type_info.Bytes

                    restrictions = OrderedDict()

                    if type_info.Min != None:
                        if type_info.Min == 0:
                            type = "nonNegative{}{}".format(type[0].upper(), type[1:])
                        else:
                            restrictions["minInclusive"] = type_info.Min

                    if type_info.Max != None:
                        if type_info.Max == 0:
                            type = "negative{}{}".format(type[0].upper(), type[1:])
                        else:
                            restrictions["maxInclusive"] = type_info.Max

                    return textwrap.dedent(
                        """\
                        <xs:restriction base="xs:{}">{}</xs:restriction>
                        """).format( type,
                                     "\n{}\n".format('\n'.join([ '    <xs:{k} value="{v}" />'.format(k=k, v=v) for k, v in restrictions.iteritems() ])) if restrictions else '',
                                   )

                # ---------------------------------------------------------------------------
                def TypeInfoToString_Float(type_info):
                    restrictions = OrderedDict()

                    if type_info.Min != None:
                        restrictions["minInclusive"] = type_info.Min

                    if type_info.Max != None:
                        restrictions["maxInclusive"] = type_info.Max

                    return textwrap.dedent(
                        """\
                        <xs:restriction base="xs:decimal">{}</xs:restriction>
                        """).format("\n{}\n".format('\n'.join([ '    <xs:{k} value="{v}" />'.format(k=k, v=v) for k, v in restrictions.iteritems() ])) if restrictions else '')

                # ---------------------------------------------------------------------------
                def TypeInfoToString_Filename(type_info):
                    return textwrap.dedent(
                        """\
                        <xs:restriction base="xs:string">
                            <xs:minLength value="1" />
                        </xs:restriction>
                        """)

                # ---------------------------------------------------------------------------
                def TypeInfoToString_Directory(type_info):
                    return TypeInfoToString_Filename(type_info)

                # ---------------------------------------------------------------------------
                def TypeInfoToString_Bool(type_info):
                    return textwrap.dedent(
                        """\
                        <xs:restriction base="xs:boolean" />
                        """)

                # ---------------------------------------------------------------------------
                def TypeInfoToString_Guid(type_info):
                    return textwrap.dedent(
                        """\
                        <xs:restriction base="xs:string">
                            <xs:pattern value="\\{%(char)s{8}-%(char)s{4}-%(char)s{4}-%(char)s{4}-%(char)s{12}\\}" />
                        </xs:restriction>
                        """) % { "char" : "[0-9A-Fa-f]",
                               }

                # ---------------------------------------------------------------------------
                def TypeInfoToString_DateTime(type_info):
                    return textwrap.dedent(
                        """\
                        <xs:restriction base="xs:dateTime" />
                        """)

                # ---------------------------------------------------------------------------
                def TypeInfoToString_Date(type_info):
                    return textwrap.dedent(
                        """\
                        <xs:restriction base="xs:date" />
                        """)

                # ---------------------------------------------------------------------------
                def TypeInfoToString_Time(type_info):
                    return textwrap.dedent(
                        """\
                        <xs:restriction base="xs:time" />
                        """)

                # ---------------------------------------------------------------------------
                def TypeInfoToString_Duration(type_info):
                    return textwrap.dedent(
                        """\
                        <xs:restriction base="xs:duration" />
                        """)

                # ---------------------------------------------------------------------------
                def TypeInfoToString(type_info):
                    type_map = { StringTypeInfo : TypeInfoToString_String,
                                 EnumTypeInfo : TypeInfoToString_Enum,
                                 IntTypeInfo : TypeInfoToString_Int,
                                 FloatTypeInfo : TypeInfoToString_Float,
                                 FilenameTypeInfo : TypeInfoToString_Filename,
                                 DirectoryTypeInfo : TypeInfoToString_Directory,
                                 BoolTypeInfo : TypeInfoToString_Bool,
                                 GuidTypeInfo : TypeInfoToString_Guid,
                                 DateTimeTypeInfo : TypeInfoToString_DateTime,
                                 DateTypeInfo : TypeInfoToString_Date,
                                 TimeTypeInfo : TypeInfoToString_Time,
                                 DurationTypeInfo : TypeInfoToString_Duration,
                               }

                    if type(type_info) not in type_map:
                        raise Exception("'{}' was unexpected".format(type(type_info)))

                    return type_map[type(type_info)](type_info)

                # ---------------------------------------------------------------------------
                def DefineType_Fundamental(element, is_in):
                    if not is_in:
                        return

                    f.write(textwrap.dedent(
                        """\
                        <xs:simpleType name="_{}">
                        {}
                        </xs:simpleType>

                        """).format( element.DottedTypeName,
                                     StreamDecorator.LeftJustify( TypeInfoToString(element.TypeInfo).strip(),
                                                                  4,
                                                                  skip_first_line=False,
                                                                ),
                                   ))

                # ---------------------------------------------------------------------------
                def DefineType_Simple(element, is_in):
                    if is_in:
                        return
                    
                    f.write(textwrap.dedent(
                        """\
                        <xs:simpleType name="_{name}_content">
                            {content}
                        </xs:simpleType>

                        <xs:complexType name="_{name}">
                            <xs:simpleContent>
                                <xs:extension base="_{name}_content">
                                    {attributes}
                                </xs:extension>
                            </xs:simpleContent>
                        </xs:complexType>

                        """).format( name=element.DottedTypeName,
                                     content=StreamDecorator.LeftJustify( TypeInfoToString(element.TypeInfo).strip(),
                                                                          4,
                                                                        ),
                                     attributes=StreamDecorator.LeftJustify( ''.join([ textwrap.dedent(
                                                                                         """\
                                                                                         <xs:attribute name="{name}" use="{use}" type="_{type}" />
                                                                                         """).format( name=attribute.GivenName,
                                                                                                      use="optional" if attribute_type_info.Arity.IsOptional else "required",
                                                                                                      type=attribute.ResolveAll().DottedTypeName,
                                                                                                    )
                                                                                       for attribute, attribute_type_info in itertools.izip(element.Attributes, element.AttributeTypeInfo.Items.itervalues())
                                                                                     ]).strip(),
                                                                             12,
                                                                           ),
                                   ))

                # ---------------------------------------------------------------------------
                def DefineType_Compound(element, is_in):
                    if is_in:
                        return

                    if not element.define:
                        return

                    content = None

                    if element.polymorphic and not element.Base:
                        content = textwrap.dedent(
                            """\
                            <xs:choice{arity}>
                                {content}
                            </xs:choice>
                            """).format( arity=ArityToString(element.TypeInfo.Arity) if element.Parent != None else '',
                                         content=StreamDecorator.LeftJustify( ''.join([ textwrap.dedent(
                                                                                            """\
                                                                                            <xs:element name="{name}" type="_{name}" />
                                                                                            """).format(name=derived.DottedTypeName)
                                                                                        for derived in cls._GetDerivedElements(element)
                                                                                      ]).strip(),
                                                                              4,
                                                                            ).strip(),
                                       )
                    else:
                        content = textwrap.dedent(
                            """\
                            <xs:sequence>
                                {}
                            </xs:sequence>
                            """).format(StreamDecorator.LeftJustify( ''.join([ textwrap.dedent(
                                                                                   """\
                                                                                   <xs:element name="{name}" type="_{type}"{arity} />
                                                                                   """).format( name=child.GivenName,
                                                                                                type=child.ResolveAll().DottedTypeName,
                                                                                                arity=ArityToString(child.TypeInfo.Arity),
                                                                                              )
                                                                               for child in cls._GetAllChildren(element)
                                                                             ]).strip(),
                                                                     4,
                                                                   ).strip())

                    assert content != None
                    
                    f.write(textwrap.dedent(
                        """\
                        <xs:complexType name="_{name}">
                            {content}
                        </xs:complexType>

                        """).format( name=element.DottedTypeName,
                                     content=StreamDecorator.LeftJustify(content, 4).strip(),
                                   ))

                # ---------------------------------------------------------------------------
                def DefineType_Alias(element, is_in):
                    # Nothing to do here
                    pass

                # ---------------------------------------------------------------------------
                def DefineType_Augmented(element, is_in):
                    # Nothing to do here
                    pass

                # ---------------------------------------------------------------------------
                def DefineType(element, is_in):
                    type_map = { FundamentalElement : DefineType_Fundamental,
                                 CompoundElement : DefineType_Compound,
                                 SimpleElement : DefineType_Simple,
                                 AliasElement : DefineType_Alias,
                                 AugmentedElement : DefineType_Augmented,
                               }

                    if type(element) not in type_map:
                        raise Exception("'{}' was unexpected".format(type(element)))

                    type_map[type(element)](element, is_in)

                # ---------------------------------------------------------------------------
                def Enumerate(func):
                    # ---------------------------------------------------------------------------
                    def Impl(element):
                        func(element, True)
                        with CallOnExit(lambda: func(element, False)):
                            for child in getattr(element, "Children", []):
                                Impl(child)

                    # ---------------------------------------------------------------------------
                    
                    for element in elements:
                        Impl(element)

                # ---------------------------------------------------------------------------
                
                Enumerate(DefineType)

                f.write(textwrap.dedent(
                    """\
                    <xs:element name="{}">
                        <xs:complexType>
                            <xs:sequence>
                    """).format(name))

                stream = StreamDecorator(f, line_prefix=' ' * 12)

                for element in elements:
                    if element.IsDefinitionOnly or element.Name[0] == '_':
                        continue

                    if isinstance(element, CompoundElement) and not element.define:
                        continue

                    stream.write(textwrap.dedent(
                        """\
                        <xs:element name="{name}" type="_{type}"{arity} />
                        """).format( name=element.GivenName,
                                     type=element.ResolveAll().DottedTypeName,
                                     arity=ArityToString(element.TypeInfo.Arity),
                                   ))

                f.write(textwrap.dedent(
                    """\
                            </xs:sequence>
                        </xs:complexType>
                    </xs:element>

                    </xs:schema>
                    """))
            