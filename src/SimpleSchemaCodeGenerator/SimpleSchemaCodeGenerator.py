# ---------------------------------------------------------------------------
# |  
# |  SimpleSchemaCodeGenerator.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/10/2015 03:50:27 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Code generator that consumes a SimpleSchema and produces output according to a specific plugin.
"""

import imp
import inspect
import os
import re
import sys

from collections import OrderedDict
import cPickle as pickle

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment.Interface import *
from CommonEnvironment.NamedTuple import NamedTuple
from CommonEnvironment import Package
from CommonEnvironment.StreamDecorator import StreamDecorator

from CommonEnvironment.Compiler import CodeGenerator as CodeGeneratorMod

from CommonEnvironment.Compiler.InputProcessingMixin.AtomicInputProcessingMixin import AtomicInputProcessingMixin
from CommonEnvironment.Compiler.InvocationQueryMixin.ConditionalInvocationQueryMixin import ConditionalInvocationQueryMixin
from CommonEnvironment.Compiler.InvocationMixin.CustomInvocationMixin import CustomInvocationMixin
from CommonEnvironment.Compiler.OutputMixin.MultipleOutputMixin import MultipleOutputMixin

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, "SimpleSchema"))
with CallOnExit(lambda: sys.path.pop(0)):
    import Elements
    from Exceptions import *
    import Parse

# ---------------------------------------------------------------------------
PluginInfo = NamedTuple("PluginInfo", "mod", "plugin")

# There are 2 ways of loading plugins:
#   - Using the DynamicPluginArchitecture
#   - Files found in the Plugins directory
_plugin_mods = []

if os.getenv("DEVELOPMENT_ENVIRONMENT_SIMPLE_SCHEMA_PLUGINS"):
    assert os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")
    sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))

    with CallOnExit(lambda: sys.path.pop(0)):
        from SourceRepositoryTools import DynamicPluginArchitecture

        _plugin_mods = list(DynamicPluginArchitecture.EnumeratePlugins("DEVELOPMENT_ENVIRONMENT_SIMPLE_SCHEMA_PLUGINS"))

else:
    plugins_dir = os.path.join(_script_dir, "Plugins")
    if not os.path.isdir(plugins_dir):
        raise Exception("The plugin dir '{}' was not found".format(plugins_dir))

    for filename in FileSystem.WalkFiles( plugins_dir,
                                          include_file_base_names=[ lambda name: name.endswith("Plugin"), ],
                                          include_file_extensions=[ ".py", ],
                                          recurse=True,
                                        ):
        name = os.path.splitext(os.path.basename(filename))[0]
        _plugin_mods.append(imp.load_source(name, filename))

assert _plugin_mods

PLUGINS = OrderedDict()

for plugin_mod in _plugin_mods:
    obj = getattr(plugin_mod, "Plugin", None)
    if obj == None:
        sys.stdout.write("WARNING: The object defined at '{}' does not contain a 'Plugin' class.\n".format(plugin_mod.__file__))
    else:
        obj = obj()
        PLUGINS[obj.Name] = PluginInfo(plugin_mod, obj)

del _plugin_mods

# ---------------------------------------------------------------------------
def CommandLineSuffix():
    return StreamDecorator.LeftJustify( textwrap.dedent(
                                            """\
                                            Where valid values for <plugin> are:
                                            {}

                                            """).format('\n'.join([ "    - {}".format(name) for name in PLUGINS.iterkeys() ])),
                                        4,
                                        skip_first_line=False,
                                      )

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
@staticderived
class CodeGenerator( CustomInvocationMixin,
                     ConditionalInvocationQueryMixin,
                     AtomicInputProcessingMixin,
                     MultipleOutputMixin,
                     CodeGeneratorMod.CodeGenerator,
                   ):
    
    # ---------------------------------------------------------------------------
    # |
    # |  Public Properties
    # |
    # ---------------------------------------------------------------------------
    Name                                    = "SimpleSchemaCodeGenerator"
    Description                             = "Processes a SimpleSchema file and produces output according to a provided plugin"
    Type                                    = CodeGeneratorMod.CodeGenerator.TypeValue.File

    # ---------------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ---------------------------------------------------------------------------
    @staticmethod
    def IsSupported(item):
        return item.lower().endswith(".simpleschema")

    # ---------------------------------------------------------------------------
    # |
    # |  Protected Methods
    # |
    # ---------------------------------------------------------------------------
    @classmethod
    def _GetAdditionalGeneratorItems(cls, context):
        plugin = cls._GetPlugin(context.plugin_name)

        return [ plugin, ] + \
               plugin.GetAdditionalGeneratorItems(context) + \
               super(CodeGenerator, cls)._GetAdditionalGeneratorItems(context)
    
    # ---------------------------------------------------------------------------
    # |
    # |  Private Methods
    # |
    # ---------------------------------------------------------------------------
    @classmethod
    def _GetRequiredMetadataNames(cls):
        return [ "plugin_name",
                 "output_name",
               ] + \
               super(CodeGenerator, cls)._GetRequiredMetadataNames()

    # ---------------------------------------------------------------------------
    @classmethod
    def _GetOptionalMetadata(cls):
        return [ ( "includes", [] ),
                 ( "excludes", [] ),
                 ( "plugin_settings", {} ),
               ] + \
               super(CodeGenerator, cls)._GetOptionalMetadata()

    # ---------------------------------------------------------------------------
    @staticmethod
    def _GetPlugin(plugin_name):
        if plugin_name not in PLUGINS:
            raise Exception("'{}' is not a valid plugin".format(plugin_name))

        return PLUGINS[plugin_name].plugin

    # ---------------------------------------------------------------------------
    @classmethod
    def _PostprocessContextItem(cls, context):
        plugin = cls._GetPlugin(context.plugin_name)

        # Plugin settings
        for k, v in plugin.GenerateCustomSettingsAndDefaults():
            if k not in context.plugin_settings:
                context.plugin_settings[k] = v

        elements = Parse.ParseFiles(context.input_filenames, plugin)

        # Calculate the include indexes
        includes = [ re.compile("^{}$".format(include)) for include in context.includes ]
        excludes = [ re.compile("^{}$".format(exclude)) for exclude in context.excludes ]

        del context.includes
        del context.excludes

        include_indexes = range(len(elements))

        if excludes:
            include_indexes = [ index for index in include_indexes if not CommonEnvironment.Any(excludes, lambda exclude, index=index: exclude.match(elements[index].Name)) ]
        
        if includes:
            include_indexes = [ index for index in include_indexes if CommonEnvironment.Any(includes, lambda include, index=index: include.match(elements[index].Name)) ]

        context.elements = elements
        context.include_indexes = include_indexes

        context = plugin.PostprocessContextItem(context)

        context.output_filenames = [ os.path.join(context.output_dir, filename) for filename in plugin.GenerateOutputFilenames(context) ]

        # This is a bit strange, but to detect changes, we need to compare the data associated with
        # the elements and not the elements themselves (as the elements will be different instances 
        # during each invocation). Therefore, save the data (via pickling) and remove the elements.
        # During invocation below, we will deserialize the elements from the pickled data before 
        # invoking the plugin's Generate method.
        
        context.pickled_elements = pickle.dumps(context.elements)
        del context.elements

        return super(CodeGenerator, cls)._PostprocessContextItem(context)

    # ---------------------------------------------------------------------------
    @classmethod
    def _InvokeImpl( cls,
                     invoke_reason,
                     context,
                     status_stream,
                     output_stream,
                   ):
        elements = pickle.loads(context.pickled_elements)

        return cls._GetPlugin(context.plugin_name).Generate( cls,
                                                             invoke_reason,
                                                             context.input_filenames,
                                                             context.output_filenames,
                                                             context.output_name,
                                                             elements,
                                                             context.include_indexes,
                                                             status_stream,
                                                             output_stream,
                                                             **context.plugin_settings
                                                           )

    # ---------------------------------------------------------------------------
    @classmethod
    def _CustomContextComparison(cls, context, prev_context):
        return super(CodeGenerator, cls)._CustomContextComparison(context, prev_context)

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( plugin=CommandLine.EnumTypeInfo(PLUGINS.keys()),
                                  output_name=CommandLine.StringTypeInfo(),
                                  output_dir=CommandLine.StringTypeInfo(),
                                  input=CommandLine.FilenameTypeInfo(CommandLine.FilenameTypeInfo.Type_Either, arity='+'),
                                  include=CommandLine.StringTypeInfo(arity='*'),
                                  exclude=CommandLine.StringTypeInfo(arity='*'),
                                  plugin_arg=CommandLine.DictTypeInfo(),
                                  output_stream=None,
                                )
def Generate( plugin,
              output_name,
              output_dir,
              input,
              include=None,
              exclude=None,
              plugin_arg={},
              force=False,
              output_stream=sys.stdout,
              verbose=False,
            ):
    try:
        return CodeGeneratorMod.CommandLineGenerate( CodeGenerator,
                                                     input,
                                                     output_stream,
                                                     verbose,

                                                     # Compiler-specific metadata
                                                     plugin_name=plugin,
                                                     output_name=output_name,
                                                     output_dir=output_dir,
                                                     
                                                     includes=include,
                                                     excludes=exclude,

                                                     plugin_settings=plugin_arg,

                                                     force=force,
                                                     plugin_verbose=verbose,
                                                   )
    except SimpleSchemaException, ex:
        output_stream.write("ERROR: {}\n".format(StreamDecorator.LeftJustify( str(ex), 
                                                                              len("ERROR: "),
                                                                            ).rstrip()))
        
        return -1

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( output_dir=CommandLine.StringTypeInfo(),
                                  output_stream=None,
                                )
def Clean( output_dir,
           output_stream=sys.stdout,
         ):
    return CodeGeneratorMod.CommandLineClean(output_dir, output_stream)

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
