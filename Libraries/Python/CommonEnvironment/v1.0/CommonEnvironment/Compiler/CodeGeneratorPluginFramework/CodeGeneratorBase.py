# ----------------------------------------------------------------------
# |  
# |  CodeGeneratorBase.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-08-04 13:31:21
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import imp
import inspect
import os
import sys

from collections import OrderedDict

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment.Interface import *
from CommonEnvironment.NamedTuple import NamedTuple
from CommonEnvironment.TypeInfo.FundamentalTypes import *
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import StringSerialization
from CommonEnvironment.StreamDecorator import StreamDecorator

from CommonEnvironment.Compiler import CodeGenerator as CodeGeneratorMod

from CommonEnvironment.Compiler.InputProcessingMixin.AtomicInputProcessingMixin import AtomicInputProcessingMixin
from CommonEnvironment.Compiler.InvocationQueryMixin.ConditionalInvocationQueryMixin import ConditionalInvocationQueryMixin
from CommonEnvironment.Compiler.InvocationMixin.CustomInvocationMixin import CustomInvocationMixin
from CommonEnvironment.Compiler.OutputMixin.MultipleOutputMixin import MultipleOutputMixin

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
PluginInfo = NamedTuple("PluginInfo", "mod", "plugin")

# ----------------------------------------------------------------------
def GetPlugins( dynamic_plugin_architecture_environment_key,
                plugins_dir,
              ):
    # There are 2 ways of loading plugins:
    #   1) Using the dynamic plugin architecture
    #   2) Files found in a specific directory

    plugin_mods = []

    if os.getenv(dynamic_plugin_architecture_environment_key):
        assert os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")

        sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
        with CallOnExit(lambda: sys.path.pop(0)):
            from SourceRepositoryTools import DynamicPluginArchitecture

            plugin_mods = list(DynamicPluginArchitecture.EnumeratePlugins(dynamic_plugin_architecture_environment_key))

    else:
        if not os.path.isdir(plugins_dir):
            raise Exception("The directory '{]' does not exist".format(plugins_dir))

        for filename in FileSystem.WalkFiles( plugins_dir,
                                              include_file_base_names=[ lambda name: name.endswith("Plugin"), ],
                                              include_file_extensions=[ ".py", ],
                                              recurse=True,
                                            ):
            name = os.path.splitext(os.path.basename(filename))[0]
            plugin_mods.append(imp.load_source(name, filename))

    plugins = OrderedDict()

    # ----------------------------------------------------------------------
    # This method will be added to all plugins discovered
    def GetPluginsImpl(plugin_name):
        if plugin_name not in plugins:
            raise Exception("'{}' is not a valid plugin".format(plugin_name))

        return plugins[plugin_name]

    # ----------------------------------------------------------------------
    
    warning_stream = StreamDecorator( sys.stdout,
                                      line_prefix="WARNING: ",
                                      suffix='\n',
                                    )
    with CallOnExit(lambda: warning_stream.flush(force_suffix=True)):
        if not plugin_mods:
            warning_stream.write("No plugins were found.\n")

        for plugin_mod in plugin_mods:
            obj = getattr(plugin_mod, "Plugin", None)
            if obj == None:
                warning_stream.write("The module defined at '{}' does not contain a 'Plugin' class.\n".format(plugin_mod.__file__))
                continue

            # Dynamically add the method GetPlugin to the plugin objects; this will
            # allow a plugin to query for other plugins. This is a bit wonky, but it
            # works with the plugin architecture where most of the plugins are static
            # objects.
            obj.GetPlugin = staticmethod(GetPluginsImpl)

            obj = obj()

            if not obj.IsValidEnvironment():
                warning_stream.write("The plugin '{}' is not valid within this environment ({}).\n".format(obj.Name, plugin_mod.__file__))
                continue

            plugins[obj.Name] = PluginInfo(plugin_mod, obj)

    return plugins

