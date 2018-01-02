# ---------------------------------------------------------------------------
# |  
# |  CompleteResults.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/01/2015 09:14:21 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-18.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import sys
import textwrap

from .Results import Results

from CommonEnvironment.StreamDecorator import StreamDecorator

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
class CompleteResults(object):

    # ---------------------------------------------------------------------------
    def __init__(self, item):
        self.Item                           = item
        self.debug                          = Results()
        self.release                        = Results()

    # ---------------------------------------------------------------------------
    def CompositeResult(self):
        found_value = False

        for results in [ self.debug,
                         self.release,
                       ]:
            if results == None:
                continue

            result = results.CompositeResult()
            if result:
                return result

            found_value = found_value or result == 0

        return 0 if found_value else None

    # ---------------------------------------------------------------------------
    def __str__(self):
        return self.ToString(None, None, None, None)

    # ---------------------------------------------------------------------------
    def ToString( self,
                  compiler,
                  test_parser,
                  code_coverage_extractor,
                  code_coverage_validator,
                ):
        header_length = max(80, len(self.Item) + 4)

        return textwrap.dedent(
            """\
            {header}
            |{item:^{item_length}}|
            {header}

            DEBUG:
            {debug}

            RELEASE:
            {release}
            """).format( header='=' * header_length,
                         item=self.Item,
                         item_length=header_length - 2,
                         debug="N/A" if not self.debug else StreamDecorator.LeftJustify(self.debug.ToString(compiler, test_parser, code_coverage_extractor, code_coverage_validator), 4, skip_first_line=False),
                         release="N/A" if not self.release else StreamDecorator.LeftJustify(self.release.ToString(compiler, test_parser, code_coverage_extractor, code_coverage_validator), 4, skip_first_line=False),
                       )
