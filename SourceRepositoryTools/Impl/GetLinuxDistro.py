try:
    # Python 2
    import __builtin__
    print_ = getattr(__builtin__, "print")
except ImportError:
    # Python 3
    print_ = print
        
import platform

result = platform.dist()[0]
if result == "Debian":
    result = "Ubuntu"

print_(result)