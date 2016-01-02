# ---------------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/21/2015 03:33:35 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""\
Provides functionality for files that implement or consume builder functionality.
A builder is a file that is capable of building or cleaning a binary, where the
mechanics associated with the implementation of that functionality is considered to
be an implementation detail.
"""

import inspect
import os
import subprocess
import re
import sys
import textwrap

from ..CallOnExit import CallOnExit
from .. import CommandLine
from .. import FileSystem
from .. import RegularExpression
from .. import Shell

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
# <Too many instance attributes> pylint: disable = R0902
# <Too few public methods> pylint: disable = R0903
class Configuration(object):

    # ---------------------------------------------------------------------------
    # |  Public Types
    DEFAULT_PRIORITY                        = 10000

    # ---------------------------------------------------------------------------
    # |  Public Methods
    def __init__( self,
                  name,
                  priority=DEFAULT_PRIORITY,
                  suggested_output_dir_location='',
                  requires_output_dir=True,
                  configurations=None,
                  required_development_environment=None,
                  required_development_configurations=None,
                  disable_if_dependency_environment=False,
                ):
        self.Name                                       = name
        self.Priority                                   = priority
        self.RequiresOutputDir                          = requires_output_dir
        self.Configurations                             = configurations or []
        self.RequiredDevelopmentEnvironment             = required_development_environment
        self.RequiredDevelopmentConfigurations          = required_development_configurations or []
        self.DisableIfDependencyEnvironment             = disable_if_dependency_environment
        self.SuggestedOutputDirLocation                 = suggested_output_dir_location or self.Name
    
# ---------------------------------------------------------------------------
class CompleteConfiguration(Configuration):

    # ---------------------------------------------------------------------------
    @classmethod
    def FromBuildFile( cls,
                       build_filename,
                       strip_path=None,
                     ):
        assert os.path.isfile(build_filename), build_filename

        # Extract metadata auto-generated from the build file to create
        # the configuration. Note that some portions of the metadata will
        # be based on the current dir, so switch to the root dir before
        # extracting the information to ensure that things work as expected.
        if strip_path:
            assert os.path.isdir(strip_path), strip_path

            current_dir = os.getcwd()
            os.chdir(strip_path)

            # ---------------------------------------------------------------------------
            def Cleanup():
                os.chdir(current_dir)

            # ---------------------------------------------------------------------------
        else:
            # ---------------------------------------------------------------------------
            def Cleanup():
                pass

            # ---------------------------------------------------------------------------
            
        with CallOnExit(Cleanup):
            result = subprocess.Popen( 'python "{}" Metadata'.format(build_filename),
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                     )
            output = result.stdout.read()
            result = result.wait() or 0

            assert result == 0, (result, output)
            
            match = RegularExpression.TemplateStringToRegex(cls._VIEW_METADATA_TEMPLATE).match(output)
            assert match, output

            # ---------------------------------------------------------------------------
            def FromList(value):
                value = match.group(value)
                return [] if value == "None" else [ item.strip() for item in value.split(',') if item.strip() ]

            # ---------------------------------------------------------------------------
            def FromOptional(value):
                value = match.group(value)
                return None if value == "None" else value

            # ---------------------------------------------------------------------------
            def FromBool(value):
                value = match.group(value)
                return value == "True"

            # ---------------------------------------------------------------------------
            
            return cls( exposed_functions=FromList("commands"),
                        config=Configuration( name=match.group("name"),
                                              priority=int(match.group("priority")),
                                              suggested_output_dir_location=match.group("suggested_output_dir_location"),
                                              requires_output_dir=FromBool("requires_output_dir"),
                                              configurations=FromList("configurations"),
                                              required_development_environment=FromOptional("required_dev_environment"),
                                              required_development_configurations=FromList("required_dev_configurations"),
                                              disable_if_dependency_environment=FromBool("disable_if_dependency"),
                                            ),
                      )

    # ---------------------------------------------------------------------------
    def __init__(self, exposed_functions, config):
        self.__dict__                                   = config.__dict__
        self.ExposedFunctions                           = list(exposed_functions)

    # ---------------------------------------------------------------------------
    def GetCustomCommands(self):
        return [ command for command in self.ExposedFunctions if command not in [ "Build", "Clean", "Rebuild", "Metadata", ] ]

    # ---------------------------------------------------------------------------
    def __str__(self):
        custom_commands = self.GetCustomCommands()

        return self._VIEW_METADATA_TEMPLATE.format( name=self.Name,
                                                    priority=self.Priority,
                                                    requires_output_dir="True" if self.RequiresOutputDir else "False",
                                                    suggested_output_dir_location=self.SuggestedOutputDirLocation,
                                                    configurations=', '.join(self.Configurations) if self.Configurations else "None",
                                                    commands=', '.join(self.ExposedFunctions),
                                                    custom_commands=', '.join(custom_commands) if custom_commands else "None",
                                                    required_dev_environment=self.RequiredDevelopmentEnvironment or "None",
                                                    required_dev_configurations=', '.join(self.RequiredDevelopmentConfigurations) if self.RequiredDevelopmentConfigurations else "None",
                                                    disable_if_dependency="True" if self.DisableIfDependencyEnvironment else "False",
                                                  )

    # ---------------------------------------------------------------------------
    # |
    # |  Private Types
    # |
    # ---------------------------------------------------------------------------
    # <Wrong indentation> pylint: disable = C0330
    _VIEW_METADATA_TEMPLATE                             = textwrap.dedent(
       r"""
        Name:                                                   {name}
        Priority:                                               {priority}

        Requires Output Dir:                                    {requires_output_dir}
        Suggested Output Dir Location:                          {suggested_output_dir_location}
        
        Available Configurations:                               {configurations}
        Available Commands:                                     {commands}
        Custom Commands:                                        {custom_commands}

        Required Development Environment:                       {required_dev_environment}
        Required Development Environment Configurations:        {required_dev_configurations}
        Disable If Dependency Environment:                      {disable_if_dependency}
        """).lstrip()

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
# <Dangerous default value> pylint: disable = W0102
def Main( config,
          original_args=sys.argv,
          command_line_arg_prefix='/',
          command_line_keyword_separator='=',
          command_line_dict_tag_value_separator=':',
          verbose=False,
          output_stream=sys.stderr,
        ):
    assert config

    # Some functions are required, others are not
    required = { "build" : lambda ep: _RedirectEntryPoint("Build", ep, config),
                 "clean" : lambda ep: _RedirectEntryPoint("Clean", ep, config),
               }

    required_names = set(required.keys())

    entry_points = CommandLine.EntryPointData.FromModule(sys.modules["__main__"])
    for entry_point in entry_points:
        entry_point_name_lower = entry_point.Name.lower()

        if entry_point_name_lower in required_names:
            required[entry_point_name_lower](entry_point)
            required[entry_point_name_lower] = entry_point

            required_names.remove(entry_point_name_lower)

        else:
            assert entry_point_name_lower != "rebuild"

    if required_names:
        raise Exception("These methods are required: {}".format(', '.join(required_names)))

    entry_points.append(CommandLine.EntryPointData.FromFunction(_GenerateRebuild( required["clean"],
                                                                                   required["build"],
                                                                                   config,
                                                                                 )))

    # ---------------------------------------------------------------------------
    @CommandLine.EntryPoint
    def Metadata():
        sys.stdout.write(str(config))
    
    # ---------------------------------------------------------------------------
    
    entry_points.append(CommandLine.EntryPointData.FromFunction(Metadata))

    config = CompleteConfiguration( [ entry_point.Name for entry_point in entry_points ],
                                    config,
                                  )

    script_description_suffix = None
    if config.Configurations:
        script_description_suffix = "    Where <configuration> can be:\n\n{}\n".format('\n'.join([ "        - {}".format(cfg) for cfg in config.Configurations ]))

    # Execute
    stack_frame = inspect.stack()[-1]

    current_dir = os.getcwd()
    os.chdir(os.path.dirname(os.path.abspath(stack_frame[1])))

    with CallOnExit(lambda: os.chdir(current_dir)):
        # Ensure that an output directory is created prior to invoking build functionality.
        if config.RequiresOutputDir and len(original_args) >= 2 and original_args[1].lower() == "build":
            output_dir = None

            if config.Configurations:
                # Command Line is: <script> build <config> <output_dir> ...
                if len(original_args) >= 4:
                    output_dir = original_args[3]
            else:
                # Command Line is: <script> build <output_dir> ...
                if len(original_args) >= 3:
                    output_dir = original_args[2]

            if output_dir and not os.path.isdir(output_dir):
                os.makedirs(output_dir)

        return CommandLine.Executor( args=original_args,
                                     command_line_arg_prefix=command_line_arg_prefix,
                                     command_line_keyword_separator=command_line_keyword_separator,
                                     command_line_dict_tag_value_separator=command_line_dict_tag_value_separator,
                                     script_description=inspect.getmodule(stack_frame[0]).__doc__ or '',
                                     script_description_suffix=script_description_suffix,
                                     entry_points=entry_points,
                                   ).Invoke( verbose=verbose,
                                             output_stream=output_stream,
                                           )

# ---------------------------------------------------------------------------
# |
# |  Private Methods
# |
# ---------------------------------------------------------------------------
# <Invalid function name> pylint: disable = C0103
def _RedirectEntryPoint_IsSupportedDevelopmentConfiguration(configurations):
    # Note that this function can't be defined inline, as the caller uses
    # exec and eval.

    dev_configuration = os.getenv("DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION")
    return any(re.match(dev_cfg, dev_configuration) for dev_cfg in configurations)
        
# ---------------------------------------------------------------------------
def _RedirectEntryPoint(function_name, entry_point, config):
    assert function_name
    assert entry_point
    assert config

    required_arguments = []

    if config.Configurations:
        assert "configuration" in entry_point.ConstraintsDecorator.Preconditions, function_name
        entry_point.ConstraintsDecorator.Preconditions["configuration"] = CommandLine.EnumTypeInfo(config.Configurations)

        required_arguments.append("configuration")

    if config.RequiresOutputDir:
        required_arguments.append("output_dir")

    num_required_args = entry_point.Func.func_code.co_argcount - (len(entry_point.Func.func_defaults or []))
    arguments = entry_point.Func.func_code.co_varnames[:num_required_args]
    
    if required_arguments and list(arguments[:len(required_arguments) + 1]) != required_arguments:
        raise Exception("The entry point '{}' should begin with the arguments '{}' ('{}' were found)".format( function_name, 
                                                                                                              ', '.join(required_arguments),
                                                                                                              ', '.join(arguments),
                                                                                                            ))

    # <Use of eval and exec> pylint: disable = W0122, W0123

    if config.RequiredDevelopmentEnvironment and config.RequiredDevelopmentEnvironment.lower() != Shell.GetEnvironment().Name.lower():
        # Dynamically redefine the function so that it prints information that lets the user know that the 
        # functionality can't be executed on the current platform.
        exec(textwrap.dedent(
            """\
            def {name}({args}):
                sys.stdout.write("\nINFO: This can only be run on '{env}'.\n")
                return 0
            """).format( name=function_name,
                         args=', '.join(arguments),
                         env=config.RequiredDevelopmentEnvironment,
                       ))

        entry_point.Func = eval(function_name)

    elif config.RequiredDevelopmentConfigurations and not _RedirectEntryPoint_IsSupportedDevelopmentConfiguration(config.RequiredDevelopmentConfigurations):
        exec(textwrap.dedent(
            """\
            def {name}({args}):
                sys.stdout.write("\nINFO: This can only be run in development environments activated with the configurations {configs}.\n")
                return 0
            """).format( name=function_name,
                         args=', '.join(arguments),
                         configs=', '.join([ "'{}'".format(dev_cfg) for dev_cfg in config.RequiredDevelopmentConfigurations ]), 
                       ))
        
        entry_point.Func = eval(function_name)

    elif config.DisableIfDependencyEnvironment:
        repo_path = os.getenv("DEVELOPMENT_ENVIRONMENT_REPOSITORY")
        if FileSystem.RemoveTrailingSep(FileSystem.GetCommonPath(repo_path, inspect.getfile(function))) != repo_path:
            exec(textwrap.dedent(
                """\
                def {name}({args}):
                    sys.stdout.write("\nINFO: This module is not built when invoked as a dependency environment.\n")
                    return 0
                """).format( name=function_name,
                             args=', '.join(arguments),
                           ))

            entry_point.Func = eval(function_name)

# ---------------------------------------------------------------------------
def _GenerateRebuild(clean_func, build_func, config):
    assert clean_func
    assert build_func
    assert config

    # ---------------------------------------------------------------------------
    def Impl(configuration, output_dir, clean_func, build_func):
        result = clean_func(configuration, output_dir)
        if result != None and result != 0:
            return result

        if config.RequiresOutputDir and not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        result = build_func(configuration, output_dir)
        if result != None and result != 0:
            return result

        return 0

    # ---------------------------------------------------------------------------
    
    if config.Configurations:
        if config.RequiresOutputDir:
            @CommandLine.EntryPoint
            @CommandLine.FunctionConstraints( configuration=CommandLine.EnumTypeInfo(config.Configurations),
                                              output_dir=CommandLine.StringTypeInfo(),
                                            )
            def Rebuild(configuration, output_dir):
                return Impl( configuration, 
                             output_dir,
                             clean_func,
                             build_func,
                           )

        else:
            @CommandLine.EntryPoint
            @CommandLine.FunctionConstraints(configuration=CommandLine.EnumTypeInfo(config.Configurations))
            def Rebuild(configuration):
                return Impl( configuration, 
                             None,
                             lambda cfg, output_dir: clean_func(cfg),
                             lambda cfg, output_dir: build_func(cfg),
                           )

    else:
        if config.RequiresOutputDir:
            @CommandLine.EntryPoint
            @CommandLine.FunctionConstraints(output_dir=CommandLine.StringTypeInfo())
            def Rebuild(output_dir):
                return Impl( None,
                             output_dir,
                             lambda cfg, output_dir: clean_func(output_dir),
                             lambda cfg, output_dir: build_func(output_dir),
                           )

        else:
            @CommandLine.EntryPoint
            def Rebuild():
                return Impl( None,
                             None,
                             lambda cfg, output_dir: clean_func(),
                             lambda cfg, output_dir: build_func(),
                           )

    return Rebuild
