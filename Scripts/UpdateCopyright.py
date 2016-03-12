# ---------------------------------------------------------------------------
# |  
# |  UpdateCopyright.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  01/01/2016 06:12:15 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""\
Iterates through a directory of files looking for common copyright signatures.
When one is encountered, it will be updated to include the current year.
"""

import io
import inflect
import os
import re
import sys
import time
import traceback

from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment.StreamDecorator import StreamDecorator

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

COPYRIGHT_EXPRESSIONS = [ re.compile(r".*?Copyright \(c\) (?P<copyright>\S*).*"),   # Matches 'Copyright (c) 2011-16 David Brownell. Permission to use, copy, '
                          re.compile(r".*?Copyright (?P<copyright>[^\.]+)\..*"),    # Matches 'Copyright David Brownell 2011.'
                        ]
      
# The following expressions must have a 'begin' capture; 'end' is optional.                        
YEAR_EXPRESSIONS = [ re.compile(r"(?P<begin>\d{4})-(?P<end>\d{2,4})"),              # Matches multi-year range
                     re.compile(r"(?P<begin>\d{4})"),                               # Matches single year
                   ]

MAX_FILE_SIZE = 100 * 1024 * 1024       # 100 Mb

# ---------------------------------------------------------------------------
plural = inflect.engine()

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( code_dir=CommandLine.DirectoryTypeInfo(),
                                  year=CommandLine.IntTypeInfo(min=1, max=10000, arity='?'),
                                  output_stream=None,
                                )
def EntryPoint( code_dir,
                year=None,
                output_stream=sys.stdout,
                verbose=False,
              ):
    year = year or str(time.localtime()[0])
    two_digit_year = str(int(year) % 100)

    updates = [ 0, ]

    # ---------------------------------------------------------------------------
    def GlobalDoneSuffix():
        return "{} {} updated".format( plural.no("file", updates[0]),
                                       plural.plural_verb("was", updates[0]),
                                     )

    # ---------------------------------------------------------------------------
    
    output_stream.write("Processing files in '{}'...".format(code_dir))
    with StreamDecorator(output_stream).DoneManager( display_exceptions=False,
                                                     done_suffix_functor=GlobalDoneSuffix,
                                                   ) as dm:
        for fullpath in FileSystem.WalkFiles( code_dir,
                                              exclude_file_extensions=[ ".pyc", ".pyo", ".obj", ".pdb", ".idb", ],
                                              traverse_exclude_dir_names=[ "Generated", lambda name: name[0] == '.', ],
                                            ):
            try:
                if os.path.getsize(fullpath) > MAX_FILE_SIZE:
                    if verbose:
                        dm.stream.write("INFO: '{}' is too large to process.\n".format(fullpath))
                    continue

                copyright_updated = [ False, ]

                # ---------------------------------------------------------------------------
                def DoneSuffix():
                    if copyright_updated[0]:
                        return "***** Copyright was updated *****"

                # ---------------------------------------------------------------------------
                
                dm.stream.write("Processing '{}'...".format(fullpath))
                with dm.stream.DoneManager( done_suffix_functor=DoneSuffix,
                                          ) as file_dm:
                    with io.open(fullpath, 'r') as f:
                        try:
                            lines = f.read().split('\n')
                            newline_char = (f.newlines[0] if isinstance(f.newlines, tuple) else f.newlines) or '\r\n'
                    
                        except (UnicodeDecodeError, MemoryError):
                            if verbose:
                                file_dm.stream.write("INFO: '{}' appears to be a binary file name cannot be processed.\n".format(fullpath))
                            continue

                    for index, line in enumerate(lines):
                        for copyright_expr in COPYRIGHT_EXPRESSIONS:
                            copyright_match = copyright_expr.match(line)
                            if not copyright_match:
                                continue

                            copyright = copyright_match.group("copyright")

                            year_match = None
                            for year_expr in YEAR_EXPRESSIONS:
                                year_match = year_expr.search(copyright)
                                if year_match:
                                    break

                            if not year_match:
                                file_dm.stream.write("WARNING: '{}' appears to have a copyright, but it isn't in an expected format ('{}') [0].\n".format(fullpath, line.strip()))
                                continue

                            begin = year_match.group("begin")
                            end = year_match.group("end") if "end" in year_match.groupdict() else begin

                            if len(end) == 2:
                                end = str(((int(year) / 100) * 100) + int(end))

                            if len(begin) != 4:
                                file_dm.stream.write("WARNING: '{}' appears to have a copyright, but it isn't in an expected format ('{}') [1].\n".format(fullpath, line.strip()))
                                continue

                            if len(end) != 4:
                                file_dm.stream.write("WARNING: '{}' appears to have a copyright, but it isn't in an expected format ('{}') [2].\n".format(fullpath, line.strip()))
                                continue

                            if end == year:
                                continue

                            copyright = "{}{}{}".format( copyright[:year_match.start()],
                                                         "{}-{}".format(begin, two_digit_year),
                                                         copyright[year_match.end():],
                                                       )

                            line = "{}{}{}".format( line[:copyright_match.start() + copyright_match.start("copyright")],
                                                    copyright,
                                                    line[copyright_match.end("copyright"):],
                                                  )

                            lines[index] = line
                            copyright_updated[0] = True

                    if copyright_updated[0]:
                        file_dm.stream.write("Updating...")
                        with file_dm.stream.DoneManager():
                            with io.open(fullpath, 'w', newline=newline_char) as f:
                                f.write('\n'.join(lines))

                        updates[0] += 1
                
            except:
                content = traceback.format_exc()
                output_stream.write("ERROR: {}".format(StreamDecorator.LeftJustify(content, len("ERROR: "))))

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
