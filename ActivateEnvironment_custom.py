# <Invalid module name> pylint: disable = C0103
# ---------------------------------------------------------------------------
# |  
# |  ActivateEnvironment_custom.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/20/2015 07:15:12 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-18.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Custom steps to activate Common_Environment
"""

import os
import sys

import six

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import Shell

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

sys.path.insert(0, _script_dir)
with CallOnExit(lambda: sys.path.pop(0)):
    from SourceRepositoryTools import DelayExecute
    from SourceRepositoryTools import DynamicPluginArchitecture

# ---------------------------------------------------------------------------
def CustomActions(fast):
    commands = []

    if fast:
        commands.append(Shell.Message("** FAST: Dynamic tester information has not been activated. ({}) **".format(_script_fullpath)))
    else:
        commands += DynamicPluginArchitecture.CreateRegistrationStatements( "DEVELOPMENT_ENVIRONMENT_COMPILERS",
                                                                            os.path.join(_script_dir, "Scripts", "Compilers"),
                                                                            lambda fullpath, name, ext: ext == ".py" and (name.endswith("Compiler") or name.endswith("CodeGenerator") or name.endswith("Verifier")),
                                                                          )
        
        commands += DynamicPluginArchitecture.CreateRegistrationStatements( "DEVELOPMENT_ENVIRONMENT_TEST_PARSERS",
                                                                            os.path.join(_script_dir, "Scripts", "TestParsers"),
                                                                            lambda fullpath, name, ext: ext == ".py" and name.endswith("TestParser"),
                                                                          )
        
        commands += DynamicPluginArchitecture.CreateRegistrationStatements( "DEVELOPMENT_ENVIRONMENT_CODE_COVERAGE_EXTRACTORS",
                                                                            os.path.join(_script_dir, "Scripts", "CodeCoverageExtractors"),
                                                                            lambda fullpath, name, ext: ext == ".py" and name.endswith("CodeCoverageExtractor"),
                                                                          )
        
        commands += DynamicPluginArchitecture.CreateRegistrationStatements( "DEVELOPMENT_ENVIRONMENT_CODE_COVERAGE_VALIDATORS",
                                                                            os.path.join(_script_dir, "Scripts", "CodeCoverageValidators"),
                                                                            lambda fullpath, name, ext: ext == ".py" and name.endswith("CodeCoverageValidator"),
                                                                          )
        
        commands += DelayExecute(_DelayExecute)
    
    return commands

# ---------------------------------------------------------------------------
def CustomScriptExtractors(environment):
    """
    Returns a list of additional dirs to search and a dictionary
    that contains lookup functionality organized by file extension.
    """

    # ---------------------------------------------------------------------------
    def PythonWrapper(script_filename):
        # <Redefining name> pylint: disable = W0621
        # <Reimport> pylint: disable = W0404
        import os

        if os.path.basename(script_filename) == "__init__.py":
            return

        return [ environment.Execute('python "{script}" {all_args}'.format( script=script_filename,
                                                                            all_args=environment.AllArgumentsScriptVariable,
                                                                          )),
               ]

    # ---------------------------------------------------------------------------
    def PythonDocs(script_filename):
        import six

        from CommonEnvironment.StreamDecorator import StreamDecorator
        
        try:
            co = compile(open(script_filename, "rb").read(), script_filename, "exec")
            
            if co and co.co_consts and isinstance(co.co_consts[0], six.string_types) and co.co_consts[0][0] != '_':
                return StreamDecorator.Wrap(co.co_consts[0], 100)

        except:
            raise

    # ---------------------------------------------------------------------------
    def PowershellScriptWrapper(script_filename):
        return [ environment.Execute('Powershell -executionpolicy unrestricted "{script}" {all_args}'.format( script=script_filename,
                                                                                                              all_args=environment.AllArgumentsScriptVariable,
                                                                                                            )),
               ]

    # ---------------------------------------------------------------------------
    def EnvironmentScriptWrapper(script_filename):
        return [ environment.Call('{script} {all_args}'.format( script=script_filename,
                                                                all_args=environment.AllArgumentsScriptVariable,
                                                              )),
               ]

    # ---------------------------------------------------------------------------
    
    return { ".py" : ( PythonWrapper, PythonDocs, ),
             ".ps1" : PowershellScriptWrapper,
             environment.ScriptExtension : EnvironmentScriptWrapper,
           }

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
def _DelayExecute():
    return [ Shell.AugmentSet( "DEVELOPMENT_ENVIRONMENT_TESTER_CONFIGURATIONS",
                               [ "python-compiler-PyLint",
                                 "python-test_parser-Python",
                                 "python-code_coverage_extractor-Python",
                               ],
                             ),
           ]
