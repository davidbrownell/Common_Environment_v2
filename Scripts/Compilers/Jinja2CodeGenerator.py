# ----------------------------------------------------------------------
# |  
# |  Jinja2CodeGenerator.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-02-15 19:17:35
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import itertools
import os
import sys
import textwrap

from collections import OrderedDict

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Interface
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment.StreamDecorator import StreamDecorator

from CommonEnvironment.Compiler import CodeGenerator as CodeGeneratorMod
from CommonEnvironment.Compiler.InputProcessingMixin.AtomicInputProcessingMixin import AtomicInputProcessingMixin
from CommonEnvironment.Compiler.InvocationQueryMixin.ConditionalInvocationQueryMixin import ConditionalInvocationQueryMixin
from CommonEnvironment.Compiler.InvocationMixin.CustomInvocationMixin import CustomInvocationMixin
from CommonEnvironment.Compiler.OutputMixin.MultipleOutputMixin import MultipleOutputMixin

from jinja2 import Template

import os
import sys

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
@Interface.staticderived
class CodeGenerator( AtomicInputProcessingMixin,
                     ConditionalInvocationQueryMixin,
                     CustomInvocationMixin,
                     MultipleOutputMixin,
                     CodeGeneratorMod.CodeGenerator,
                   ):
    # ---------------------------------------------------------------------------
    # |
    # |  Public Properties
    # |
    # ---------------------------------------------------------------------------
    Name                                    = "Jinja2CodeGenerator"
    Description                             = "Processes a Jinja2 template and produces output"
    Type                                    = CodeGeneratorMod.CodeGenerator.TypeValue.File

    # ---------------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ---------------------------------------------------------------------------
    @staticmethod
    def IsSupported(item):
        if not os.path.isfile(item):
            return False

        return "Jinja2" in item.split('.')

    # ---------------------------------------------------------------------------
    # |
    # |  Private Methods
    # |
    # ---------------------------------------------------------------------------
    
    # ---------------------------------------------------------------------------
    @classmethod
    def _GetOptionalMetadata(cls):
        return [ ( "jinja2_context", {} ),
                 ( "jinja2_context_code", [] ),
                 ( "preserve_dir_structure", False ),
               ] + \
               super(CodeGenerator, cls)._GetOptionalMetadata()

    # ---------------------------------------------------------------------------
    @classmethod
    def _PostprocessContextItem(cls, context):
        jinja2_context = {}

        # Load the custom context defined in code
        for context_code in context.jinja2_context_code:
            dirname, filename = os.path.split(context_code.filename)

            sys.path.insert(0, dirname)
            with CallOnExit(lambda: sys.path.pop(0)):
                mod = __import__(os.path.splitext(filename)[0])

            var = getattr(mod, context_code.var_name)
            del mod

            if isinstance(var, dict):
                for k, v in var.iteritems():
                    jinja2_context[k] = v
            else:
                jinja2_context[context_code.var_name] = var

        del context.jinja2_context_code

        # Load the custom context
        for k, v in context.jinja2_context.iteritems():
            if len(v) == 1:
                jinja2_context[k] = v[0]
            else:
                jinja2_context[k] = v

        context.jinja2_context = jinja2_context

        # Get the output filenames
        if not context.preserve_dir_structure:
            # ----------------------------------------------------------------------
            def GetBaseDir(input_filename):
                return ''

            # ----------------------------------------------------------------------
        else:
            if len(context.input_filenames) == 1:
                common_prefix = os.path.dirname(context.input_filenames[0])
            else:
                common_prefix = FileSystem.GetCommonPath(*context.input_filenames)

            # ----------------------------------------------------------------------
            def GetBaseDir(input_filename):
                dirname = os.path.dirname(input_filename)

                assert dirname.startswith(common_prefix), (dirname, common_prefix)
                dirname = dirname[len(common_prefix):]

                if dirname.startswith(os.path.sep):
                    dirname = dirname[len(os.path.sep):]

                return dirname

            # ----------------------------------------------------------------------
            
        output_filenames = []

        for input_filename in context.input_filenames:
            output_filenames.append(os.path.join( context.output_dir,
                                                  GetBaseDir(input_filename),
                                                  '.'.join([ part for part in os.path.basename(input_filename).split('.') if part != "Jinja2" ]),
                                                ))


        context.output_filenames = output_filenames

        return super(CodeGenerator, cls)._PostprocessContextItem(context)

    # ----------------------------------------------------------------------
    @staticmethod
    def _CustomContextComparison(context, prev_context):
        return

    # ---------------------------------------------------------------------------
    @classmethod
    def _InvokeImpl( cls,
                     invoke_reason,
                     context,
                     status_stream,
                     output_stream,
                   ):
        total_rval = 0

        status_stream = StreamDecorator(status_stream)

        for index, (input_filename, output_filename) in enumerate(itertools.izip( context.input_filenames,
                                                                                  context.output_filenames,
                                                                                )):
            status_stream.write("Processing '{}' ({} of {})...".format( input_filename,
                                                                        index + 1,
                                                                        len(context.output_filenames),
                                                                      ))
            with status_stream.DoneManager(suppress_exceptions=True) as dm:
                try:
                    template = Template(open(input_filename).read())

                    with open(output_filename, 'w') as f:
                        f.write(template.render(**context.jinja2_context))

                except:
                    total_rval = -1
                    raise

        return total_rval

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( input=CommandLine.FilenameTypeInfo(type=CommandLine.FilenameTypeInfo.Type_Either, arity='+'),
                                  output_dir=CommandLine.DirectoryTypeInfo(ensure_exists=False),
                                  context=CommandLine.DictTypeInfo(require_exact_match=False, arity='?'),
                                  context_code=CommandLine.StringTypeInfo(validation_expression="^.+:.+$", arity='*'),
                                  output_stream=None,
                                )
def Generate( input,                          # <Redefining build-in type> pylint: disable = W0622
              output_dir,
              context=None,
              context_code=None,
              preserve_dir_structure=False,
              force=False,
              output_stream=sys.stdout,
              verbose=False,
            ):
    context_code = [ item.rsplit(':', 1) for item in context_code ]
    context_code = [ QuickObject( filename=item[0],
                                  var_name=item[1],
                                )
                     for item in context_code
                   ]

    return CodeGeneratorMod.CommandLineGenerate( CodeGenerator,
                                                 input,
                                                 output_stream,
                                                 verbose,

                                                 output_dir=output_dir,
                                                 force=force,

                                                 jinja2_context=context,
                                                 jinja2_context_code=context_code,
                                                 preserve_dir_structure=preserve_dir_structure,
                                               )

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( output_dir=CommandLine.DirectoryTypeInfo(),
                                  output_stream=None,
                                )
def Clean( output_dir,
           output_stream=sys.stdout,
           verbose=False,
         ):
    return CodeGeneratorMod.CommandLineCleanOutputDir(output_dir, output_stream)

# ----------------------------------------------------------------------
def CommandLineSuffix():
    return StreamDecorator.LeftJustify( textwrap.dedent(
                                            """\
                                            Where <context_code> is in the form:
                                                <filename>:<var_name>

                                                Example:
                                                    /Location/Of/Python/File:var_in_file
                                                    C:\My\Dir\Location:ContextData

                                            """),
                                        4,
                                        skip_first_line=False,
                                      )

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
