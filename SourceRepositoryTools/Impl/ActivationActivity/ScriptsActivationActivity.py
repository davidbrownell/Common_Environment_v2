# ----------------------------------------------------------------------
# |  
# |  ScriptsActivationActivity.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-02-16 21:39:47
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import re
import sys
import textwrap

from collections import OrderedDict

import six
from six.moves import cPickle as pickle

from SourceRepositoryTools.Impl import CommonEnvironmentImports
from SourceRepositoryTools.Impl import Constants

from SourceRepositoryTools.Impl.ActivationActivity import IActivationActivity

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# <Wrong hanging indentation> pylint: disable = C0330

# ----------------------------------------------------------------------
@CommonEnvironmentImports.Interface.staticderived
class ScriptsActivationActivity(IActivationActivity.IActivationActivity):

    # ----------------------------------------------------------------------
    Name                                    = "Scripts"
    DelayExecute                            = True
    Clean                                   = True
    Display                                 = True

    # ----------------------------------------------------------------------
    @classmethod
    def _CreateCommandsImpl( cls,
                             constants,
                             environment,
                             configuration,
                             repositories,
                             version_specs,
                             generated_dir,
                           ):
        # ----------------------------------------------------------------------
        ExtractorInfo                       = CommonEnvironmentImports.NamedTuple( "ExtractorInfo",
                                                                                   "Repo",
                                                                                   "CreateCommands",
                                                                                   "CreateDocumentation",
                                                                                   "ScriptNameDecorator",
                                                                                 )

        DirGeneratorResult                  = CommonEnvironmentImports.NamedTuple( "DirGeneratorResult",
                                                                                   "Dir",
                                                                                   "Recurse",
                                                                                 )

        WrapperInfo                         = CommonEnvironmentImports.NamedTuple( "WrapperInfo",
                                                                                   "Repo",
                                                                                   "Extractor",
                                                                                   "ScriptFilename",
                                                                                 )

        WrappedInfoItem                     = CommonEnvironmentImports.NamedTuple( "WrappedInfoItem",
                                                                                   "Name",
                                                                                   "Desc",
                                                                                   "WrappedInfo",
                                                                                 )

        # ----------------------------------------------------------------------

        assert constants.ScriptsDir == cls.Name, (constants.ScriptsDir, cls.Name)

        dest_dir = os.path.join(generated_dir, cls.Name)

        if cls.Clean:
            CommonEnvironmentImports.FileSystem.RemoveTree(dest_dir)

        CommonEnvironmentImports.FileSystem.MakeDirs(dest_dir)

        commands = [ environment.EchoOff(),
                   ]

        # Scripts can come in a variety of different froms, and customization methods
        # may return new ways to traverse a directory. Maintain a list of all potential
        # generators to use when parsing script directories.
        dir_generators = [ lambda dir, version_specs: os.path.join(dir, cls.Name),
                         ]

        # Extractors are functions that can open a script and extract relevant information
        extractors = OrderedDict()

        args = { "environment" : environment,
                 "repositories" : repositories,
                 "version_specs" : version_specs,
               }

        for repository in repositories:
            results = cls.CallCustomMethod( os.path.join(repository.Root, constants.RepoCustomizationFilename), 
                                            Constants.ACTIVATE_ENVIRONMENT_CUSTOM_SCRIPT_EXTRACTOR_METHOD_NAME, 
                                            args,
                                          )
            if results is None:
                continue

            for result in results:
                # The results can be:
                #   
                #   ( ExtractorMap, DirGenerators )
                #   ( ExtractorMap, DirGenerator )
                #   ExtractorMap

                if isinstance(result, tuple):
                    these_extractors, these_generators = result

                    if not isinstance(these_generators, list):
                        these_generators = [ these_generators, ]

                    dir_generators += these_generators
                else:
                    these_extractors = result

                for k, v in six.iteritems(these_extractors):
                    if k in extractors:
                        raise Exception(textwrap.dedent(
                            """\
                            A wrapper for '{ext}' was already defined.

                            New:            {new_name} <{new_id}> [{new_root}]
                            Original:       {old_name} <{old_id}> [{old_root}]
                            """).format( ext=k,
                                         new_name=repository.Name,
                                         new_id=repository.Id,
                                         new_root=repository.Root,
                                         old_name=extractors[k].Repository.Name,
                                         old_id=extractors[k].Repository.Id,
                                         old_root=extractors[k].Repository.Root,
                                       ))

                    # Extract values can be:
                    #
                    #   ( CreateCommands, CreateDocumentation, ScriptNameDecorator )
                    #   ( CreateCommands, CreateDocumentation )
                    #   ( CreateCommands )
                    #   CreateCommands
                    
                    if not isinstance(v, tuple):
                        v = ( v, )

                    extractors[k] = ExtractorInfo( repository,
                                                   v[0],
                                                   v[1] if len(v) > 1 else lambda x: '',
                                                   v[2] if len(v) > 2 else lambda x: x,
                                                 )

        # Get all the scripts to wrap
        wrapped_info = []

        if extractors:
            for repository in repositories:
                for dir_generator in dir_generators:
                    # Generator values can be:
                    #
                    #   [ (str, recurse), ]
                    #   [ str, ]
                    #   (str, recurse)
                    #   str

                    results = dir_generator(repository.Root, version_specs)
                    if results is None:
                        continue

                    if not isinstance(results, list):
                        results = [ results, ]

                    for result in results:
                        if isinstance(result, str):
                            result = DirGeneratorResult(result, True)
                        else:
                            result = DirGeneratorResult(result[0], result[1])

                        if result.Recurse:
                            # ----------------------------------------------------------------------
                            def GenerateFilenames():
                                for item in CommonEnvironmentImports.FileSystem.WalkFiles( result.Dir,
                                                                                           traverse_exclude_dir_names=[ lambda name: name.lower().endswith("impl"),
                                                                                                                      ],
                                                                                         ):
                                    yield item

                            # ----------------------------------------------------------------------

                        else:
                            # ----------------------------------------------------------------------
                            def GenerateFilenames():
                                for item in os.listdir(result.Dir):
                                    fullpath = os.path.join(result.Dir, item)

                                    if os.path.isfile(fullpath):
                                        yield fullpath

                            # ----------------------------------------------------------------------

                        for script_filename in GenerateFilenames():
                            ext = os.path.splitext(script_filename)[1]

                            extractor = extractors.get(ext, None)
                            if extractor is None:
                                continue

                            wrapped_info.append(WrapperInfo( repository,
                                                             extractor,
                                                             script_filename,
                                                           ))

        # We have a list of script files and the functions used to extract information
        # from them when creating a wrapper. Files were extracted based on repositories 
        # ordered from the lowest to highest level. However, it is likely that the user
        # will want to use scripts from higher-level repos. Reverse the order so higher-
        # level scripts get their standard name where conflicts in lower-level libraries
        # are renamed.
        wrapped_info.reverse()

        wrapped_info_items = []

        original_script_regex = re.compile(r"Original Script: (?P<filename>[^\n]+)")

        for wi in wrapped_info:
            these_commands = wi.Extractor.CreateCommands(wi.ScriptFilename)
            if not isinstance(these_commands, list):
                continue

            # Create a unique name for this wrapper
            base_output_name = wi.Extractor.ScriptNameDecorator(os.path.splitext(os.path.basename(wi.ScriptFilename))[0])

            conflicts = []

            while True:
                potential_filename = os.path.join(dest_dir, "{name}{suffix}{ext}".format( name=base_output_name,
                                                                                          suffix=len(conflicts) + 1 if conflicts else '',
                                                                                          ext=environment.ScriptExtension,
                                                                                        ))

                if not os.path.isfile(potential_filename):
                    output_filename = potential_filename

                    if conflicts and cls.Display:
                        commands.append(environment.Message(CommonEnvironmentImports.StreamDecorator.LeftJustify( textwrap.dedent(
                                                                                                                    """\
                                                                                                                    The wrapper script for '{original_name}' has been renamed '{new_name}' to avoid naming conflicts with:
                                                                                                                    {conflicts}
                                                                                                                    """).format( original_name=wi.ScriptFilename,
                                                                                                                                 new_name=os.path.splitext(os.path.basename(output_filename))[0],
                                                                                                                                 conflicts='\n'.join([ "    - {}".format(conflict) for conflict in conflicts ]),
                                                                                                                               ),
                                                                                                                  4,
                                                                                                                  skip_first_line=False,
                                                                                                                )))
                    break

                with open(potential_filename) as f:
                    match = original_script_regex.search(f.read())
                    assert match

                    conflicts.append(match.group("filename").strip())

            # Create the invocation wrapper
            with open(output_filename, 'w') as f:
                f.write(environment.GenerateCommands([ environment.EchoOff(),
                                                       environment.Comment("Original Script: {}".format(wi.ScriptFilename)),
                                                       environment.Comment("Repository Root: {}".format(wi.Repo.Root)),
                                                     ] + these_commands))

            environment.MakeFileExecutable(output_filename)

            desc = wi.Extractor.CreateDocumentation(wi.ScriptFilename)

            # Create the wrapper data
            with open("{}.data".format(output_filename), 'wb') as f:
                pickle.dump( { "original_script" : wi.ScriptFilename,
                               "repository" : wi.Repo,
                               "desc" : desc,
                             },
                             f,
                           )

            wrapped_info_items.append(WrappedInfoItem( "{}{}".format(os.path.splitext(os.path.basename(output_filename))[0], environment.ScriptExtension),
                                                       desc,
                                                       wi,
                                                     ))

        # Sort the items for display; compare by repo then by name
        wrapped_info_items.sort(key=lambda item: (item.WrappedInfo.Repo.Root, item.Name.lower()))

        # Write the index file
        filename = os.path.join(dest_dir, environment.CreateScriptName(Constants.SCRIPT_LIST_NAME))

        with open(filename, 'w') as f:
            these_commands = [ environment.EchoOff(),
                               environment.Message("\nAvailable scripts are:\n"),
                             ]

            prev_repo = None

            for wii in wrapped_info_items:
                if wii.WrappedInfo.Repo != prev_repo:
                    name = "{name:<70} {location:>80}".format( name="{} <{}>".format(wii.WrappedInfo.Repo.Name, wii.WrappedInfo.Repo.Id),
                                                               location=wii.WrappedInfo.Repo.Root,
                                                            )

                    these_commands.append(environment.Message(CommonEnvironmentImports.StreamDecorator.LeftJustify( textwrap.dedent(
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

                    prev_repo = wii.WrappedInfo.Repo

                assert wii.WrappedInfo.ScriptFilename.startswith(wii.WrappedInfo.Repo.Root), (wii.WrappedInfo.ScriptFilename, wii.WrappedInfo.Repo.Root)
                display_location = CommonEnvironmentImports.FileSystem.RemoveInitialSep(wii.WrappedInfo.ScriptFilename[len(wii.WrappedInfo.Repo.Root):])

                content = "{0:<70} {1:>78}".format(wii.Name, display_location)
                content += "\n{}\n".format('-' * len(content))

                if wii.Desc:
                    content += "{}\n".format(CommonEnvironmentImports.StreamDecorator.LeftJustify(wii.Desc.rstrip(), 2, skip_first_line=False))

                these_commands.append(environment.Message(CommonEnvironmentImports.StreamDecorator.LeftJustify(content, 4, skip_first_line=False)))

            f.write(environment.GenerateCommands(these_commands))

        environment.MakeFileExecutable(filename)

        # Add the dir to the path
        commands.append(environment.AugmentPath(dest_dir))

        # Create the output text
        lines = textwrap.dedent(
            """\
            Shell wrappers have been created for all the files contained within the directory
            '{script_dir}' across all repositories. For a complete list of these wrappers, run:

            {script_name}
            """).format( script_dir=cls.Name,
                         script_name=environment.CreateScriptName(Constants.SCRIPT_LIST_NAME),
                       ).rstrip().split('\n')

        max_length = max(*[ len(line) for line in lines ])

        centered_template = "|  {{:^{}}}  |".format(max_length)

        commands.append(environment.Message(textwrap.dedent(
            """\
            
            {line}
            |  {whitespace}  |
            {content}
            |  {whitespace}  |
            {line}
            """).format( line='-' * (max_length + 6),
                         whitespace=' ' * max_length,
                         content='\n'.join([ centered_template.format(line) for line in lines ]),
                       )))

        return commands
