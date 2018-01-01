# ---------------------------------------------------------------------------
# |  
# |  UpdateHgRepositoryRegistry.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/11/2015 06:53:54 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-18.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Updated the hg repository registry on the local machine.
"""

import inflect
import os
import sys
import textwrap

from collections import OrderedDict

import six

from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import SourceControlManagement
from CommonEnvironment.StreamDecorator import StreamDecorator

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

pluralize = inflect.engine()

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.FunctionConstraints( root_dir=CommandLine.DirectoryTypeInfo(),
                                  output_stream=None,
                                )
def EntryPoint( root_dir,
                output_stream=sys.stdout,
              ):
    # Get the repos
    repos = []

    output_stream.write("\nSearching for repositories in '{}'...".format(root_dir))
    with StreamDecorator(output_stream).DoneManager( done_suffix_functor=lambda: "{} found".format(pluralize.no("repository", len(repos))),
                                                   ):
        for scm, root in SourceControlManagement.EnumSCMDirectories(root_dir):
            if scm.Name != "Mercurial":
                continue

            repos.append(root)

    # Organize them
    repo_dict = OrderedDict()

    common_prefix = FileSystem.GetCommonPath(*repos)
    common_prefix_len = len(common_prefix)

    for repo in repos:
        suffix = repo[common_prefix_len:]
        
        parts = suffix.split(os.path.sep)
        repo_name = parts[-1]
        prefixes = parts[:-1]

        rd = repo_dict
        for prefix in prefixes:
            rd.setdefault(prefix, OrderedDict())
            rd = rd[prefix]

        rd[repo_name] = repo

    # Write the file

    # ---------------------------------------------------------------------------
    def GenerateContent(root, is_root):
        items = []

        for k, v in six.iteritems(root):
            if isinstance(v, six.string_types):
                items.append('<repo root="{dir}" shortname="{name}" />\n'.format( dir=v,
                                                                                  name=os.path.split(k)[1],
                                                                                ))
            else:
                tag_name = "allgroup" if is_root else "group"

                items.append(textwrap.dedent(
                    """\
                    <{tag_name} name="{name}">
                      {content}
                    </{tag_name}>
                    """).format( tag_name=tag_name,
                                 name=k,
                                 content=StreamDecorator.LeftJustify(GenerateContent(v, False), 2).rstrip(),
                               ))
        
        return ''.join(items)

    # ---------------------------------------------------------------------------
    
    filename = os.path.join(os.getenv("APPDATA"), "TortoiseHg", "thg-reporegistry.xml")
    assert os.path.isfile(filename), filename

    with open(filename, 'w') as f:
        f.write(textwrap.dedent(
            """\
            <?xml version="1.0" encoding="UTF-8"?>
            <reporegistry>
              <treeitem>
            {content}
              </treeitem>
            </reporegistry>
            """).format( content=StreamDecorator.LeftJustify( GenerateContent(repo_dict, True), 
                                                              4,
                                                              skip_first_line=False,
                                                            ),
                       ))

    output_stream.write("\nThe repository registry has been updated.\n")

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
