# ---------------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  11/25/2015 07:59:00 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
"""\
The distinction between Populate and Validate may seem arbitrary but is actually calculated.

Populate leverages ANTLR to populate Item objects via generated tokens; all operations are
relative to a single Item and have no contextual meaning other than the enforcement of the 
rules associated with the provided Observer.

Validate validates Item objects across itself and other Items within a collection.

Populate will never working with more than one atomic until within an Item at a single point
in time, where Validate will (potentially) work with many atomic untils within a single 
Item, or even Items in relationship to each other.
"""