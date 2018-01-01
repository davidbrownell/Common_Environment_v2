# ---------------------------------------------------------------------------
# |  
# |  RecursiveBuild.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/21/2015 03:14:36 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-18.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Recursively builds Build.py files."""

import os
import sys

import inflect

from CommonEnvironment.Build import CompleteConfiguration as Configuration

from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment.StreamDecorator import StreamDecorator

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

BUILD_FILENAME                              = "Build.py"
BUILD_FILENAME_IGNORE                       = "{}-ignore".format(BUILD_FILENAME)

BUILD_LOG_TEMPLATE                          = "Build.{}.log"

COMPLETE_CONFIGURATION_NAME                 = "Complete"

# ---------------------------------------------------------------------------
Pluralize = inflect.engine()

# ---------------------------------------------------------------------------
# <Dangerous default> pylint: disable = W0102
@CommandLine.EntryPoint(mode=CommandLine.EntryPoint.ArgumentInfo(description='Defaults to [ "clean", "build", ]'))
@CommandLine.FunctionConstraints( code_dir=CommandLine.DirectoryTypeInfo(),
                                  output_dir=CommandLine.StringTypeInfo(),
                                  mode=CommandLine.StringTypeInfo(arity='*'),
                                  output_stream=None,
                                )
def Execute( code_dir,
             output_dir,
             mode=None,
             debug_only=False,
             release_only=False,
             output_stream=sys.stdout,
             verbose=False,
           ):
    assert os.path.isdir(code_dir), code_dir
    assert output_dir
    assert isinstance(mode, list)
    assert output_stream
    
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    modes = mode or [ "clean", "build", ]
    
    with StreamDecorator(output_stream).DoneManager( line_prefix='', 
                                                     done_prefix="\n\nComposite Results: ",
                                                   ) as total_si:
        build_info = _GetBuildInfo(code_dir, output_stream)
        if not build_info:
            total_si.result = 0
            return total_si.result

        # Find all the build files that have configurations that we can process
        build_configurations = []

        total_si.stream.write("Processing build files...")
        with total_si.stream.DoneManager( done_suffix_functor=lambda: "{} found".format(Pluralize.no("configuration", len(build_configurations))),
                                        ):
            # ---------------------------------------------------------------------------
            def GetSupportedConfigurations(configurations):
                # If there is a configuration that indicates completeness, execute that
                # and skip everything else.
                if COMPLETE_CONFIGURATION_NAME in configurations:
                    yield COMPLETE_CONFIGURATION_NAME
                    return

                for config in configurations:
                    config_lower = config.lower()

                    if ( (debug_only and "debug" in config_lower) or
                         (release_only and "release" in config_lower) or 
                         (not debug_only and not release_only)
                       ):
                        yield config

            # ---------------------------------------------------------------------------
            
            for info in build_info:
                if not info.configuration.Configurations:
                    build_configurations.append(( info.filename,
                                                  info.configuration,
                                                  None,
                                                ))
                else:
                    for config in GetSupportedConfigurations(info.configuration.Configurations):
                        build_configurations.append(( info.filename,
                                                      info.configuration,
                                                      config,
                                                    ))

        if not build_configurations:
            return total_si.result

        total_si.stream.write('\n')
        for mode_index, mode in enumerate(modes):
            total_si.stream.write("Processing with '{}' ({} of {})...".format(mode, mode_index + 1, len(modes)))
            with total_si.stream.DoneManager() as mode_si:
                for build_index, (build_filename, config, configuration) in enumerate(build_configurations):
                    mode_si.stream.write("Processing '{}'{} ({} of {})...".format( build_filename,
                                                                                   " - '{}'".format(configuration) if configuration else '',
                                                                                   build_index + 1,
                                                                                   len(build_configurations),
                                                                                 ))
                    with mode_si.stream.DoneManager() as build_si:
                        build_output_dir = os.path.join(output_dir, config.SuggestedOutputDirLocation, configuration or "Build")
                        if not os.path.isdir(build_output_dir):
                            os.makedirs(build_output_dir)

                        # <Wrong indentations> pylint: disable = C0330
                        command_line = 'python "{build_filename}" {mode}{configuration}{output_dir}'.format( 
                                            build_filename=build_filename,
                                            mode=mode,
                                            configuration=' "{}"'.format(configuration) if configuration else '',
                                            output_dir=' "{}"'.format(build_output_dir) if config.RequiresOutputDir else '',
                                        )

                        build_si.result, output = Process.Execute(command_line)
                        
                        # It is possible that the cleaning process may deleted the directory. Recreate it if necessary.
                        if mode == "clean" and not os.path.isdir(build_output_dir):
                            os.makedirs(build_output_dir)

                        with open(os.path.join(build_output_dir, BUILD_LOG_TEMPLATE.format(mode)), 'w') as f:
                            f.write(output)

                        if build_si.result != 0:
                            build_si.stream.write(output)
                        elif verbose:
                            build_si.stream.write(output, "INFO: ")

            total_si.stream.write('\n')

        return total_si.result

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( code_dir=CommandLine.DirectoryTypeInfo(),
                                  output_stream=None,
                                )
def ListPriorities( code_dir,
                    output_stream=sys.stdout,
                  ):
    assert os.path.isdir(code_dir), code_dir
    assert output_stream

    for info in _GetBuildInfo(code_dir, output_stream):
        output_stream.write("{filename:<120} {priority}\n".format( filename="{}:".format(info.filename), 
                                                                   priority=info.configuration.Priority,
                                                                 ))

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
def _GetBuildInfo(code_dir, output_stream):
    code_dir = os.path.abspath(code_dir)

    build_info = []

    output_stream.write("\nSearching for build files...")
    with StreamDecorator(output_stream).DoneManager( done_suffix_functor=lambda: "{} found".format(Pluralize.no("build file", len(build_info))),
                                                   ):
        name, ext = os.path.splitext(BUILD_FILENAME)
        
        for fullpath in FileSystem.WalkFiles( code_dir,
                                              include_file_base_names=[ name, ],
                                              include_file_extensions=[ ext, ],
                                            ):
            if os.path.isfile(os.path.join(os.path.dirname(fullpath), BUILD_FILENAME_IGNORE)):
                continue

            build_info.append(QuickObject( filename=fullpath,
                                           configuration=Configuration.FromBuildFile( fullpath,
                                                                                      strip_path=code_dir,
                                                                                    ),
                                         ))

        build_info.sort(key=lambda item: item.configuration.Priority)

        return build_info
        
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
