# ---------------------------------------------------------------------------
# |  
# |  Results.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/30/2015 07:56:59 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import datetime
import os
import re
import sys
import textwrap

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

class Results(object):

    # ---------------------------------------------------------------------------
    def __init__(self):
        self.context                        = None

        self.compile_binary                 = None
        self.compile_result                 = None
        self.compile_log                    = None
        self.compile_time                   = None

        self.test_result                    = None
        self.test_log                       = None
        self.test_time                      = None

        self.test_parse_result              = None
        self.test_parse_time                = None

        self.coverage_data                  = None
        self.coverage_result                = None
        self.coverage_log                   = None
        self.coverage_time                  = None

        self.coverage_percentage            = None
        self.coverage_percentages           = None

        self.coverage_validation_result     = None
        self.coverage_validation_min        = None

    # ---------------------------------------------------------------------------
    def CompositeResult(self):
        results = [ self.compile_result,
                    self.test_result,
                    self.test_parse_result,
                    self.coverage_result,
                    self.coverage_validation_result,
                  ]

        found_value = False
        for result in results:
            if result:
                return result

            if result == 0:
                found_value = True

        return 0 if found_value else None

    # ---------------------------------------------------------------------------
    def __str__(self):
        return self.ToString(None, None, None, None)

    # ---------------------------------------------------------------------------
    def ToString( self,
                  optional_compiler,
                  optional_test_parser,
                  optional_code_coverage_extractor,
                  optional_code_coverage_validator,
                ):
        composite_result = self.CompositeResult()
        if composite_result == None:
            return "Result:                                         {}".format(self._ResultToString(composite_result))

        return textwrap.dedent(
            """\
            Result:                                         {composite_result}

            {compiler}    Compile Result:                             {compile_result}
                Compile Binary:                             {compile_binary}
                Compile Log Filename:                       {compile_log}
                Compile Time:                               {compile_time}

            {test_parser}    Test Execution Result:                      {test_result}
                Test Execution Log Filename:                {test_log}
                Test Execution Time:                        {test_time}
                
                Test Parse Result:                          {test_parse_result}
                Test Parse Time:                            {test_parse_time}

            {code_coverage_extractor}    Code Coverage Extraction Result:            {coverage_result}
                Code Coverage Extraction Log Filename:      {coverage_log}
                Code Coverage Extraction Time:              {coverage_time}
                Code Coverage Extraction Data:              {coverage_data}
                Code Coverage Percentage:                   {coverage_percentage}
                Code Coverage Percentages:                  {coverage_percentages}

            {code_coverage_validator}    Code Coverage Validation Result:            {validation_result}
                Code Coverage Minimum Percentage:           {validation_min}
            """).format( composite_result=self._ResultToString(composite_result),
                         
                         compiler="[Compiler: {}]\n\n".format(optional_compiler.Name) if optional_compiler else '',
                         compile_result=self._ResultToString(self.compile_result),
                         compile_binary=self.compile_binary or "N/A",
                         compile_log=self.compile_log or "N/A",
                         compile_time=self.compile_time or "N/A",
                         
                         test_parser="[Test Parser: {}]\n\n".format(optional_test_parser.Name) if optional_test_parser else '',
                         test_parse_result=self._ResultToString(self.test_parse_result),
                         test_parse_time=self.test_parse_time or "N/A",
                         test_result=self._ResultToString(self.test_result),
                         test_log=self.test_log or "N/A",
                         test_time=self.test_time or "N/A",

                         code_coverage_extractor="[Code Coverage Extractor: {}]\n\n".format(optional_code_coverage_extractor.Name) if optional_code_coverage_extractor else '',
                         coverage_result=self._ResultToString(self.coverage_result),
                         coverage_log=self.coverage_log or "N/A",
                         coverage_time=self.coverage_time or "N/A",
                         coverage_data=self.coverage_data or "N/A",

                         code_coverage_validator="[Code Coverage Validator: {}]\n\n".format(optional_code_coverage_validator.Name) if optional_code_coverage_validator else '',
                         validation_result=self._ResultToString(self.coverage_validation_result),
                         validation_min="{}%".format(self.coverage_validation_min) if self.coverage_validation_min != None else "N/A",
                         coverage_percentage="{}%".format(self.coverage_percentage) if self.coverage_percentage != None else "N/A",
                         coverage_percentages="N/A" if self.coverage_percentages == None else "\n{}".format('\n'.join([ "        - [{value:<7}] {name}".format(value="{0:0.2f}%".format(percentage), name=name) for name, percentage in self.coverage_percentages.iteritems() ])),
                       )
        
    # ---------------------------------------------------------------------------
    def TotalTime(self):
        parser = re.compile(r"(?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d+(?:\.\d+)?)")
        
        # ---------------------------------------------------------------------------
        def ToTimeDelta(value):
            match = parser.match(value)
            assert match, value

            return datetime.timedelta( hours=int(match.group("hours")),
                                       minutes=int(match.group("minutes")),
                                       seconds=float(match.group("seconds")),
                                     )

        # ---------------------------------------------------------------------------
        
        total_time = datetime.timedelta(seconds=0)

        if self.compile_result != None: total_time += ToTimeDelta(self.compile_time)
        if self.test_result != None: total_time += ToTimeDelta(self.test_time)
        if self.test_parse_result != None: total_time += ToTimeDelta(self.test_parse_time)
        if self.coverage_result != None: total_time += ToTimeDelta(self.coverage_time)

        return str(total_time)

    # ---------------------------------------------------------------------------
    @staticmethod
    def _ResultToString(result):
        if result == None:
            return "N/A"
        if result == 0:
            return "Succeeded"
        if result < 0:
            return "Failed ({})".format(result)
        if result > 0:
            return "Unknown ({})".format(result)

        assert False, result