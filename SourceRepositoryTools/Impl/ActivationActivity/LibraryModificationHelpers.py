# ----------------------------------------------------------------------
# |  
# |  LibraryModificationHelpers.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-09-11 07:35:58
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017-18.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""\
Functionality that helps when activating environments.
"""

import os
import shutil
import sys
import textwrap

from collections import OrderedDict

import six

from CommonEnvironment import ModifiableValue
from CommonEnvironment import FileSystem
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment import Shell
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

from SourceRepositoryTools.Impl import Constants

# ----------------------------------------------------------------------
def GetNewLibraryContent( library_dir, 
                          script_dir,
                          library_ignore_items=None,
                          script_ignore_items=None,
                        ):
    library_ignore_items = library_ignore_items or set()
    script_ignore_items = script_ignore_items or set()

    environment = Shell.GetEnvironment()

    # Get the libraries
    libraries = []

    if library_dir and os.path.isdir(library_dir):
        for item in os.listdir(library_dir):
            if item in library_ignore_items:
                continue
            
            fullpath = os.path.join(library_dir, item)
            if not environment.IsSymLink(fullpath):
                libraries.append(fullpath)

    # Get the scripts
    scripts = []

    if script_dir and os.path.isdir(script_dir):
        for item in os.listdir(script_dir):
            if item in script_ignore_items:
                continue

            fullpath = os.path.join(script_dir, item)

            if not environment.IsSymLink(fullpath):
                scripts.append(fullpath)

    return QuickObject( libraries=libraries,
                        scripts=scripts,
                      )

# ----------------------------------------------------------------------
def DisplayNewLibraryContent( new_content,
                              output_stream,
                            ):
    operations = []

    if new_content.libraries:
        operations.append(( "Libraries", new_content.libraries ))

    if new_content.scripts:
        operations.append(( "Scripts", new_content.scripts ))

    if not operations:
        output_stream.write("No changes were detected.\n")
        return

    cols = [ 40, 9, 100, ]
    template = "{name:<%d}  {type:<%d}  {fullpath:<%d}" % tuple(cols)

    for name, items in operations:
        output_stream.write(textwrap.dedent(
            """\
            {sep}
            {name}
            {sep}

            {header}
            {underline}
            {content}

            """).format( sep='=' * len(name),
                         name=name,
                         header=template.format( name="Name",
                                                 type="Type",
                                                 fullpath="Fullpath",
                                               ),
                         underline=template.format( name='-' * cols[0],
                                                    type='-' * cols[1],
                                                    fullpath='-' * cols[2],
                                                  ),
                         content='\n'.join([ template.format( name=os.path.split(item)[1],
                                                              type="Directory" if os.path.isdir(item) else "File",
                                                              fullpath=item,
                                                            )
                                             for item in items
                                           ]),
                       ))

# ----------------------------------------------------------------------
def ResetLibraryContent(library_name, output_stream):
    output_stream = StreamDecorator(output_stream)

    made_modifications = False

    output_dir = os.getenv("DEVELOPMENT_ENVIRONMENT_REPOSITORY_GENERATED")
    library_output_dir = os.path.join(output_dir, library_name)

    if os.path.isdir(library_output_dir):
        output_stream.write("Removing '{}'...".format(library_output_dir))
        with output_stream.DoneManager():
            FileSystem.RemoveTree(library_output_dir)
            made_modifications = True

    for ext in [ ".txt", ".pickle", ]:
        filename = os.path.join(output_dir, "{}{}".format(library_name, ext))
        if os.path.isfile(filename):
            output_stream.write("Removing '{}'...".format(filename))
            with output_stream.DoneManager():
                os.remove(filename)
                made_modifications = True

    if made_modifications:
        output_stream.write(textwrap.dedent(
            """\

            Changes have been made to the library. Please run:

                {}

            """).format(Shell.GetEnvironment().CreateScriptName(Constants.ACTIVATE_ENVIRONMENT_NAME)))
    else:
        output_stream.write("No changes were found.\n")

    return 0
