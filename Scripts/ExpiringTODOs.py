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
import threading

import inflect

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import TaskPool

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
                output_stream=sys.stdout,
                verbose=False,
              ):
    data = QuickObject( files=0, 
                        comments=0, 
                        failures=0, 
                      )
    data_lock = threading.Lock()
    
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
            )""") % '|'.join(StringSerialization.GetRegularExpressionStringInfo(DateTypeInfo())))

        filenames = list(FileSystem.WalkFiles( code_dir,
                                               traverse_exclude_dir_names=FileSystem.CODE_EXCLUDE_DIR_NAMES,
                                               exclude_file_extensions=FileSystem.CODE_EXCLUDE_FILE_EXTENSIONS,
                                               # If the filename is bigger than N Mb, we probably aren't looking at a source
                                               # code file. N Mb is an arbitrary number.
                                               include_full_paths=lambda filename: os.path.getsize(filename) < 10 * 1024 * 1024,
                                             ))

        today = datetime.date.today()
        date_type_info = DateTypeInfo()

        # ---------------------------------------------------------------------------
        def Execute(task_index, output_stream):
            task_output_stream = output_stream

            try:
                comments = CommonEnvironment.ModifiableValue(0)
                has_error = CommonEnvironment.ModifiableValue(False)
                
                # ---------------------------------------------------------------------------
                def Cleanup():
                    if comments.value or has_error.value:
                        task_output_stream.write("{}, {}\n".format( inflect_engine.no("comment", comments.value),
                                                                    inflect_engine.no("error", 1 if has_error.value else 0),
                                                                  ))
                        with data_lock:
                            data.comments += comments.value
                            
                        if has_error.value:
                            data.failures += 1
                            
                # ---------------------------------------------------------------------------
                
                with CallOnExit(Cleanup):
                    for line_index, line in enumerate(open(filenames[task_index]).readlines()):
                        match = regex.search(line)
                        if not match:
                            continue
                           
                        comments.value += 1
                            
                        date = StringSerialization.DeserializeItem(date_type_info, match.group("date"))
                        
                        if date < today:
                            has_error.value = True
                                
                            task_output_stream.write(textwrap.dedent(
                                """\
                            
                                The comment has expired:
                                    Source:         {}
                                    Line:           {}
                                    Expiration:     {}
                                    Comment:        {}
                            
                                """).format( filename,
                                             line_index + 1,
                                             StringSerialization.SerializeItem(date_type_info, date),
                                             line.strip(),
                                           ))
                                           
                            return -1
                            
            except IOError:
                pass
                
        # ---------------------------------------------------------------------------

        dm.result = TaskPool.Execute( [ TaskPool.Task( filename,
                                                       "Processing '{}'".format(filename),
                                                       Execute,
                                                     )
                                        for index, filename in enumerate(filenames)
                                      ],
                                      output_stream=dm.stream,
                                      progress_bar=True,
                                      verbose=verbose,
                                    )
                                
        return dm.result

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
