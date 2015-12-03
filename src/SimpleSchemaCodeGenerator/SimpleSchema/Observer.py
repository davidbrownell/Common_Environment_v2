# ---------------------------------------------------------------------------
# |  
# |  Observer.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  10/05/2015 03:20:55 PM
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

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

class Observer(Interface):

    # ---------------------------------------------------------------------------
    # |  Public Types
    class ParseFlags(object):
        # Fundamental support
        SupportAttributes                   = 1
        SupportIncludeStatements            = SupportAttributes << 1
        SupportConfigDeclarations           = SupportIncludeStatements << 1
        
        SupportUnnamedDeclarations          = SupportConfigDeclarations << 1
        SupportUnnamedObjects               = SupportUnnamedDeclarations << 1
        SupportNamedDeclarations            = SupportUnnamedObjects << 1
        SupportNamedObjects                 = SupportNamedDeclarations << 1

        SupportRootDeclarations             = SupportNamedObjects << 1
        SupportRootObjects                  = SupportRootDeclarations << 1
        SupportChildDeclarations            = SupportRootObjects << 1
        SupportChildObjects                 = SupportChildDeclarations << 1

        SupportCustomTypes                  = SupportChildObjects << 1

        SupportAliases                      = SupportCustomTypes << 1
        SupportAugmentations                = SupportAliases << 1
        SupportSimpleObjects                = SupportAugmentations << 1
        
        # Parse behavior
        ResolveReferences                   = SupportSimpleObjects << 1

        # Multi-bit flags
        SupportDeclarations                 = SupportUnnamedDeclarations | SupportNamedDeclarations
        SupportObjects                      = SupportUnnamedObjects | SupportNamedObjects
        
    # ---------------------------------------------------------------------------
    # |  Public Properties
    @abstractproperty
    def Name(self):
        raise Exception("Abstract property")

    @abstractproperty
    def Flags(self):
        raise Exception("Abstract property")

    # ---------------------------------------------------------------------------
    # |  Public Methods
    @staticmethod
    @abstractmethod
    def GetExtensions():
        """Returns a list of extensions"""
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetRequiredMetadata(item_type, name):
        raise Exception("Abstract method")

    # ---------------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetOptionalMetadata(item_type, name):
        raise Exception("Abstract method")

# ---------------------------------------------------------------------------
@staticderived
class DefaultObserver(Observer):
    
    # ---------------------------------------------------------------------------
    # |  Public Properties
    Name                                    = ''
    Flags                                   = 0xFFFFFFFF

    # ---------------------------------------------------------------------------
    # |  Public Methods
    @staticmethod
    def GetExtensions():
        return []

    # ---------------------------------------------------------------------------
    @staticmethod
    def GetRequiredMetadata(item_type, name):
        return []

    # ---------------------------------------------------------------------------
    @staticmethod
    def GetOptionalMetadata(item_type, name):
        return []

    