# ----------------------------------------------------------------------
# |  
# |  IActivationActivity.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-02-13 20:17:08
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import importlib
import os
import sys

import six

from SourceRepositoryTools.Impl import CommonEnvironmentImports
from SourceRepositoryTools.Impl import Utilities

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class Constants(object):
    def __init__( self,
                  libraries_dir,
                  scripts_dir,
                  tools_dir,
                  repo_customization_filename,
                ):
        self.LibrariesDir               = libraries_dir
        self.ScriptsDir                 = scripts_dir
        self.ToolsDir                   = tools_dir

        self.RepoCustomizationFilename  = repo_customization_filename

# ----------------------------------------------------------------------
class IActivationActivity(CommonEnvironmentImports.Interface.Interface):
    """\
    Activity that can be performed at any time (during activation or later).
    Derived classes should account for repeated invocations within the 
    same environment.
    """

    # ----------------------------------------------------------------------
    # |  
    # |  Public Properties
    # |  
    # ----------------------------------------------------------------------
    @CommonEnvironmentImports.Interface.abstractproperty
    def Name(self):
        raise Exception("Abstract property")

    @CommonEnvironmentImports.Interface.abstractproperty
    def DelayExecue(self):
        """\
        True if the commands should be executed via DelayExecute.
        """
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    # |  
    # |  Public Commands
    # |  
    # ----------------------------------------------------------------------
    @classmethod
    def CreateCommands( cls,
                        constants,
                        environment, 
                        configuration,
                        repositories,
                        version_specs,
                        generated_dir,
                        context=None,
                      ):
        commands = [ environment.Message("Activating '{}'...".format(cls.Name)),
                   ]

        if cls.DelayExecute:
            commands += Utilities.DelayExecute( _DeferredCallback,
                                                cls,
                                                constants,
                                                environment,
                                                configuration,
                                                repositories,
                                                version_specs,
                                                generated_dir,
                                                context,
                                              )
        else:
            assert context == None, "Context is not necessary when DelayExecute is set for False as information can be associated with the cls object"

            commands += cls._CreateCommandsImpl( constants,
                                                 environment,
                                                 configuration,
                                                 repositories,
                                                 version_specs,
                                                 generated_dir,
                                               )

        return commands

    # ----------------------------------------------------------------------
    @staticmethod
    def CallCustomMethod(customization_filename, method, kwargs):
        """\
        Calls the specified method if it exists with the args that it expected
        (which is assumpted to be a subset of the args provided). Ensure that the
        return value is None or a list of items.
        """
    
        if not os.path.isfile(customization_filename):
            return 
    
        customization_path, customization_name = os.path.split(customization_filename)
        customization_name = os.path.splitext(customization_name)[0]
    
        sys.path.insert(0, customization_path)
        with CommonEnvironmentImports.CallOnExit(lambda: sys.path.pop(0)):
            mod = importlib.import_module(customization_name)
            with CommonEnvironmentImports.CallOnExit(lambda: sys.modules.pop(customization_name)):
                method = getattr(mod, method, None)
                if method is None:
                    return
    
                method = CommonEnvironmentImports.Interface.CreateCulledCallable(method)
                
                result = method(kwargs)
                if not isinstance(result, list) and result is not None:
                    result = [ result, ]
    
                return result
    
    # ----------------------------------------------------------------------
    # |  
    # |  Private Methods
    # |  
    # ----------------------------------------------------------------------
    @staticmethod
    @CommonEnvironmentImports.Interface.abstractmethod
    def _CreateCommandsImpl( constants,
                             environment,
                             configuration,
                             repositories,
                             version_specs,
                             generated_dir,
                           ):
        raise Exception("Abstract method")

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _DeferredCallback( cls,
                       constants,
                       environment,
                       configuration,
                       repositories,
                       version_specs,
                       generated_dir,
                       context,
                     ):
    for k, v in six.iteritems(context or {}):
        setattr(cls, k, v)

    return cls._CreateCommandsImpl( constants,
                                    environment,
                                    configuration,
                                    repositories,
                                    version_specs,
                                    generated_dir,
                                  )
