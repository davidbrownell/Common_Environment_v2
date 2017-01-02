# ---------------------------------------------------------------------------
# |  
# |  ScriptsActivationActivity.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/25/2015 03:32:39 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
from __future__ import absolute_import 

import os
import shutil
import string
import sys
import textwrap

from collections import OrderedDict
import cPickle as pickle

from CommonEnvironment import FileSystem
from CommonEnvironment.Interface import staticderived
from CommonEnvironment import Package, ModifiableValue
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment.StreamDecorator import StreamDecorator

with Package.NameInfo(__package__) as ni:
    __package__ = ni.created
    
    from .IActivationActivity import IActivationActivity

    __package__ = ni.original
    
# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

@staticderived
class ScriptsActivationActivity(IActivationActivity):

    # ---------------------------------------------------------------------------
    Name                                    = "Scripts"
    DelayExecute                            = True

    CustomizationMethod                     = "CustomScriptExtractors"
    IndexScriptFilename                     = "DevEnvScripts"

    # ---------------------------------------------------------------------------

    # <Too many branches> pylint: disable = R0912
    # <Too many variables> pylint: disable = R0914
    @classmethod
    def _CreateCommandsImpl( cls,
                             constants,
                             environment,
                             configuration,
                             repositories,
                             version_specs,
                             generated_dir,
                           ):
        assert(constants.ScriptsDir == cls.Name), (constants.ScriptsDir, cls.Name)

        dest_dir = os.path.join(generated_dir, cls.Name)

        # Remove previously generated content (if any)
        if os.path.isdir(dest_dir):
            shutil.rmtree(dest_dir)

        os.makedirs(dest_dir)

        commands = [ environment.EchoOff(),
                   ]

        # Get all of the customization functionality defined in the repositories
        dir_generators = [ lambda dir, version_specs: os.path.join(dir, cls.Name),
                         ]

        extractors = OrderedDict()

        args = { "environment" : environment,
                 "repositories" : repositories,
                 "version_specs" : version_specs,
               }

        for repository in repositories:
            results = cls.CallCustomMethod(os.path.join(repository.root, constants.RepoCustomizationFilename), cls.CustomizationMethod, **args)
            if results == None:
                continue

            for result in results:
                # The result can be:
                #   ( ExtractorMap, DirGenerators, )
                #   ( ExtractorMap, DirGenerator, )
                #   ExtractorMap

                if isinstance(result, tuple):
                    these_extractors, these_generators = result

                    if not isinstance(these_generators, list):
                        these_generators = [ these_generators, ]

                    dir_generators += these_generators
                else:
                    these_extractors = result

                for k, v in these_extractors.iteritems():
                    if k in extractors:
                        raise Exception(textwrap.dedent(
                            """\
                            A wrapper for '{ext}' was already defined.

                            New:            {new_name} <{new_id}> [{new_root}]
                            Original:       {old_name} <{old_id}> [{old_root}]
                            """).format( ext=k,
                                         new_name=repository.name,
                                         new_id=repository.id,
                                         new_root=repository.root,
                                         old_name=extractors[k].repository.name,
                                         old_id=extractors[k].repository.id,
                                         old_root=extractors[k].repository.root,
                                       ))

                    # Extractor value can be:
                    #   ( CreateCommands, CreateDocumentation, ScriptNameDecorator )
                    #   ( CreateCommands, CreateDocumentation, )
                    #   ( CreateCommands, )
                    #   CreateCommands
                    if not isinstance(v, tuple):
                        v = ( v, )

                    extractors[k] = QuickObject( repository=repository,
                                                 CreateCommands=v[0],
                                                 CreateDocumentation=v[1] if len(v) > 1 else lambda x: '',
                                                 ScriptNameDecorator=v[2] if len(v) > 2 else lambda x: x,
                                               )

        # Get all the scripts to wrap
        wrapped_info = []

        if extractors:
            for repository in repositories:
                for dir_generator in dir_generators:
                    # Generator value can be:
                    #   [ (str, Recurse), ]
                    #   [ str, ]
                    #   (str, Recurse)
                    #   str

                    results = dir_generator(repository.root, version_specs)
                    if results == None:
                        continue

                    if not isinstance(results, list):
                        results = [ results, ]

                    for result in results:
                        if isinstance(result, str):
                            result = QuickObject( dir=result,
                                                  recurse=True,
                                                )
                        else:
                            dir, recurse = result
                            result = QuickObject( dir=result,
                                                  recurse=recurse,
                                                )

                        if result.recurse:
                            # ---------------------------------------------------------------------------
                            def GenerateFilenames():
                                for item in FileSystem.WalkFiles( result.dir,
                                                                  traverse_exclude_dir_names=[ lambda name: name.lower().endswith("impl"), 
                                                                                             ],
                                                                ):
                                    yield item

                            # ---------------------------------------------------------------------------
                        else:
                            # ---------------------------------------------------------------------------
                            def GenerateFilenames():
                                for item in os.listdir(result.dir):
                                    fullpath = os.path.join(result.dir, item)

                                    if os.path.isfile(fullpath):
                                        yield fullpath

                            # ---------------------------------------------------------------------------
                            
                        for script_filename in GenerateFilenames():
                            ext = os.path.splitext(script_filename)[1]

                            extractor = extractors.get(ext, None)
                            if extractor == None:
                                continue

                            wrapped_info.append(QuickObject( repository=repository,
                                                             extractor=extractor,
                                                             script_filename=script_filename,
                                                           ))

        # We not have a list of script files and the function used to extract information
        # that creates the wrapper. Files were extracted based on the repositories ordered
        # from lowest- to highest-level. However, it is likely that the user will want to 
        # use scripts from higher-level repositories, so reverse the order.
        wrapped_info.reverse()
        
        wrapped_info_items = []

        for wi in wrapped_info:
            these_commands = wi.extractor.CreateCommands(wi.script_filename)
            if not isinstance(these_commands, list):
                continue

            # Create a unique name for this wrapper
            base_output_name = wi.extractor.ScriptNameDecorator(os.path.splitext(os.path.basename(wi.script_filename))[0])

            suffix = 1
            while True:
                potential_filename = os.path.join(dest_dir, "{name}{suffix}{ext}".format( name=base_output_name,
                                                                                          suffix=suffix if suffix > 1 else '',
                                                                                          ext=environment.ScriptExtension,
                                                                                        ))
                if not os.path.isfile(potential_filename):
                    output_filename = potential_filename

                    if suffix > 1:
                        commands.append(environment.Message("Script References: To avoid naming conflicts, the wrapper script for '{original_name}' has been renamed '{name}'.".format( original_name=wi.script_filename,
                                                                                                                                                                                        name=os.path.splitext(os.path.basename(output_filename))[0],
                                                                                                                                                                                      )))
                    break

                suffix += 1

            # Create the invoke wrapper
            with open(output_filename, 'w') as f:
                f.write(environment.GenerateCommands([ environment.EchoOff(),
                                                       environment.Comment("Original Script: {}".format(wi.script_filename)),
                                                       environment.Comment("Repository Root: {}".format(wi.repository.root)),
                                                     ] + these_commands))

            environment.MakeFileExecutable(output_filename)

            desc = wi.extractor.CreateDocumentation(wi.script_filename)

            # Create the wrapper data
            with open("{}.data".format(output_filename), 'w') as f:
                f.write(pickle.dumps({ "original_script" : wi.script_filename,
                                       "repository" : wi.repository,
                                       "desc" : desc,
                                     }))

            wrapped_info_items.append(QuickObject( name="{}{}".format(os.path.splitext(os.path.basename(output_filename))[0], environment.ScriptExtension),
                                                   desc=desc,
                                                   wrapped_info=wi,
                                                 ))

        # ---------------------------------------------------------------------------
        def CustomCompare(a, b):
            # Initially compare by repo root
            result = cmp(a.wrapped_info.repository.root, b.wrapped_info.repository.root)
            if result != 0:
                return result
        
            # Compare by script filename
            return cmp(a.name.lower(), b.name.lower())
        
        # ---------------------------------------------------------------------------
        
        wrapped_info_items.sort(CustomCompare)
        
        # Write the index file
        filename = os.path.join(dest_dir, environment.CreateScriptName(cls.IndexScriptFilename))
        
        with open(filename, 'w') as f:
            these_commands = [ environment.EchoOff(),
                               environment.Message("\nAvailable scripts are:\n"),
                             ]
        
            prev_repo = None
            
            for wii in wrapped_info_items:
                if wii.wrapped_info.repository != prev_repo:
                    name = "{name:<70} {location:>80}".format( name="{} <{}>".format(wii.wrapped_info.repository.name, wii.wrapped_info.repository.id),
                                                               location=wii.wrapped_info.repository.root,
                                                             )
        
                    these_commands.append(environment.Message(StreamDecorator.LeftJustify( textwrap.dedent(
                        """\
                        {sep}
                        {name}
                        {sep}
                        """).format( sep='=' * max(80, len(name)),
                                     name=name,
                                   ),
                                                                                           2,
                                                                                           skip_first_line=False,
                                                                                         )))
        
                    prev_repo = wii.wrapped_info.repository
                    
                assert wii.wrapped_info.script_filename.startswith(wii.wrapped_info.repository.root), (wii.wrapped_info.script_filename, wii.wrapped_info.repository.root)
                display_location = wii.wrapped_info.script_filename[len(wii.wrapped_info.repository.root):]
                if display_location.startswith(os.path.sep):
                    display_location = display_location[len(os.path.sep):]
        
                content = "{0:<70} {1:>78}".format(wii.name, display_location)
                content += '\n{}\n'.format('-' * len(content))

                if wii.desc:
                    content += "{}\n".format(StreamDecorator.LeftJustify(wii.desc.rstrip(), 2, skip_first_line=False))
        
                these_commands.append(environment.Message(StreamDecorator.LeftJustify(content, 4, skip_first_line=False)))
        
            f.write(environment.GenerateCommands(these_commands))
        
        environment.MakeFileExecutable(filename)
        
        # Add the dir to the path
        commands.append(environment.AugmentPath(dest_dir))

        # Create the output text
        commands.append(environment.Message(textwrap.dedent(
            """\

            -------------------------------------------------------------------------------
            = Shell wrappers have been created for all the files contained within the directory 
            = '{script_dir}' across all repositories. For a complete list of all wrappers, run:
            =
            =  {script_name}
            =
            -------------------------------------------------------------------------------
            """).format( script_dir=cls.Name,
                         script_name=string.center(environment.CreateScriptName(cls.IndexScriptFilename), 80),
                       )))

        return commands
