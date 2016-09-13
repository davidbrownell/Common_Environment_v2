# ---------------------------------------------------------------------------
# |  
# |  PythonVerifier.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/01/2015 09:17:54 PM
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
Verifies Python source code
"""

import os
import re
import subprocess
import sys
import textwrap
import time

from StringIO import StringIO

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import Interface
from CommonEnvironment import Shell

from CommonEnvironment.Compiler import Verifier as VerifierMod
from CommonEnvironment.Compiler.InvocationMixin.CustomInvocationMixin import CustomInvocationMixin

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
@Interface.staticderived                    # <Not Implemented> pylint: disable = R0923
class Verifier( CustomInvocationMixin,
                VerifierMod.Verifier,
              ):
    # ---------------------------------------------------------------------------
    # |
    # |  Public Properties
    # |
    # ---------------------------------------------------------------------------
    Name                                    = "PyLint"
    Description                             = "Statically analyzes Python source code, reporting common mistakes and errors."

    DEFAULT_PASSING_SCORE                   = 9.0
    
    CONFIGURATION_ENVIRONMENT_VAR_NAME      = "DEVELOPMENT_ENVIRONMENT_PYTHON_VERIFIER_CONFIGURATION"   # Default is "PythonVerifier.default_configuration"

    # ---------------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ---------------------------------------------------------------------------
    @staticmethod
    def IsSupported(item):
        path, filename = os.path.split(item)
        name, ext = os.path.splitext(filename)

        return ext.lower() in [ ".py", ] and name not in [ "Build", ]

    # ---------------------------------------------------------------------------
    @staticmethod
    def IsSupportedTestFile(item):
        name, ext = os.path.splitext(os.path.basename(item))
        return ext.lower() in [ ".py", ] and name != "__init__"
        
    # ---------------------------------------------------------------------------
    @staticmethod
    def ItemNameToTestName(item_name, test_name):
        path, filename = os.path.split(item_name)
        filename, ext = os.path.splitext(filename)

        return os.path.join(path, test_name, "{filename}_{test_name}{ext}".format( filename=filename,
                                                                                   test_name=test_name[:-1] if test_name[-1] == 's' else test_name,
                                                                                   ext=ext,
                                                                                 ))

    # ---------------------------------------------------------------------------
    @staticmethod
    def GetSystemUnderTest(test_filename):
        path, name = os.path.split(test_filename)
        if name == "__init__.py":
            return test_filename

        match = re.match( r"^(?P<name>.+)_(?P<test_type>.+?Test)(?P<ext>\..+)$",
                          name,
                        )
        if not match:
            return test_filename

        name = "{}{}".format(match.group("name"), match.group("ext"))
        test_type = match.group("test_type")

        if path and os.path.basename(path) == "{}{}".format(test_type, '' if test_type[-1] == 's' else 's'):
            path = os.path.dirname(path)

        return os.path.join(path, name)
        
    # ---------------------------------------------------------------------------
    # |
    # |  Private Methods
    # |
    # ---------------------------------------------------------------------------
    @classmethod
    def _GetOptionalMetadata(cls):
        return [ ( "passing_score", None ),
               ] + super(Verifier, cls)._GetOptionalMetadata()

    # ---------------------------------------------------------------------------
    @classmethod
    def _PostprocessContextItem(cls, context):
        if context.passing_score == None:
            context.passing_score = cls.DEFAULT_PASSING_SCORE
            context.explicit_passing_score = False
        else:
            context.explicit_passing_score = True

        return super(Verifier, cls)._PostprocessContextItem(context)

    # ---------------------------------------------------------------------------
    @classmethod
    def _InvokeImpl( cls,
                     invoke_reason,
                     context,
                     status_stream,
                     output_stream,
                   ):                       # <Too many local variables> pylint: disable = R0914
        environment = Shell.GetEnvironment()

        # If the file being invoked is a test file, measure the file under
        # test rather than the test itself.
        filename = cls.GetSystemUnderTest(context.input_filename)
        assert os.path.isfile(filename), filename

        # Create the lint file
        configuration_file = os.getenv(cls.CONFIGURATION_ENVIRONMENT_VAR_NAME) or os.path.join(_script_dir, "PythonVerifier.default_configuration")
        assert os.path.isfile(configuration_file), configuration_file

        temp_filename = environment.CreateTempFilename(".py")
        with open(temp_filename, 'w') as f:
            f.write(textwrap.dedent(
                """\
                import sys

                from pylint import lint

                lint.Run([ r"--rcfile={config}",
                           r"--msg-template={{path}}({{line}}): [{{msg_id}}] {{msg}}",
                           r"{filename}",
                         ])
                """).format( config=configuration_file,
                             filename=filename,
                           ))

        # ---------------------------------------------------------------------------
        def SafeDelete():
            # There have been periodic errors when attempting to delete this file
            # (file in use). If that happens, wait and then try again.
            retries = 0

            while True:
                try:
                    os.remove(temp_filename)
                    break
                except:
                    if retries == 5:
                        raise

                    time.sleep(1) # seconds
                    retries += 1

        # ---------------------------------------------------------------------------
        
        with CallOnExit(SafeDelete):
            # Run the generated file
            command_line = 'python "{}"'.format(temp_filename)

            result = subprocess.Popen( command_line,
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                     )
            sink = StringIO()

            while True:
                content = result.stdout.readline()
                if not content:
                    break

                output_stream.write(content)
                sink.write(content)

            result = result.wait() or 0
            
            output_stream.write("\n\n")
            sink = sink.getvalue()

            # Extract the results
            match = re.search(r"Your code has been rated at (?P<score>[-\d\.]+)/(?P<max>[\d\.]+)", sink, re.MULTILINE)
            if not match:
                return -1

            score = float(match.group("score"))
            max_score = float(match.group("max"))
            assert max_score != 0.0

            # Don't meausre scores for files in Impl directories
            is_impl_file = os.path.split(os.path.dirname(filename))[1].endswith("Impl")

            if (not is_impl_file or context.explicit_passing_score) and score < context.passing_score:
                return -1

            return 0

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( input=CommandLine.FilenameTypeInfo(match_any=True, arity='+'),
                                  passing_score=CommandLine.FloatTypeInfo(min=0.0, max=10.0, arity='?'),
                                  output_stream=None,
                                )
def Verify( input,                          # <Redefining build-in type> pylint: disable = W0622
            passing_score=None,
            output_stream=sys.stdout,
            verbose=False,
          ):
    return VerifierMod.CommandLineVerify( Verifier,
                                          input,
                                          output_stream,
                                          verbose,
                                          passing_score=passing_score,
                                        )

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
