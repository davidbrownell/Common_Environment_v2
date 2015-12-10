# ---------------------------------------------------------------------------
# |  
# |  Selector.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  12/09/2015 06:44:51 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""Contains selector functionality
"""

import os
import sys

import CommonEnvironment
from CommonEnvironment.Interface import *

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
class Selector(Interface):

    # ---------------------------------------------------------------------------
    def __init__( self,
                  selector_criteria,        # def Func(node) -> Bool
                  action=None,              # def Func(node)
                ):
        if not selector_criteria:
            raise Exception("Invalid argument - selector_criteria")

        self.Action                         = action
        self._selector_criteria             = selector_criteria
        
    # ---------------------------------------------------------------------------
    def Apply(self, element):
        child_selectors = []

        if self._selector_criteria(element):
            child_selectors.extend(self._GetChildSelectors(True))

            if self.Action:
                self.Action(element)

        else:
            child_selectors.extend(self._GetChildSelectors(False))

        return child_selectors

    # ---------------------------------------------------------------------------
    @staticmethod
    def ApplyAll(element_or_elements, selector_or_selectors):
        
        # ---------------------------------------------------------------------------
        def Impl(element, selectors):
            child_selectors = []

            for selector in selectors:
                child_selectors.extend(selector.Apply(element))

            if not child_selectors:
                return

            for child_element in getattr(element, "Children", []):
                Impl(child_element, child_selectors)
        
        # ---------------------------------------------------------------------------
        
        elements = element_or_elements if isinstance(element_or_elements, list) else [ element_or_elements, ]
        selectors = selector_or_selectors if isinstance(selector_or_selectors, list) else [ selector_or_selectors, ]
        
        for element in elements:
            Impl(element, selectors)
             
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    @abstractmethod
    def _GetChildSelectors(self, result):
        raise Exception("Abstract method")

# ---------------------------------------------------------------------------
class StandardSelector(Selector):

    # ---------------------------------------------------------------------------
    def __init__( self, 
                  selector_criteria,
                  child_selectors,
                  action=None,
                ):
        super(StandardSelector, self).__init__( selector_criteria=selector_criteria,
                                                action=action,
                                              )

        self._child_selectors               = child_selectors

    # ---------------------------------------------------------------------------
    def _GetChildSelectors(self, result):
        return self._child_selectors if result else []

# ---------------------------------------------------------------------------
class RepeatSelector(Selector):

    # ---------------------------------------------------------------------------
    def __init__( self, 
                  selector_criteria,
                  child_selectors,
                  min,
                  max=None,
                  action=None,
                ):
        super(WildcardSelector, self).__init__( selector_criteria=selector_criteria,
                                                action=action,
                                              )

        if not isinstance(min, int) or min < 0:
            raise Exception("Invalid argument - min")

        if max != None and ( not isinstance(max, int) or 
                             max < min
                           ):
            raise Exception("Invalid argument - max")

        self._child_selectors               = child_selectors
        self._min                           = min
        self._max                           = max

    # ---------------------------------------------------------------------------
    def _GetChildSelectors(self, result):
        child_selectors = []

        if self._min <= 1:
            child_selectors.extend(self._child_selectors)

        if self._max == None or self._max >= 1:
            child_selectors.append(WildcardSelector( self._child_selectors,
                                                     max(0, self._min - 1),
                                                     None if self._max == None else self._max - 1,
                                                     self.Action,
                                                   ))

        return child_selectors



