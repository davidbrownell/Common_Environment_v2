# ---------------------------------------------------------------------------
# |  
# |  CleanRepositoryData.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/08/2015 01:58:54 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""\
Activating a repository creates temporary state information that is required while the 
associated environment is active. This script removes that information when it is no
longer useful.
"""

import datetime
import os
import stat
import sys
import textwrap
import time

import six

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment import Shell
from CommonEnvironment.StreamDecorator import StreamDecorator

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

assert os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")
sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
with CallOnExit(lambda: sys.path.pop(0)):
    from SourceRepositoryTools import Constants

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint(delete_days=CommandLine.EntryPoint.ArgumentInfo(description="Delete files that are older than the specified number of days"))
@CommandLine.FunctionConstraints( delete_days=CommandLine.IntTypeInfo(min=0),
                                  output_stream=None,
                                )
def EntryPoint( delete_days=7,
                no_prompt=False,
                output_stream=sys.stdout,
                verbose=False,
              ):
    output_stream = StreamDecorator(output_stream)
    verbose_stream = StreamDecorator(output_stream if verbose else None, line_prefix="INFO: ")

    environment = Shell.GetEnvironment()
    
    # Find the files
    t = time.time()

    output_stream.write("Searching for files...")
    with output_stream.DoneManager():
        file_info = []

        for temp_directory in environment.TempDirectories:
            for filename in FileSystem.WalkFiles(temp_directory, include_file_extensions=[ Constants.TEMPORARY_FILE_EXTENSION, ]):
                name = os.path.splitext(os.path.basename(filename))[0].split('.')
                
                if len(name) == 1:
                    type_ = ''
                    name = name[0]
                else:
                    type_ = name[-1]
                    name = '.'.join(name[:-1])
                    
                age = datetime.timedelta(seconds=t - os.stat(filename)[stat.ST_MTIME]).days
                
                file_info.append(QuickObject( name=name,
                                              type_=type_,
                                              filename=filename,
                                              age=age,
                                              size=os.stat(filename)[stat.ST_SIZE],
                                            ))
    
    output_stream.write('\n')

    if not file_info:
        output_stream.write("No files were found.\n")
        return 0
                
    output_stream.write("{num} {files} {were} found.\n".format( num=len(file_info),
                                                                files="files" if len(file_info) > 1 else "file",
                                                                were="were" if len(file_info) > 1 else "was",
                                                              ))

    verbose_stream.write("Files found:\n{}\n\n".format('\n'.join([ str(f) for f in file_info ])))

    # Trim the list
    file_info = [ fi for fi in file_info if fi.age >= delete_days ]

    if not file_info:
        output_stream.write("No files were found older than '{}' days.\n".format(delete_days))
        return 0

    if not no_prompt:
        total_size = 0
        for fi in file_info:
            total_size += fi.size

        output_stream.write(textwrap.dedent(
            """\
            Would you like to delete the following '{num}' files:

                Name                        Type                Size     Age (days)  Fullpath
                --------------------------  ------------------  -------  ----------  -----------------------------------------------
            {files}

            ? ({total_size}) [y/N] """).format( num=len(file_info),
                                                files='\n'.join([ "    {name:<26}  {type:18}  {size:<7}  {age:<11}  {fullpath}".format( name=fi.name,
                                                                                                                                        type=fi.type_,
                                                                                                                                        size=fi.size,
                                                                                                                                        age=fi.age,
                                                                                                                                        fullpath=fi.filename,
                                                                                                                                      )
                                                                  for fi in file_info
                                                                ]),
                                                total_size=FileSystem.GetSizeDisplay(total_size),
                                              ))
        value = six.moves.input().strip()
        if not value:
            value = 'N'

        value = value.lower()

        if value in [ "0", "n", "no", ]:
            return 0

    output_stream.write("\nRemoving files...")
    with output_stream.DoneManager() as si:
        for index, fi in enumerate(file_info):
            si.stream.write("Removing '{}' [{} of {}]...".format(fi.filename, index + 1, len(file_info)))
            with si.stream.DoneManager() as this_si:
                os.remove(fi.filename)

            si.result = si.result or this_si.result

    return si.result

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