# ----------------------------------------------------------------------
def CodeGeneratorFactory( plugin_info_map,
                          name,
                          description,
                          is_supported_func,            # def Func(item) -> bool
                          get_optional_metadata_func,   # def Func() -> [ (k, v), ...]
                          preprocess_context_func,      # def Func(context, plugin) -> context
                          postprocess_context_func,     # def Func(context, plugin) -> context
                          invoke_func,                  # def Func(cls, invoke_reason, context, status_stream, output_stream, plugin)
                          requires_output_name=True,
                        ):
    assert is_supported_func
    assert get_optional_metadata_func
    assert preprocess_context_func
    assert postprocess_context_func

    calling_frame = inspect.stack()[1]
    calling_mod_filename = os.path.realpath(inspect.getmodule(calling_frame[0]).__file__)
            
    # ----------------------------------------------------------------------
    @staticderived
    class CodeGenerator( AtomicInputProcessingMixin,
                         ConditionalInvocationQueryMixin,
                         CustomInvocationMixin,
                         MultipleOutputMixin,
                         CodeGeneratorMod.CodeGenerator,
                       ):
        # ----------------------------------------------------------------------
        # |  
        # |  Public Properties
        # |  
        # ----------------------------------------------------------------------
        Name                                = name
        Description                         = description
        Type                                = CodeGeneratorMod.CodeGenerator.TypeValue.File
        OriginalModuleFilename              = calling_mod_filename
        RequiresOutputName                  = requires_output_name

        # ----------------------------------------------------------------------
        # |  
        # |  Public Methods
        # |  
        # ----------------------------------------------------------------------
        @staticmethod
        def IsSupported(item):
            return is_supported_func(item)

        # ----------------------------------------------------------------------
        # |  
        # |  Protected Methods
        # |  
        # ----------------------------------------------------------------------
        @classmethod
        def _GetAdditionalGeneratorItems(cls, context):
            # ----------------------------------------------------------------------
            def ProcessGeneratorItem(item):
                if isinstance(item, (str, unicode)):
                    assert item in plugin_info_map, item
                    return plugin_info_map[item].plugin

                return item

            # ----------------------------------------------------------------------
            
            plugin = plugin_info_map[context.plugin_name].plugin

            return [ cls, 
                     cls.OriginalModuleFilename,
                     plugin, 
                   ] + \
                   [ ProcessGeneratorItem(item) for item in plugin.GetAdditionalGeneratorItems(context) ] + \
                   super(CodeGenerator, cls)._GetAdditionalGeneratorItems(context)

        # ----------------------------------------------------------------------
        # |  
        # |  Private Methods
        # |  
        # ----------------------------------------------------------------------
        @classmethod
        def _GetRequiredMetadataNames(cls):
            names = [ "plugin_name",
                    ]

            if requires_output_name:
                names += [ "output_name", ]

            names += super(CodeGenerator, cls)._GetRequiredMetadataNames()

            return names

        # ----------------------------------------------------------------------
        @classmethod
        def _GetOptionalMetadata(cls):
            return get_optional_metadata_func() + \
                   [ ( "plugin_settings", {} ), 
                   ] + \
                   super(CodeGenerator, cls)._GetOptionalMetadata()

        # ----------------------------------------------------------------------
        @classmethod
        def _PostprocessContextItem(cls, context):
            if context.plugin_name not in plugin_info_map:
                raise CommandLine.UsageException("'{}' is not a valid plugin".format(context.plugin_name))

            plugin = plugin_info_map[context.plugin_name].plugin

            # Ensure that all plugin settings are present and that they
            # are the expected type.
            custom_settings = { k : v for k, v in plugin.GenerateCustomSettingsAndDefaults() }

            for k, v in context.plugin_settings.iteritems():
                if k not in custom_settings:
                    raise CommandLine.UsageException("'{}' is not a valid key for plugin_arg".format(k))

                desired_type = type(custom_settings[k])

                if type(v) != desired_type:
                    assert isinstance(v, (str, unicode))
                    context.plugin_settings[k] = StringSerialization.DeserializeItem(CreateTypeInfo(desired_type), v)

            for k, v in custom_settings.iteritems():
                if k not in context.plugin_settings:
                    context.plugin_settings[k] = v

            context.plugin_settings = plugin.PreprocessCustomSettings(**context.plugin_settings)

            # Invoke custom functionality
            context = preprocess_context_func(context, plugin)

            # Postprocess and validate the context with the plugin
            context = plugin.PostprocessContextItem(context, pre_validate=True)

            context.output_filenames = [ os.path.join(context.output_dir, filename) for filename in plugin.GenerateOutputFilenames(context) ]

            plugin.ValidateContextItem(context)

            context = plugin.PostprocessContextItem(context, pre_validate=False)

            context = postprocess_context_func(context, plugin)

            return super(CodeGenerator, cls)._PostprocessContextItem(context)

        # ----------------------------------------------------------------------
        @classmethod
        def _InvokeImpl( cls,
                         invoke_reason,
                         context,
                         status_stream,
                         output_stream,
                       ):
            return invoke_func( cls,
                                invoke_reason,
                                context, 
                                status_stream,
                                output_stream,
                                plugin_info_map[context.plugin_name].plugin,
                              )

    # ----------------------------------------------------------------------
    
    return CodeGenerator

# ----------------------------------------------------------------------
class DoesNotExist(object): pass

GenerateArg                                 = NamedTuple( "GenerateArg",
                                                          "Name", 
                                                          "TypeInfo",
                                                          DefaultValue=DoesNotExist(),  # If == DoesNotExist, the command line argument becomes a required one
                                                          ContextAttributeName=None,    # If == None, the context attribute name is the same as "Name"
                                                        )
                                                            
