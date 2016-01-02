# ---------------------------------------------------------------------------
# |  
# |  PythonCodeCoverageExtractor.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/20/2015 05:04:10 PM
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
<Used by other scripts>
"""

import os
import re
import subprocess
import sys
import textwrap

from collections import OrderedDict
from xml.etree import ElementTree as ET

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CodeCoverageExtractor as CodeCoverageExtractorMod
from CommonEnvironment import Interface
from CommonEnvironment import Shell
from CommonEnvironment.TimeDelta import TimeDelta

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

@Interface.staticderived
class CodeCoverageExtractor(CodeCoverageExtractorMod.CodeCoverageExtractor):
    """\
    Extracts code coverage information from python files. Coverage includes and
    excludes are extracted from comments embedded in the source.

    Available comments are:

        # code_coverage: disable

        # code_coverage: include = Relative or full path to Python File #1
        # code_coverage: include = Relative or full path to Python File #2
        # ...
        # code_coverage: include = Relative or full path to Python File #N

        # code_coverage: exclude = Relative or full path to Python File #1
        # code_coverage: exclude = Relative or full path to Python File #2
        # ...
        # code_coverage: exclude = Relative or full path to Python File #N

    Note that if no values are extracted from the source, the code will make
    a best-guess to find the production code, assuming that the executed filename
    ends with _*Test.py
    """

    # ---------------------------------------------------------------------------
    # |  Public Properties
    Name                                    = "Python"
    Description                             = "Extracts code coverage information for Python source code using coverage.py"

    # ---------------------------------------------------------------------------
    # |  Public Methods
    @staticmethod
    def ValidateEnvironment():
        # No explicit environment requirements
        return

    # ---------------------------------------------------------------------------
    @staticmethod
    def IsSupportedCompiler(compiler):
        # Supports any compiler that supports python - use this file as a test subject
        return compiler.IsSupported(_script_fullpath if os.path.splitext(_script_name)[1] == ".py" else "{}.py".format(os.path.splitext(_script_fullpath)[0]))

    # ---------------------------------------------------------------------------
    @staticmethod
    def Execute( compiler,
                 context,
                 command_line,
                 includes=None,
                 excludes=None,
                 verbose=False,
               ):
        assert command_line
        
        includes = includes or []
        excludes = excludes or []

        # Get the name of the script to execute
        if command_line.lower().startswith("python"):
            filename = command_line[len("python"):].replace('"', '').strip()
            assert os.path.isfile(filename), filename
        else:
            filename = command_line

        # Attempt to extract include and exclude information from the source
        disable_code_coverage = False

        if not disable_code_coverage and not includes and not excludes:
            # <Wrong indentation> pylint: disable = C0330
            regex = re.compile(textwrap.dedent(
               r"""(?#
                Header          )^.*?#\s*(?#
                Label           )code_coverage\s*:\s*(?#
                Action          )(?P<action>\S+)(?#
                +Optional       )(?:(?#
                    Assignment  )\s*=\s*(?#
                    +Quote      )(?P<quote>")?(?#
                    Name        )(?P<name>.+?)(?#
                    -Quote      )(?P=quote)?(?#
                -Optional       ))?(?#
                Suffix          )\s*$(?#
                )"""))

            for index, line in enumerate(open(filename).readlines()):
                match = regex.match(line)
                if not match:
                    continue

                action = match.group("action").lower()

                if action == "disable":
                    disable_code_coverage = True

                elif action in [ "include", "exclude", ]:
                    referenced_filename = match.group("name")
                    referenced_filename = os.path.abspath(os.path.join(os.path.dirname(filename), referenced_filename))

                    if not os.path.isfile(referenced_filename):
                        raise Exception("'{}', referenced on line {}, is not a valid filename".format(referenced_filename, index + 1))

                    if action == "include":
                        includes.append(referenced_filename)
                    elif action == "exclude":
                        excludes.append(referenced_filename)
                    else:
                        assert False

                else:
                    raise Exception("'{}' is not a supported action".format(action))

        # Attempt to determine include and exclude information based on the original filename
        if not disable_code_coverage and not includes and not excludes:
            includes.append(compiler.GetSystemUnderTest(filename))
    
        if disable_code_coverage:
            from NoopCodeCoverageExtractor import CodeCoverageExtractor as NoopCodeCoverageExtractor

            return NoopCodeCoverageExtractor().Execute( compiler,
                                                        context,
                                                        'python "{}"'.format(filename),
                                                      )

        # Run the process and calculate the code coverage
        results = CodeCoverageExtractorMod.Results()

        # Create the python file that will run with code coverage
        environment = Shell.GetEnvironment()

        temp_filename = environment.CreateTempFilename(".py")

        with open(temp_filename, 'w') as f:
            f.write(textwrap.dedent(
                """\
                from coverage.cmdline import main

                main()
                """))

        with CallOnExit(lambda: os.remove(temp_filename)):
            command_line_template = 'python "%s" "{}"' % temp_filename

            # Run the process
            start_time = TimeDelta()

            command_line = '{template} "{filename}"'.format( template=command_line_template.format("run"),
                                                             filename=filename,
                                                           )
            result = subprocess.Popen( command_line,
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                     )

            results.test_output = result.stdout.read()
            results.test_result = result.wait() or 0
            results.test_duration = start_time.CalculateDelta(as_string=True)

            # Get the code coverage info
            xml_temp_filename = environment.CreateTempFilename(".xml")
        
            start_time = TimeDelta()

            command_line = '{template} -o "{output}" {includes} {excludes}'.format( template=command_line_template.format("xml"),
                                                                                    output=xml_temp_filename,
                                                                                    includes='"--include={}"'.format(','.join(includes)) if includes else '',
                                                                                    excludes='"--omit={}"'.format(','.join(excludes)) if excludes else '',
                                                                                  )
            result = subprocess.Popen( command_line,
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                     )
            results.coverage_output = result.stdout.read()
            results.coverage_result = result.wait() or 0
            results.coverage_duration = start_time.CalculateDelta(as_string=True)

            results.data = xml_temp_filename

        # Get the percentage info
        if results.coverage_result != 0 or not os.path.isfile(results.data):
            results.total_percentage = 0.0
            results.individual_percentages = {}
        else:
            root = ET.fromstring(open(results.data).read())

            results.total_percentage = float(root.attrib["line-rate"]) * 100
            results.individual_percentages = OrderedDict()

            for package in root.findall("packages/package"):
                for class_ in package.findall("classes/class"):
                    results.individual_percentages[class_.attrib["filename"]] = float(class_.attrib["line-rate"]) * 100

        return results
