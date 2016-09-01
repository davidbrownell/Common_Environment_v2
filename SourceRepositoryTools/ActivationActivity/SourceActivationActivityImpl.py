# ---------------------------------------------------------------------------
# |  
# |  SourceActivationActivityImpl.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/26/2015 03:39:53 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
from __future__ import absolute_import 

import os
import sys
import subprocess
import textwrap

from collections import OrderedDict

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import Package, ModifiableValue
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment.StreamDecorator import StreamDecorator

with Package.NameInfo(__package__) as ni:
    __package__ = ni.created
    
    import SourceRepositoryTools
    from .IActivationActivity import IActivationActivity
    
    __package__ = ni.original

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

class SourceActivationActivityImpl(IActivationActivity):

    # ---------------------------------------------------------------------------
    @classmethod
    def _CreateCommandsImpl( cls,
                             
                             source_dir,
                             dest_dir,
                             mappings,             # k, v = <dest subfolders>, def Func(source_dir, dest_dir, name) -> Shell.SymbolicLink or [ Shell.SymbolicLink, ]
                             constants,
                             environment,
                             _configuration,
                             repositories,
                             version_specs,
                             generated_dir,
                           ):
        # This can be called when activating python, so we need
        # to relay on the environment variable to point to python
        # rather than using it directly.

        assert os.getenv("PYTHON_BINARY")
        return SourceRepositoryTools.DelayExecuteWithPython( os.getenv("PYTHON_BINARY"),
                                                             _DelayedCallback,
                                                             cls,

                                                             source_dir,
                                                             dest_dir,
                                                             mappings,

                                                             constants,
                                                             environment,
                                                             repositories,
                                                             version_specs,
                                                             generated_dir,
                                                           )

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# <Too many branches> pylint: disable = R0912
# <Too many local variables> pylint: disable = R0914
def _DelayedCallback( cls,
                      
                      source_dir,
                      dest_dir,
                      mappings,

                      constants,
                      environment,
                      repositories,
                      version_specs,
                      generated_dir,
                    ):
    version_info = []
    if version_specs and cls.Name in version_specs.Libraries:
        version_info = version_specs.Libraries[cls.Name]

    commands = [ environment.EchoOff(),
               ]

    # Remove the existing content (if any)
    if os.path.isdir(dest_dir):
        for root, dirs, filenames in os.walk(dest_dir):
            new_dirs = []

            for directory in dirs:
                fullpath = os.path.join(root, directory)

                if environment.IsSymLink(fullpath):
                    command = environment.DeleteSymLink(fullpath, command_only=True)
                    if command:
                        commands.append(environment.Raw(command))

                    continue

                new_dirs.append(directory)

            dirs[:] = new_dirs

            for filename in filenames:
                fullpath = os.path.join(root, filename)

                if environment.IsSymLink(fullpath):
                    command = environment.DeleteSymLink(fullpath, command_only=True)
                    if command:
                        commands.append(environment.Raw(command))
                else:
                    os.remove(fullpath)

    # Convert the mapping names into a hierarchy
    mapping_tree = {}

    for mapping_key in mappings.keys():
        tree = mapping_tree

        for item in mapping_key:
            tree = tree.setdefault(item, {})

    # ---------------------------------------------------------------------------
    def MapContent(source, dest, mapping_tree):
        if not os.path.isdir(source):
            return
            
        if not os.path.isdir(dest):
            os.makedirs(dest)

        for item in os.listdir(source):
            if item in mapping_tree:
                continue

            commands.append(environment.SymbolicLink(os.path.join(dest, item), os.path.join(source, item)))

        for k, v in mapping_tree.iteritems():
            MapContent(os.path.join(source, k), os.path.join(dest, k), v)

    # ---------------------------------------------------------------------------
    
    MapContent(source_dir, dest_dir, mapping_tree)

    # Link all of the libraries
    link_map = OrderedDict()

    for repository in repositories:
        potential_library_dir = os.path.join(repository.root, constants.LibrariesDir, cls.Name)
        if not os.path.isdir(potential_library_dir):
            continue

        for item in os.listdir(potential_library_dir):
            fullpath = os.path.join(potential_library_dir, item)
            if not os.path.isdir(fullpath):
                continue

            if item in link_map:
                raise Exception(textwrap.dedent(
                    """\
                    The library '{name}' has already been defined.

                    Original:           {original_name} <{original_id}> [{original_root}]
                    New:                {new_name} <{new_id}> [{new_root}]
                    """).format( name=item,
                                 original_name=link_map[item].repository.name,
                                 original_id=link_map[item].repository.id,
                                 original_root=link_map[item].repository.root,
                                 new_name=repository.name,
                                 new_id=repository.id,
                                 new_root=repository.root,
                               ))
    
            fullpath, version = SourceRepositoryTools.GetVersionedDirectoryEx(version_info, fullpath)

            for k, v in mappings.iteritems():
                results = v(fullpath, os.path.join(dest_dir, *k), item)
                if results == None:
                    continue

                if not isinstance(results, list):
                    results = [ results, ]

                commands += results

            link_map[item] = QuickObject( repository=repository,
                                          version=version,
                                          fullpath=fullpath,
                                        )

    # On some systems, the symbolc link commands will generate output that we will like to 
    # be supressed in most cases. Instead of executing the content directly, execute it
    # ourselves.
    temp_filename = environment.CreateTempFilename(environment.ScriptExtension)

    with open(temp_filename, 'w') as f:
        f.write(environment.GenerateCommands(commands))

    with CallOnExit(lambda: os.remove(temp_filename)):
        environment.MakeFileExecutable(temp_filename)

        result = subprocess.Popen( temp_filename,
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                 )

        content = result.stdout.read()
        result = result.wait() or 0

        if result != 0:
            raise Exception(textwrap.dedent(
                """\
                Error generating links ({code}):
                {error}
                """).format( code=result,
                             error=StreamDecorator.LeftJustify(content, 4, skip_first_line=False),
                           ))

    # Write the link file
    with open(os.path.join(generated_dir, "{}.txt".format(cls.Name)), 'w') as f:
        link_map_keys = link_map.keys()
        link_map_keys.sort(key=lambda i: i.lower())
        
        f.write(textwrap.dedent(
            """\
            {name}
            {underline}
            Source:             {source}
            Dest:               {dest}
            
            Processed Subdirs:
            {subdirs}
            
            Libraries:
            {links}
            """).format( name=cls.Name,
                         underline='-' * len(cls.Name),
                         source=source_dir,
                         dest=dest_dir,
                         subdirs='\n'.join([ str(list(mapping)) for mapping in mappings.keys() ]),
                         links='\n'.join([ "{name:<40}  {version:10}  {fullpath}".format( name=name,
                                                                                          version=link_map[name].version,
                                                                                          fullpath=link_map[name].fullpath,
                                                                                        )
                                           for name in link_map_keys
                                         ]),
                       ))
