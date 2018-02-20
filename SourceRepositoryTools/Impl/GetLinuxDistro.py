from __future__ import print_function
        
import platform

result = platform.dist()[0]
if result == "Debian":
    result = "Ubuntu"

print_(result)