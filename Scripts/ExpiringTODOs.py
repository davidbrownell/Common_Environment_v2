# ----------------------------------------------------------------------
# |  
# |  ExpiringTODOs.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-03-08 17:33:04
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import datetime
import os
import re
import sys
import textwrap

import inflect

from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment.StreamDecorator import StreamDecorator

from CommonEnvironment.TypeInfo.FundamentalTypes.DateTypeInfo import DateTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import StringSerialization

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect_engine = inflect.engine()

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( code_dir=CommandLine.DirectoryTypeInfo(),
                                  output_stream=None,
                                )
def EntryPoint( code_dir,
                verbose=False,
                output_stream=sys.stdout,
              ):
    data = QuickObject( files=0, 
                        comments=0, 
                        failures=0, 
                      )

    output_stream.write("Processing '{}'...".format(code_dir))
    with StreamDecorator(output_stream).DoneManager( done_suffix_functor=lambda: "{}, {}, {}".format( inflect_engine.no("file", data.files),
                                                                                                      inflect_engine.no("comment", data.comments),
                                                                                                      inflect_engine.no("failure", data.failures),
                                                                                                    ),
                                                   ) as dm:
        regex = re.compile(textwrap.dedent(
           r"""(?#
            TODO                    )TODO\s+(?#
            [Optional] by           )(?:by\s+)?(?#
            [Optional] Left Brace   )(?:[\(\[])?\s*(?#
            Date                    )(?P<date>%s)(?#
            [Optional] Right Brace  )(?:[\)\]])?(?#
            )""") % StringSerialization.GetRegularExpressionString(DateTypeInfo()))

        filenames = list(FileSystem.WalkFiles( code_dir,
                                               traverse_exclude_dir_names=FileSystem.CODE_EXCLUDE_DIR_NAMES,
                                               exclude_file_extensions=FileSystem.CODE_EXCLUDE_FILE_EXTENSIONS,
                                               # If the filename is bigger than N Mb, we probably aren't looking at a source
                                               # code file. N Mb is an arbitrary number.
                                               include_full_paths=lambda filename: os.path.getsize(filename) < 10 * 1024 * 1024,
                                             ))

        today = datetime.date.today()
        date_type_info = DateTypeInfo()

        for index, filename in enumerate(filenames):
            data.files += 1

            dm.stream.write("Scanning '{}' ({} of {})...".format( filename,
                                                                  index + 1,
                                                                  len(filenames),
                                                                ))
            with dm.stream.DoneManager() as this_dm:
                verbose_stream = StreamDecorator(this_dm.stream if verbose else None, line_prefix="INFO: ")
                error_stream = StreamDecorator(this_dm.stream, line_prefix="ERROR: ")

                for line_index, line in enumerate(open(filename).readlines()):
                    match = regex.search(line)
                    if not match:
                        continue

                    data.comments += 1

                    date = date_type_info.FromString(match.group("date"))
                    
                    verbose_stream.write("Found comment expiring on {} ({} [{}])\n".format( date_type_info.ToString(date),
                                                                                            filename,
                                                                                            line_index + 1,
                                                                                          ))

                    if date < today:
                        data.failures += 1
                        this_dm.result = -1

                        error_stream.write(textwrap.dedent(
                            """\

                            The comment has expired:
                                Source:         {}
                                Line:           {}
                                Expiration:     {}
                                Comment:        {}

                            """).format( filename,
                                         line_index + 1,
                                         date_type_info.ToString(date),
                                         line.strip(),
                                       ))

        return dm.result

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
