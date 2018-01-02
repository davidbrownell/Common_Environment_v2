# ----------------------------------------------------------------------
# |  
# |  PluginBase.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2016-08-04 13:29:42
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2016-18.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import sys
import textwrap

from CommonEnvironment.Interface import *

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class Plugin(Interface):
    """\
    Abstract base class for plugins that can be used by a concrete CodeGeneratorBase 
    to perform actual generation activities.
    """

    # ----------------------------------------------------------------------
    # |  
    # |  Public Properties
    # |  
    # ----------------------------------------------------------------------
    @abstractproperty
    def Name(self):
        raise Exception("Abstract property")

    @abstractproperty
    def Description(self):
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    # |  
    # |  Public Methods
    # |  
    # ----------------------------------------------------------------------
    @staticmethod
    def GetPlugin(plugin_name):
        raise Exception("The implementation of this function is provided by the generator")

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def IsValidEnvironment():
        """Return False if the plugin is not valid within the active environment"""
        return True

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GenerateCustomSettingsAndDefaults():
        # Generator that provides key/value tuples
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def PreprocessCustomSettings(**kwargs):
        """\
        Opportunity for a derived class to extract custom settings prior to generation.
        This can be useful when settings are used to provide default metadata values or
        other action that happen globally before specific content information is generated.

        This represents a fairly exotic scenario, and it most casses settings can be 
        consumed directly within the Generate method.
        """
        return kwargs

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def GetAdditionalGeneratorItems(context):
        """\
        Return an item or string representing a plugin, where changes in those
        item(s) indicates that all content should be regenerated.
        """
        return []

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def PostprocessContextItem(context, pre_validate):
        """\
        Perform any custom modification to the context. This is called before
        and after validation.
        """
        return context

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def ValidateContextItem(context):
        """\
        Raise exceptions if the context item is not in an expected (or required)
        format.
        """
        pass

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GenerateOutputFilenames(context):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    # |  
    # |  Protected Methods
    # |  
    # ----------------------------------------------------------------------
    @staticmethod
    def _GenerateFileHeader( prefix='',
                             line_break="---------------------------------------------------------------------------",
                           ):
        return textwrap.dedent(
            """\
            {prefix}{line_break}
            {prefix}|
            {prefix}|  WARNING:
            {prefix}|  This file was generated; any local changes will be overwritten during 
            {prefix}|  future invocations of the generator!
            {prefix}|
            {prefix}{line_break}
            """).format( prefix=prefix,
                         line_break=line_break,
                       )

    