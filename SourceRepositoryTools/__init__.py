# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-02-18 14:37:39
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import sys
import textwrap

from collections import OrderedDict

# Backwards compatibility
from SourceRepositoryTools.Impl.Configuration import *
from SourceRepositoryTools.Impl import Constants
from SourceRepositoryTools.Impl.Utilities import DelayExecute, \
                                                 GetLatestVersion, \
                                                 GetRepositoryUniqueId, \
                                                 GetVersionedDirectory

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

try:
    # six isn't available in all environments, so make its inclusion optional.
    import six
except ImportError:
    pass

try:
    # Wrapt isn't available in all environments, so make its inclusion optional.
    import wrapt

    @wrapt.decorator
    def ToolRepository(wrapped, instance, args, kwargs):
        """\
        Signals that a repository is a tool repository (a repository that contains
        items that help in the development process but doesn't contain primitives
        used by other dependent repositories during the build process.
        """
        return wrapped(*args, **kwargs)

except ImportError:
    pass

# ----------------------------------------------------------------------
def CreateDependencyMap(root_dir):

    # Note that this functionality if very similar to that found in ActivationData.
    # The difference between the two is this function will compile a map of all repositories
    # under the code dir, while the code in ActivationData will only traverse environment
    # data created during setup. Theoretically, it is possible for ActivationData
    # to be implemented in terms of this function, but that would be too inefficient for 
    # general use.

    from CommonEnvironment.NamedTuple import NamedTuple
    from CommonEnvironment import Shell
    from CommonEnvironment import SourceControlManagement

    from SourceRepositoryTools.Impl.EnvironmentBootstrap import EnvironmentBootstrap

    # ----------------------------------------------------------------------
    RepoInfo                                = NamedTuple( "RepoInfo",
                                                          "UniqueId",
                                                          "Name",
                                                          "Root",
                                                          "Configurations",
                                                        )

    ConfigInfo                              = NamedTuple( "ConfigInfo",
                                                          "ReliesOn",
                                                          "ReliedUponBy",
                                                        )

    DependencyInfo                          = NamedTuple( "DependencyInfo",
                                                          "Configuration",
                                                          "Dependency",
                                                        )

    # ----------------------------------------------------------------------

    assert os.path.isdir(root_dir), root_dir
    
    environent = Shell.GetEnvironment()

    repositories = OrderedDict()

    for scm, directory in SourceControlManagement.EnumSCMDirectories(root_dir):
        result = GetRepositoryUniqueId( directory,
                                        scm=scm,
                                        throw_on_error=False,
                                      )
        if result is None:
            continue

        repo_name, repo_id = result

        assert repo_id not in repositories, (repo_id, directory, repositories[repo_id].Root)

        repo_bootstrap_data = EnvironmentBootstrap.Load(directory, environment=environent)

        repo_bootstrap_data.Name = repo_name
        repo_bootstrap_data.Id = repo_id
        repo_bootstrap_data.Root = directory
        repo_bootstrap_data.PriorityModifier = 0

        repositories[repo_id] = repo_bootstrap_data
        
    # Order by priority

    # ----------------------------------------------------------------------
    def Walk(repo_id, priority_modifier):
        assert repo_id in repositories, repo_id

        repo_info = repositories[repo_id]

        repo_info.PriorityModifier += priority_modifier

        for configuration in six.itervalues(repo_info.Configurations):
            for dependency in configuration.Dependencies:
                Walk(dependency.Id, priority_modifier + 1)

    # ----------------------------------------------------------------------

    for repo_id in six.iterkeys(repositories):
        Walk(repo_id, 1)

    priority_values = list(six.iteritems(repositories))
    priority_values.sort(key=lambda x: x[1].PriorityModifier, reverse=True)

    # Convert the repositories into a structure that is easier to process
    results = OrderedDict()

    for unique_id, repo_info in priority_values:
        results[unique_id] = RepoInfo( unique_id,
                                       repo_info.Name,
                                       repo_info.Root,
                                       OrderedDict(),
                                     )

        for config_name in six.iterkeys(repo_info.Configurations):
            results[unique_id].Configurations[config_name] = ConfigInfo([], [])

    # Populate the dependencies
    for unique_id, repo_info in priority_values:
        for config_name, config_info in six.iteritems(repo_info.Configurations):
            # It is possible that a dependency is included more than once (as will be the case if someone
            # includes Common_Enviroment as a dependency even though a dependency on Common_Enviroment is
            # implied). Ensure that we are only looking at unique dependencies.
            these_dependencies = []
            dependency_lookup = set()
    
            for dependency in config_info.Dependencies:
                if dependency.Id in dependency_lookup:
                    continue
    
                these_dependencies.append(( dependency, repositories[dependency.Id].PriorityModifier ))
                dependency_lookup.add(dependency.Id)
    
            # Ensure that the dependencies are ordered in priority order
            these_dependencies.sort(key=lambda x: x[0].Id, reverse=True)
    
            for dependency, priority_modifier in these_dependencies:
                results[unique_id].Configurations[config_name].ReliesOn.append(DependencyInfo(dependency.Configuration, results[dependency.Id]))
                results[dependency.Id].Configurations[dependency.Configuration].ReliedUponBy.append(DependencyInfo(config_name, results[unique_id]))


    # Ensure that we can index by repo path as well as id
    for unique_id in list(six.iterkeys(results)):
        results[results[unique_id].Root] = results[unique_id]

    return results

# ----------------------------------------------------------------------
def DisplayDependencyMap( dependency_map,
                          output_stream=sys.stdout,
                        ):
    from CommonEnvironment.StreamDecorator import StreamDecorator

    # ----------------------------------------------------------------------

    for k, v in six.iteritems(dependency_map):
        if not os.path.isdir(k):
            continue

        output_stream.write(textwrap.dedent(
            """\
            Name:                           {name} ({unique_id})
            Directory:                      {dir}
            Configurations:
            {configurations}

            """).format( name=v.Name,
                         unique_id=v.UniqueId,
                         dir=k,
                         configurations=StreamDecorator.LeftJustify( '\n'.join([ textwrap.dedent(
                                                                                    """\
                                                                                    {name}
                                                                                      ReliesOn:
                                                                                    {relies_on}

                                                                                      ReliedUponBy:
                                                                                    {relied_upon_by}
                                                                                    """).format( name=ck,
                                                                                                 relies_on='\n'.join([ "    - {} <{}> [{}]".format(item.Dependency.Name, item.Configuration, item.Dependency.Root) for item in cv.ReliesOn ]) if cv.ReliesOn else "    <None>",
                                                                                                 relied_upon_by='\n'.join([ "    - {} <{}> [{}]".format(item.Dependency.Name, item.Configuration, item.Dependency.Root) for item in cv.ReliedUponBy ]) if cv.ReliedUponBy else "    <None>",
                                                                                               )
                                                                                 for ck, cv in six.iteritems(v.Configurations)
                                                                               ]),
                                                                     2,
                                                                     skip_first_line=False,
                                                                   ),
                       ))

# ----------------------------------------------------------------------
def EnumRepositories():
    from SourceRepositoryTools.Impl.ActivationData import ActivationData

    # ----------------------------------------------------------------------

    for repo in ActivationData.Load(None, None).PrioritizedRepos:
        yield repo
