# ---------------------------------------------------------------------------
# |  
# |  TesterEx.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/04/2015 05:26:32 PM
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
General purpose test executor. See Tester for a simplier command line interface.
"""

import colorama
import inflect
import os
import multiprocessing
import re
import sys
import tempfile
import textwrap
import threading
import traceback

from StringIO import StringIO

from xml.etree import ElementTree as ET

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import Compiler
from CommonEnvironment import FileSystem
from CommonEnvironment import Package
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment import Shell
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import TaskPool
from CommonEnvironment.TimeDelta import TimeDelta

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

assert os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")
sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
with CallOnExit(lambda: sys.path.pop(0)):
    from SourceRepositoryTools import DynamicPluginArchitecture as DPA

with Package.NameInfo(__package__) as ni:
    __package__ = ni.created

    from .Impl.CompleteResults import CompleteResults

    __package__ = ni.original

pluralize = inflect.engine()

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
TEST_IGNORE_FILENAME_TEMPLATE = "{}-ignore"

COMPILERS = [ Compiler.LoadFromModule(mod) for mod in DPA.EnumeratePlugins("DEVELOPMENT_ENVIRONMENT_COMPILERS") ]
TEST_PARSERS = [ mod.TestParser for mod in DPA.EnumeratePlugins("DEVELOPMENT_ENVIRONMENT_TEST_PARSERS") ]
CODE_COVERAGE_EXTRACTORS = [ mod.CodeCoverageExtractor for mod in DPA.EnumeratePlugins("DEVELOPMENT_ENVIRONMENT_CODE_COVERAGE_EXTRACTORS") ]
CODE_COVERAGE_VALIDATORS = [ mod.CodeCoverageValidator for mod in DPA.EnumeratePlugins("DEVELOPMENT_ENVIRONMENT_CODE_COVERAGE_VALIDATORS") ]

_CompilerTypeInfo = CommandLine.EnumTypeInfo(values=[ compiler.Name for compiler in COMPILERS ] + [ str(i) for i in xrange(1, len(COMPILERS) + 1) ])
_TestParserTypeInfo = CommandLine.EnumTypeInfo(values=[ test_parser.Name for test_parser in TEST_PARSERS ] + [ str(i) for i in xrange(1, len(TEST_PARSERS) + 1) ])
_CodeCoverageExtractorTypeInfo = CommandLine.EnumTypeInfo(values=[ code_coverage_extractor.Name for code_coverage_extractor in CODE_COVERAGE_EXTRACTORS ] + [ str(i) for i in xrange(1, len(CODE_COVERAGE_EXTRACTORS) + 1) ])
_CodeCoverageValidatorTypeInfo = CommandLine.EnumTypeInfo(values=[ code_coverage_validator.Name for code_coverage_validator in CODE_COVERAGE_VALIDATORS ] + [ str(i) for i in xrange(1, len(CODE_COVERAGE_VALIDATORS) + 1) ])

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
def Test( test_items,
          output_dir,
          compiler,
          test_parser,
          code_coverage_extractor,
          code_coverage_validator,
          execute_in_parallel=False,
          iterations=1,
          continue_iterations_on_error=False,
          debug_on_error=False,
          max_num_concurrent_tasks=multiprocessing.cpu_count(),
          output_stream=sys.stdout,
          debug_only=False,
          release_only=False,
        ):
    assert test_items
    assert output_dir
    assert compiler
    assert test_parser
    assert code_coverage_extractor
    assert code_coverage_validator
    assert iterations > 0, iterations
    assert max_num_concurrent_tasks > 0, max_num_concurrent_tasks
    assert output_stream

    # Check for congruent plugins
    result = compiler.ValidateEnvironment()
    if result:
        output_stream.write("ERROR: The current environment is not supported by the compiler '{}': {}.\n".format(compiler.Name, result))
        return []

    result = code_coverage_extractor.ValidateEnvironment()
    if result:
        output_stream.write("ERROR: The current environment is not supported by the code coverage extractor '{}': {}.\n".format(code_coverage_extractor.Name, result))
        return []

    if not test_parser.IsSupportedCompiler(compiler):
        raise Exception("The test parser '{}' does not support the compiler '{}'".format(test_parser.Name, compiler.Name))

    if not code_coverage_extractor.IsSupportedCompiler(compiler):
        raise Exception("The code coverage extractor '{}' does not support the compiler '{}'".format(code_coverage_extractor.Name, compiler.Name))

    # Prepare the environment
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    # Ensure that we only build debug with code coverage
    is_valid_code_coverage_extractor = (code_coverage_extractor.Name != "Noop")
    if is_valid_code_coverage_extractor:
        execute_in_parallel = False

        if compiler.IsCompiler:
            debug_only = True
            release_only = False

    # ---------------------------------------------------------------------------
    # |  Prepare the results
    results = []

    if len(test_items) == 1:
        common_prefix = FileSystem.GetCommonPath(test_items[0], os.path.abspath(os.getcwd()))
    else:
        common_prefix = FileSystem.GetCommonPath(*test_items)

    for test_item in test_items:
        if not compiler.IsSupported(test_item):
            continue

        # The base name used for all output for this particular test is based on the name
        # of the test itself.
        base_output_name = test_item
        if common_prefix:
            assert base_output_name.startswith(common_prefix), (base_output_name, common_prefix)
            base_output_name = base_output_name[len(common_prefix):]

        for bad_char in [ '\\', '/', ':', '*', '?', '"', '<', '>', '|', ]:
            base_output_name = base_output_name.replace(bad_char, '_')

        # Trim output names that are larger, as this will cause problems on Windows systems
        if Shell.GetEnvironment().Name == "Windows":
            while len(base_output_name) > 150:
                # The logic here assumes that the differentiating parts of the filename appear
                # at the end of the filename, meaning we should remove content towards the
                # start of the name. This may cause collisions.
                base_output_name = "{}...{}".format(base_output_name[:15], base_output_name[45:])

        final_output_name = os.path.join(output_dir, base_output_name)

        results.append(QuickObject( complete_results=CompleteResults(test_item),
                                    output_base_name=final_output_name,
                                    execution_lock=threading.Lock(),
                                  ))

    # ---------------------------------------------------------------------------
    # |  Compile
    for result in results:
        # Note that some compilers rely on COM, which has zany threading perversions which require
        # that dependent code run on specific threads. Therefore, we are creating context here in the 
        # main thread rather than delaying the creation to the thread which is closer to the location
        # in which the context is actually used.

        # ---------------------------------------------------------------------------
        def PopulateResults(results, flavor, is_debug):
            output_dir = os.path.join(result.output_base_name, flavor)
            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            if compiler.IsVerifier:
                results.compiler_binary = result.complete_results.Item
            else:
                results.compile_binary = os.path.join(output_dir, "test")
                ext = getattr(compiler, "BinaryExtension", None)
                if ext:
                    results.compile_binary += ext

            results.compile_log = os.path.join(output_dir, "compile.txt")

            results.context = compiler.GenerateContextItem( result.complete_results.Item,
                                                            is_debug=is_debug,
                                                            is_profile=is_valid_code_coverage_extractor,
                                                            output_filename=results.compile_binary,
                                                            force=True,
                                                          )

            # Context mey be None if it has been disabled for this specific environment
            if results.context == None:
                results.compile_binary = None

        # ---------------------------------------------------------------------------
        
        if not release_only or not compiler.IsCompiler: 
            PopulateResults(result.complete_results.debug, "Debug", True)

        if not debug_only and compiler.IsCompiler:
            PopulateResults(result.complete_results.release, "Release", False)
    
    # ---------------------------------------------------------------------------
    def BuildThreadProc(index, out):
        result = results[index % len(results)]

        with result.execution_lock:
            flavor_results = result.complete_results.release if index >= len(results) else result.complete_results.debug

            if flavor_results.context == None:
                return

            start_time = TimeDelta()

            try:
                sink = StringIO()

                if compiler.IsCompiler:
                    compile_result = compiler.Compile(flavor_results.context, sink)
                    compiler.RemoveTemporaryArtifacts(flavor_results.context)
                elif compiler.IsCodeGenerator:
                    compile_result = compiler.Generate(flavor_results.context, sink)
                elif compiler.IsVerifier:
                    compile_result = compiler.Verify(flavor_results.context, sink)
                else:
                    assert False, compiler.Name

                compile_output = sink.getvalue()

                if compile_result != 0:
                    out.write(compile_output)

            except:
                compile_result = -1
                compile_output = traceback.format_exc()

                raise

            flavor_results.compile_result = compile_result
            flavor_results.compile_time = start_time.CalculateDelta(as_string=True)

            with open(flavor_results.compile_log, 'w') as f:
                f.write(compile_output.replace('\r\n', '\n'))

            return compile_result

    # ---------------------------------------------------------------------------
    
    debug_tasks = []
    release_tasks = []

    for result in results:
        # Rather than add the tasks back-to-back, add all of the debug tasks followed
        # by all the release tasks. This will help avoid potential build issues
        # associated with building the same app with slightly different output.
        debug_tasks.append(TaskPool.Task( result.complete_results.Item,
                                          "Building '{}' [Debug]".format(result.complete_results.Item),
                                          BuildThreadProc,
                                        ))

        release_tasks.append(TaskPool.Task( result.complete_results.Item,
                                            "Building '{}' [Release]".format(result.complete_results.Item),
                                            BuildThreadProc,
                                          ))

    # If the compiler operates on individual files, we can execute them in parallel. If
    # the compiler doesn't operate on files, we have to execute them one at a time, as we
    # can't make assumptions about what the compiler is doing or the files that it modifies.
    TaskPool.Execute( tasks=debug_tasks + release_tasks,
                      num_concurrent_tasks=max_num_concurrent_tasks if compiler.Type == compiler.TypeValue.File else 1,
                      output_stream=output_stream,
                    )

    # ---------------------------------------------------------------------------
    # |  Execute

    # Calculate the tests to run
    test_info_list = []
    test_tasks = []

    # ---------------------------------------------------------------------------
    def TestThreadProc(index, out):
        test_info = test_info_list[index / iterations]

        # Don't continue on error unless explicitly requested
        if ( not continue_iterations_on_error and 
             test_info.result.test_parse_result != None and 
             test_info.result.test_parse_result != 0
           ):
            return

        iteration = (index % iterations) + 1

        # ---------------------------------------------------------------------------
        def WriteLog(log_name, content):
            if content == None:
                return

            log_filename = os.path.join( test_info.output_base_name,
                                         test_info.flavor,
                                         "{0}.{1:06d}.txt".format(log_name, iteration),
                                       )

            with open(log_filename, 'w') as f:
                f.write(content.replace('\r\n', '\n'))

            return log_filename

        # ---------------------------------------------------------------------------
        
        final_result = 0

        try:
            execute_command_line = test_parser.CreateInvokeCommandLine(test_info.result.context, debug_on_error)
            
            execute_result = code_coverage_extractor.Execute( compiler, 
                                                              test_info.result.context,
                                                              execute_command_line, 
                                                            )

            # Copy the test results
            test_info.result.test_result = execute_result.test_result
            test_info.result.test_time = execute_result.test_duration
            test_info.result.test_log = WriteLog("test", execute_result.test_output)

            final_result = final_result or test_info.result.test_result

        except:
            output = traceback.format_exc()

            test_info.result.test_result = -1
            test_info.result.test_log = WriteLog("test", output)

            out.write(output)

            return -1

        # Copy the code coverage information
        test_info.result.coverage_data = execute_result.data
        test_info.result.coverage_result = execute_result.coverage_result
        test_info.result.coverage_log = WriteLog("code_coverage_extractor", execute_result.coverage_output)
        test_info.result.coverage_time = execute_result.coverage_duration
        test_info.result.coverage_percentage = execute_result.total_percentage
        test_info.result.coverage_percentages = execute_result.individual_percentages

        final_result = final_result or test_info.result.coverage_result

        # Code coverage validation information
        if test_info.result.coverage_result != None:
            try:
                coverage_result = code_coverage_validator.Validate(test_info.test_item, test_info.result.coverage_percentage)

                test_info.result.coverage_validation_result = coverage_result[0]
                test_info.result.coverage_validation_min = coverage_result[1]

            except:
                test_info.result.coverage_validation_result = -1

            final_result = final_result or test_info.result.coverage_validation_result

        # Parse test results
        start_time = TimeDelta()

        test_parse_result = test_parser.Parse(execute_result.test_output)
        test_parse_time = start_time.CalculateDelta(as_string=True)

        if test_parse_result != 0:
            out.write(execute_result.test_output)

        if test_info.result.test_parse_result == None or test_info.result.test_parse_result == 0:
            test_info.result.test_parse_result = test_parse_result
            test_info.result.test_parse_time = test_parse_time
            final_result = final_result or test_info.result.test_parse_result
            
        return final_result

    # ---------------------------------------------------------------------------
    def EnqueueTestIfNecessary( result,
                                flavor,
                                test_item,
                                output_base_name,
                              ):
        if result.context == None or result.compile_result != 0:
            return

        test_info_list.append(QuickObject( result=result,
                                           flavor=flavor,
                                           test_item=test_item,
                                           output_base_name=output_base_name,
                                           should_continue=True,
                                         ))

        for iteration in xrange(1, iterations + 1):
            additional_desc = ''

            if iterations > 1:
                additional_desc = " - Iteration {} of {}".format(iteration, iterations)

            test_tasks.append(TaskPool.Task( test_item,
                                             "Executing '{}' [{}]{}".format(result.compile_binary or test_item, flavor, additional_desc),
                                             TestThreadProc,
                                           ))

    # ---------------------------------------------------------------------------
    
    for result in results:
        EnqueueTestIfNecessary(result.complete_results.debug, "Debug", result.complete_results.Item, result.output_base_name)
        EnqueueTestIfNecessary(result.complete_results.release, "Release", result.complete_results.Item, result.output_base_name)

    if test_tasks:
        output_stream.write('\n')

        TaskPool.Execute( tasks=test_tasks,
                          num_concurrent_tasks=max_num_concurrent_tasks if execute_in_parallel else 1,
                          output_stream=output_stream,
                        )

    return [ result.complete_results for result in results ]

# ---------------------------------------------------------------------------
def ExtractTestItems( input_dir,
                      test_subdir,
                      compiler,
                      verbose_stream=None,
                    ):
    assert os.path.isdir(input_dir), input_dir
    assert test_subdir
    assert compiler

    verbose_stream = StreamDecorator(verbose_stream, prefix='\n', line_prefix='  ')

    traverse_exclude_dir_names = [ "Generated", ]

    test_items = []

    if compiler.Type == compiler.TypeValue.File:
        for fullpath in FileSystem.WalkFiles( input_dir,
                                              include_dir_names=[ test_subdir, ],
                                              traverse_exclude_dir_names=traverse_exclude_dir_names,
                                            ):
            if os.path.isfile(TEST_IGNORE_FILENAME_TEMPLATE.format(fullpath)):
                continue

            if compiler.IsSupported(fullpath) and compiler.IsSupportedTestFile(fullpath):
                test_items.append(fullpath)
            else:
                verbose_stream.write("'{}' is not supported by the compiler.\n".format(fullpath))

    elif compiler.Type == compiler.TypeValue.Directory:
        search_string = ".{}.".format(test_subdir)

        for root, filenames in FileSystem.WalkDirs( input_dir,
                                                    include_dir_names=[ lambda d: search_string in d, ],
                                                    traverse_exclude_dir_names=traverse_exclude_dir_names,
                                                  ):
            if os.path.isfile(TEST_IGNORE_FILENAME_TEMPLATE.format(root)):
                continue

            if compiler.IsSupported(root):
                test_items.append(root)
            else:
                verbose_stream.write("'{}' is not supported by the compiler.\n".format(root))

    else:
        assert False, (compiler.Name, compiler.Type)
     
    return test_items

# ---------------------------------------------------------------------------
def PrettyPrint( complete_results,
                 compiler,
                 test_parser,
                 code_coverage_extractor,
                 code_coverage_validator,
                 output_stream,
                 preserve_ansi_escape_sequences,
                 verbose,
               ):
    pretty_print = _ShouldPrettyPrint(output_stream)

    if pretty_print:
        colorama.init( autoreset=True,
                       strip=(not preserve_ansi_escape_sequences),
                       convert=(not preserve_ansi_escape_sequences),
                     )

        output_stream = sys.stdout

        result_re = re.compile(r"(?P<prefix>(?P<header>.*?)Result:\s+)(?P<value>.+)")

    # ---------------------------------------------------------------------------
    def WriteVerboseResults(name, results):
        
        if results == None:
            return

        # ---------------------------------------------------------------------------
        def WriteContent(header, filename):
            if filename == None or not os.path.isfile(filename):
                return

            output_stream.write(textwrap.dedent(
                """\

                --------------------------------------------------------------------------------
                | {name:<77}|
                --------------------------------------------------------------------------------
                {content}
                """).format( name="{} <{}>".format(name, header),
                             content=open(filename).read().strip(),
                           ))

        # ---------------------------------------------------------------------------
        
        WriteContent("Compile Log", results.compile_log)
        WriteContent("Execution Log", results.test_log)
        WriteContent("Code Coverage Log", results.coverage_log)

    # ---------------------------------------------------------------------------
    def ToColorString(value):
        value = value.lower()

        if value.startswith("succeeded"):
            color = colorama.Fore.GREEN
        elif value.startswith("failed"):
            color = colorama.Fore.RED
        elif value.startswith("unknown"):
            color = colorama.Fore.YELLOW
        elif value.startswith("n/a"):
            color = colorama.Fore.WHITE
        else:
            color = ''

        if color:
            color += colorama.Style.BRIGHT

        return color

    # ---------------------------------------------------------------------------
    
    for complete_result in complete_results:
        result_data = complete_result.ToString( compiler,
                                                test_parser,
                                                code_coverage_extractor,
                                                code_coverage_validator,
                                              )

        if not pretty_print:
            output_stream.write("\n{}".format(result_data))
            continue
    
        for line in result_data.split('\n'):
            line = "{}\n".format(line)

            if ( line.startswith("==") or 
                 line.startswith("--") or 
                 (len(line) >= 3 and line[0] == '|' and line[-2] == '|')
               ):
                output_stream.write(colorama.Fore.WHITE + colorama.Style.BRIGHT + line)
                continue

            match = result_re.match(line)
            if not match:
                output_stream.write(colorama.Fore.WHITE + colorama.Style.NORMAL + line)
                continue

            prefix = match.group("prefix")
            value = match.group("value")

            color_string = ToColorString(value)

            if not match.group("header").strip():
                output_stream.write("{}{}".format(color_string, prefix))
            else:
                output_stream.write(prefix)

            output_stream.write("{}{}\n".format(color_string, value))

        if verbose:
            WriteVerboseResults("Debug", complete_result.debug)
            WriteVerboseResults("Release", complete_result.release)

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
@CommandLine.EntryPoint( input=CommandLine.EntryPoint.ArgumentInfo(description="Test to compile and/or execute."),
                         compiler=CommandLine.EntryPoint.ArgumentInfo(description="Index or name of the Compiler to use to compile tests prior to execution."),
                         test_parser=CommandLine.EntryPoint.ArgumentInfo(description="Index or name of the Test Parser to use to extract test results from the invoked test."),
                         code_coverage_extractor=CommandLine.EntryPoint.ArgumentInfo(description="Index or name of the Code Coverage Extractor to use to extract code coverage information from the invoked test."),
                         code_coverage_validator=CommandLine.EntryPoint.ArgumentInfo(description="Index or name of the Code Coverage Validator to use to generate final results based on the evaluation of extacted code coverage information."),
                         iterations=CommandLine.EntryPoint.ArgumentInfo(description="Number of times to execute each test."),
                         compiler_flag=CommandLine.EntryPoint.ArgumentInfo(description="Flags to use when invoking the Compiler."),
                         test_parser_flag=CommandLine.EntryPoint.ArgumentInfo(description="Flags to use when invoking the Test Parser."),
                         code_coverage_extractor_flag=CommandLine.EntryPoint.ArgumentInfo(description="Flags to use when invoking the Code Coverage Extractor."),
                         code_coverage_validator_flag=CommandLine.EntryPoint.ArgumentInfo(description="Flags to use when invoking the Code Coverage Validator."),
                         preserve_ansi_escape_sequences=CommandLine.EntryPoint.ArgumentInfo(description="Preserve colorized output when invoking this script from another one."),
                       )
@CommandLine.FunctionConstraints( input=CommandLine.FilenameTypeInfo(),
                                  compiler=_CompilerTypeInfo,
                                  test_parser=_TestParserTypeInfo,
                                  code_coverage_extractor=_CodeCoverageExtractorTypeInfo,
                                  code_coverage_validator=CommandLine.EnumTypeInfo(values=_CodeCoverageValidatorTypeInfo.Values, arity='?'),
                                  iterations=CommandLine.IntTypeInfo(min=1),
                                  compiler_flag=CommandLine.StringTypeInfo(arity='*'),
                                  test_parser_flag=CommandLine.StringTypeInfo(arity='*'),
                                  code_coverage_extractor_flag=CommandLine.StringTypeInfo(arity='*'),
                                  code_coverage_validator_flag=CommandLine.StringTypeInfo(arity='*'),
                                  output_stream=None,
                                )
def Execute( input,
             compiler,
             test_parser,
             code_coverage_extractor,
             code_coverage_validator=None,
             iterations=1,
             debug_on_error=False,
             continue_iterations_on_error=False,
             compiler_flag=[],
             test_parser_flag=[],
             code_coverage_extractor_flag=[],
             code_coverage_validator_flag=[],
             debug_only=False,
             release_only=False,
             output_stream=sys.stdout,
             verbose=False,
             preserve_ansi_escape_sequences=False,
           ):
    """\
    Executes a specific test.
    """
    
    compiler = _GetCompiler(compiler)
    test_parser = _GetTestParser(test_parser)
    code_coverage_extractor = _GetCodeCoverageExtractor(code_coverage_extractor)
    code_coverage_validator = _GetCodeCoverageValidator(code_coverage_validator or "1")

    if not compiler.IsSupported(input):
        sys.stderr.write("ERROR: The compiler '{}' does not support the file '{}'.\n".format(compiler.Name, input))
        return -1

    complete_results = Test( [ input, ],
                             tempfile.mkdtemp(),
                             compiler,
                             test_parser,
                             code_coverage_extractor,
                             code_coverage_validator,
                             iterations=iterations,
                             debug_on_error=debug_on_error,
                             continue_iterations_on_error=continue_iterations_on_error,
                             output_stream=output_stream,
                             debug_only=debug_only,
                             release_only=release_only,
                          )

    if not complete_results:
        return 

    output_stream.write("\n")

    PrettyPrint( complete_results,
                 compiler,
                 test_parser,
                 code_coverage_extractor,
                 code_coverage_validator,
                 output_stream,
                 preserve_ansi_escape_sequences,
                 verbose,
               )

    return complete_results[0].CompositeResult()

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint( input_dir=CommandLine.EntryPoint.ArgumentInfo(description="Root directory used to search for potential test files."),
                         test_type=CommandLine.EntryPoint.ArgumentInfo(description="Name of subdirectory that contains tests to execute."),
                         output_dir=CommandLine.EntryPoint.ArgumentInfo(description="Output directory that will contain the generated results."),
                         compiler=CommandLine.EntryPoint.ArgumentInfo(description="Index or name of the Compiler to use to compile tests prior to execution."),
                         test_parser=CommandLine.EntryPoint.ArgumentInfo(description="Index or name of the Test Parser to use to extract test results from the invoked test."),
                         code_coverage_extractor=CommandLine.EntryPoint.ArgumentInfo(description="Index or name of the Code Coverage Extractor to use to extract code coverage information from the invoked test."),
                         code_coverage_validator=CommandLine.EntryPoint.ArgumentInfo(description="Index or name of the Code Coverage Validator to use to generate final results based on the evaluation of extacted code coverage information."),
                         iterations=CommandLine.EntryPoint.ArgumentInfo(description="Number of times to execute each test."),
                         compiler_flag=CommandLine.EntryPoint.ArgumentInfo(description="Flags to use when invoking the Compiler."),
                         test_parser_flag=CommandLine.EntryPoint.ArgumentInfo(description="Flags to use when invoking the Test Parser."),
                         code_coverage_extractor_flag=CommandLine.EntryPoint.ArgumentInfo(description="Flags to use when invoking the Code Coverage Extractor."),
                         code_coverage_validator_flag=CommandLine.EntryPoint.ArgumentInfo(description="Flags to use when invoking the Code Coverage Validator."),
                         preserve_ansi_escape_sequences=CommandLine.EntryPoint.ArgumentInfo(description="Preserve colorized output when invoking this script from another one."),
                       )
@CommandLine.FunctionConstraints( input_dir=CommandLine.DirectoryTypeInfo(),
                                  test_type=CommandLine.StringTypeInfo(),
                                  output_dir=CommandLine.StringTypeInfo(),
                                  compiler=_CompilerTypeInfo,
                                  test_parser=_TestParserTypeInfo,
                                  code_coverage_extractor=_CodeCoverageExtractorTypeInfo,
                                  code_coverage_validator=CommandLine.EnumTypeInfo(values=_CodeCoverageValidatorTypeInfo.Values, arity='?'),
                                  iterations=CommandLine.IntTypeInfo(min=1),
                                  compiler_flag=CommandLine.StringTypeInfo(arity='*'),
                                  test_parser_flag=CommandLine.StringTypeInfo(arity='*'),
                                  code_coverage_extractor_flag=CommandLine.StringTypeInfo(arity='*'),
                                  code_coverage_validator_flag=CommandLine.StringTypeInfo(arity='*'),
                                  output_stream=None,
                                )
def ExecuteTree( input_dir,
                 test_type,
                 output_dir,
                 compiler,
                 test_parser,
                 code_coverage_extractor,
                 code_coverage_validator=None,
                 iterations=1,
                 debug_on_error=False,
                 continue_iterations_on_error=False,
                 compiler_flag=[],
                 test_parser_flag=[],
                 code_coverage_extractor_flag=[],
                 code_coverage_validator_flag=[],
                 debug_only=False,
                 release_only=False,
                 output_stream=sys.stdout,
                 verbose=False,
                 quiet=False,
                 preserve_ansi_escape_sequences=False,
               ):
    """\
    Executes tests found found within 'test_type' subdirectories.
    """
    
    compiler = _GetCompiler(compiler)
    test_parser = _GetTestParser(test_parser)
    code_coverage_extractor = _GetCodeCoverageExtractor(code_coverage_extractor)
    code_coverage_validator = _GetCodeCoverageValidator(code_coverage_validator or "1")

    if verbose and quiet:
        quiet = False

    start_time = TimeDelta()

    output_stream.write("Parsing '{}'...".format(input_dir))
    with StreamDecorator(output_stream).DoneManager(done_suffix='\n') as parse_manager:
        test_items = ExtractTestItems( input_dir,
                                       test_type,
                                       compiler,
                                       verbose_stream=(parse_manager.stream if verbose else None),
                                     )

    if not test_items:
        output_stream.write("No tests were found.\n")
        return

    complete_results = Test( test_items,
                             output_dir,
                             compiler,
                             test_parser,
                             code_coverage_extractor,
                             code_coverage_validator,
                             execute_in_parallel=(test_type == "UnitTests"),
                             iterations=iterations,
                             debug_on_error=debug_on_error,
                             continue_iterations_on_error=continue_iterations_on_error,
                             output_stream=output_stream,
                             debug_only=debug_only,
                             release_only=release_only,
                           )

    if not complete_results:
        return

    if quiet:
        sys.stdout.write("\n")
    else:
        PrettyPrint( complete_results,
                     compiler,
                     test_parser,
                     code_coverage_extractor,
                     code_coverage_validator,
                     output_stream,
                     preserve_ansi_escape_sequences,
                     verbose,
                   )

    tests = [ 0, ]
    failures = [ 0, ]

    if _ShouldPrettyPrint(output_stream):
        output_stream = sys.stdout

        # ---------------------------------------------------------------------------
        def Print(content):
            if content.startswith("Succeeded"):
                output_stream.write("{}{}{}".format(colorama.Fore.GREEN, colorama.Style.BRIGHT, content))
            elif content.startswith("Failed"):
                output_stream.write("{}{}{}".format(colorama.Fore.RED, colorama.Style.BRIGHT, content))
            else:
                output_stream.write("{}{}{}".format(colorama.Fore.WHITE, colorama.Style.BRIGHT, content))

        # ---------------------------------------------------------------------------
    else:
        # ---------------------------------------------------------------------------
        def Print(content):
            output_stream.write(content)

        # ---------------------------------------------------------------------------
        
    # ---------------------------------------------------------------------------
    def Output(test_item, result_type, results):
        result = results.CompositeResult()
        if result == None:
            return

        Print("{result} {item}, {result_type}, {time}\n".format( result="Succeeded:" if result == 0 else "Failed:   ",
                                                                 item=test_item,
                                                                 result_type=result_type,
                                                                 time=results.TotalTime(),
                                                               ))

        tests[0] += 1
        if result != 0:
            failures[0] += 1

    # ---------------------------------------------------------------------------
    
    for complete_result in complete_results:
        Output(complete_result.Item, "Debug", complete_result.debug)
        Output(complete_result.Item, "Release", complete_result.release)

    Print("\n{percentage:.02f}% - {total} built and run with {failures} (Total execution time: {time}).\n".format( percentage=((float(tests[0]) - failures[0]) / tests[0]) * 100,
                                                                                                                   total=pluralize.no("test", tests[0]),
                                                                                                                   failures=pluralize.no("failure", failures[0]),
                                                                                                                   time=start_time.CalculateDelta(as_string=True),
                                                                                                                 ))

    result = 0
    for complete_result in complete_results:
        result = complete_result.CompositeResult()
        if result != 0:
            break

    return result
    
# ---------------------------------------------------------------------------
@CommandLine.EntryPoint( input_dir=CommandLine.EntryPoint.ArgumentInfo(description="Root directory used to search for potential test files."),
                         test_type=CommandLine.EntryPoint.ArgumentInfo(description="Name of subdirectory that contains tests to execute."),
                         compiler=CommandLine.EntryPoint.ArgumentInfo(description="Index or name of the Compiler to use to compile tests prior to execution."),
                         compiler_flag=CommandLine.EntryPoint.ArgumentInfo(description="Flags to use when invoking the Compiler."),
                       )
@CommandLine.FunctionConstraints( input_dir=CommandLine.DirectoryTypeInfo(),
                                  test_type=CommandLine.StringTypeInfo(),
                                  compiler=_CompilerTypeInfo,
                                  compiler_flag=CommandLine.StringTypeInfo(arity='*'),
                                  output_stream=None,
                                )
def MatchTests( input_dir,
                test_type,
                compiler,
                compiler_flag=[],
                output_stream=sys.stdout,
                verbose=False,
              ):
    """\
    Matches tests to production code for tests found within 'test_type' subdirectories.
    """
    
    compiler = _GetCompiler(compiler)
    
    if not compiler.Type == compiler.TypeValue.File:
        output_stream.write("Tests can only be matched for compilers that operate on individual files.\n")
        return 0

    traverse_exclude_dir_names = [ "Generated", "Impl", "Details", ]

    output_stream.write("Parsing '{}'...".format(input_dir))
    with StreamDecorator(output_stream).DoneManager(done_suffix='\n') as dm:
        source_files = list(FileSystem.WalkFiles( input_dir,
                                                  include_dir_paths=[ lambda fullpath: os.path.isdir(os.path.join(fullpath, test_type)), ],
                                                  include_full_paths=[ compiler.IsSupported, ],
                                                  exclude_file_names=[ "Build.py", ],
                                                  traverse_exclude_dir_names=traverse_exclude_dir_names,
                                                ))

        test_items = ExtractTestItems( input_dir,
                                       test_type,
                                       compiler,
                                       dm.stream if verbose else None,
                                     )

        # Remove any test items that correspond to sources that were explicitly removed.
        # We want to run these tests, but don't want to report them as an error.

        # ----------------------------------------------------------------------
        def IsMissingTest(filename):
            parts = filename.split(os.path.sep)

            for part in parts:
                if part in traverse_exclude_dir_names:
                    return False

            return True

        # ----------------------------------------------------------------------
        
        test_items = [ test_item for test_item in test_items if IsMissingTest(test_item) ]
        
    output_stream.write(textwrap.dedent(
        """\
        Source Files:   {}
        Test Files:     {}

        """).format(len(source_files), len(test_items)))

    output_template = "{source:<120} -> {test}\n"

    verbose_stream = StreamDecorator(output_stream if verbose else None)

    index = 0
    while index < len(source_files):
        source_filename = source_files[index]

        test_item = compiler.ItemNameToTestName(source_filename, test_type)

        if os.path.isfile(test_item):
            # We can't be sure that the test is in the file, as multiple source files may map to the
            # same test file (as in the case of headers with ".h" and ".hpp" extensions)
            if test_item in test_items:
                test_items.remove(test_item)

            del source_files[index]

            verbose_stream.write(output_template.format(source=source_filename, test=test_item))
        else:
            index += 1

    verbose_stream.write("\n\n")

    if source_files:
        header = "Source files without corresponding tests: {}".format(len(source_files))

        output_stream.write(textwrap.dedent(
            """\
            {header}
            {sep}
            {content}

            """).format( header=header,
                         sep='-' * len(header),
                         content=''.join('\n'.join(source_files)),
                       ))

    if test_items:
        header = "Test files without corresponding sources: {}".format(len(test_items))

        output_stream.write(textwrap.dedent(
            """\
            {header}
            {sep}
            {content}

            """).format( header=header,
                         sep='-' * len(header),
                         content=''.join('\n'.join(test_items)),
                       ))

    return 0 if not source_files and not test_items else -1
                       
# ---------------------------------------------------------------------------
def CommandLineSuffix():
    return textwrap.dedent(
        """\
        Where...

            Available values for 'compiler' are:
        {compilers}

            Available values for 'test_parser' are:
        {test_parsers}

            Available values for 'code_coverage_extractor' are:
        {code_coverage_extractors}

            Available values for 'code_coverage_validator' are:
        {code_coverage_validators}

        In all cases, the item index or name may be used.

        """).format( compilers='\n'.join([ "        {index}) {name:<20} {desc}".format(index=index + 1, name=compiler.Name, desc=compiler.Description) for index, compiler in enumerate(COMPILERS) ]),
                     test_parsers='\n'.join([ "        {index}) {name:<20} {desc}".format(index=index + 1, name=compiler.Name, desc=compiler.Description) for index, compiler in enumerate(TEST_PARSERS) ]),
                     code_coverage_extractors='\n'.join([ "        {index}) {name:<20} {desc}".format(index=index + 1, name=compiler.Name, desc=compiler.Description) for index, compiler in enumerate(CODE_COVERAGE_EXTRACTORS) ]),
                     code_coverage_validators='\n'.join([ "        {index}) {name:<20} {desc}".format(index=index + 1, name=compiler.Name, desc=compiler.Description) for index, compiler in enumerate(CODE_COVERAGE_VALIDATORS) ]),
                   )

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
def _GetCompiler(value):
    return _GetItem(value, COMPILERS)

# ---------------------------------------------------------------------------
def _GetTestParser(value):
    return _GetItem(value, TEST_PARSERS)

# ---------------------------------------------------------------------------
def _GetCodeCoverageExtractor(value):
    return _GetItem(value, CODE_COVERAGE_EXTRACTORS)

# ---------------------------------------------------------------------------
def _GetCodeCoverageValidator(value):
    return _GetItem(value, CODE_COVERAGE_VALIDATORS)

# ---------------------------------------------------------------------------
def _GetItem(value, items):
    if value.isdigit():
        value = int(value) - 1
    else:
        value = value.lower()

        for index, item in enumerate(items):
            if item.Name.lower() == value:
                value = index
                break

    if value < 0 or value >= len(items):
        return None

    return items[value]()

# ---------------------------------------------------------------------------
def _ShouldPrettyPrint(output_stream):
    return ( output_stream == sys.stdout or
             isinstance(output_stream, colorama.ansitowin32.StreamWrapper) or 
             isinstance(sys.stdout, colorama.ansitowin32.StreamWrapper)
           )

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
