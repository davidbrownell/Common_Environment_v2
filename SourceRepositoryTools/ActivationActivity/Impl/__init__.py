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
def ActivateLibraries( name,
                       create_commands_func,            # def Func(<args>) -> environment commands
                                                        #
                                                        #   where <args> can be any of the following:
                                                        #       libraries
                                                        #       create_message_statement_func   # def Func(message) -> message command that will not be suppressed during output
                       environment,
                       repositories,
                       version_specs,
                       generated_dir,
                       library_version_dirs=None,       # { ( <potential_version_dir>, ) : <dir_to_use>, }
                     ):
    library_version_dirs = library_version_dirs or {}

    version_info = version_specs.Libraries.get(name, [])
    create_commands_func = CreateCulledCallable(create_commands_func)

    # Create the libraries
    libraries = OrderedDict()

    # ----------------------------------------------------------------------
    def ToRepositoryName(repository):
        if repositories.configuration:
            return "{} ({})".format(repository.name, repository.configuration)

        return repository.name

    # ----------------------------------------------------------------------
    def AugmentLibraryDir(fullpath):
        while True:
            prev_fullpath = fullpath

            dirs = [ item for item in os.listdir(fullpath) if os.path.isdir(os.path.join(fullpath, item)) ]

            for library_versions, this_version in six.iteritems(library_version_dirs):
                found = True

                for library_version in library_versions:
                    if library_version not in dirs:
                        found = False
                        break

                if found:
                    assert this_version in library_versions, this_version
                    fullpath = os.path.join(fullpath, this_version)

                    break

            if prev_fullpath == fullpath:
                break

        return fullpath

    # ----------------------------------------------------------------------
    
    for repository in repositories:
        potential_library_dir = os.path.join(repository.root, Constants.LIBRARIES_SUBDIR, name)
        if not os.path.isdir(potential_library_dir):
            continue

        for item in os.listdir(potential_library_dir):
            if item in libraries:
                raise Exception(textwrap.dedent(
                        """\
                        The library '{name}' has already been defined.

                        Original:               {original_name} <{original_id}> [{original_root}]
                        New:                    {new_name} <{new_id}> [{new_root}]
                        """).format( name=item,
                                     original_name=ToRepositoryName(libraries[item].repository),
                                     original_id=libraries[item].repository.id,
                                     original_root=libraries[item].repository.root,
                                     new_name=ToRepositoryName(repository),
                                     new_id=repository.id,
                                     new_root=repository.root,
                                   ))

            fullpath = os.path.join(potential_library_dir, item)
            assert os.path.isdir(fullpath), fullpath

            fullpath = AugmentLibraryDir(fullpath)
            assert os.path.isdir(fullpath), fullpath

            fullpath, version = SourceRepositoryTools.GetVersionedDirectoryEx(version_info, fullpath)
            fullpath = SourceRepositoryTools.GetCustomizedPath(fullpath)

            libraries[item] = QuickObject( repository=repository,
                                           fullpath=fullpath,
                                           version=version,
                                         )

    # On some systems, the symbolc link commands will generate output that we would like to 
    # be supressed in most cases. Instead of executing the content directly, execute it
    # ourselves.
    display_sentinel = "__DISPLAY__??!! "
    
    commands = create_commands_func(OrderedDict([ ( "libraries", libraries ),
                                                  ( "create_message_statement_func", lambda message: environment.Message("{}{}".format(display_sentinel, message)) ),
                                                  ( "display_sentinel", display_sentinel ),
                                                ]))

    if commands:
        temp_filename = environment.CreateTempFilename(environment.ScriptExtension)

        with open(temp_filename, 'w') as f:
            f.write(environment.GenerateCommands(commands))

        with CallOnExit(lambda: os.remove(temp_filename)):
            environment.MakeFileExecutable(temp_filename)

            content = []

            # ----------------------------------------------------------------------
            def OnLine(line):
                content.append(line)

                if line.startswith(display_sentinel):
                    sys.stdout.write("{}".format(line[len(display_sentinel):]))

            # ----------------------------------------------------------------------
            
            result = Process.Execute( temp_filename, 
                                      OnLine,
                                      line_delimited_output=True,
                                    )
            
            if result != 0:
                content = ''.join(content)

                raise Exception(textwrap.dedent(
                    """\
                    Error generating links ({code}):
                        {error}
                    """).format( code=result,
                                 error=StreamDecorator.LeftJustify(content, 4),
                               ))

    # Write the link file
    with open(os.path.join(generated_dir, "{}.txt".format(name)), 'w') as f:
        library_keys = list(six.iterkeys(libraries))
        library_keys.sort(key=lambda name: name.lower())

        f.write(textwrap.dedent(
            """\
            {0:<40}  {1:<15}  {2}
            {3}  {4}  {5}
            """).format( "Name",
                         "Version",
                         "Fullpath",
                         '-' * 40,
                         '-' * 15,
                         '-' * 60,
                       ))

        f.write('\n'.join([ "{name:<40}  {version:<15}  {fullpath}".format( name=library_name,
                                                                            version=libraries[library_name].version,
                                                                            fullpath=libraries[library_name].fullpath,
                                                                          )
                            for library_name in library_keys
                          ]))

    # Write the pickle file
    with open(os.path.join(generated_dir, "{}.pickle".format(name)), 'wb') as f:
        pickle.dump(libraries, f)

