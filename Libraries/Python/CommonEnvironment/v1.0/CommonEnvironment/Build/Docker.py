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
import json
import os
import re
import shutil
import sys
import textwrap
import time
import uuid

import six

from CommonEnvironment import Listify
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment import Shell
from CommonEnvironment import SourceControlManagement
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
            if not _VerifyDocker():
                dm.stream.write("ERROR: Ensure that docker is installed and available within this environment.\n")
                dm.result = -1

                return dm.result
            
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
def CreateRepositoryBuildFunc( repository_name,
                               repository_uri,
                               docker_account_name,
                               docker_image_name,
                               base_docker_image,
                               maintainer,
                               no_activation=False,
                               repository_setup_configurations=None,
                               repository_activation_configurations=None,
                               repository_source_excludes=None,
                             ):
    """\
    Creates a build function that is able to build repository-based Docker images.
    To use this functionality, the dockerfile template MUST include the variable

        {{ repository_content }}

    This template will be populated by different values during the build process.

    At least 2 docker images will be created:

        1) A "_base" image that has setup the environment but not activated it.
        2+) Images that have been activated (optionally based on a configuration)
        
    """

    calling_dir = _GetCallingDir()
    repository_activation_configurations = repository_activation_configurations or [ None, ]

    # ----------------------------------------------------------------------
    @CommandLine.EntryPoint
    @CommandLine.FunctionConstraints( output_stream=None,
                                    )
    def Build( force=False,
               no_squash=False,
               keep_temp_image=False,
               username="user",
               groupname="codegroup",
               output_stream=sys.stdout,
               verbose=False,
             ):
        # TODO: Runas user

        with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                         done_prefix="\nResults: ",
                                                         done_suffix='\n',
                                                       ) as dm:
            if not _VerifyDocker():
                dm.stream.write("ERROR: Ensure that docker is installed and available within this environment.\n")
                dm.result = -1

                return dm.result

            output_dir = os.path.join(calling_dir, "Generated")
            
            source_dir = os.path.join(output_dir, "Source")
            base_dir = os.path.join(output_dir, "Base")
            activated_dir = os.path.join(output_dir, "Activated")

            image_code_base = "/usr/lib/DavidBrownell"
            image_code_dir = "{}/{}".format( image_code_base,
                                             repository_name.replace('_', '/'),
                                           )

            now = time.localtime()
            now_tag = "{0}.{1:02d}.{2:02d}".format(now[0], now[1], now[2])

            environment = Shell.GetEnvironment()

            # Create the base image
            dm.stream.write("Creating base image...")
            with dm.stream.DoneManager( done_suffix='\n',
                                      ) as this_dm:
                # Verify that base image exists
                this_dm.result, output = Process.Execute('docker image history "{}"'.format(base_docker_image))
                if this_dm.result != 0:
                    this_dm.stream.write("ERROR: The image '{}' doesn't exist.\n".format(base_docker_image))
                    return this_dm.result

                FileSystem.MakeDirs(base_dir)

                # Get the full source code
                scm = SourceControlManagement.GetSCMEx(calling_dir)
                has_changes = True

                if os.path.isdir(source_dir):
                    this_dm.stream.write("Updating source...")
                    with this_dm.stream.DoneManager() as update_dm:
                        update_dm.result, output = scm.Pull(source_dir)
                        if update_dm.result != 0:
                            update_dm.stream.write(output)
                            return update_dm.result

                        if "no changes found" in output:
                            # TODO: This only works for Mercurial
                            has_changes = False
                        else:
                            update_dm.result, output = scm.Update(source_dir, SourceControlManagement.EmptyUpdateMergeArg())
                            if update_dm.result != 0:
                                update_dm.stream.write(output)
                                return update_dm.result
                        
                else:
                    if not os.path.isdir(os.path.dirname(source_dir)):
                        os.makedirs(os.path.dirname(source_dir))

                    this_dm.stream.write("Cloning source...")
                    with this_dm.stream.DoneManager() as clone_dm:
                        temp_dir = environment.CreateTempDirectory()

                        clone_dm.result, output = scm.Clone(repository_uri, temp_dir)
                        if clone_dm.result != 0:
                            clone_dm.stream.write(output)
                            return clone_dm.result

                        os.rename(temp_dir, source_dir)

                # Filter the source
                filtered_dir = os.path.join(base_dir, "Filtered")
                        
                if os.path.isdir(filtered_dir) and not force and not has_changes:
                    this_dm.stream.write("No changes were detected.\n")
                else:
                    with this_dm.stream.SingleLineDoneManager( "Filtering source...",
                                                             ) as copy_dm:
                        temp_dir = environment.CreateTempDirectory()
                        FileSystem.RemoveTree(temp_dir)
                        
                        FileSystem.CopyTree( source_dir,
                                             temp_dir,
                                             excludes=[ "/.git",
                                                        "/.gitignore",
                                                        "/.hg",
                                                        "/.hgignore",
                        
                                                        "*/Generated",
                                                        "*/__pycache__",
                                                        "*/Windows",
                                                        "/*/src",
                        
                                                        "*.cmd",
                                                        "*.pyc",
                                                        "*.pyo",
                                                      ] + (repository_source_excludes or []),
                                             output_stream=copy_dm.stream,
                                           )
                        
                        FileSystem.RemoveTree(filtered_dir)
                        
                        os.rename(temp_dir, filtered_dir)

                # Create the dockerfile
                this_dm.stream.write("Creating dockerfile...")
                with this_dm.stream.DoneManager():
                    if "baseimage" in base_docker_image:
                        foundation_commands = textwrap.dedent(
                            """\
                            RUN link /usr/bin/python3 /usr/bin/python
                            """)
                    else:
                        foundation_commands = ''

                    with open(os.path.join(base_dir, "Dockerfile"), 'w') as f:
                        f.write(textwrap.dedent(
                            """\
                            FROM {base_image}

                            CMD [ "/sbin/my_init" ]

                            {foundation_commands}

                            COPY Filtered {image_code_dir}

                            RUN cd {image_code_dir} \\
                             && ./SetupEnvironment.sh {configurations}

                            LABEL maintainer="{maintainer}"

                            RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
                            """).format( base_image=base_docker_image,
                                         foundation_commands=foundation_commands,
                                         image_code_dir=image_code_dir,
                                         configurations='' if not repository_setup_configurations else ' '.join([ '"/configuration={}"'.format(config) for config in repository_setup_configurations ]),
                                         maintainer=maintainer,
                                       ))

                # Build the image
                this_dm.stream.write("\nBuilding Docker image...")
                with this_dm.stream.DoneManager() as docker_dm:
                    base_docker_image_name = "{}/{}_base".format( docker_account_name,
                                                                  docker_image_name,
                                                                )

                    command_line = 'docker build "{dir}" --tag "{name}:latest" --tag "{name}:{now_tag}"{squash}{force}' \
                                        .format( dir=base_dir,
                                                 name=base_docker_image_name,
                                                 now_tag=now_tag,
                                                 squash='' if no_squash else " --squash",
                                                 force=" --no-cache" if force else '',
                                               )

                    docker_dm.result = Process.Execute(command_line, docker_dm.stream)
                    if docker_dm.result != 0:
                        return docker_dm.result
                                                    
            if not no_activation:
                # Create the activated image(s)
                for index, configuration in enumerate(repository_activation_configurations):
                    dm.stream.write("Creating activated image{} ({} of {})...".format( '' if not configuration else " for the configuration '{}'".format(configuration),
                                                                                       index + 1,
                                                                                       len(repository_activation_configurations),
                                                                                     ))
                    with dm.stream.DoneManager( done_suffix='\n',
                                              ) as this_dm:
                        this_activated_dir = os.path.join(activated_dir, configuration or "Default")
                        FileSystem.MakeDirs(this_activated_dir)

                        unique_id = str(uuid.uuid4())

                        temp_image_name = "{}_image".format(unique_id)
                        temp_container_name = "{}_container".format(unique_id)

                        # Activate the image
                        this_dm.stream.write("Activating...")
                        with this_dm.stream.DoneManager() as extract_dm:
                            command_line = 'docker run -it --name "{container_name}" "{docker_account_name}/{image_name}_base:latest" bash -c "cd {image_code_dir} && . ./ActivateEnvironment.sh {configuration} && python {image_code_base}/Common/Environment/SourceRepositoryTools/Impl/ActivateEnvironment.py EnvironmentDiffs"' \
                                                .format( container_name=temp_container_name,
                                                         docker_account_name=docker_account_name,
                                                         image_name=docker_image_name,
                                                         configuration=configuration or '',
                                                         image_code_dir=image_code_dir,
                                                         image_code_base=image_code_base,
                                                       )
                                                       
                            extract_dm.result, output = Process.Execute(command_line)
                
                            if extract_dm.result != 0:
                                extract_dm.stream.write(output)
                                return extract_dm.result
                
                            # Get the environment diffs
                            match = re.search( textwrap.dedent(
                                                    """\
                                                    ////////////////////////////////////////////////////////////////////////////////
                                                    (?P<content>.+?)
                                                    ////////////////////////////////////////////////////////////////////////////////
                                                    """),
                                               output,
                                               re.MULTILINE | re.DOTALL,
                                             )
                            assert match, output
                            environment_diffs = json.loads(match.group("content"))
                                      
                        # ----------------------------------------------------------------------
                        def RemoveTempContainer():
                            this_dm.stream.write("Removing temp container...")
                            with this_dm.stream.DoneManager() as remove_dm:
                                remove_dm.result, output = Process.Execute('docker rm "{}"'.format(temp_container_name))
                                if remove_dm.result != 0:
                                    remove_dm.stream.write(output)
                
                        # ----------------------------------------------------------------------
                
                        with CallOnExit(RemoveTempContainer):
                            # Commit the activate image
                            this_dm.stream.write("Committing...")
                            with this_dm.stream.DoneManager() as commit_dm:
                                command_line = 'docker commit {container_name} {image_name}' \
                                                    .format( container_name=temp_container_name,
                                                             image_name=temp_image_name,
                                                           )
                
                                commit_dm.result, output = Process.Execute(command_line)
                
                                if commit_dm.result != 0:
                                    commit_dm.stream.write(output)
                                    return commit_dm.result
                
                            # ----------------------------------------------------------------------
                            def RemoveTempImage():
                                if keep_temp_image:
                                    return

                                this_dm.stream.write("Removing temp activated image...")
                                with this_dm.stream.DoneManager() as remove_dm:
                                    remove_dm.result, output = Process.Execute('docker rmi "{}"'.format(temp_image_name))
                                    if remove_dm.result != 0:
                                        remove_dm.stream.write(output)
                
                            # ----------------------------------------------------------------------
                            
                            with CallOnExit(RemoveTempImage):
                                # Create the new dockerfile
                                this_dm.stream.write("Creating dockerfile...")
                                with this_dm.stream.DoneManager():
                                    with open(os.path.join(this_activated_dir, "Dockerfile"), 'w') as f:
                                        f.write(textwrap.dedent(
                                            """\
                                            FROM {temp_image_name}
                                            
                                            # Restrict access to files
                                            RUN adduser --disabled-password --disabled-login --gecos "" "{username}" \\
                                             && addgroup "{groupname}" \\
                                             && adduser "{username}" "{groupname}" \\
                                             && chown -R "{username}:{groupname}" "{image_code_base}" \\
                                             && chmod -R o-rwx "{image_code_base}"

                                            ENV {env}

                                            LABEL maintainer="{maintainer}"

                                            # The following code ensures that the user is logged in as the appropriate 
                                            # user in a bash prompt as the default behavior.
                                            CMD [ "/sbin/my_init", "/sbin/setuser", "{username}", "bash" ]
                                            WORKDIR {image_code_dir}
                                            
                                            """).format( temp_image_name=temp_image_name,
                                                         env='\\\n'.join([ '  {}={} '.format(k, v) for k, v in six.iteritems(environment_diffs) ]),
                                                         image_code_base=image_code_base,
                                                         image_code_dir=image_code_dir,                             
                                                         maintainer=maintainer,
                                                         username=username,
                                                         groupname=groupname,
                                                       ))
                                
                                this_dm.stream.write("\nBuilding Docker image...")
                                with this_dm.stream.DoneManager() as docker_dm:
                                    name = "{}/{}".format( docker_account_name,
                                                           docker_image_name,
                                                         )
                                    if configuration:
                                        name += "_{}".format(configuration)
                                
                                    command_line = 'docker build "{dir}" --tag "{name}:latest" --tag "{name}:{now_tag}"{squash}{force}' \
                                                        .format( dir=this_activated_dir,
                                                                 name=name,
                                                                 now_tag=now_tag,
                                                                 squash='' if no_squash else " --squash",
                                                                 force=" --no-cache" if force else '',
                                                               )
                                
                                    docker_dm.result = Process.Execute(command_line, docker_dm.stream)
                                    if docker_dm.result != 0:
                                        return docker_dm.result

            return dm.result

    # ----------------------------------------------------------------------

    return Build

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
def _VerifyDocker():
    result, output = Process.Execute("docker version")
    return "Client:" in output and "Server:" in output

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
