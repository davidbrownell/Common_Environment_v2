# ---------------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/11/2015 05:04:48 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import sys

from CommonEnvironment.Interface import *

from SimpleSchema.Observer import Observer

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

class Plugin(Observer):
    
    # ---------------------------------------------------------------------------
    # |
    # |  Public Properties
    # |
    # ---------------------------------------------------------------------------
    
    # ---------------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GenerateOutputFilenames(context):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GenerateCustomSettingsAndDefaults():
        # Generator that provides key/value tuples
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetAdditionalGeneratorItems(context):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def PostprocessContextItem(context):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Generate( simple_schema_code_generator,
                  invoke_reason,
                  input_filenames,
                  output_filenames,
                  name,
                  elements,
                  include_indexes,
                  status_stream,
                  output_stream,
                  **custom_settings_and_defaults
                ):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    # |
    # |  Protected Methods
    # |
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GetDerivedElements(element):
        assert element.polymorphic
        assert not element.Base

        derived_elements = []
        
        search = [ element, ]

        while search:
            item = search.pop(0)

            if item.DerivedElements:
                search.extend(item.DerivedElements)
                continue

            if item not in derived_elements:
                derived_elements.append(item)

        return derived_elements

    # ---------------------------------------------------------------------------
    @staticmethod
    def _GetAllChildren(element):
        children = []

        while element:
            for child in element.Children:
                if not child.IsDefinitionOnly:
                    children.append(child)
        
            element = element.Base

        return children

    