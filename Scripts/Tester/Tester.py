# ---------------------------------------------------------------------------
# |  
# |  Tester.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/02/2015 08:43:44 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""\
Convience wrapper for TesterEx.
"""

import os
import re
import string
import sys
import textwrap

from collections import OrderedDict

import six

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import Compiler
from CommonEnvironment import Process
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment import Shell
from CommonEnvironment.StreamDecorator import StreamDecorator

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

assert os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")
sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
with CallOnExit(lambda: sys.path.pop(0)):
    from SourceRepositoryTools import DynamicPluginArchitecture as DPA

# ----------------------------------------------------------------------
StreamDecorator.InitAnsiSequenceStreams()

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
CONFIGURATIONS = OrderedDict()

# Extract configuration-specific information from other repositories. This ensures that this file,
# which is in the fundamental repo, doesn't take a dependency on repos that depend on this one.
#
# Expected format is a list of items delimited by the os-specific delimiter stored in an
# environment variable. Each item is in the form:
#
#       "<configuration name>-<compiler|test_parser|code_coverage>-<value>"

custom_configurations = os.getenv("DEVELOPMENT_ENVIRONMENT_TESTER_CONFIGURATIONS")
if custom_configurations:
    environment = Shell.GetEnvironment()

    regex = re.compile(textwrap.dedent(
       r"""(?#
                    )\s*"?(?#
        Name        )(?P<name>.+?)(?#
                    )\s*-\s*(?#
        Type        )(?P<type>(?:compiler|test_parser|code_coverage_extractor))(?#
                    )\s*-\s*(?#
        Value       )(?P<value>[^"]+)(?#
                    )"?\s*(?#
        )"""))

    configuration_map = OrderedDict()

    for configuration in [ item for item in custom_configurations.split(environment.EnvironmentVariableDelimiter) if item.strip() ]:
        match = regex.match(configuration)
        assert match, configuration

        configuration_name = match.group("name").lower()
        type_ = match.group("type")
        value = match.group("value")

        if configuration_name not in configuration_map:
            configuration_map[configuration_name] = {}

        if type_ in configuration_map[configuration_name]:
            if not isinstance(configuration_map[configuration_name][type_], list):
                configuration_map[configuration_name][type_] = [ configuration_map[configuration_name][type_], ]

            configuration_map[configuration_name][type_].append(value)
        else:
            configuration_map[configuration_name][type_] = value

    for key, item_map in six.iteritems(configuration_map):
        # compiler and test_parser are requried
        if "compiler" not in item_map or "test_parser" not in item_map:
            continue

        if isinstance(item_map["compiler"], list):
            compiler_info = [ ( "{}-{}".format(key, compiler),
                                compiler,
                              ) for compiler in item_map["compiler"]
                            ]

        elif isinstance(item_map["compiler"], str):
            compiler_info = [ ( key, item_map["compiler"] ),
                            ]

        else:
            assert False, type(item_map["compiler"])

        for key, compiler in compiler_info:
            CONFIGURATIONS[key] = QuickObject( standard_args=[ compiler, item_map["test_parser"], ],
                                               coverage_args=[ item_map.get("code_coverage_extractor", "Noop"), ],
                                             )

# ---------------------------------------------------------------------------
_UNIVERSAL_BASIC_FLAGS = []
_UNIVERSAL_CODE_COVERAGE_FLAGS = [ "/code_coverage_validator=Standard", ]

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( configuration=CommandLine.EnumTypeInfo(values=CONFIGURATIONS.keys()),
                                  filename_or_dir=CommandLine.FilenameTypeInfo(match_any=True),
                                  test_type=CommandLine.StringTypeInfo(min_length=0),
                                  output_dir=CommandLine.StringTypeInfo(min_length=0),
                                  iterations=CommandLine.IntTypeInfo(min=1),
                                  output_stream=None,
                                )
def Test( configuration,
          filename_or_dir,
          test_type='',
          output_dir='',
          iterations=1,
          debug_on_error=False,
          continue_iterations_on_error=False,
          code_coverage=False,
          debug_only=False,
          release_only=False,
          verbose=False,
          quiet=False,
          xml_output=False,
          no_status=False,
          output_stream=sys.stdout,
          print_command_line=False,
        ):
    assert configuration
    assert os.path.exists(filename_or_dir), filename_or_dir

    configuration = configuration.lower()
    assert configuration in CONFIGURATIONS, configuration

    if os.path.isdir(filename_or_dir):
        if not test_type:
            raise CommandLine.UsageException("The 'test_type' command line argument must be provided when 'filename_or_dir' is a directory.")

        if not output_dir:
            raise CommandLine.UsageException("The 'output_dir' command line argument must be provided when 'filename_or_dir' is a directory.")

    # Create the command line
    command_line = [ os.path.join(_script_dir, "TesterEx.py"), ]
    assert os.path.isfile(command_line[0]), command_line[0]

    if os.path.isdir(filename_or_dir):
        command_line += [ "ExecuteTree",
                          filename_or_dir,
                          test_type,
                          output_dir,
                        ]
    elif os.path.isfile(filename_or_dir):
        command_line += [ "Execute",
                          filename_or_dir,
                        ]
    else:
        assert False

    command_line += CONFIGURATIONS[configuration].standard_args

    if code_coverage:
        command_line += CONFIGURATIONS[configuration].coverage_args
        command_line += _UNIVERSAL_CODE_COVERAGE_FLAGS
    else:
        command_line.append("Noop")

    command_line += _UNIVERSAL_BASIC_FLAGS
    
    if debug_only:                          command_line.append("/debug_only")
    if release_only:                        command_line.append("/release_only")
    if verbose:                             command_line.append("/verbose")
    if quiet:                               command_line.append("/quiet")
    if xml_output:                          command_line.append("/xml_output")
    if iterations > 1:                      command_line.append("/iterations={}".format(iterations))
    if debug_on_error:                      command_line.append("/debug_on_error")
    if continue_iterations_on_error:        command_line.append("/continue_iterations_on_error")
    if no_status:                           command_line.append("/no_status")

    command_line.append("/preserve_ansi_escape_sequences")
    
    command_line = "python {}".format(' '.join([ '"{}"'.format(arg) for arg in command_line ]))

    if print_command_line:
        output_stream.write("Command Line:\n{}\n\n".format(command_line))

    return Process.ExecuteWithColorama( command_line,
                                        output_stream=output_stream,
                                      )
    
# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( input=CommandLine.FilenameTypeInfo(),
                                  output_dir=CommandLine.StringTypeInfo(min_length=0),
                                  iterations=CommandLine.IntTypeInfo(min=1),
                                  output_stream=None,
                                )
def TestFile( input,
              output_dir='',
              iterations=1,
              debug_on_error=False,
              continue_iterations_on_error=False,
              code_coverage=False,
              debug_only=False,
              release_only=False,
              verbose=False,
              quiet=False,
              xml_output=False,
              no_status=False,
              output_stream=sys.stdout,
              print_command_line=False,
            ):
    """Determines the configuration of the provided file and then runs its test."""
    
    # ---------------------------------------------------------------------------
    def GetConfiguration():
        compilers = [ Compiler.LoadFromModule(mod) for mod in DPA.EnumeratePlugins("DEVELOPMENT_ENVIRONMENT_COMPILERS") ]
        
        for configuration, arg_info in six.iteritems(CONFIGURATIONS):
            compiler_name = arg_info.standard_args[0]

            for potential_compiler in compilers:
                if potential_compiler.Name == compiler_name:
                    if potential_compiler.IsSupported(input):
                        return configuration

                    # No need to search the compilers any more since we found
                    # the compiler whose name matched the query.
                    break

        return None

    # ---------------------------------------------------------------------------
    
    configuration = GetConfiguration()
    if not configuration:
        sys.stderr.write("ERROR: Unable to find a configuration with a compiler that supports the file '{}'.\n".format(input))
        return -1

    return Test( configuration,
                 input,
                 test_type='',
                 output_dir=output_dir,
                 iterations=iterations,
                 debug_on_error=debug_on_error,
                 continue_iterations_on_error=continue_iterations_on_error,
                 code_coverage=code_coverage,
                 debug_only=debug_only,
                 release_only=release_only,
                 verbose=verbose,
                 quiet=quiet,
                 xml_output=xml_output,
                 no_status=no_status,
                 output_stream=output_stream,
                 print_command_line=print_command_line,
               )

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( configuration=CommandLine.EnumTypeInfo(values=CONFIGURATIONS.keys()),
                                  input_dir=CommandLine.DirectoryTypeInfo(),
                                  test_type=CommandLine.StringTypeInfo(),
                                  output_dir=CommandLine.StringTypeInfo(),
                                  iterations=CommandLine.IntTypeInfo(min=1),
                                  output_stream=None,
                                )
def TestType( configuration,
              input_dir,
              test_type,
              output_dir,
              iterations=1,
              debug_on_error=False,
              continue_iterations_on_error=False,
              code_coverage=False,
              debug_only=False,
              release_only=False,
              verbose=False,
              quiet=False,
              xml_output=False,
              no_status=False,
              output_stream=sys.stdout,
              print_command_line=False,
            ):
    """Runs tests of the specific type based on the subdir name provided."""
    
    assert os.path.isdir(input_dir), input_dir

    return Test( configuration,
                 input_dir,
                 test_type=test_type,
                 output_dir=output_dir,
                 iterations=iterations,
                 debug_on_error=debug_on_error,
                 continue_iterations_on_error=continue_iterations_on_error,
                 code_coverage=code_coverage,
                 debug_only=debug_only,
                 release_only=release_only,
                 verbose=verbose,
                 quiet=quiet,
                 xml_output=xml_output,
                 no_status=no_status,
                 output_stream=output_stream,
                 print_command_line=print_command_line,
               )

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( input_dir=CommandLine.DirectoryTypeInfo(),
                                  test_type=CommandLine.StringTypeInfo(),
                                  output_dir=CommandLine.FilenameTypeInfo(ensure_exists=False),
                                  iterations=CommandLine.IntTypeInfo(min=1),
                                  output_stream=None,
                                )
def TestAll( input_dir,
             test_type,
             output_dir,
             iterations=1,
             debug_on_error=False,
             continue_iterations_on_error=False,
             code_coverage=False,
             debug_only=False,
             release_only=False,
             verbose=False,
             quiet=False,
             xml_output=False,
             no_status=False,
             output_stream=sys.stdout,
             print_command_line=False,
           ):
    with StreamDecorator(output_stream).DoneManager( done_prefix="\n\nComposite Results: ",
                                                     line_prefix='',
                                                   ) as dm:
        for index, configuration in enumerate(six.iterkeys(CONFIGURATIONS)):
            desc = "Testing '{}' ({} of {})...".format( configuration,
                                                        index + 1,
                                                        len(CONFIGURATIONS),
                                                      )
            dm.stream.write("{}\n{}\n{}\n".format( '-' * len(desc), 
                                                   desc, 
                                                   '-' * len(desc),
                                                 ))

            with dm.stream.DoneManager( line_prefix='',
                                        done_prefix="\n{} Results: ".format(configuration),
                                        done_suffix="\n",
                                      ) as this_dm:
                this_dm.result = TestType( configuration,
                                           input_dir,
                                           test_type,
                                           output_dir,
                                           iterations=iterations,
                                           debug_on_error=debug_on_error,
                                           continue_iterations_on_error=continue_iterations_on_error,
                                           code_coverage=code_coverage,
                                           debug_only=debug_only,
                                           release_only=release_only,
                                           verbose=verbose,
                                           quiet=quiet,
                                           xml_output=xml_output,
                                           no_status=no_status,
                                           output_stream=this_dm.stream,
                                           print_command_line=print_command_line,
                                         )

        return dm.result

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( configuration=CommandLine.EnumTypeInfo(values=CONFIGURATIONS.keys()),
                                  input_dir=CommandLine.DirectoryTypeInfo(),
                                  test_type=CommandLine.StringTypeInfo(),
                                  output_stream=None,
                                )
def MatchTests( configuration,
                input_dir,
                test_type,
                output_stream=sys.stdout,
                verbose=False,
              ):
    return Process.ExecuteWithColorama( 'python "{script}" MatchTests "{dir}" "{test_type}" {compiler}{verbose}' \
                                            .format( script=os.path.join(_script_dir, "TesterEx.py"),
                                                     dir=input_dir,
                                                     test_type=test_type,
                                                     compiler=CONFIGURATIONS[configuration].standard_args[0],
                                                     verbose='' if not verbose else " /verbose",
                                                   ),
                                        output_stream=output_stream,
                                      )
    
# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( input_dir=CommandLine.DirectoryTypeInfo(),
                                  test_type=CommandLine.StringTypeInfo(),
                                  output_stream=None,
                                )
def MatchAllTests( input_dir,
                   test_type,
                   output_stream=sys.stdout,
                   verbose=False,
                 ):
    with StreamDecorator(output_stream).DoneManager( done_prefix="\n\nComposite Results: ",
                                                     line_prefix='',
                                                   ) as dm:
        for index, configuration in enumerate(six.iterkeys(CONFIGURATIONS)):
            dm.stream.write("Matching '{}' ({} of {})...".format( configuration, 
                                                                  index + 1, 
                                                                  len(CONFIGURATIONS),
                                                                ))
            with dm.stream.DoneManager(line_prefix="    ") as this_dm:
                this_dm.result = MatchTests( configuration,
                                             input_dir,
                                             test_type,
                                             output_stream=this_dm.stream,
                                             verbose=verbose,
                                           )

        return dm.result

# ---------------------------------------------------------------------------
def CommandLineSuffix():
    return StreamDecorator.LeftJustify( textwrap.dedent(
                                            """\
                                            Where <configuration> can be:
                                            {}

                                            """).format('\n'.join([ "    - {}".format(config) for config in six.iterkeys(CONFIGURATIONS) ])),
                                        4,
                                        skip_first_line=False,
                                      )

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