# ----------------------------------------------------------------------
def ActivateLibraryScripts( dest_dir,
                            libraries,
                            library_script_dir_name,
                            environment,
                          ):
    actions = []

    all_scripts = OrderedDict()

    for name, info in six.iteritems(libraries):
        potential_dir = os.path.join(info.fullpath, library_script_dir_name)
        if not os.path.isdir(potential_dir):
            continue

        potential_dir = SourceRepositoryTools.GetCustomizedPath(potential_dir)
        
        for item in os.listdir(potential_dir):
            if item in all_scripts:
                # ----------------------------------------------------------------------
                def GenerateNewName(repository):
                    filename, ext = os.path.splitext(item)
                    
                    new_name = "{}.{}{}".format( filename,
                                                 repository.name,
                                                 ext,
                                               )

                    actions.append(environment.Message("To avoid conflicts, the script '{}' has been renamed '{}' ({} <{}> [{}]).\n" \
                                                            .format( item,
                                                                     new_name,
                                                                     repository.name,
                                                                     repository.id,
                                                                     repository.root,
                                                                   )))

                # ----------------------------------------------------------------------
                
                if all_scripts[item] != None:
                    new_name = GenerateNewName(all_scripts[item].repository)
                    
                    all_scripts[new_name] = all_scripts[item]
                    all_scripts[item] = None

                new_name = GenerateNewName(info.repository)

                item = new_name

            all_scripts[item] = QuickObject( fullpath=os.path.join(potential_dir, item),
                                             repository=info.repository,
                                           )

    FileSystem.RemoveTree(dest_dir)

    if all_scripts:
        os.makedirs(dest_dir)

        for script_name, script_info in six.iteritems(all_scripts):
            if script_info == None:
                continue

            actions.append(environment.SymbolicLink(os.path.join(dest_dir, script_name), script_info.fullpath))

    return actions

# ----------------------------------------------------------------------
def CreateCleanSymLinkStatements(environment, path):
    if not os.path.isdir(path):
        return []
    
    statements = []
    
    for root, dirs, filenames in os.walk(path):
        new_traverse_dirs = []
    
        for directory in dirs:
            fullpath = os.path.join(root, directory)
    
            if environment.IsSymLink(fullpath):
                statement = environment.DeleteSymLink(fullpath, command_only=True)
                if statement:
                    statements.append(statement)
    
            else:
                new_traverse_dirs.append(directory)
    
        dirs[:] = new_traverse_dirs
    
        for filename in filenames:
            fullpath = os.path.join(root, filename)
    
            if environment.IsSymLink(fullpath):
                statement = environment.DeleteSymLink(fullpath, command_only=True)
                if statement:
                    statements.append(statement)
    
    return statements

# ----------------------------------------------------------------------
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
def CopyNewLibraryContent( type_name,
                           library_dir,
                           script_dir,
                           get_library_version_func,    # def Func(library_fullpath) -> version string
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
        move_func = shutil.move
    
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

                        for potential_library in libraries.iterkeys():
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
                        if not os.path.isdir(dest_fullpath.value):
                            os.makedirs(dest_fullpath.value)

                        move_func(script_fullpath, dest_fullpath.value)

                    except Exception as ex:
                        this_dm.result = -1
                        this_dm.stream.write("ERROR: {}\n".format(StreamDecorator.LeftJustify( str(ex), # traceback.format_exc(),
                                                                                               len("ERROR: "),
                                                                                             )))

        return dm.result

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

    return 0
                         