# ---------------------------------------------------------------------------
# |  
# |  CogCodeGenerator.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/17/2015 07:02:38 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import subprocess
import sys

from CommonEnvironment import CommandLine
from CommonEnvironment import Interface
from CommonEnvironment import Shell
from CommonEnvironment.StreamDecorator import StreamDecorator

from CommonEnvironment.Compiler import CodeGenerator as CodeGeneratorMod
from CommonEnvironment.Compiler.InputProcessingMixin.IndividualInputProcessingMixin import IndividualInputProcessingMixin
from CommonEnvironment.Compiler.InvocationQueryMixin.AlwaysInvocationQueryMixin import AlwaysInvocationQueryMixin
from CommonEnvironment.Compiler.InvocationMixin.CommandLineInvocationMixin import CommandLineInvocationMixin
from CommonEnvironment.Compiler.OutputMixin.SingleOutputMixin import SingleOutputMixin

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
@Interface.staticderived
class CodeGenerator( IndividualInputProcessingMixin,
                     AlwaysInvocationQueryMixin,
                     CommandLineInvocationMixin,
                     SingleOutputMixin,
                     CodeGeneratorMod.CodeGenerator,
                   ):
    # ---------------------------------------------------------------------------
    # |
    # |  Public Properties
    # |
    # ---------------------------------------------------------------------------
    Name                                    = "CogCodeGenerator"
    Description                             = "Invokes cog on a supported file"
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

        if os.path.getsize(item) > 10 * 1024 * 1024: # 10 MB
            return False

        for line in open(item):
            if line.find("[[[end]]]") != -1:
                return True

        return False

    # ---------------------------------------------------------------------------
    @classmethod
    def Clean(cls, context, status_stream, verbose_stream):
        # Override clean, as it has a very different meaning since operations are 
        # performed in place.
        output_stream.write("Restoring '{}'...".format(context.output_filename))
        with StreamDecorator(status_stream).DoneManager() as dm:
            result = subprocess.Popen( cls._CreateCommandLine(context, is_clean=True),
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       shell=True,
                                       encoding="ansi",
                                     )

            content = result.stdout.read()
            dm.result = result.wait() or 0

            if dm.result != 1:
                dm.stream.write(content)
            else:
                verbose_stream.write(content)

            return dm.result

    # ---------------------------------------------------------------------------
    @classmethod
    def CreateInvokeCommandLine(cls, context, verbose_stream):
        return cls._CreateCommandLine(context, is_clean=False)

    # ---------------------------------------------------------------------------
    # |
    # |  Private Methods
    # |
    # ---------------------------------------------------------------------------
    
    # ---------------------------------------------------------------------------
    @classmethod
    def _GetOptionalMetadata(cls):
        return [ ( "defines", {} ),
               ] + \
               super(CodeGenerator, cls)._GetOptionalMetadata()

    # ---------------------------------------------------------------------------
    @classmethod
    def _PostprocessContextItem(cls, context):
        context.output_filename = context.input_filename

        return super(CodeGenerator, cls)._PostprocessContextItem(context)

    # ---------------------------------------------------------------------------
    @classmethod
    def _CreateCommandLine(cls, context, is_clean):
        return '"{script}" -r{flag} {defines} "{file}"'.format \
                    ( script=Shell.GetEnvironment().CreateScriptName("cog"),
                      flag='x' if is_clean else 'c',
                      file=context.input_filename,
                      defines=' '.join([ '-D "{}={}"'.format(k, v) for k, v in context.defines.iteritems() ]),
                    )

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( input=CommandLine.FilenameTypeInfo(match_any=True, arity='+'),
                                  define=CommandLine.DictTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def Generate( input,                          # <Redefining build-in type> pylint: disable = W0622
              define=None,
              output_stream=sys.stdout,
              verbose=False,
            ):
    return CodeGeneratorMod.CommandLineGenerate( CodeGenerator,
                                                 input,
                                                 output_stream,
                                                 verbose,

                                                 defines=define,
                                               )

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( input=CommandLine.FilenameTypeInfo(match_any=True, arity='+'),
                                  output_stream=None,
                                )
def Clean( input,
           output_stream=sys.stdout,
           verbose=False,
         ):
    return CodeGeneratorMod.CommandLineClean( CodeGenerator,
                                              input,
                                              output_stream,
                                              verbose,
                                            )

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
