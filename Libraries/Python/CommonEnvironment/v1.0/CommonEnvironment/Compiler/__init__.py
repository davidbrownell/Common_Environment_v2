# ---------------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/31/2015 06:08:53 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import copy
import inspect
import os
import re
import shutil
import sys
import textwrap

from StringIO import StringIO

from CommonEnvironment import CommandLine
from CommonEnvironment import Enum
from CommonEnvironment.FileSystem import *
from CommonEnvironment.Interface import *
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment import RegularExpression
from CommonEnvironment.StreamDecorator import StreamDecorator

from .InputProcessingMixin import InputProcessingMixin
from .InvocationMixin import InvocationMixin
from .InvocationQueryMixin import InvocationQueryMixin
from .OutputMixin import OutputMixin

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
class Base( InputProcessingMixin,
            InvocationMixin,
            InvocationQueryMixin,
            OutputMixin,
          ):
    """\
    Base class for Compilers, CodeGenerators, Validators, and other compiler-like
    super classes. For simplicity, these classes are referred to as "compilers" 
    within this file.
    """

    # ---------------------------------------------------------------------------
    # |
    # |  Public Types
    # |
    # ---------------------------------------------------------------------------
    TypeValue = Enum.Create( "File",        # The compiler operates on individual files (1 or more)
                             "Directory",   # The compiler operates on files within a directory
                           )

    # ---------------------------------------------------------------------------
    # |
    # |  Public Properties
    # |
    # ---------------------------------------------------------------------------
    
    @abstractproperty
    def Name(self):
        raise Exception("Abstract property")

    @abstractproperty
    def Description(self):
        raise Exception("Abstract property")

    @abstractproperty
    def Type(self):
        raise Exception("Abstract property")

    @abstractproperty
    def InvokeVerb(self):
        raise Exception("Abstract property")

    # ---------------------------------------------------------------------------
    # |  One of the following values will be set to True by a super class
    IsCompiler                              = False
    IsCodeGenerator                         = False
    IsVerifier                              = False
    
    # ---------------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ---------------------------------------------------------------------------
    @extensionmethod
    @staticmethod
    def ValidateEnvironment():
        """\
        Overload this method if the compiler can only run in certain environments.
        Return a string with text if the environment isn't valid.
        """
        pass

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def IsSupported(item):
        """\
        Returns True if the given input is supported by the compiler.
        """
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @extensionmethod
    @staticmethod
    def IsSupportedTestFile(item):
        return True
        
    # ---------------------------------------------------------------------------
    @extensionmethod
    @classmethod
    def ItemNameToTestName(cls, item_name, test_name):
        """Returns the likely name of the test given the source filename."""

        if cls.Type == cls.TypeValue.Directory:
            # We can't reason about test directories, so just return the directory itself
            return item_name

        elif cls.Type == cls.TypeValue.File:            # <Instance of '<obj>' has no '<name>' member> pylint: disable = E1101, E1103
            path, name = os.path.split(item_name)
            name, ext = os.path.splitext(name)

            return os.path.join(path, test_name, "{name}.{test_type}{ext}".format( name=name,
                                                                                   test_type=test_name[:-1] if test_name[-1] == 's' else test_name,
                                                                                   ext=ext,
                                                                                 ))

        else:
            assert False, (cls.Name, cls.Type)
    
    # ---------------------------------------------------------------------------
    @extensionmethod
    @classmethod
    def GetSystemUnderTest(cls, test_filename):
        if cls.Type == cls.TypeValue.Directory:
            # We can't reason about test directories, so just return the directory itself
            return test_filename

        elif cls.Type == cls.TypeValue.File:            # <Instance of '<obj>' has no '<name>' member> pylint: disable = E1101, E1103
            path, name = os.path.split(test_filename)

            match = re.match( r"^(?P<name>.+?)\.(?P<test_type>.+?)(?P<ext>\..+?)$",
                              name,
                            )
            assert match, name

            name = "{}{}".format(match.group("name"), match.group("ext"))
            test_type = match.group("test_type")

            if path and os.path.basename(path) == "{}{}".format(test_type, '' if test_type[-1] == 's' else 's'):
                path = os.path.dirname(path)

            return os.path.join(path, name)

        else:
            assert False, (cls.Name, cls.Type)

    # ---------------------------------------------------------------------------
    @classmethod
    def GenerateContextItems( cls,
                              inputs,
                              **kwargs
                            ):
        """\
        Yields one or more context items depending on the compiler type (file vs. directory),
        how it processes input (individual vs. atomic), and the input actually provided
        (file vs. directory).
        """

        # This method will always be called early within the invocation process, so use
        # it as a hook to ensure that we are working with fully formed objects.

        # ---------------------------------------------------------------------------
        def EnsureValid():
            classes = inspect.getmro(cls)

            # ---------------------------------------------------------------------------
            def Impl(desc, *items):
                base_count = 0

                for item in items:
                    if item in classes:
                        base_count += 1

                assert base_count == 1, (cls.Name, desc, base_count, '\n'.join([ str(c) for c in classes ]))

            # ---------------------------------------------------------------------------
            
            # CompilerType
            from CommonEnvironment.Compiler.Compiler import Compiler as CompilerClass
            from CommonEnvironment.Compiler.CodeGenerator import CodeGenerator
            from CommonEnvironment.Compiler.Verifier import Verifier

            Impl("CompilerType", CompilerClass, CodeGenerator, Verifier)

            # InputProcessingMixin
            from CommonEnvironment.Compiler.InputProcessingMixin.AtomicInputProcessingMixin import AtomicInputProcessingMixin
            from CommonEnvironment.Compiler.InputProcessingMixin.IndividualInputProcessingMixin import IndividualInputProcessingMixin
            
            Impl("InputProcessingMixin", AtomicInputProcessingMixin, IndividualInputProcessingMixin)

            # InvocationQueryMixin
            from CommonEnvironment.Compiler.InvocationQueryMixin.AlwaysInvocationQueryMixin import AlwaysInvocationQueryMixin
            from CommonEnvironment.Compiler.InvocationQueryMixin.ConditionalInvocationQueryMixin import ConditionalInvocationQueryMixin

            Impl("InvocationQueryMixin", AlwaysInvocationQueryMixin, ConditionalInvocationQueryMixin)

            # InvocationMixin
            from CommonEnvironment.Compiler.InvocationMixin.CommandLineInvocationMixin import CommandLineInvocationMixin
            from CommonEnvironment.Compiler.InvocationMixin.CustomInvocationMixin import CustomInvocationMixin

            Impl("InvocationMixin", CommandLineInvocationMixin, CustomInvocationMixin)

            # OutputMixin
            from CommonEnvironment.Compiler.OutputMixin.MultipleOutputMixin import MultipleOutputMixin
            from CommonEnvironment.Compiler.OutputMixin.NoOutputMixin import NoOutputMixin
            from CommonEnvironment.Compiler.OutputMixin.SingleOutputMixin import SingleOutputMixin

            Impl("OutputMixin", MultipleOutputMixin, NoOutputMixin, SingleOutputMixin)

        # ---------------------------------------------------------------------------
        
        EnsureValid()

        # Continue with normal processing
        if not isinstance(inputs, list):
            inputs = [ inputs, ]

        invocation_group_inputs = []

        for input in inputs:
            if os.path.isfile(input):
                if cls.Type == cls.TypeValue.File:      # <Instance of '<obj>' has no '<name>' member> pylint: disable = E1101, E1103
                    potential_inputs = [ input, ]
                elif cls.Type == cls.TypeValue.Directory:
                    raise Exception("The filename '{}' was provided as input, but this compiler operates on directories".format(input))
                else:
                    assert False, (cls.Name, cls.Type)

            elif os.path.isdir(input):
                if cls.Type == cls.TypeValue.File:      # <Instance of '<obj>' has no '<name>' member> pylint: disable = E1101, E1103
                    potential_inputs = list(WalkFiles(input))
                elif cls.Type == cls.TypeValue.Directory:
                    potential_inputs = [ input, ]
                else:
                    assert False, (cls.Name, cls.Type)

            else:
                raise Exception("The input '{}' is not a valid file or directory".format(input))

            added_input = False

            for potential_input in potential_inputs:
                if cls.IsSupported(potential_input):
                    invocation_group_inputs.append(potential_input)
                    added_input = True

        optional_metadata = cls._GetOptionalMetadata()
        
        if isinstance(optional_metadata, dict):
            # ---------------------------------------------------------------------------
            def Generator():
                for item in optional_metadata.iteritems():
                    yield item

            # ---------------------------------------------------------------------------
            
        elif isinstance(optional_metadata, list):
            # ---------------------------------------------------------------------------
            def Generator():
                for item in optional_metadata:
                    yield item

            # ---------------------------------------------------------------------------
            
        else:
            assert False, type(optional_metadata)

        for k, v in Generator():
            if k not in kwargs or kwargs[k] == None or kwargs[k] == '':
                kwargs[k] = v

        input_key = None

        for metadata in cls._CreateInvocationMetadataItems(invocation_group_inputs, copy.deepcopy(kwargs)):
            for required_name in cls._GetRequiredMetadataNames():
                if required_name not in metadata:
                    raise Exception("'{}' is required metadata".format(required_name))

            context = QuickObject(**metadata)

            if not cls._GetInputItems(context):
                continue

            display_name = cls._GetDisplayName(context)
            if display_name:
                context.display_name = display_name

            context = cls._PostprocessContextItem(context)
            if not context:
                continue

            for required_name in cls._GetRequiredContextNames():
                if not hasattr(context, required_name):
                    raise Exception("'{}' is required for {} ({})".format( required_name,
                                                                           cls.Name,
                                                                           ', '.join([ "'{}'".format(input) for input in cls._GetInputItems(context) ]),
                                                                         ))

            yield context

    # ---------------------------------------------------------------------------
    @classmethod
    def GenerateContextItem( cls,
                             inputs,
                             **kwargs
                           ):
        """\
        Convenience method when one and only one context item is expected.
        """

        contexts = list(cls.GenerateContextItems(inputs, **kwargs))
        if not contexts:
            return

        if len(contexts) != 1:
            raise BaseException("Multiple contexts were found ({})".format(len(contexts)))

        return contexts[0]

    # ---------------------------------------------------------------------------
    @classmethod
    def Clean(cls, context, output_stream):
        """\
        Handles the complexities of cleaning, ultimately calling _CleanImpl.
        """

        assert context
        # output_stream can be None
        
        output_stream.write(cls._GetStatusText("Cleaning", context, cls._GetInputItems(context)))
        with output_stream.DoneManager() as dm:
            dm.result = cls._CleanImpl(context, dm.stream) or 0
            return dm.result
           
    # ---------------------------------------------------------------------------
    # |
    # |  Protected Methods
    # |
    # ---------------------------------------------------------------------------
    @classmethod
    def _Invoke(cls, context, status_stream, verbose):
        """\
        Handles the complexities of invocation, ultimate calling _InvokeImpl.
        """

        assert context
        # status_stream can be None
        status_stream = StreamDecorator(status_stream)

        invoke_reason = cls._GetInvokeReason(context, StreamDecorator(status_stream if verbose else None))
        if invoke_reason == None:
            status_stream.write("No changes were detected.\n")
            return 0

        input_items = cls._GetInputItems(context)

        status_stream.write(cls._GetStatusText(cls.InvokeVerb, context, input_items))
        with status_stream.DoneManager() as dm:
            if verbose:
                output_items = cls._GetOutputFilenames(context)

                if hasattr(context, "display_name") or len(input_items) == 1:
                    indentation = 4
                else:
                    indentation = 8

                verbose_stream = StreamDecorator( StreamDecorator(dm.stream),
                                                  prefix=StreamDecorator.LeftJustify( textwrap.dedent(
                                                                                        """\
                                                                                        
                                                                                        ========================================
                                                                                        VERBOSE Output

                                                                                        {}
                                                                                                ->
                                                                                            {}
                                                                                        ========================================
                                                                                        """).format( '\n'.join(input_items),
                                                                                                     StreamDecorator.LeftJustify('\n'.join(output_items) if output_items else "[None]", 4),
                                                                                                   ),
                                                                                      2,
                                                                                      skip_first_line=False,
                                                                                    ),
                                                  suffix='\n',
                                                  line_prefix=' ' * indentation,
                                                )
                status_stream = verbose_stream
            else:
                status_stream = dm.stream
                verbose_stream = StreamDecorator(None)

            dm.result = cls._InvokeImpl( invoke_reason, 
                                         context, 
                                         status_stream, 
                                         verbose_stream, 
                                         verbose,
                                       )

            if dm.result == 0:
                cls._PersistContext(context)

            return dm.result

    # ----------------------------------------------------------------------
    @staticmethod
    def ApplyExternalConfigurations( configuration_filename,
                                     load_filename,             # def Func(config_filename) -> configuration contents
                                     process_config_info,       # def Func(filename, config_info, normalize_path_functor)
                                     input_filenames,
                                   ):
        for input_filename in input_filenames:
            # Get all of the external configuration files that exist within the path
            # hierarchy of this file.
            configuration_filenames = []

            dirname = os.path.dirname(os.path.abspath(input_filename))
            while True:
                potential_filename = os.path.join(dirname, configuration_filename)
                if os.path.isfile(potential_filename):
                    configuration_filenames.append(potential_filename)

                new_dirname = os.path.dirname(dirname)
                if new_dirname == dirname:
                    break

                dirname = new_dirname
        
            # Process the configuration files
            for configuration_filename in configuration_filenames:
                dirname = os.path.dirname(configuration_filename)
                normalize_path_functor = lambda value: os.path.abspath(os.path.join(dirname, ValueError))

                content = load_filename(dirname)

                for source in content.sources:
                    if not RegularExpression.WildcardSearchToRegularExpression(source.name.replace('/', os.path.sep)).match(input_filename):
                        continue

                    process_config_info( input_filename, 
                                         source,
                                         normalize_path_functor,
                                       )

    # ----------------------------------------------------------------------
    @classmethod
    def ShouldProcessConfigInfo( cls,
                                 config_info,
                                 environment,
                                 is_debug,
                               ):
        for attribute_name, required_value in [ ( "environment", environment.Name ),
                                                ( "compiler_name", cls.Name ),
                                                ( "compiler_version", cls.Version ),
                                                ( "build", "debug" if is_debug else "release" ),
                                              ]:
            value = getattr(config_info, attribute_name, None)
            if value != None and value != required_value:
                return False

        return True

    # ----------------------------------------------------------------------
    @staticmethod
    def PopulateEnvironmentVars(s, **additional_args):
        """\
        Will replace placeholders in the form '$(var)' in the given string with
        the value in the current environment.
        """

        placeholder = "<<!!--__"

        additional_args_lower = {}
        for k, v in additional_args.iteritems():
            additional_args_lower[k.lower()] = v

        environ_lower = {}
        for k, v in os.environ.iteritems():
            environ_lower[k.lower()] = v

        regexp = re.compile(r"\$\((?P<var>.+?)\)")

        # ----------------------------------------------------------------------
        def Sub(match):
            var = match.group("var").lower()

            if var in additional_args_lower:
                return additional_args_lower[var]

            if var in environ_lower:
                return environ_lower[var]

            return match.string[match.start() : match.end()].replace("$(", placeholder)

        # ----------------------------------------------------------------------
        
        while "$(" in s:
            s = regexp.sub(Sub, s)

        return s.replace(placeholder, "$(")

    # ---------------------------------------------------------------------------
    # |
    # |  Private Methods
    # |
    # ---------------------------------------------------------------------------
    
    # ---------------------------------------------------------------------------
    # |  The following methods MAY be overridden to customize behavior
    @extensionmethod
    @staticmethod
    def _GetAdditionalGeneratorItems(context):
        """\
        Return a list of filenames or objects of any plugin files that participate
        in compilation. This information will be used to detect modifications that
        imply recompilation is necessary.
        """
        return []

    # ---------------------------------------------------------------------------
    @extensionmethod
    @staticmethod
    def _GetDisplayName(context):
        """\
        Name used to uniquely identify the compilation in output messages.
        """
        return None
    
    # ---------------------------------------------------------------------------
    @extensionmethod
    @staticmethod
    def _GetOptionalMetadata():
        """\
        Returns key-value pairs
        """
        return []

    # ---------------------------------------------------------------------------
    @extensionmethod
    @staticmethod
    def _GetRequiredMetadataNames():
        """\
        All names that should be provided in metadata when generating context.
        """
        return []

    # ---------------------------------------------------------------------------
    @extensionmethod
    @staticmethod
    def _GetRequiredContextNames():
        """\
        All names that should be provided (either by metadata or via _PostProcessContextItem)
        when generating context.
        """
        return []

    # ---------------------------------------------------------------------------
    # |  The following methods are implemented by mixins
    @staticmethod
    def _PostprocessContextItem(context):
        """\
        Returns a context object tuned specifically for the provided input.
        """
        return context
    
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    @classmethod
    def _GetStatusText(cls, prefix, context, input_items):
        if hasattr(context, "display_name"):
            status_suffix = '"{}"...'.format(context.display_name)
        elif len(input_items) == 1:
            status_suffix = '"{}"...'.format(input_items[0])
        else:
            status_suffix = textwrap.dedent(
                """\

                {}
                """).format('\n'.join([ "    - {}".format(input_item) for input_item in input_items ]))

        return "{} {}".format(prefix, status_suffix)
    
# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
def CommandLineInvoke( compiler,
                       inputs,
                       output_stream,
                       verbose, 
                       output_via_stderr=False,
                       output_start_line=None,
                       output_end_line=None,
                       **compiler_kwargs
                     ):
    # ---------------------------------------------------------------------------
    def Invoke(context, output_stream):
        if compiler.IsCompiler:
            method_name = "Compile"
        elif compiler.IsCodeGenerator:
            method_name = "Generate"
        elif compiler.IsVerifier:
            method_name = "Verify"
        else:
            assert False, compiler

        return getattr(compiler, method_name)(context, output_stream, verbose)

    # ---------------------------------------------------------------------------
    
    return _CommandLineImpl( compiler, 
                             inputs,
                             Invoke,
                             output_stream,
                             compiler_kwargs,
                             output_via_stderr=output_via_stderr,
                             output_start_line=output_start_line,
                             output_end_line=output_end_line,
                           )
    
# ---------------------------------------------------------------------------
def CommandLineClean( compiler,
                      inputs,
                      output_stream,
                      **compiler_kwargs
                    ):
    return _CommandLineImpl( compiler,
                             inputs,
                             compiler.Clean,
                             output_stream,
                             compiler_kwargs,
                           )

# ---------------------------------------------------------------------------
def CommandLineCleanOutputDir(output_dir, output_stream):
    if not os.path.isdir(output_dir):
        output_stream.write("'{}' does not exist.\n".format(output_dir))
        return 0

    output_stream.write("Removing '{}'...".format(output_dir))
    with StreamDecorator(output_stream).DoneManager() as stream_info:
        shutil.rmtree(output_dir)

    return stream_info.result
        
