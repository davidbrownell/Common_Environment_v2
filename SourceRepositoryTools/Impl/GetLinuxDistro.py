try:
    # Python 2
    import __builtin__
    print_ = getattr(__builtin__, "print")
except ImportError:
    # Python 3
    print_ = print
        
import platform

print_(platform.dist()[0])