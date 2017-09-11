# ----------------------------------------------------------------------
# |  
# |  ActivationHelpers.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-09-11 07:35:58
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""\
Functionality that helps when activating environments.
"""

import os
import sys
import textwrap

from collections import OrderedDict

import six
import six.moves.cPickle as pickle

from CommonEnvironment import ModifiableValue
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import FileSystem
from CommonEnvironment.Interface import CreateCulledCallable
from CommonEnvironment import Process
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

import Constants
import SourceRepositoryTools

# ----------------------------------------------------------------------
def WriteLibraryInfo( generated_dir,
                      name,
                      libraries,            # { "<name>" : { "version" : "<version>",
                                            #                "fullpath" : "<fullpath>",
                                            #              },
                                            # }
                    ):
    # Write the link file
    with open(os.path.join(generated_dir, "{}.txt".format(name)), 'w') as f:
        library_keys = list(six.iterkeys(libraries))
        library_keys.sort(key=lambda name: name.lower())

        cols = OrderedDict([ ( "Name", 40 ),
                             ( "Version", 15 ),
                             ( "Fullpath", 60 ),
                           ])

        template = '  '.join([ '{{{}:<{}}}'.format(index, v) for index, v in enumerate(six.itervalues(cols)) ])

        f.write(textwrap.dedent(
            """\
            {}
            {}
            {}
            """).format( template.format(*six.iterkeys(cols)),
                         template.format(*[ '-' * v for v in six.itervalues(cols) ]),
                         '\n'.join([ template.format(*[ key, 
                                                        libraries[key].version,
                                                        libraries[key].fullpath,
                                                      ])
                                     for key in library_keys
                                   ]),
                       ))
        
    # Write the pickle file
    with open(os.path.join(generated_dir, "{}.pickle".format(name)), 'wb') as f:
        pickle.dump(libraries, f)

# ----------------------------------------------------------------------
def ActivateLibraries( name,
                       create_commands_func,            # def Func(<args>) -> environment commands
                                                        #
                                                        #   where <args> can be any of the following:
                                                        #       libraries
                                                        #       create_message_statement_func   # def Func(message) -> message command that will not be suppressed during output
                                                        #       display_sentinel                # string
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
        if repository.configuration:
            return "{} ({})".format(repository.name, repository.configuration)

        return repository.name

    # ----------------------------------------------------------------------
    def AugmentLibraryDir(fullpath):
        while True:
            prev_fullpath = fullpath

            dirs = [ item for item in os.listdir(fullpath) if os.path.isdir(os.path.join(fullpath, item)) ]

            for library_versions, this_version in six.iteritems(library_version_dirs):
                applies = True
                
                for directory in dirs:
                    if directory not in library_versions:
                        applies = False
                        break

                if not applies:
                    continue

                if this_version not in dirs:
                    return None

                fullpath = os.path.join(fullpath, this_version)
                break

            if prev_fullpath == fullpath:
                break

        return fullpath

    # ----------------------------------------------------------------------
    
    errors = []
    
    for repository in repositories:
        potential_library_dir = os.path.join(repository.root, Constants.LIBRARIES_SUBDIR, name)
        if not os.path.isdir(potential_library_dir):
            continue

        for item in os.listdir(potential_library_dir):
            if item in libraries:
                errors.append(textwrap.dedent(
                        """\
                        The library '{name}' has already been defined.

                            Original:       {original_name} <<{original_version}>> <{original_id}> [{original_root}]
                            New:            {new_name} <{new_id}> [{new_root}]
                        
                        """).format( name=item,
                                     original_name=ToRepositoryName(libraries[item].repository),
                                     original_version=libraries[item].version,
                                     original_id=libraries[item].repository.id,
                                     original_root=libraries[item].repository.root,
                                     new_name=ToRepositoryName(repository),
                                     new_id=repository.id,
                                     new_root=repository.root,
                                   ))
                continue

            fullpath = os.path.join(potential_library_dir, item)
            
            # Library names can be customized in the following ways:
            version = ModifiableValue(None)

            # ----------------------------------------------------------------------
            def GetVersionedDirectoryEx(fullpath):
                fullpath, this_version = SourceRepositoryTools.GetVersionedDirectoryEx(version_info, fullpath)
                version.value = this_version

                return fullpath

            # ----------------------------------------------------------------------

            try:
                apply_library = True

                for index, method in enumerate([ SourceRepositoryTools.GetCustomizedPath,
                                                 AugmentLibraryDir,
                                                 GetVersionedDirectoryEx,
                                                 SourceRepositoryTools.GetCustomizedPath,
                                                 AugmentLibraryDir,
                                               ]):
                    result = method(fullpath)
                    if result == None:
                        apply_library = False
                        break

                    fullpath = result
                    assert os.path.isdir(fullpath), (index, fullpath)
                
                if apply_library:
                    libraries[item] = QuickObject( repository=repository,
                                                   fullpath=fullpath,
                                                   version=version.value,
                                                 )
            except Exception as ex:
                sys.stdout.write("    WARNING: {}\n".format(ex))

    if errors:
        raise Exception(''.join(errors))
        
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

                if line.startswith("{}".format(display_sentinel)):
                    sys.stdout.write("{}\n".format(line[len(display_sentinel):].rstrip()))

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

    WriteLibraryInfo( generated_dir,
                      name,
                      libraries,
                    )

# ----------------------------------------------------------------------
def ActivateLibraryScripts( dest_dir,
                            libraries,
                            library_script_dir_name,
                            environment,
                          ):
    actions = []

    all_scripts = OrderedDict()

    for info in six.itervalues(libraries):
        potential_dir = os.path.join(info.fullpath, library_script_dir_name)
        if not os.path.isdir(potential_dir):
            continue

        try:
            potential_dir = SourceRepositoryTools.GetCustomizedPath(potential_dir)
        except Exception as ex:
            actions.append(environment.Message("WARNING: {}\n".format(str(ex))))
            continue

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

                    return new_name

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
    os.makedirs(dest_dir)

    if all_scripts:
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
