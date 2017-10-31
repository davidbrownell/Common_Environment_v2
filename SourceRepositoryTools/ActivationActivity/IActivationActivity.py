# ---------------------------------------------------------------------------
# |  
# |  IActivationActivity.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/23/2015 02:46:10 PM
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

import inspect
import os
import copy
import sys

from contextlib import contextmanager

import six

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment.Interface import Interface, abstractmethod, abstractproperty
from CommonEnvironment import Package
from CommonEnvironment import Process

SourceRepositoryTools                       = Package.ImportInit("..")

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# <Too few public methods> pylint: disable = R0903
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

# ---------------------------------------------------------------------------
class IActivationActivity(Interface):
    """\
    Activity that can be performed at any time (during activation or later).
    Derived classes should account for secondary invocations.
    """
    
    # ---------------------------------------------------------------------------
    # |
    # |  Public Properties
    # |
    # ---------------------------------------------------------------------------
    @abstractproperty
    def Name(self):
        raise Exception("Abstract property")

    @abstractproperty
    def DelayExecute(self):
        """\
        True if the commands should be executed via DelayExecute.
        """
        raise Exception("Abstract property")

    # ---------------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ---------------------------------------------------------------------------
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
            commands += SourceRepositoryTools.DelayExecute( _DeferedCallback,
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
            assert context == None, "Context is not necessary when DelayExecute is set to False, as information can be associated with the cls object"

            commands += cls._CreateCommandsImpl( constants,
                                                 environment,
                                                 configuration,
                                                 repositories,
                                                 version_specs,
                                                 generated_dir,
                                               )
        return commands

    # ---------------------------------------------------------------------------
    @classmethod
    def Execute( cls,
                 constants,
                 environment,
                 configuration,
                 repositories,
                 version_specs,
                 generated_dir,
                 output_stream,
                 process_lines=True,
               ):
        temp_filename = environment.CreateTempFilename(environment.ScriptExtension)

        with open(temp_filename, 'w') as f:
            f.write(environment.GenerateCommands(cls._CreateCommandsImpl( constants,
                                                                          environment,
                                                                          configuration,
                                                                          repositories,
                                                                          version_specs,
                                                                          generated_dir,
                                                                        )))

        with CallOnExit(lambda: os.remove(temp_filename)):
            environment.MakeFileExecutable(temp_filename)

            return Process.Execute(temp_filename, output_stream.write)

    # ----------------------------------------------------------------------
    @staticmethod
    @contextmanager
    def CustomMethodManager(customization_filename, method_name):
        if not os.path.isfile(customization_filename):
            yield None
            return

        customization_path, customization_name = os.path.split(customization_filename)
        customization_name = os.path.splitext(customization_name)[0]

        sys.path.insert(0, customization_path)
        with CallOnExit(lambda: sys.path.pop(0)):
            mod = __import__(customization_name)
            with CallOnExit(lambda: sys.modules.pop(customization_name)):
                yield getattr(mod, method_name, None)

    # ---------------------------------------------------------------------------
    @staticmethod
    def CallMethod(method, **kwargs):
        # Get the args
        result = inspect.getargspec(method)
        if not result.args and result.keywords:
            args = copy.deepcopy(kwargs)
        else:
            func_code = six.get_function_code(method)

            arg_names = func_code.co_varnames[:func_code.co_argcount]

            new_args = {}
            for k, v in six.iteritems(kwargs):
                if k in arg_names or (len(arg_names) == 1 and arg_names[0] == "kwargs"):
                    new_args[k] = v

            args = new_args

        # Call the function
        result = method(**args)

        # Ensure that the result is a list
        if result == None:
            return []

        if not isinstance(result, list):
            result = [ result, ]

        return result

    # ---------------------------------------------------------------------------
    @classmethod
    def CallCustomMethod(cls, customization_filename, method_name, **kwargs):
        """\
        Calls the specified method if it exists, with the args that it expects
        (which is assumed to be a subset of the args provided). Ensures that the
        return value is None or a list of items.
        """

        with cls.CustomMethodManager(customization_filename, method_name) as method:
            if not method:
                return

            return cls.CallMethod(method, **kwargs)

    # ---------------------------------------------------------------------------
    # |
    # |  Private Methods
    # |
    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _CreateCommandsImpl( constants,
                             environment,
                             configuration,
                             repositories,
                             version_specs,
                             generated_dir,
                           ):
        raise Exception("Abstract method")
    
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
def _DeferedCallback( cls,
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

    # <Access to a protected member> pylint: disable = W0212
    return cls._CreateCommandsImpl( constants,
                                    environment,
                                    configuration,
                                    repositories,
                                    version_specs,
                                    generated_dir,
                                  )
