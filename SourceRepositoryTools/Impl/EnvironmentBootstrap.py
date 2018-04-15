# ----------------------------------------------------------------------
# |  
# |  EnvironmentBootstrap.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-02-11 20:41:18
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import copy
import json
import os
import sys
import textwrap

import six

from SourceRepositoryTools.Impl import CommonEnvironmentImports
from SourceRepositoryTools.Impl import Configuration
from SourceRepositoryTools.Impl import Constants

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class EnvironmentBootstrap(object):

    NoneJsonKeyReplacementName              = "__None__"

    # ----------------------------------------------------------------------
    @classmethod
    def Load( cls, 
              repo_root,
              environment=None,
            ):
        environment = environment or CommonEnvironmentImports.Shell.GetEnvironment()

        # ----------------------------------------------------------------------
        def RestoreRelative(value):
            fullpath = os.path.normpath(os.path.join(repo_root, value))
            
            if not os.path.exists(fullpath):
                raise Exception(textwrap.dedent(
                    """\
                    '{}' does not exist. 

                    This is usually an indication that something fundamental has changed 
                    or this repository's location has moved. To address either issue, 
                    please run this command for this repository:

                        {}

                    """).format( fullpath,
                                 environment.CreateScriptName(Constants.SETUP_ENVIRONMENT_NAME),
                               ))

            return fullpath

        # ----------------------------------------------------------------------
        
        filename = os.path.join(repo_root, Constants.GENERATED_DIRECTORY_NAME, environment.CategoryName, Constants.GENERATED_BOOTSTRAP_JSON_FILENAME)
        assert os.path.isfile(filename), filename

        with open(filename) as f:
            data = json.load(f)

        python_binary = RestoreRelative(data["python_binary"])
        fundamental_repo = RestoreRelative(data["fundamental_repo"])
        is_tool_repo = data["is_tool_repo"]
        is_configurable = data["is_configurable"]

        configurations = {}

        for config_name, config_info in six.iteritems(data["configurations"]):
            # Get the dependencies
            dependencies = []

            for dependency in config_info["Dependencies"]:
                dependencies.append(Configuration.Dependency( dependency["Id"],
                                                              dependency["FriendlyName"],
                                                              dependency["Configuration"],
                                                            ))
                dependencies[-1].RepositoryRoot = RestoreRelative(dependency["RepositoryRoot"])

            # Get the VersionSpecs
            tools = []

            for tool in config_info["VersionSpecs"]["Tools"]:
                tools.append(Configuration.VersionInfo(tool["Name"], tool["Version"]))

            libraries = {}

            for k, version_infos in six.iteritems(config_info["VersionSpecs"]["Libraries"]):
                libraries[k] = [ Configuration.VersionInfo(vi["Name"], vi["Version"]) for vi in version_infos ]

            # Create the config info
            configurations[config_name] = Configuration.Configuration( dependencies,
                                                                       Configuration.VersionSpecs(tools, libraries),
                                                                       config_info["Description"],
                                                                     )
            configurations[config_name].Fingerprint = config_info["Fingerprint"]

        if cls.NoneJsonKeyReplacementName in configurations:
            configurations[None] = configurations[cls.NoneJsonKeyReplacementName]
            del configurations[cls.NoneJsonKeyReplacementName]

        return cls( python_binary,
                    fundamental_repo,
                    is_tool_repo,
                    is_configurable,
                    configurations,
                  )

    # ----------------------------------------------------------------------
    def __init__( self,
                  python_binary,
                  fundamental_repo,
                  is_tool_repo,
                  is_configurable,
                  configurations,
                ):
        assert os.path.isfile(python_binary), python_binary
        assert os.path.isdir(fundamental_repo), fundamental_repo

        self.PythonBinary                   = python_binary
        self.FundamentalRepo                = fundamental_repo
        self.IsToolRepo                     = is_tool_repo
        self.IsConfigurable                 = is_configurable
        self.Configurations                 = configurations

    # ----------------------------------------------------------------------
    def Save( self, 
              repo_root,
              environment=None,
            ):
        environment = environment or CommonEnvironmentImports.Shell.GetEnvironment()

        python_binary = CommonEnvironmentImports.FileSystem.GetRelativePath(repo_root, self.PythonBinary)
        fundamental_repo = CommonEnvironmentImports.FileSystem.GetRelativePath(repo_root, self.FundamentalRepo)
        
        configurations = copy.deepcopy(self.Configurations)
        dependencies_converted = set()

        for config_info in six.itervalues(configurations):
            for dependency in config_info.Dependencies:
                if dependency not in dependencies_converted:
                    dependency.RepositoryRoot = CommonEnvironmentImports.FileSystem.GetRelativePath(repo_root, dependency.RepositoryRoot)
                    dependencies_converted.add(dependency)

        # Write the output files
        output_dir = os.path.join(repo_root, Constants.GENERATED_DIRECTORY_NAME, environment.CategoryName)
        CommonEnvironmentImports.FileSystem.MakeDirs(output_dir)

        # Write the json file
        output_filename = os.path.join(output_dir, Constants.GENERATED_BOOTSTRAP_JSON_FILENAME)

        # JSON can't handle dictionary keys that are None, so change it if necessary
        if None in configurations:
            configurations[self.NoneJsonKeyReplacementName] = configurations[None]
            del configurations[None]

            # ----------------------------------------------------------------------
            def RestoreNone():
                configurations[None] = configurations[self.NoneJsonKeyReplacementName]
                del configurations[self.NoneJsonKeyReplacementName]

            # ----------------------------------------------------------------------
        else:
            RestoreNone = lambda: None

        with CommonEnvironmentImports.CallOnExit(RestoreNone):
            with open(output_filename, 'w') as f:
                # ----------------------------------------------------------------------
                class Encoder(json.JSONEncoder):
                    def default(self, obj):
                        return obj.__dict__

                # ----------------------------------------------------------------------

                json.dump( { "python_binary" : python_binary,
                             "fundamental_repo" : fundamental_repo,
                             "is_tool_repo" : self.IsToolRepo,
                             "is_configurable" : self.IsConfigurable,
                             "configurations" : configurations,
                           },
                           f,
                           cls=Encoder,
                         )

        # Write the data file
        output_filename = os.path.join(output_dir, Constants.GENERATED_BOOTSTRAP_DATA_FILENAME)
        
        with open(output_filename, 'w') as f:
            f.write(textwrap.dedent(
                """\
                python_binary={python_binary}
                fundamental_repo={fundamental_repo}
                is_tool_repo={is_tool_repo}
                is_configurable={is_configurable}
                """).format( fundamental_repo=fundamental_repo,
                             python_binary=python_binary,
                             is_tool_repo="1" if self.IsToolRepo else "0",
                             is_configurable="1" if self.IsConfigurable else "0",
                           ))

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironmentImports.CommonEnvironment.ObjStrImpl(self)
