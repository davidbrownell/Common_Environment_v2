# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-11-10 19:07:52
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-17.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import shutil
import sys
import textwrap
import traceback

from collections import OrderedDict

import six

import six.moves.cPickle as pickle

from CommonEnvironment import ModifiableValue
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import FileSystem
from CommonEnvironment.Interface import CreateCulledCallable
from CommonEnvironment import Process
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment import six_plus
from CommonEnvironment import Shell
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

import Constants
import SourceRepositoryTools



# ----------------------------------------------------------------------
# BugBug: LibraryModifications
def GetNewLibraryContent(library_dir, script_dir):
    # Don't treat the scripts dir as a library if it happens to
    # be a sibling.
    library_ignore_dir = None

    if library_dir and script_dir:
        common_path = FileSystem.GetCommonPath(library_dir, script_dir)
        if common_path:
            assert not library_dir.endswith(os.path.sep)
            assert common_path.endswith(os.path.sep)

            common_path = common_path[:-len(os.path.sep)]
            if common_path == library_dir:
                script_subdir = script_dir[len(common_path) + len(os.path.sep):]
                library_ignore_dir = script_subdir.split(os.path.sep)[0]

    environment = Shell.GetEnvironment()

    # Get the libraries
    libraries = []

    if library_dir and os.path.isdir(library_dir):
        for item in os.listdir(library_dir):
            if item == library_ignore_dir:
                continue

            fullpath = os.path.join(library_dir, item)
            if not environment.IsSymLink(fullpath):
                libraries.append(fullpath)

    # Get the scripts
    scripts = []

    if script_dir and os.path.isdir(script_dir):
        for item in os.listdir(script_dir):
            fullpath = os.path.join(script_dir, item)

            if not environment.IsSymLink(fullpath):
                scripts.append(fullpath)

    return QuickObject( libraries=libraries,
                        scripts=scripts,
                      )

# ----------------------------------------------------------------------
# BugBug: LibraryModifications
def DisplayNewLibraryContent(library_dir, script_dir, output_stream):
    results = GetNewLibraryContent(library_dir, script_dir)

    operations = []

    if library_dir:
        operations.append(( "Libraries", results.libraries ))

    if script_dir:
        operations.append(( "Scripts", results.scripts ))

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
# BugBug: LibraryModifications
def CopyNewLibraryContent( type_name,
                           library_dir,
                           script_dir,
                           get_library_version_func,     # def Func(library_fullpath) -> version string
                           dest_script_dir_name,
                           dest_has_nested_lib_name,
                           output_stream,
                           is_noop,
                         ):
    # This code makes assumptions about libraries and their relative structure
    # (eg libraries will always be contained in a directory) and may not be 
    # suitable for all scenarios.
    if is_noop:
        output_stream.write("***** Output is for information only; nothing will be copied. *****\n\n")
        move_func = lambda *args, **kwargs: None
    else:
        # ----------------------------------------------------------------------
        def Move(source_dir_or_filename, dest_dir):
            if os.path.isfile(source_dir_or_filename):
                if not os.path.isdir(dest_dir):
                    os.makedirs(dest_dir)

            shutil.move(source_dir_or_filename, dest_dir)

        # ----------------------------------------------------------------------

        move_func = Move
    
    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     done_prefix="Composite Results: ",
                                                   ) as dm:
        dm.stream.write("Getting New Library Content...")
        with dm.stream.DoneManager(done_suffix='\n'):
            content = GetNewLibraryContent(library_dir, script_dir)

        libraries = OrderedDict()

        dm.stream.write("Copying Libraries...")
        with dm.stream.DoneManager( done_suffix='\n',
                                  ) as copy_dm:
            for index, library_fullpath in enumerate(content.libraries):
                library_name = os.path.basename(library_fullpath)
                dest_dir = ModifiableValue(None)

                copy_dm.stream.write("Processing '{}' ({} of {})...".format( library_name,
                                                                             index + 1,
                                                                             len(content.libraries),
                                                                           ))
                with copy_dm.stream.DoneManager( done_suffix_functor=lambda: None if not dest_dir.value else "Destination: '{}'".format(dest_dir.value),
                                               ) as this_dm:
                    try:
                        if os.path.isfile(library_fullpath):
                            this_dm.result = 1
                            this_dm.stream.write("WARNING: '{}' is a file and will not be processed.\n".format(library_name))
                            continue

                        version = get_library_version_func(library_fullpath)
                        assert version

                        if not version.startswith("v"):
                            version = "v{}".format(version)

                        potential_dest_dir = os.path.join(os.getenv("DEVELOPMENT_ENVIRONMENT_REPOSITORY"), Constants.LIBRARIES_SUBDIR, type_name, library_name, version)

                        if os.path.isdir(potential_dest_dir):
                            this_dm.result = -1
                            this_dm.stream.write("ERROR: '{}' already exists.\n".format(potential_dest_dir))
                            continue

                        dest_dir.value = potential_dest_dir

                        if dest_has_nested_lib_name:
                            dest_dir.value = os.path.join(dest_dir.value, library_name)

                        move_func(library_fullpath, dest_dir.value)
                        
                        libraries[library_name] = dest_dir.value
                    
                    except Exception as ex:
                        this_dm.result = -1
                        this_dm.stream.write("ERROR: {}\n".format(StreamDecorator.LeftJustify( str(ex), # traceback.format_exc(),
                                                                                               len("ERROR: "),
                                                                                             )))

        dm.stream.write("Copying Scripts...")
        with dm.stream.DoneManager( done_suffix='\n',
                                  ) as copy_dm:
            for index, script_fullpath in enumerate(content.scripts):
                script_name = os.path.basename(script_fullpath)
                dest_fullpath = ModifiableValue(None)

                copy_dm.stream.write("Processing '{}' ({} of {})...".format( script_name,
                                                                             index + 1,
                                                                             len(content.scripts),
                                                                           ))

                with copy_dm.stream.DoneManager( done_suffix_functor=lambda: None if not dest_fullpath.value else "Destination: '{}'".format(dest_fullpath.value),
                                               ) as this_dm:
                    try:
                        if os.path.isdir(script_fullpath):
                            this_dm.result = 1
                            this_dm.stream.write("WARNING: '{}' is a directory and will not be processed.\n".format(script_fullpath))
                            continue

                        # Attempt to find the library that the script is associated with.
                        script_name_lower = os.path.splitext(script_name)[0].lower()
                        library = None

                        for potential_library in six.iterkeys(libraries):
                            if potential_library.lower() in script_name_lower:
                                library = potential_library
                                break

                        if library == None:
                            this_dm.result = 1
                            this_dm.stream.write("WARNING: The library for the script '{}' could not be determined.\n".format(script_name))
                            continue

                        potential_dest_fullpath = libraries[library]
                        if dest_has_nested_lib_name:
                            potential_dest_fullpath = os.path.dirname(potential_dest_fullpath)

                        potential_dest_fullpath = os.path.join(potential_dest_fullpath, dest_script_dir_name)

                        dest_fullpath.value = potential_dest_fullpath
                        move_func(script_fullpath, dest_fullpath.value)

                    except Exception as ex:
                        this_dm.result = -1
                        this_dm.stream.write("ERROR: {}\n".format(StreamDecorator.LeftJustify( str(ex), # traceback.format_exc(),
                                                                                               len("ERROR: "),
                                                                                             )))

        return dm.result

# ----------------------------------------------------------------------
# BugBug: LibraryModifications
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

            """).format(Shell.GetEnvironment().CreateScriptName(SourceRepositoryTools.ACTIVATE_ENVIRONMENT_NAME)))

    return 0