# ---------------------------------------------------------------------------
def CommandLineCleanOutputFilename(output_filename, output_stream):
    if not os.path.isfile(output_filename):
        output_stream.write("'{}' does not exist.\n".format(output_filename))
        return 0

    output_stream.write("Removing '{}'...".format(output_filename))
    with StreamDecorator(output_stream).DoneManager() as stream_info:
        os.remove(output_filename)

    return stream_info.result

# ---------------------------------------------------------------------------
def LoadFromModule(mod):
    for potential_name in [ "Compiler",
                            "CodeGenerator",
                            "Verifier",
                          ]:
        result = getattr(mod, potential_name, None)
        if result != None:
            return result

    assert False, mod

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
def _CommandLineImpl( compiler,
                      inputs,
                      functor,              # def Func(context, output_stream) -> rval
                      output_stream,
                      compiler_kwargs,
                      output_via_stderr=False,
                      output_start_line=None,
                      output_end_line=None,
                    ):
    assert compiler
    assert inputs
    assert output_stream

    result = compiler.ValidateEnvironment()
    if result:
        output_stream.write("{}\n".format(result.rstrip()))
        return -1

    # Validate the input
    inputs = [ os.path.realpath(input) for input in inputs ]

    for input in inputs:
        if not os.path.exists(input):
            raise CommandLine.UsageException("'{}' is not a valid file or directory".format(input))

        if os.path.isfile(input):
            if compiler.Type == compiler.TypeValue.File and not compiler.IsSupported(input):
                raise CommandLine.UsageException("'{}' is not a supported file".format(input))
            elif compiler.Type == compiler.TypeValue.Directory:
                raise CommandLine.UsageException("'{}' is a file, but this compiler operates on directories".format(input))

    # Prepare the streams
    output_stream = StreamDecorator(output_stream, suffix='\n')
    
    # Execute
    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     done_prefix='\nExecution is ',
                                                     done_suffix='\n',
                                                     display_exceptions=False,
                                                   ) as stream_info:
        stream_info.stream.write("Generating context...")
        with stream_info.stream.DoneManager():
            contexts = list(compiler.GenerateContextItems(inputs, **compiler_kwargs))
            
        for index, context in enumerate(contexts):
            stream_info.stream.flush()

            result = functor(context, output_stream)
            
            stream_info.result = stream_info.result or result
            
    return stream_info.result
