# ---------------------------------------------------------------------------
# |  
# |  DisplayPythonLibraryModifications.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/13/2015 07:24:09 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-18.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Displays modifications made to the local Python library virtual environment.
"""

import os
import json
import re
import shutil
import sys
import textwrap
import threading

from collections import OrderedDict

import inflect
import six

from CommonEnvironment import ModifiableValue
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment import Shell
from CommonEnvironment import SourceControlManagement
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import TaskPool

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

assert os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")
sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
with CallOnExit(lambda: sys.path.pop(0)):
    from SourceRepositoryTools import Constants

    from SourceRepositoryTools.Impl.ActivationActivity.PythonActivationActivity import PythonActivationActivity, \
                                                                                       EASY_INSTALL_PTH_FILENAME, \
                                                                                       WRAPPERS_FILENAME, \
                                                                                       SCRIPTS_DIR_NAME

    from SourceRepositoryTools.Impl.ActivationActivity.LibraryModificationHelpers import GetNewLibraryContent as GetNewLibraryContentBase, \
                                                                                         DisplayNewLibraryContent, \
                                                                                         ResetLibraryContent

inflect_engine                              = inflect.engine()

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints(output_stream=None)
def Display( output_stream=sys.stdout,
           ):
    """\
    Displays python libraries that have been temporarily added to the environment;
    use Copy to prepare the libraries to be permanently added to the active environment.
    """

    settings = PythonActivationActivity.GetEnvironmentSettings()

    new_library_content = _GetNewLibraryContent(settings)
    
    DisplayNewLibraryContent(new_library_content, output_stream)

    # Augment the display with extension and binary info
    environment = Shell.GetEnvironment()

    if new_library_content.extensions:
        output_stream.write(textwrap.dedent(
            """\
        
            ==========
            Extensions
            ==========
            """))
        
        for k, v in six.iteritems(new_library_content.extensions):
            output_stream.write("{}\n{}\n\n".format( k, 
                                                     StreamDecorator.LeftJustify( '\n'.join(v),
                                                                                  4,
                                                                                  skip_first_line=False,
                                                                                ),
                                                   ))

    if new_library_content.script_extensions:
        output_stream.write(textwrap.dedent(
            """\
        
            ========
            Binaries
            ========
            {}
        
            """).format('\n'.join(new_library_content.script_extensions)))

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( output_stream=None,
                                )
def Move( no_move=False,
          output_stream=sys.stdout,
        ):
    # LibraryModificationHelpers.CopyNewLibraryContent works well when there
    # is a 1:1 relationship between a src dir and dest dir. Unfortunately, Python
    # has a M:1 relationship between src dirs and dest dirs. As a result, we need to 
    # process the content manually.

    if no_move:
        output_stream.write("***** Output is for information only; nothing will be moved. *****\n\n")
        move_func = lambda *ags, **kwargs: None
    else:
        # ----------------------------------------------------------------------
        def Move(source_dir_or_filename, dest_dir):
            if os.path.isfile(source_dir_or_filename) and not os.path.isdir(dest_dir):
                os.makedirs(dest_dir)

            shutil.move(source_dir_or_filename, dest_dir)

        # ----------------------------------------------------------------------

        move_func = Move

    # ----------------------------------------------------------------------
    class PythonLibrary(object):
        def __init__(self, fullpath):
            self.Fullpath                   = fullpath
            self.dist_info_path             = None
            self.version                    = None
            self.dest_dir                   = None

    # ----------------------------------------------------------------------

    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     done_prefix="Composite Results: ",
                                                   ) as dm:
        environment = Shell.GetEnvironment()

        dm.stream.write("Calculating new library content...")
        with dm.stream.DoneManager():
            settings = PythonActivationActivity.GetEnvironmentSettings()

            new_content = _GetNewLibraryContent(settings)

        # Group libraries and distinfo bundles
        libraries = OrderedDict()

        dm.stream.write("Grouping libraries...")
        with dm.stream.DoneManager( done_suffix='\n',
                                  ) as this_dm:
            for library_path in new_content.libraries:
                if os.path.isfile(library_path):
                    this_dm.result = 1
                    this_dm.stream.write("WARNING: '{}' is a file and will not be processed.\n".format(library_path))
                    continue

                basename = os.path.basename(library_path)
                if not basename.endswith(".dist-info"):
                    libraries[basename] = PythonLibrary(library_path)

            for library_path in new_content.libraries:
                if os.path.isfile(library_path):
                    continue

                basename = os.path.basename(library_path)
                if basename.endswith(".dist-info"):
                    potential_name = basename[:-len(".dist-info")]

                    index = potential_name.rfind('-')
                    if index == -1:
                        this_dm.result = 1
                        this_dm.stream.write("WARNING: The library name for '{}' could not be extracted ({}).\n".format(potential_name, basename))
                        continue

                    potential_name = potential_name[:index]
                    if potential_name not in libraries:
                        this_dm.result = 1
                        this_dm.stream.write("WARNING: The library name '{}' was not found ({}).\n".format(potential_name, basename))
                        continue

                    if libraries[potential_name].dist_info_path is not None:
                        this_dm.result = -1
                        this_dm.stream.write("ERROR: The dist info path for '{}' was already populated (existing: {}, new: {}).\n".format(potential_name, libraries[potential_name].DistInfoPath, library_path))
                        continue

                    libraries[potential_name].dist_info_path = library_path

                    metadata_filename = os.path.join(library_path, "metadata.json")
                    if not os.path.isfile(metadata_filename):
                        this_dm.result = 1
                        this_dm.stream.write("WARNING: Metadata was not found for '{}'.\n".format(library_path))
                        continue

                    with open(metadata_filename) as f:
                        data = json.load(f)

                    if "version" not in data:
                        this_dm.result = -1
                        this_dm.stream.write("ERROR: 'version' was not found in '{}'.\n".format(metadata_filename))
                        continue

                    version = data["version"]
                    if not version.startswith("v"):
                        version = "v{}".format(version)

                    libraries[potential_name].version = version

        dm.stream.write("Moving libraries...")
        with dm.stream.DoneManager( done_suffix='\n',
                                  ) as move_dm:
            python_version_dir = "v{}".format(os.getenv("DEVELOPMENT_ENVIRONMENT_PYTHON_VERSION").split('.')[0])

            for index, (name, lib_info) in enumerate(six.iteritems(libraries)):
                move_dm.stream.write("Processing '{}' ({} of {})...".format( name,
                                                                             index + 1,
                                                                             len(libraries),
                                                                           ))
                with move_dm.stream.DoneManager( done_suffix_functor=lambda: None if not lib_info.dest_dir else "Destination: '{}'".format(lib_info.dest_dir),
                                               ) as this_dm:
                    if not (lib_info.dist_info_path and lib_info.version):
                        if not lib_info.dist_info_path:
                            this_dm.result = 1
                            this_dm.stream.write("WARNING: Distribution info was not found for '{}'.\n".format(lib_info.Fullpath))
                            continue

                    try:
                        # TODO: <lib_name>/<category_name>/<lib_version>/<python_version>/
                        # TODO: Should be <lib_name>/<lib_version>/<category_name>/<python_version>/; need to update existing libs
                        
                        if lib_info.Fullpath in new_content.extensions:
                            potential_dest_dir = os.path.join(os.getenv("DEVELOPMENT_ENVIRONMENT_REPOSITORY"), Constants.LIBRARIES_SUBDIR, PythonActivationActivity.Name, name, python_version_dir, lib_info.version, environment.CategoryName)
                        else:
                            potential_dest_dir = os.path.join(os.getenv("DEVELOPMENT_ENVIRONMENT_REPOSITORY"), Constants.LIBRARIES_SUBDIR, PythonActivationActivity.Name, name, lib_info.version)

                        if os.path.isdir(potential_dest_dir):
                            this_dm.result = -1
                            this_dm.stream.write("ERROR: '{}' already exists.\n".format(potential_dest_dir))
                            continue

                        lib_info.dest_dir = potential_dest_dir

                        move_func(lib_info.Fullpath, os.path.join(lib_info.dest_dir, os.path.basename(lib_info.Fullpath)))
                        move_func(lib_info.dist_info_path, os.path.join(lib_info.dest_dir, os.path.basename(lib_info.dist_info_path)))

                    except Exception as ex:
                        this_dm.result = -1
                        this_dm.stream.write("ERROR: {}\n".format(StreamDecorator.LeftJustify( str(ex), # traceback.format_exc(),
                                                                                               len("ERROR: "),
                                                                                             )))

        dm.stream.write("Moving scripts...")
        with dm.stream.DoneManager( done_suffix='\n',
                                  ) as move_dm:
            for index, script_fullpath in enumerate(new_content.scripts):
                script_name = os.path.basename(script_fullpath)
                dest_fullpath = ModifiableValue(None)

                move_dm.stream.write("Processing '{}' ({} of {})...".format( script_name,
                                                                             index + 1,
                                                                             len(new_content.scripts),
                                                                           ))
                with move_dm.stream.DoneManager( done_suffix_functor=lambda: None if not dest_fullpath.value else "Destrination: '{}'".format(dest_fullpath.value),
                                               ) as this_dm:
                    try:
                        if os.path.isdir(script_fullpath):
                            this_dm.result = 1
                            this_dm.stream.write("WARNING: '{}' is a directory and will not be processed.\n".format(script_fullpath))
                            continue

                        # Attempt to find the library that the script is associated with.
                        script_name_lower = os.path.splitext(script_name)[0].lower()
                        lib_info = None

                        for potential_library, potential_lib_info in six.iteritems(libraries):
                            if not potential_lib_info.dist_info_path:
                                continue

                            if potential_library.lower() in script_name_lower:
                                lib_info = potential_lib_info
                                break

                        if lib_info is None:
                            this_dm.result = 1
                            this_dm.stream.write("WARNING: The library for the script '{}' could not be determined.\n".format(script_name))
                            continue

                        dest_fullpath.value = lib_info.dest_dir

                        move_func(script_fullpath, os.path.join(dest_fullpath.value, SCRIPTS_DIR_NAME))

                    except Exception as ex:
                        this_dm.result = -1
                        this_dm.stream.write("ERROR: {}\n".format(StreamDecorator.LeftJustify( str(ex), # traceback.format_exc(),
                                                                                               len("ERROR: "),
                                                                                             )))

        return dm.result

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( output_stream=None,
                                )
def Reset( output_stream=sys.stdout,
         ):
    return ResetLibraryContent("Python", output_stream)

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( lib_name=CommandLine.StringTypeInfo(),
                                  pip_arg=CommandLine.StringTypeInfo(arity='*'),
                                  output_stream=None,
                                )
def Install( lib_name,
             pip_arg=None,
             output_stream=sys.stdout,
             verbose=False,
           ):
    pip_args = pip_arg; del pip_arg;

    repo_root = os.getenv("DEVELOPMENT_ENVIRONMENT_REPOSITORY")

    scm = SourceControlManagement.GetSCM(repo_root)
    if not scm:
        output_stream.write("ERROR: A SCM could not be found.\n")
        return -1

    if scm.HasWorkingChanges(repo_root) or scm.HasUntrackedWorkingChanges(repo_root):
        output_stream.write("ERROR: Changes were detected in the working directory; please revert/shelve these changes and run this script again.\n")
        return -1

    # Execute an installation
    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     done_prefix="\nComplete Result: ",
                                                     done_suffix='\n',
                                                   ) as dm:
        pip_command_line = 'pip install "{}"{}'.format( lib_name,
                                                        '' if not pip_args else " {}".format(' '.join([ '"{}"'.format(pip_arg) for pip_arg in pip_args ])),
                                                      )

        dm.stream.write("Detecting libraries...")
        with dm.stream.DoneManager( done_suffix='\n',
                                  ) as this_dm:
            libraries = []

            # ----------------------------------------------------------------------
            def OnOutput(line):
                this_dm.stream.write(line)

                if not line.startswith("Installing collected packages: "):
                    return True

                line = line[len("Installing collected packages: "):]

                for library in line.split(','):
                    library = library.strip()
                    if library:
                        libraries.append(library)

                return False

            # ----------------------------------------------------------------------

            Process.Execute( pip_command_line,
                             OnOutput,
                             line_delimited_output=True,
                           )

        dm.stream.write("Reverting local changes...")
        with dm.stream.DoneManager() as this_dm:
            this_dm.result = scm.Clean(repo_root, no_prompt=True)[0]

        dm.stream.write("Removing existing libraries...")
        with dm.stream.DoneManager( done_suffix='\n',
                                  ) as this_dm:
            environment = Shell.GetEnvironment()
            python_settings = PythonActivationActivity.GetEnvironmentSettings()

            lib_dir = os.path.join(os.getenv("DEVELOPMENT_ENVIRONMENT_REPOSITORY_GENERATED"), PythonActivationActivity.Name, python_settings["library_dir"])
            assert os.path.isdir(lib_dir), lib_dir

            library_items = {}
            
            for name in os.listdir(lib_dir):
                fullpath = os.path.join(lib_dir, name)

                if not os.path.isdir(fullpath):
                    continue

                library_items[name.lower()] = environment.IsSymLink(fullpath)

            # ----------------------------------------------------------------------
            def RemoveItem(name):
                if library_items[name]:
                    this_dm.stream.write("Removing '{}' for upgrade.\n".format(name))
                    os.remove(os.path.join(lib_dir, name))
                else:
                    this_dm.stream.write("Removing temporary '{}'.\n".format(name))
                    FileSystem.RemoveTree(os.path.join(lib_dir, name))

                del library_items[name]

            # ----------------------------------------------------------------------

            for library in libraries:
                potential_library_names = [ library.lower(), ]
                
                # Sometimes a library's name will begin with 'Py' but be saved in the
                # filesystem without the 'Py' prefix. Account for that scenario.
                library_lower = library.lower()

                if library_lower.startswith("py"):
                    potential_library_names.append(library_lower[len("py"):])

                for potential_library_name in potential_library_names:
                    if potential_library_name not in library_items:
                        continue

                    RemoveItem(potential_library_name)
                    
                    # Is there a dist info as well?
                    dist_info_name = None

                    for item in six.iterkeys(library_items):
                        if item.endswith(".dist-info") and item.startswith(potential_library_name):
                            dist_info_name = item
                            break

                    if dist_info_name:
                        RemoveItem(dist_info_name)

                    break

        dm.stream.write("Installing...")
        with dm.stream.DoneManager() as this_dm:
            this_dm.result = Process.Execute(pip_command_line, this_dm.stream)

        return dm.result

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraint( input_dir=CommandLine.DirectoryTypeInfo(),
                                 output_stream=None,
                               )
def PatchExecutables( input_dir,
                      output_stream=sys.stdout,
                    ):
    """\
    During pip installation, binaries may be created that embed the current
    python path into the executable. This isn't desirable, as python may
    by installed to a different location when the repository is used on 
    another machine. This code strips the full path to python; this works 
    because the python binary is added to the environment path during the
    activation process.
    """

    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     done_prefix="\nResults: ",
                                                     done_suffix='\n',
                                                   ) as dm:
        dm.stream.write("\n")

        dm.stream.write("Searching for potential binaries..")
        
        filenames = []

        with dm.stream.DoneManager( done_suffix_functor=lambda: "{} found".format(inflect_engine.no("binary", len(filenames))),
                                  ) as this_dm:
            filenames = list(FileSystem.WalkFiles( input_dir, 
                                                   include_file_extensions=[ ".exe", ],
                                                   traverse_exclude_dir_names=[ "Generated", ],
                                                 ))
        
            if not filenames:
                return this_dm.result

        modified = []
        modified_lock = threading.Lock()

        with dm.stream.SingleLineDoneManager( "Processing {}...".format(inflect_engine.no("file", len(filenames))),
                                              done_suffix_functor=lambda: "{} modified".format(inflect_engine.no("binary", len(modified))),
                                            ) as this_dm:
            if sys.version_info[0] == 2:
                shebang_line_regex = re.compile(r"(#!.+pythonw?\.exe)")
            else:
                shebang_line_regex = re.compile(b"(#!.+pythonw?\.exe)")

            # ----------------------------------------------------------------------
            def Invoke(filename, on_status_functor):
                on_status_functor("Processing")

                with open(filename, 'rb') as f:
                    original_content = f.read()

                content = shebang_line_regex.split(original_content, maxsplit=1)
                
                if len(content) != 3:
                    return

                content[1] = b"#!python.exe\r\n"

                final_content = b''.join(content)
                assert final_content != original_content

                with open(filename, 'wb') as f:
                    f.write(final_content)

                with modified_lock:
                    modified.append(filename)
                
            # ----------------------------------------------------------------------

            TaskPool.Transform( filenames,
                                Invoke,
                                this_dm.stream,
                              )

        if modified:
            dm.stream.write("\nThe following binaries have been modified:\n{}\n".format('\n'.join([ "    - {}".format(filename) for filename in modified ])))

        return dm.result

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _GetNewLibraryContent(settings):
    # Augment LibraryModificationHelpers.GetNewLibraryContent with python-specific
    # info.
    
    # Crack the script's wrappers file to get a list of all the script files
    # that should be ignored.
    script_ignore_items = set([ "__pycache__", WRAPPERS_FILENAME, ])

    potential_filename = os.path.join(settings["script_dir"], WRAPPERS_FILENAME)
    if os.path.isfile(potential_filename):
        for name in [ line.strip() for line in open(potential_filename).readlines() if line.strip() ]:
            script_ignore_items.add(name)

    new_library_content = GetNewLibraryContentBase( settings["library_dir"],
                                                    settings["script_dir"],
                                                    library_ignore_items=set([ "__pycache__", EASY_INSTALL_PTH_FILENAME, ]),
                                                    script_ignore_items=script_ignore_items,
                                                  )

    # Ignore Python 2.7 .pyc files
    new_library_content.libraries = [ item for item in new_library_content.libraries if not item.endswith(".pyc") ]

    # Augment the display with extension and binary info
    environment = Shell.GetEnvironment()

    extensions = OrderedDict()

    for library_path in new_library_content.libraries:
        exts = list(FileSystem.WalkFiles( library_path,
                                          include_file_extensions=[ ".pyd", ".so", environment.ScriptExtension, environment.ExecutableExtension, ],
                                        ))

        if exts:
            extensions[library_path] = exts

    new_library_content.extensions = extensions

    new_library_content.script_extensions = [ script for script in new_library_content.scripts if os.path.splitext(script)[1] in [ environment.ScriptExtension, environment.ExecutableExtension, ] ]

    return new_library_content

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
