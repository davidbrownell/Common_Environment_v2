# ----------------------------------------------------------------------
# |  
# |  Docker.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-01-11 08:26:15
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Implements common build functionality for Docker-based builds"""

import inspect
import os
import shutil
import six
import sys

from CommonEnvironment import Listify
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment import Shell
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

def CreateBuildFunc( name,
                     configurations,                    # dictionary, keys are configuration names and values are substitution dicts passed to the Jinja2CodeGenerator
                     local_files=None,                  # Any files that should be copied to the destination directory
                     pre_build_funcs=None,              # def Func(output_dir, output_stream)
                     post_build_funcs=None,             # def Func(output_dir, output_stream)
                     dockerfile="Dockerfile.Jinja2",
                   ):
    local_files = Listify(local_files or [])
    post_build_funcs = Listify(post_build_funcs or [])

    calling_dir = _GetCallingDir()
    
    # ----------------------------------------------------------------------
    @CommandLine.EntryPoint
    @CommandLine.FunctionConstraints( configuration=CommandLine.EnumTypeInfo(configurations.keys()),
                                      output_stream=None,
                                    )
    def Build( configuration,
               force=False,
               docker_build=False,
               output_stream=sys.stdout,
               verbose=False,
             ):
        with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                         done_prefix="\nResults: ",
                                                         done_suffix='\n',
                                                       ) as dm:
            configuration_key = configuration
            configuration = configurations[configuration_key]

            output_dir = _GetOutputDir(calling_dir, configuration_key)
            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            environment = Shell.GetEnvironment()

            # Prebuild funcs
            if pre_build_funcs:
                for pre_build_func in pre_build_funcs:
                    dm.result = pre_build_func(output_dir, dm.stream) or 0
                    if dm.result != 0:
                        return dm.result

            # Jinja2
            dm.stream.write("Executing template...")
            with dm.stream.DoneManager( done_suffix='\n',
                                      ) as this_dm:
                command_line = '"{script}" Generate "/input={input}" "/output_dir={output}" {context}{force}{verbose}' \
                                    .format( script="Jinja2CodeGenerator{}".format(environment.ScriptExtension),
                                             input=os.path.join(calling_dir, dockerfile),
                                             output=output_dir,
                                             context=' '.join([ '"/context={}:{}"'.format(k, v) for k, v in six.iteritems(configuration) ]),
                                             force=" /force" if force else '',
                                             verbose=" /verbose" if verbose else '',
                                           )

                this_dm.result = Process.Execute(command_line, this_dm.stream)
                if this_dm.result != 0:
                    return this_dm.result

            # Copy files
            if local_files:
                dm.stream.write("Copying files...")
                with dm.stream.DoneManager() as this_dm:
                    for index, filename in enumerate(local_files):
                        basename = os.path.basename(filename)

                        this_dm.stream.write("Copying '{}' ({} of {})...".format( basename,
                                                                                  index + 1,
                                                                                  len(local_files),
                                                                                ))
                        with this_dm.stream.DoneManager():
                            shutil.copyfile(os.path.join(calling_dir, filename), os.path.join(output_dir, basename))

            # Post build funcs
            if post_build_funcs:
                for post_build_func in post_build_funcs:
                    dm.result = post_build_func(output_dir, dm.stream) or 0
                    if dm.result != 0:
                        return dm.result

            # Docker build
            if docker_build:
                dm.stream.write("\nDocker build...")
                with dm.stream.DoneManager( done_suffix='\n',
                                          ) as this_dm:
                    this_dm.result = _DockerBuildImpl( name,
                                                       output_dir,
                                                       latest=False,
                                                       force=force,
                                                       output_stream=this_dm.stream,
                                                       verbose=verbose,
                                                     )
                    if this_dm.result != 0:
                        return this_dm.result

            return dm.result

    # ----------------------------------------------------------------------

    return Build

# ----------------------------------------------------------------------
def CreateCleanFunc( configurations,
                   ):
    calling_dir = _GetCallingDir()

    # ----------------------------------------------------------------------
    @CommandLine.EntryPoint
    @CommandLine.FunctionConstraints( configuration=CommandLine.EnumTypeInfo(configurations.keys()),
                                      output_stream=None,
                                    )
    def Clean( configuration,
               output_stream=sys.stdout,
               verbose=False,
             ):
        with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                         done_prefix="\nResults: ",
                                                         done_suffix='\n',
                                                       ) as dm:
            configuration_key = configuration
            configuration = configurations[configuration_key]

            output_dir = _GetOutputDir(calling_dir, configuration_key)

            FileSystem.RemoveTree(output_dir)

            return dm.result

    # ----------------------------------------------------------------------

    return Clean

# ----------------------------------------------------------------------
def CreateDockerBuild( name,
                       configurations,
                     ):
    calling_dir = _GetCallingDir()

    # ----------------------------------------------------------------------
    @CommandLine.EntryPoint
    @CommandLine.FunctionConstraints( configuration=CommandLine.EnumTypeInfo(configurations.keys()),
                                      output_stream=None,
                                    )
    def DockerBuild( configuration,
                     latest=False,
                     force=False,
                     output_stream=sys.stdout,
                     verbose=False,
                   ):
        with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                         done_prefix="\nResults: ",
                                                         done_suffix='\n',
                                                       ) as dm:
            output_dir = _GetOutputDir(calling_dir, configuration)

            return _DockerBuildImpl( name,
                                     output_dir,
                                     latest=latest,
                                     force=force,
                                     output_stream=dm.stream,
                                     verbose=verbose,
                                   )

    # ----------------------------------------------------------------------

    return DockerBuild

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _GetCallingDir():
    frame = inspect.stack()[2]
    module = inspect.getmodule(frame[0])
    
    calling_dir = os.path.dirname(os.path.realpath(module.__file__))
    assert os.path.isdir(calling_dir), calling_dir

    return calling_dir

# ----------------------------------------------------------------------
def _GetOutputDir(calling_dir, configuration):
    return os.path.join(calling_dir, "GeneratedCode", configuration)

# ----------------------------------------------------------------------
def _DockerBuildImpl( name,
                      output_dir,
                      latest,
                      force,
                      output_stream,
                      verbose,
                    ):
    tags = [ os.path.basename(output_dir),
           ]

    if latest:
        tags.append("latest")

    command_line = 'docker build "{output}" {tags}{force}' \
                        .format( output=output_dir,
                                 tags=' '.join([ '--tag {}:{}'.format(name, tag) for tag in tags ]),
                                 force=" --no-cache" if force else '',
                               )

    return Process.Execute(command_line, output_stream)