def GenerateFactory( plugin_info_map,
                     code_generator,
                     command_line_args,     # [ <GenerateArg>, ... ]
                   ):
    # Dynamicly generate the Generate method due to the presence of optional params
    positional_args = []
    keyword_args = []

    for arg in command_line_args:
        if isinstance(arg.DefaultValue, DoesNotExist):
            positional_args.append(arg)
        else:
            keyword_args.append(arg)

    if code_generator.RequiresOutputName:
        output_name_constraint = "output_name=CommandLine.StringTypeInfo()," 
        output_name_param = "output_name,"
        output_name_arg = "output_name=output_name," 
    else:
        output_name_constraint = ""
        output_name_param = ""
        output_name_arg = ""

    dynamic_content = textwrap.dedent(
        """\
        @CommandLine.EntryPoint()
        @CommandLine.FunctionConstraints( plugin=CommandLine.EnumTypeInfo(plugin_info_map.keys()),
                                          {output_name_constraint}
                                          output_dir=CommandLine.DirectoryTypeInfo(ensure_exists=False),
                                          input=CommandLine.FilenameTypeInfo(match_any=True, arity='+'),
                                          plugin_arg=CommandLine.DictTypeInfo(require_exact_match=False),
                                          output_stream=None,
                                          {constraints}
                                        )
        def Generate( plugin,
                      {output_name_param}
                      output_dir,
                      input,
                      {positional_params}plugin_arg={{}},
                      force=False,
                      output_stream=sys.stdout,
                      verbose=False,{keyword_params}
                    ):
            return CodeGeneratorMod.CommandLineGenerate( code_generator,
                                                         input,
                                                         output_stream,
                                                         verbose,
                                                       
                                                         plugin_name=plugin,
                                                         {output_name_arg}
                                                         output_dir=output_dir,
                                                       
                                                         plugin_settings=plugin_arg,
                                                       
                                                         force=force,

                                                         {args}
                                                       )
        """).format( output_name_constraint=output_name_constraint,
                     output_name_param=output_name_param,
                     output_name_arg=output_name_arg,
                     constraints=StreamDecorator.LeftJustify( '\n'.join([ "{}={},".format(arg.Name, arg.TypeInfo.PythonDefinitionString) for arg in command_line_args ]),
                                                              len("@CommandLine.FunctionConstraints( "),
                                                            ),
                     positional_params='' if not positional_args else StreamDecorator.LeftJustify( "{}\n".format('\n'.join([ "{},".format(arg.Name) for arg in positional_args ])),
                                                                                                   len("def Generate( "),
                                                                                                   add_suffix=True,
                                                                                                 ),
                     keyword_params='' if not keyword_args else StreamDecorator.LeftJustify( "\n{}".format('\n'.join([ "{}={},".format(arg.Name, arg.DefaultValue) for arg in keyword_args ])),
                                                                                             len("def Generate( "),
                                                                                           ),
                     args='' if not command_line_args else StreamDecorator.LeftJustify( '\n'.join([ "{}={},".format(arg.ContextAttributeName or arg.Name, arg.Name) for arg in command_line_args ]),
                                                                                        4 + len("return CodeGeneratorMod.CommandLineGenerate( "),
                                                                                      ),
                                                                                                   
                   )

    exec( dynamic_content, 
          { "CodeGeneratorMod" : CodeGeneratorMod, 
            "plugin_info_map" : plugin_info_map,
            "code_generator" : code_generator,
          }, 
          globals(),
        )

    return Generate

# ----------------------------------------------------------------------
def CleanFactory():
    # ----------------------------------------------------------------------
    @CommandLine.EntryPoint()
    @CommandLine.FunctionConstraints( output_dir=CommandLine.DirectoryTypeInfo(),
                                      output_stream=None,
                                    )
    def Clean( output_dir,
               output_stream=sys.stdout,
             ):
        return CodeGeneratorMod.CommandLineClean(output_dir, output_stream)

    # ----------------------------------------------------------------------
    
    return Clean

# ----------------------------------------------------------------------
def ListFactory(plugin_info_map):
    # ----------------------------------------------------------------------
    @CommandLine.EntryPoint()
    @CommandLine.FunctionConstraints( output_stream=None,
                                    )
    def List( json=False,
              output_stream=sys.stdout,
            ):
        if json:
            d = OrderedDict()

            # ----------------------------------------------------------------------
            def ProcessEntry(k, v):
                mod_filename = v.mod.__file__
    
                if os.path.splitext(mod_filename)[1] == ".pyc":
                    mod_filename = mod_filename[:-1]
    
                assert os.path.isfile(mod_filename), mod_filename
    
                d[k] = { "python_filename" : mod_filename,
                       }
    
            # ----------------------------------------------------------------------
            def OnComplete():
                import json as json_mod
                output_stream.write(json_mod.dumps(d))
    
            # ----------------------------------------------------------------------
            
        else:
            # ----------------------------------------------------------------------
            def ProcessEntry(k, v):
                output_stream.write("{}\n".format(k))
    
            # ----------------------------------------------------------------------
            def OnComplete():
                pass
    
            # ----------------------------------------------------------------------
            
        with CallOnExit(OnComplete):
            for k, v in plugin_info_map.iteritems():
                ProcessEntry(k, v)

    # ----------------------------------------------------------------------
    
    return List
