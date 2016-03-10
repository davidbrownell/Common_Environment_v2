# ----------------------------------------------------------------------
# |  
# |  RecursiveDoxygen.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-03-10 07:41:05
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Recursively generates Doxygen documentation."""

import os
import re
import shutil
import sys
import textwrap

from collections import OrderedDict

import inflect

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect_engine = inflect.engine()

# ----------------------------------------------------------------------
DOXYGEN_EXTENSION                           = ".doxygen"
DOXYGEN_EXTENSION_IGNORE                    = "{}-ignore".format(DOXYGEN_EXTENSION)

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( code_dir=CommandLine.DirectoryTypeInfo(),
                                  output_dir=CommandLine.DirectoryTypeInfo(ensure_exists=False),
                                  output_stream=None,
                                )
def EntryPoint( code_dir,
                output_dir,
                output_stream=sys.stdout,
                verbose=False,
              ):
    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     done_prefix="\n\nComposite Results:",
                                                   ) as dm:
        # Get the doxygen files
        doxygen_files = []

        dm.stream.write("Searching for doxygen files in '{}'...".format(code_dir))
        with dm.stream.DoneManager(done_suffix='\n') as this_dm:
            for fullpath in FileSystem.WalkFiles( code_dir,
                                                  include_file_extensions=[ DOXYGEN_EXTENSION, ],
                                                  traverse_exclude_dir_names=FileSystem.CODE_EXCLUDE_DIR_NAMES,
                                                ):
                if not os.path.isfile("{}{}".format(os.path.splitext(fullpath)[0], DOXYGEN_EXTENSION_IGNORE)):
                    doxygen_files.append(fullpath)

        if not doxygen_files:
            return dm.result

        # Process the files

        # ----------------------------------------------------------------------
        class GetDoxygenValueError(KeyError):
            """\
            Exception raised when a doxygen tag is not found.
            """
            pass

        # ----------------------------------------------------------------------
        def GetDoxygenValue(tag, content):
            match = re.search( r"{}\s*=\s*(?P<value>.*)\r?\n".format(re.escape(tag)),
                               content,
                               re.IGNORECASE,
                             )
            if not match:
                raise GetDoxygenValueError("Unable to find '{}' if the doxygen configuration file".format(tag))

            return match.group("value")

        # ----------------------------------------------------------------------
        
        results = OrderedDict()
        tagfiles = OrderedDict()

        dm.stream.write("Processing {}...".format(inflect_engine.no("doxygen file", len(doxygen_files))))
        with dm.stream.DoneManager(done_suffix='\n') as doxygen_dm:
            for index, doxygen_file in enumerate(doxygen_files):
                doxygen_dm.stream.write("Processing '{}' ({} of {})...".format( doxygen_file, 
                                                                                index + 1,
                                                                                len(doxygen_files),
                                                                              ))
                with doxygen_dm.stream.DoneManager() as this_dm:
                    current_dir = os.getcwd()

                    os.chdir(os.path.dirname(doxygen_file))
                    with CallOnExit(lambda: os.chdir(current_dir)):
                        # Execute
                        this_dm.result = Process.Execute( 'dot -c && doxygen "{}"'.format(doxygen_file),
                                                          StreamDecorator(this_dm.stream if verbose else None),
                                                        )
                        if this_dm.result != 0:
                            continue

                        # Extract data from the doxygen file
                        content = open(doxygen_file).read()

                        project_name = GetDoxygenValue("PROJECT_NAME", content)

                        # Older doxygen files don't have a PROJECT_VERSION tag
                        try: 
                            project_version = GetDoxygenValue("PROJECT_VERSION", content)
                        except GetDoxygenValueError:
                            project_version = GetDoxygenValue("PROJECT_NUMBER", content)

                        output_directory = GetDoxygenValue("OUTPUT_DIRECTORY", content)

                        source_dir = os.path.dirname(doxygen_file)
                        if output_directory:
                            output_directory = os.path.join(source_dir, output_directory)

                        dest_dir = os.path.join(output_dir, project_name)
                        if project_version:
                            dest_dir = os.path.join(dest_dir, project_version)

                        dest_dir = dest_dir.replace('"', '').strip()
                        if not os.path.isdir(dest_dir):
                            os.makedirs(dest_dir)

                        for content_type in [ "html",
                                              "Latex",
                                              "RTF",
                                              "man",
                                              "XML",
                                            ]:
                            value = GetDoxygenValue("GENERATE_{}".format(content_type), content)
                            if not value or value.lower() != "yes":
                                continue

                            output_name = GetDoxygenValue("{}_OUTPUT".format(content_type), content)

                            source_fullpath = os.path.join(source_dir, output_name)
                            dest_fullpath = os.path.join(dest_dir, output_name)

                            if not os.path.isdir(source_fullpath):
                                this_dm.stream.write("ERROR: The directory '{}' does not exist.\n".format(source_fullpath))
                                this_dm.result = -1
                                continue

                            if os.path.isdir(dest_fullpath):
                                shutil.rmtree(dest_fullpath)

                            shutil.move(source_fullpath, dest_fullpath)
                            results.setdefault(doxygen_file, OrderedDict())[content_type] = dest_fullpath

                        # Tagfile
                        value = GetDoxygenValue("GENERATE_TAGFILE", content)
                        if value:
                            source_fullpath = os.path.join(source_dir, value)
                            dest_fullpath = os.path.join(dest_dir, value)

                            if not os.path.isfile(source_fullpath):
                                this_dm.stream.write("ERROR: The filename '{}' does not exist.\n".format(source_fullpath))
                                this_dm.result = -1
                            else:
                                if os.path.isfile(dest_fullpath):
                                    os.remove(dest_fullpath)

                                shutil.move(source_fullpath, dest_fullpath)
                                
                                results.setdefault(doxygen_file, OrderedDict())["tagfile"] = dest_fullpath

        # Generate the output file
        output_filename = os.path.join(output_dir, "RecursiveDoxygen.xml")

        dm.stream.write("Writing '{}'...".format(output_filename))
        with dm.stream.DoneManager() as this_dm:
            with open(output_filename, 'w') as f:
                f.write("<locations>\n")
                with CallOnExit(lambda: f.write("</locations>\n")):
                    input_filename_stream = StreamDecorator(f, line_prefix="    ")
                    type_stream = StreamDecorator(input_filename_stream, line_prefix="    ")

                    for input_filename, types in results.iteritems():
                        input_filename_stream.write('<location name="{}">\n'.format(input_filename))
                        with CallOnExit(lambda: input_filename_stream.write("</location>\n")):
                            for type, output in types.iteritems():
                                type_stream.write('<type name="{}">{}</type>\n'.format(type, output))

        return dm.result

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
